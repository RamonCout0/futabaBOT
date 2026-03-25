"""
cogs/aviso.py  ·  Avisos importantes formatados
f!aviso <mensagem>
f!aviso urgente <mensagem>
f!aviso embed <titulo> | <mensagem>
"""

from __future__ import annotations
import discord
from discord.ext import commands
from utils.embeds import aviso_embed, erro_embed, Icon, Color, SEP_ESTRELA, _now_ts, _footer
from utils.storage import get_store


class Aviso(commands.Cog, name="Avisos"):
    """Postagem de avisos formatados para a comunidade."""

    def __init__(self, bot: commands.AutoShardedBot):
        self.bot = bot
        self._store = get_store("config")

    def _cfg(self, guild_id):
        cog = self.bot.cogs.get("Configuração")
        return (lambda k: cog.get(guild_id, k)) if cog else (lambda k: None)

    async def _get_canal(self, guild):
        cfg = self._cfg(guild.id)
        cid = cfg("canal_avisos")
        if cid:
            ch = guild.get_channel(int(cid))
            if ch:
                return ch
        return None

    # ── Permissão: admin ou cargo gamedev ───────────────────────
    async def _pode(self, ctx: commands.Context) -> bool:
        if ctx.author.guild_permissions.administrator:
            return True
        cfg = self._cfg(ctx.guild.id)
        cid = cfg("cargo_gamedev")
        if cid:
            role = ctx.guild.get_role(int(cid))
            if role and role in ctx.author.roles:
                return True
        return False

    @commands.group(name="aviso", invoke_without_command=True)
    @commands.guild_only()
    async def aviso_group(self, ctx: commands.Context, *, mensagem: str = None):
        """Aviso simples: f!aviso <mensagem>"""
        if not mensagem:
            await ctx.send(embed=discord.Embed(
                title=f"{Icon.AVISO}  Comandos de Aviso",
                description=(
                    f"`f!aviso <mensagem>` — aviso padrão\n"
                    f"`f!aviso urgente <mensagem>` — aviso urgente\n"
                    f"`f!aviso embed <titulo> | <mensagem>` — aviso customizado\n"
                    f"`f!aviso rich` — aviso com formatação rica"
                ),
                color=Color.AVISO,
            ))
            return

        if not await self._pode(ctx):
            await ctx.send(embed=erro_embed("Sem permissão para enviar avisos.", self.bot.user))
            return

        em = aviso_embed(
            titulo="Aviso da Equipe",
            mensagem=mensagem,
            bot_user=self.bot.user,
        )

        canal = await self._get_canal(ctx.guild) or ctx.channel
        await canal.send(embed=em)
        if canal != ctx.channel:
            await ctx.message.add_reaction("✅")

    @aviso_group.command(name="urgente")
    @commands.guild_only()
    @commands.has_permissions(administrator=True)
    async def aviso_urgente(self, ctx: commands.Context, *, mensagem: str):
        """Aviso urgente com destaque visual."""
        em = aviso_embed(
            titulo="⚠️  Aviso Urgente",
            mensagem=mensagem,
            urgente=True,
            bot_user=self.bot.user,
        )
        canal = await self._get_canal(ctx.guild) or ctx.channel
        await canal.send(embed=em)
        if canal != ctx.channel:
            await ctx.message.add_reaction("✅")

    @aviso_group.command(name="embed")
    @commands.guild_only()
    async def aviso_embed_cmd(self, ctx: commands.Context, *, conteudo: str):
        """
        Aviso com título customizado.
        Uso: f!aviso embed Manutenção | O servidor estará offline às 23h.
        """
        if not await self._pode(ctx):
            await ctx.send(embed=erro_embed("Sem permissão.", self.bot.user))
            return

        if "|" not in conteudo:
            await ctx.send(embed=erro_embed("Use: `f!aviso embed <titulo> | <mensagem>`", self.bot.user))
            return

        titulo, _, mensagem = conteudo.partition("|")
        em = aviso_embed(
            titulo=titulo.strip(),
            mensagem=mensagem.strip(),
            bot_user=self.bot.user,
        )
        canal = await self._get_canal(ctx.guild) or ctx.channel
        await canal.send(embed=em)
        if canal != ctx.channel:
            await ctx.message.add_reaction("✅")

    @aviso_group.command(name="rich")
    @commands.guild_only()
    @commands.has_permissions(administrator=True)
    async def aviso_rich(self, ctx: commands.Context, *, texto: str):
        """
        Aviso com formatação máxima — bloco de código ANSI colorido.
        f!aviso rich <texto>
        """
        em = discord.Embed(
            title=f"{Icon.AVISO}  Comunicado Oficial",
            description=(
                "```ansi\n"
                "\u001b[1;33m╔══════════════════════════════════════╗\u001b[0m\n"
                "\u001b[1;33m║        COMUNICADO DA EQUIPE          ║\u001b[0m\n"
                "\u001b[1;33m╚══════════════════════════════════════╝\u001b[0m\n\n"
                f"\u001b[0;37m{texto}\u001b[0m\n"
                "```"
            ),
            color=Color.AVISO,
            timestamp=_now_ts(),
        )
        em.set_footer(**_footer(self.bot.user))

        canal = await self._get_canal(ctx.guild) or ctx.channel
        await canal.send(embed=em)
        if canal != ctx.channel:
            await ctx.message.add_reaction("✅")


async def setup(bot: commands.AutoShardedBot):
    await bot.add_cog(Aviso(bot))
