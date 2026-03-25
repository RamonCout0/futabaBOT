"""
cogs/config.py  ·  Configuração do servidor
f!config set <chave> <valor>
f!config show
"""

from __future__ import annotations
import discord
from discord.ext import commands
from utils.storage import get_store
from utils.embeds import sucesso_embed, erro_embed, info_embed, SEP_LINHA, Icon


# Chaves de configuração disponíveis
CONFIG_KEYS = {
    "canal_eventos":   "ID do canal onde eventos serão postados",
    "canal_gamejam":   "ID do canal exclusivo para game jams",
    "canal_avisos":    "ID do canal de avisos importantes",
    "cargo_gamedev":   "ID do cargo que pode criar eventos (além de admins)",
    "cargo_ping_jam":  "ID do cargo mencionado em novos game jams",
    "cargo_ping_evt":  "ID do cargo mencionado em novos eventos",
    "banner_padrao":   "URL do banner padrão para eventos sem imagem",
    "prefix":          "Prefixo do bot neste servidor (padrão: f!)",
}


class Config(commands.Cog, name="Configuração"):
    """Configura a Futaba para o seu servidor."""

    def __init__(self, bot: commands.AutoShardedBot):
        self.bot = bot
        self._cfg = get_store("config")

    def _guild_cfg(self, guild_id: int) -> dict:
        return self._cfg.get(str(guild_id), {})

    def _save_guild(self, guild_id: int, data: dict) -> None:
        self._cfg.set(str(guild_id), data)

    # ── Permissão ────────────────────────────────────────────────
    def _is_admin(self, ctx: commands.Context) -> bool:
        return ctx.author.guild_permissions.administrator

    # ── Comandos ─────────────────────────────────────────────────
    @commands.group(name="config", invoke_without_command=True)
    @commands.guild_only()
    async def config_group(self, ctx: commands.Context):
        await ctx.send(embed=erro_embed(
            "Use `f!config set <chave> <valor>` ou `f!config show`.",
            self.bot.user,
        ))

    @config_group.command(name="set")
    @commands.guild_only()
    @commands.has_permissions(administrator=True)
    async def cfg_set(self, ctx: commands.Context, chave: str, *, valor: str):
        if chave not in CONFIG_KEYS:
            keys = "\n".join(f"`{k}` — {v}" for k, v in CONFIG_KEYS.items())
            await ctx.send(embed=erro_embed(
                f"Chave inválida. Chaves disponíveis:\n\n{keys}",
                self.bot.user,
            ))
            return

        data = self._guild_cfg(ctx.guild.id)
        data[chave] = valor
        self._save_guild(ctx.guild.id, data)
        await self._cfg.save()

        await ctx.send(embed=sucesso_embed(
            f"**{chave}** definido como `{valor}`",
            self.bot.user,
        ))

    @config_group.command(name="show")
    @commands.guild_only()
    @commands.has_permissions(administrator=True)
    async def cfg_show(self, ctx: commands.Context):
        data = self._guild_cfg(ctx.guild.id)
        if not data:
            await ctx.send(embed=info_embed(
                "Configuração vazia",
                "Nenhuma configuração definida ainda. Use `f!config set`.",
                self.bot.user,
            ))
            return

        linhas = "\n".join(f"{Icon.ESTRELA}  **{k}**: `{v}`" for k, v in data.items())
        await ctx.send(embed=info_embed("Configuração atual", linhas, self.bot.user))

    @config_group.command(name="reset")
    @commands.guild_only()
    @commands.has_permissions(administrator=True)
    async def cfg_reset(self, ctx: commands.Context):
        self._cfg.delete(str(ctx.guild.id))
        await self._cfg.save()
        await ctx.send(embed=sucesso_embed("Configuração resetada.", self.bot.user))

    # ── Helper global ────────────────────────────────────────────
    def get(self, guild_id: int, chave: str) -> str | None:
        return self._guild_cfg(guild_id).get(chave)


async def setup(bot: commands.AutoShardedBot):
    await bot.add_cog(Config(bot))
