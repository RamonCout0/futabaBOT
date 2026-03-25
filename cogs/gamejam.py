"""
cogs/gamejam.py  ·  Game Jam  — o carro-chefe visual da Futaba
Comandos:
  f!jam criar      — wizard completo de game jam
  f!jam ativa      — mostra jam em andamento
  f!jam listar     — lista todas as jams
  f!jam encerrar <id>
  f!jam resultado <id>  — posta resultado com pódio
"""

from __future__ import annotations
import asyncio
import discord
from discord.ext import commands, tasks
from datetime import datetime, timezone
import uuid

from utils.embeds import (
    gamejam_embed, sucesso_embed, erro_embed, info_embed,
    Icon, Color, SEP_ESTRELA, SEP_LINHA, _now_ts, _footer,
)
from utils.storage import get_store


def _short_id() -> str:
    return "JAM-" + uuid.uuid4().hex[:5].upper()


def _parse_dt(s: str):
    for fmt in ("%d/%m/%Y %H:%M", "%d/%m/%Y"):
        try:
            return datetime.strptime(s.strip(), fmt).replace(tzinfo=timezone.utc)
        except ValueError:
            continue
    return None


def _fmt_dt(iso: str) -> str:
    try:
        return datetime.fromisoformat(iso).strftime("%d/%m/%Y às %H:%M UTC")
    except Exception:
        return iso


# ── Embed de Resultado / Pódio ───────────────────────────────────
def podio_embed(
    *,
    jam_nome: str,
    jam_id: str,
    ouro: str,
    prata: str = None,
    bronze: str = None,
    mencoes: list[str] = None,
    bot_user=None,
) -> discord.Embed:

    desc_parts = [
        "```ansi\n"
        "\u001b[1;33m╔═══════════════════════════════════╗\u001b[0m\n"
        "\u001b[1;33m║         RESULTADO FINAL           ║\u001b[0m\n"
        "\u001b[1;33m╚═══════════════════════════════════╝\u001b[0m\n"
        "```",
    ]

    medalhas = [
        ("🥇  1º Lugar", ouro,   "\u001b[1;33m"),
        ("🥈  2º Lugar", prata,  "\u001b[1;37m"),
        ("🥉  3º Lugar", bronze, "\u001b[1;31m"),
    ]

    blocos = []
    for titulo, nome, cor_ansi in medalhas:
        if nome:
            blocos.append(
                f"```ansi\n{cor_ansi}{titulo}\u001b[0m\n"
                f"  {nome}\n```"
            )
    desc_parts.extend(blocos)

    if mencoes:
        lista = "\n".join(f"  {Icon.ESTRELA}  {m}" for m in mencoes)
        desc_parts.append(f"**Menções Honrosas**\n{lista}")

    em = discord.Embed(
        title=f"{Icon.CONFETE}  Resultado  ·  {jam_nome}",
        description="\n".join(desc_parts),
        color=0xFFD700,
        timestamp=_now_ts(),
    )
    em.set_author(name=f"ID: {jam_id}")
    em.set_footer(**_footer(bot_user))
    return em


