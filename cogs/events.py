"""
cogs/events.py  ·  Agendamento e gerenciamento de Eventos
Comandos:
  f!evento criar  — wizard interativo
  f!evento listar — lista eventos ativos
  f!evento info <id>
  f!evento deletar <id>
  f!evento ping <id>  — re-posta menção
"""

from __future__ import annotations
import asyncio
import discord
from discord.ext import commands, tasks
from datetime import datetime, timezone
from typing import Optional
import uuid

from utils.embeds import (
    evento_embed, sucesso_embed, erro_embed, info_embed,
    Icon, Color, SEP_LINHA, SEP_ESTRELA,
)
from utils.storage import get_store


def _short_id() -> str:
    return uuid.uuid4().hex[:6].upper()


def _parse_dt(s: str) -> Optional[datetime]:
    """Tenta DD/MM/YYYY HH:MM ou DD/MM/YYYY."""
    for fmt in ("%d/%m/%Y %H:%M", "%d/%m/%Y"):
        try:
            dt = datetime.strptime(s.strip(), fmt)
            return dt.replace(tzinfo=timezone.utc)
        except ValueError:
            continue
    return None


def _fmt_dt(dt_str: str) -> str:
    """Converte ISO string → DD/MM/YYYY HH:MM."""
    try:
        dt = datetime.fromisoformat(dt_str)
        return dt.strftime("%d/%m/%Y às %H:%M UTC")
    except Exception:
        return dt_str


class Events(commands.Cog, name="Eventos"):
    """Agendamento e postagem de eventos da comunidade."""

    def __init__(self, bot: commands.AutoShardedBot):
        self.bot = bot
        self._store = get_store("events")
        self._check_reminders.start()

    def cog_unload(self):
        self._check_reminders.cancel()

    # ── Helpers ──────────────────────────────────────────────────
    def _cfg(self, guild_id: int):
        cog = self.bot.cogs.get("Configuração")
        if cog:
            return lambda k: cog.get(guild_id, k)
        return lambda k: None

    async def _get_canal(self, guild: discord.Guild, guild_id: int) -> Optional[discord.TextChannel]:
        cfg = self._cfg(guild_id)
        cid = cfg("canal_eventos")
        if cid:
            ch = guild.get_channel(int(cid))
            if ch:
                return ch
        return None

    def _guild_events(self, guild_id: int) -> dict:
        return self._store.get(str(guild_id), {})

    def _save_event(self, guild_id: int, eid: str, data: dict):
        gdata = self._guild_events(guild_id)
        gdata[eid] = data
        self._store.set(str(guild_id), gdata)

    def _delete_event(self, guild_id: int, eid: str):
        gdata = self._guild_events(guild_id)
        if eid in gdata:
            del gdata[eid]
            self._store.set(str(guild_id), gdata)

    # ── Wizard de criação ────────────────────────────────────────
    async def _ask(
        self,
        ctx: commands.Context,
        pergunta: str,
        timeout: float = 90.0,
        optional: bool = False,
    ) -> Optional[str]:
        prompt = f"{Icon.SPARKLE}  {pergunta}"
        if optional:
            prompt += "  *(envie `-` para pular)*"
        await ctx.send(embed=info_embed("📋 Criação de Evento", prompt, self.bot.user))

        def check(m):
            return m.author == ctx.author and m.channel == ctx.channel

        try:
            msg = await self.bot.wait_for("message", check=check, timeout=timeout)
            return None if (optional and msg.content.strip() == "-") else msg.content.strip()
        except asyncio.TimeoutError:
            await ctx.send(embed=erro_embed("Tempo esgotado. Criação cancelada.", self.bot.user))
            return "TIMEOUT"

    @commands.group(name="evento", invoke_without_command=True)
    @commands.guild_only()
    async def evento(self, ctx: commands.Context):
        await ctx.send(embed=info_embed(
            "Comandos de Evento",
            (
                f"{Icon.FOGUETE}  `f!evento criar` — wizard de criação\n"
                f"{Icon.CALENDARIO}  `f!evento listar` — ver eventos ativos\n"
                f"{Icon.INFO}  `f!evento info <id>` — detalhes\n"
                f"{Icon.AVISO}  `f!evento ping <id>` — re-enviar menção\n"
                f"{Icon.ERRO}  `f!evento deletar <id>` — remover"
            ),
            self.bot.user,
        ))

    @evento.command(name="criar")
    @commands.guild_only()
    async def evento_criar(self, ctx: commands.Context):
        """Wizard interativo para criar um evento."""

        # ── Cabeçalho do wizard ──────────────────────────────────
        em_intro = discord.Embed(
            title=f"{Icon.FOGUETE}  Criação de Evento",
            description=(
                "```ansi\n"
                "\u001b[1;34mVamos criar um evento incrível!\u001b[0m\n"
                f"{'─'*36}\n"
                "Responda cada pergunta no chat.\n"
                "Envie  \u001b[0;31mcancelar\u001b[0m  a qualquer momento.\n"
                "```"
            ),
            color=Color.EVENTO,
        )
        await ctx.send(embed=em_intro)

        def cancelou(val):
            return val in (None, "TIMEOUT") or val.lower() == "cancelar"

        # ── Perguntas ────────────────────────────────────────────
        titulo = await self._ask(ctx, "Qual o **título** do evento?")
        if cancelou(titulo): return

        descricao = await self._ask(ctx, "**Descrição** do evento (pode ser longa):")
        if cancelou(descricao): return

        data_inicio = await self._ask(ctx, f"{Icon.CALENDARIO}  **Data de início** (DD/MM/AAAA HH:MM):")
        if cancelou(data_inicio): return
        dt_ini = _parse_dt(data_inicio)
        if not dt_ini:
            await ctx.send(embed=erro_embed("Formato de data inválido. Use `DD/MM/AAAA HH:MM`.", self.bot.user))
            return

        data_fim = await self._ask(ctx, f"{Icon.RELOGIO}  **Data de fim** (DD/MM/AAAA HH:MM):")
        if cancelou(data_fim): return
        dt_fim = _parse_dt(data_fim)
        if not dt_fim:
            await ctx.send(embed=erro_embed("Formato de data inválido.", self.bot.user))
            return

        local = await self._ask(ctx, f"{Icon.LINK}  **Local / link** (padrão: Discord):", optional=True)
        if local == "TIMEOUT": return
        if not local: local = "Servidor do Discord"

        banner = await self._ask(ctx, f"{Icon.TEMA}  **URL do banner** (imagem):", optional=True)
        if banner == "TIMEOUT": return

        link_insc = await self._ask(ctx, f"{Icon.INSCRICAO}  **Link de inscrição**:", optional=True)
        if link_insc == "TIMEOUT": return

        vagas = await self._ask(ctx, f"{Icon.EQUIPE}  **Número de vagas** (ex: 50, Ilimitado):", optional=True)
        if vagas == "TIMEOUT": return

        # ── Salvar e postar ──────────────────────────────────────
        eid = _short_id()
        event_data = {
            "titulo":       titulo,
            "descricao":    descricao,
            "data_inicio":  dt_ini.isoformat(),
            "data_fim":     dt_fim.isoformat(),
            "local":        local,
            "banner_url":   banner,
            "link_inscricao": link_insc,
            "vagas":        vagas,
            "criado_por":   str(ctx.author.id),
            "criado_em":    datetime.now(tz=timezone.utc).isoformat(),
            "ativo":        True,
        }
        self._save_event(ctx.guild.id, eid, event_data)
        await self._store.save()

        em = evento_embed(
            titulo=titulo,
            descricao=descricao,
            data_inicio=_fmt_dt(dt_ini.isoformat()),
            data_fim=_fmt_dt(dt_fim.isoformat()),
            local=local,
            banner_url=banner,
            link_inscricao=link_insc,
            vagas=vagas,
            organizador=ctx.author.mention,
            bot_user=self.bot.user,
        )
        em.set_author(name=f"ID do evento: {eid}", icon_url=ctx.author.display_avatar.url)

        # Tentar postar no canal configurado
        canal = await self._get_canal(ctx.guild, ctx.guild.id)
        cfg = self._cfg(ctx.guild.id)
        ping_role = cfg("cargo_ping_evt")
        content = f"<@&{ping_role}>" if ping_role else None

        destino = canal or ctx.channel
        msg = await destino.send(content=content, embed=em)

        # Salvar ID da mensagem para edições futuras
        event_data["msg_id"]    = str(msg.id)
        event_data["canal_id"]  = str(destino.id)
        self._save_event(ctx.guild.id, eid, event_data)
        await self._store.save()

        if canal and canal != ctx.channel:
            await ctx.send(embed=sucesso_embed(
                f"Evento **{titulo}** criado com ID `{eid}` e postado em {canal.mention}!",
                self.bot.user,
            ))

    @evento.command(name="listar")
    @commands.guild_only()
    async def evento_listar(self, ctx: commands.Context):
        """Lista eventos ativos deste servidor."""
        gdata = self._guild_events(ctx.guild.id)
        ativos = {k: v for k, v in gdata.items() if v.get("ativo")}

        if not ativos:
            await ctx.send(embed=info_embed("Nenhum evento", "Sem eventos ativos no momento.", self.bot.user))
            return

        linhas = []
        for eid, ev in list(ativos.items())[:10]:
            dt = _fmt_dt(ev["data_inicio"])
            linhas.append(f"`{eid}`  {Icon.EVENTO}  **{ev['titulo']}**\n{Icon.CALENDARIO}  {dt}")

        await ctx.send(embed=info_embed(
            f"{Icon.CALENDARIO}  Eventos Ativos ({len(ativos)})",
            "\n\n".join(linhas),
            self.bot.user,
        ))

    @evento.command(name="info")
    @commands.guild_only()
    async def evento_info(self, ctx: commands.Context, eid: str):
        gdata = self._guild_events(ctx.guild.id)
        ev = gdata.get(eid.upper())
        if not ev:
            await ctx.send(embed=erro_embed(f"Evento `{eid}` não encontrado.", self.bot.user))
            return

        em = evento_embed(
            titulo=ev["titulo"],
            descricao=ev["descricao"],
            data_inicio=_fmt_dt(ev["data_inicio"]),
            data_fim=_fmt_dt(ev["data_fim"]),
            local=ev.get("local", "Discord"),
            banner_url=ev.get("banner_url"),
            link_inscricao=ev.get("link_inscricao"),
            vagas=ev.get("vagas"),
            bot_user=self.bot.user,
        )
        em.set_author(name=f"ID: {eid}")
        await ctx.send(embed=em)

    @evento.command(name="deletar")
    @commands.guild_only()
    @commands.has_permissions(manage_events=True)
    async def evento_deletar(self, ctx: commands.Context, eid: str):
        gdata = self._guild_events(ctx.guild.id)
        eid = eid.upper()
        if eid not in gdata:
            await ctx.send(embed=erro_embed(f"Evento `{eid}` não encontrado.", self.bot.user))
            return
        self._delete_event(ctx.guild.id, eid)
        await self._store.save()
        await ctx.send(embed=sucesso_embed(f"Evento `{eid}` removido.", self.bot.user))

    @evento.command(name="ping")
    @commands.guild_only()
    @commands.has_permissions(manage_events=True)
    async def evento_ping(self, ctx: commands.Context, eid: str):
        """Re-envia o embed do evento com menção de cargo."""
        gdata = self._guild_events(ctx.guild.id)
        ev = gdata.get(eid.upper())
        if not ev:
            await ctx.send(embed=erro_embed(f"Evento `{eid}` não encontrado.", self.bot.user))
            return

        em = evento_embed(
            titulo=ev["titulo"],
            descricao=ev["descricao"],
            data_inicio=_fmt_dt(ev["data_inicio"]),
            data_fim=_fmt_dt(ev["data_fim"]),
            local=ev.get("local", "Discord"),
            banner_url=ev.get("banner_url"),
            link_inscricao=ev.get("link_inscricao"),
            vagas=ev.get("vagas"),
            bot_user=self.bot.user,
        )
        em.set_author(name=f"🔔 Lembrete  ·  ID: {eid}")

        cfg = self._cfg(ctx.guild.id)
        ping_role = cfg("cargo_ping_evt")
        content = f"<@&{ping_role}> {Icon.RELOGIO}  **Lembrete de Evento!**" if ping_role else None
        await ctx.send(content=content, embed=em)

    # ── Loop de lembretes automáticos ────────────────────────────
    @tasks.loop(minutes=30)
    async def _check_reminders(self):
        now = datetime.now(tz=timezone.utc)
        all_data = self._store.all()
        for guild_id_str, gdata in all_data.items():
            for eid, ev in gdata.items():
                if not ev.get("ativo"):
                    continue
                try:
                    dt_ini = datetime.fromisoformat(ev["data_inicio"])
                    diff   = (dt_ini - now).total_seconds()
                    # Lembrete 1 hora antes
                    if 3300 < diff < 3900 and not ev.get("lembrete_1h"):
                        await self._send_reminder(int(guild_id_str), eid, ev, "1 hora")
                        ev["lembrete_1h"] = True
                        self._save_event(int(guild_id_str), eid, ev)
                        await self._store.save()
                    # Marcar como inativo após o fim
                    dt_fim = datetime.fromisoformat(ev["data_fim"])
                    if now > dt_fim and ev.get("ativo"):
                        ev["ativo"] = False
                        self._save_event(int(guild_id_str), eid, ev)
                        await self._store.save()
                except Exception:
                    pass

    async def _send_reminder(self, guild_id: int, eid: str, ev: dict, tempo: str):
        guild = self.bot.get_guild(guild_id)
        if not guild:
            return
        canal = await self._get_canal(guild, guild_id)
        if not canal:
            return

        cfg = self._cfg(guild_id)
        ping_role = cfg("cargo_ping_evt")
        content = f"<@&{ping_role}> {Icon.RELOGIO}  **Começa em {tempo}!**" if ping_role else None
        em = evento_embed(
            titulo=ev["titulo"],
            descricao=ev["descricao"],
            data_inicio=_fmt_dt(ev["data_inicio"]),
            data_fim=_fmt_dt(ev["data_fim"]),
            local=ev.get("local", "Discord"),
            bot_user=self.bot.user,
        )
        em.set_author(name=f"⏰  Lembrete Automático  ·  {tempo} restante")
        await canal.send(content=content, embed=em)

    @_check_reminders.before_loop
    async def _before_reminders(self):
        await self.bot.wait_until_ready()


async def setup(bot: commands.AutoShardedBot):
    await bot.add_cog(Events(bot))