class GameJam(commands.Cog, name="Game Jam"):
    """Cog exclusiva para criação e gerenciamento de Game Jams."""

    def __init__(self, bot: commands.AutoShardedBot):
        self.bot = bot
        self._store = get_store("gamejams")
        self._check_jams.start()

    def cog_unload(self):
        self._check_jams.cancel()

    # ── Helpers ──────────────────────────────────────────────────
    def _cfg(self, guild_id):
        cog = self.bot.cogs.get("Configuração")
        return (lambda k: cog.get(guild_id, k)) if cog else (lambda k: None)

    def _guild_jams(self, guild_id) -> dict:
        return self._store.get(str(guild_id), {})

    def _save_jam(self, guild_id, jid, data):
        gdata = self._guild_jams(guild_id)
        gdata[jid] = data
        self._store.set(str(guild_id), gdata)

    async def _get_canal(self, guild):
        cfg = self._cfg(guild.id)
        cid = cfg("canal_gamejam") or cfg("canal_eventos")
        if cid:
            ch = guild.get_channel(int(cid))
            if ch:
                return ch
        return None

    async def _ask(self, ctx, pergunta, timeout=90.0, optional=False):
        prompt = f"{Icon.SPARKLE}  {pergunta}"
        if optional:
            prompt += "  *(envie `-` para pular)*"
        await ctx.send(embed=info_embed("🏆 Criação de Game Jam", prompt, self.bot.user))
        def check(m):
            return m.author == ctx.author and m.channel == ctx.channel
        try:
            msg = await self.bot.wait_for("message", check=check, timeout=timeout)
            return None if (optional and msg.content.strip() == "-") else msg.content.strip()
        except asyncio.TimeoutError:
            await ctx.send(embed=erro_embed("Tempo esgotado.", self.bot.user))
            return "TIMEOUT"

    # ── Comandos ─────────────────────────────────────────────────
    @commands.group(name="jam", invoke_without_command=True)
    @commands.guild_only()
    async def jam(self, ctx: commands.Context):
        await ctx.send(embed=info_embed(
            "Comandos de Game Jam",
            (
                f"{Icon.FOGUETE}  `f!jam criar` — criar nova jam\n"
                f"{Icon.FOGO}  `f!jam ativa` — jam em andamento\n"
                f"{Icon.CALENDARIO}  `f!jam listar` — todas as jams\n"
                f"{Icon.PREMIACAO}  `f!jam resultado <id>` — pódio\n"
                f"{Icon.ERRO}  `f!jam encerrar <id>` — encerrar"
            ),
            self.bot.user,
        ))

    @jam.command(name="criar")
    @commands.guild_only()
    @commands.has_permissions(manage_events=True)
    async def jam_criar(self, ctx: commands.Context):
        """Wizard para criar uma Game Jam épica."""

        em_intro = discord.Embed(
            title=f"{Icon.GAMEJAM}  Nova Game Jam!",
            description=(
                "```ansi\n"
                "\u001b[1;35m╔═══════════════════════════════════╗\u001b[0m\n"
                "\u001b[1;35m║    CONFIGURAÇÃO DA GAME JAM       ║\u001b[0m\n"
                "\u001b[1;35m╚═══════════════════════════════════╝\u001b[0m\n"
                "\u001b[0;37mResponda as perguntas para criar\u001b[0m\n"
                "\u001b[0;37muma jam incrível para a comunidade!\u001b[0m\n"
                "```"
            ),
            color=Color.GAMEJAM,
        )
        await ctx.send(embed=em_intro)

        def can(v):
            return v in (None, "TIMEOUT") or v.lower() == "cancelar"

        nome = await self._ask(ctx, "**Nome** da Game Jam:")
        if can(nome): return

        edicao = await self._ask(ctx, "**Edição** (ex: 1ª, #3, 2024):")
        if can(edicao): return

        tema = await self._ask(ctx, f"{Icon.TEMA}  **Tema** da jam:")
        if can(tema): return

        descricao = await self._ask(ctx, "**Descrição** geral da jam:")
        if can(descricao): return

        data_inicio = await self._ask(ctx, f"{Icon.CALENDARIO}  **Início** (DD/MM/AAAA HH:MM):")
        if can(data_inicio): return
        dt_ini = _parse_dt(data_inicio)
        if not dt_ini:
            await ctx.send(embed=erro_embed("Formato inválido. Use `DD/MM/AAAA HH:MM`.", self.bot.user))
            return

        data_fim = await self._ask(ctx, f"{Icon.RELOGIO}  **Fim** (DD/MM/AAAA HH:MM):")
        if can(data_fim): return
        dt_fim = _parse_dt(data_fim)
        if not dt_fim:
            await ctx.send(embed=erro_embed("Formato inválido.", self.bot.user))
            return

        premiacao = await self._ask(ctx, f"{Icon.PREMIACAO}  **Premiação** (ex: R$500, Badge exclusivo):")
        if can(premiacao): return

        regras_raw = await self._ask(
            ctx,
            f"{Icon.REGRA}  **Regras** *(separe com `;`)*:\n"
            "Exemplo: `Jogo solo ou dupla; Assets originais; Tema obrigatório`"
        )
        if can(regras_raw): return
        regras = [r.strip() for r in regras_raw.split(";") if r.strip()]

        max_equipe = await self._ask(ctx, f"{Icon.EQUIPE}  **Tamanho máximo da equipe** (ex: 1–3):", optional=True)
        if max_equipe == "TIMEOUT": return
        if not max_equipe: max_equipe = "1–4 pessoas"

        link_itch = await self._ask(ctx, f"{Icon.LINK}  **Link itch.io** para submissão:", optional=True)
        if link_itch == "TIMEOUT": return

        banner = await self._ask(ctx, f"{Icon.TEMA}  **URL do banner** (imagem):", optional=True)
        if banner == "TIMEOUT": return

        # ── Salvar ───────────────────────────────────────────────
        jid = _short_id()
        jam_data = {
            "nome":        nome,
            "edicao":      edicao,
            "tema":        tema,
            "descricao":   descricao,
            "data_inicio": dt_ini.isoformat(),
            "data_fim":    dt_fim.isoformat(),
            "premiacao":   premiacao,
            "regras":      regras,
            "max_equipe":  max_equipe,
            "link_itch":   link_itch,
            "banner_url":  banner,
            "criado_por":  str(ctx.author.id),
            "status":      "aberta",  # aberta | andamento | encerrada
        }
        self._save_jam(ctx.guild.id, jid, jam_data)
        await self._store.save()

        # ── Postar embed ─────────────────────────────────────────
        em = gamejam_embed(
            nome=nome,
            edicao=edicao,
            tema=tema,
            descricao=descricao,
            data_inicio=_fmt_dt(dt_ini.isoformat()),
            data_fim=_fmt_dt(dt_fim.isoformat()),
            premiacao=premiacao,
            regras=regras,
            link_itch=link_itch,
            banner_url=banner,
            max_equipe=max_equipe,
            bot_user=self.bot.user,
        )
        em.set_author(name=f"ID: {jid}  ·  Criado por {ctx.author.display_name}",
                      icon_url=ctx.author.display_avatar.url)

        canal = await self._get_canal(ctx.guild)
        cfg = self._cfg(ctx.guild.id)
        ping = cfg("cargo_ping_jam")
        content = f"<@&{ping}> {Icon.FOGO}  **Nova Game Jam anunciada!**" if ping else f"{Icon.FOGO}  **Nova Game Jam anunciada!**"

        destino = canal or ctx.channel
        msg = await destino.send(content=content, embed=em)

        jam_data["msg_id"]   = str(msg.id)
        jam_data["canal_id"] = str(destino.id)
        self._save_jam(ctx.guild.id, jid, jam_data)
        await self._store.save()

        if canal and canal != ctx.channel:
            await ctx.send(embed=sucesso_embed(
                f"Game Jam **{nome}** criada com ID `{jid}` e postada em {canal.mention}!",
                self.bot.user,
            ))

    @jam.command(name="ativa")
    @commands.guild_only()
    async def jam_ativa(self, ctx: commands.Context):
        """Mostra a jam em andamento."""
        gdata = self._guild_jams(ctx.guild.id)
        ativas = {k: v for k, v in gdata.items() if v.get("status") in ("aberta", "andamento")}

        if not ativas:
            await ctx.send(embed=info_embed(
                "Sem Jam Ativa",
                "Nenhuma game jam em andamento no momento.\nFique ligado para a próxima! 👀",
                self.bot.user,
            ))
            return

        jid, jam = next(iter(ativas.items()))
        em = gamejam_embed(
            nome=jam["nome"],
            edicao=jam["edicao"],
            tema=jam["tema"],
            descricao=jam["descricao"],
            data_inicio=_fmt_dt(jam["data_inicio"]),
            data_fim=_fmt_dt(jam["data_fim"]),
            premiacao=jam["premiacao"],
            regras=jam["regras"],
            link_itch=jam.get("link_itch"),
            banner_url=jam.get("banner_url"),
            max_equipe=jam.get("max_equipe", "1–4 pessoas"),
            bot_user=self.bot.user,
        )
        em.set_author(name=f"ID: {jid}  ·  Status: {jam['status'].upper()}")
        await ctx.send(embed=em)

    @jam.command(name="listar")
    @commands.guild_only()
    async def jam_listar(self, ctx: commands.Context):
        gdata = self._guild_jams(ctx.guild.id)
        if not gdata:
            await ctx.send(embed=info_embed("Nenhuma jam", "Sem game jams registradas.", self.bot.user))
            return

        linhas = []
        status_icon = {"aberta": "🟢", "andamento": "🟡", "encerrada": "🔴"}
        for jid, j in list(gdata.items())[:10]:
            ic = status_icon.get(j.get("status", "aberta"), "⚪")
            linhas.append(f"`{jid}`  {ic}  **{j['nome']}** — {j['edicao']}\n{Icon.TEMA}  {j['tema']}")

        await ctx.send(embed=info_embed(
            f"{Icon.GAMEJAM}  Game Jams ({len(gdata)})",
            "\n\n".join(linhas),
            self.bot.user,
        ))

    @jam.command(name="encerrar")
    @commands.guild_only()
    @commands.has_permissions(manage_events=True)
    async def jam_encerrar(self, ctx: commands.Context, jid: str):
        gdata = self._guild_jams(ctx.guild.id)
        jid = jid.upper()
        if not jid.startswith("JAM-"):
            jid = "JAM-" + jid
        jam = gdata.get(jid)
        if not jam:
            await ctx.send(embed=erro_embed(f"Jam `{jid}` não encontrada.", self.bot.user))
            return
        jam["status"] = "encerrada"
        self._save_jam(ctx.guild.id, jid, jam)
        await self._store.save()
        await ctx.send(embed=sucesso_embed(f"Jam `{jid}` encerrada.", self.bot.user))

    @jam.command(name="resultado")
    @commands.guild_only()
    @commands.has_permissions(manage_events=True)
    async def jam_resultado(
        self,
        ctx: commands.Context,
        jid: str,
        ouro: str,
        prata: str = None,
        bronze: str = None,
    ):
        """
        Posta o resultado com pódio.
        Uso: f!jam resultado <ID> "Equipe Ouro" "Equipe Prata" "Equipe Bronze"
        """
        gdata = self._guild_jams(ctx.guild.id)
        jid = jid.upper()
        if not jid.startswith("JAM-"):
            jid = "JAM-" + jid
        jam = gdata.get(jid)
        if not jam:
            await ctx.send(embed=erro_embed(f"Jam `{jid}` não encontrada.", self.bot.user))
            return

        jam["status"] = "encerrada"
        self._save_jam(ctx.guild.id, jid, jam)
        await self._store.save()

        em = podio_embed(
            jam_nome=jam["nome"],
            jam_id=jid,
            ouro=ouro,
            prata=prata,
            bronze=bronze,
            bot_user=self.bot.user,
        )

        canal = await self._get_canal(ctx.guild)
        cfg = self._cfg(ctx.guild.id)
        ping = cfg("cargo_ping_jam")
        content = (
            f"<@&{ping}> {Icon.CONFETE}  **Resultado da {jam['nome']}!**"
            if ping else
            f"{Icon.CONFETE}  **Resultado da {jam['nome']}!**"
        )
        destino = canal or ctx.channel
        await destino.send(content=content, embed=em)

        if canal and canal != ctx.channel:
            await ctx.send(embed=sucesso_embed("Resultado postado!", self.bot.user))

    # ── Loop de status automático ────────────────────────────────
    @tasks.loop(minutes=15)
    async def _check_jams(self):
        now = datetime.now(tz=timezone.utc)
        for gid_str, gdata in self._store.all().items():
            changed = False
            for jid, jam in gdata.items():
                try:
                    dt_ini = datetime.fromisoformat(jam["data_inicio"])
                    dt_fim = datetime.fromisoformat(jam["data_fim"])
                    if jam["status"] == "aberta" and now >= dt_ini:
                        jam["status"] = "andamento"
                        changed = True
                    elif jam["status"] == "andamento" and now >= dt_fim:
                        jam["status"] = "encerrada"
                        changed = True
                except Exception:
                    pass
            if changed:
                self._store.set(gid_str, gdata)
                await self._store.save()

    @_check_jams.before_loop
    async def _before(self):
        await self.bot.wait_until_ready()


async def setup(bot: commands.AutoShardedBot):
    await bot.add_cog(GameJam(bot))
