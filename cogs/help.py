"""
cogs/help.py  ·  Help personalizado e bonito
f!help  /  f!ajuda
"""

from __future__ import annotations
import discord
from discord.ext import commands
from utils.embeds import Icon, Color, SEP_ESTRELA, SEP_LINHA, _now_ts, _footer


HELP_PRINCIPAL = """
```ansi
\u001b[1;35m╔══════════════════════════════════════╗\u001b[0m
\u001b[1;35m║   FUTABA SAKURA  ·  Eventos Indie    ║\u001b[0m
\u001b[1;35m╚══════════════════════════════════════╝\u001b[0m
\u001b[0;37mBot de eventos para gamedevs indie BR\u001b[0m
```
"""


class Help(commands.Cog, name="Help"):
    """Ajuda e documentação da Futaba."""

    def __init__(self, bot: commands.AutoShardedBot):
        self.bot = bot

    @commands.command(name="help", aliases=["ajuda", "h", "?"])
    async def help_cmd(self, ctx: commands.Context, *, modulo: str = None):

        if modulo:
            await self._help_modulo(ctx, modulo.lower())
            return

        em = discord.Embed(
            title=f"{Icon.SPARKLE}  Futaba Sakura — Central de Ajuda",
            description=HELP_PRINCIPAL,
            color=Color.INFO,
            timestamp=_now_ts(),
        )

        em.add_field(
            name=f"{Icon.EVENTO}  Eventos  `f!help eventos`",
            value=(
                "`f!evento criar` `f!evento listar`\n"
                "`f!evento info` `f!evento ping` `f!evento deletar`"
            ),
            inline=False,
        )

        em.add_field(
            name=f"{Icon.GAMEJAM}  Game Jam  `f!help jam`",
            value=(
                "`f!jam criar` `f!jam ativa` `f!jam listar`\n"
                "`f!jam resultado` `f!jam encerrar`"
            ),
            inline=False,
        )

        em.add_field(
            name=f"{Icon.AVISO}  Avisos  `f!help avisos`",
            value=(
                "`f!aviso <msg>` `f!aviso urgente <msg>`\n"
                "`f!aviso embed <título> | <msg>` `f!aviso rich <msg>`"
            ),
            inline=False,
        )

        em.add_field(
            name=f"⚙️  Configuração  `f!help config`",
            value=(
                "`f!config set <chave> <valor>`\n"
                "`f!config show` `f!config reset`"
            ),
            inline=False,
        )

        em.add_field(
            name=SEP_LINHA,
            value=(
                f"{Icon.FOGUETE}  Prefixo padrão: `f!`\n"
                f"{Icon.INFO}  `f!help <módulo>` para detalhes"
            ),
            inline=False,
        )

        em.set_thumbnail(url=self.bot.user.display_avatar.url)
        em.set_footer(**_footer(self.bot.user))
        await ctx.send(embed=em)

    async def _help_modulo(self, ctx, modulo: str):
        pages = {
            "eventos": self._page_eventos,
            "jam":     self._page_jam,
            "avisos":  self._page_avisos,
            "config":  self._page_config,
        }
        fn = pages.get(modulo)
        if fn:
            await ctx.send(embed=fn())
        else:
            await ctx.send(embed=discord.Embed(
                description=f"{Icon.ERRO}  Módulo `{modulo}` não encontrado. Tente: `eventos`, `jam`, `avisos`, `config`.",
                color=0xED4245,
            ))

    def _page_eventos(self) -> discord.Embed:
        em = discord.Embed(
            title=f"{Icon.EVENTO}  Módulo: Eventos",
            color=Color.EVENTO,
            timestamp=_now_ts(),
        )
        cmds = [
            ("f!evento criar",          "Abre o wizard interativo para criar um evento passo a passo."),
            ("f!evento listar",         "Exibe todos os eventos ativos no servidor."),
            ("f!evento info <id>",      "Mostra detalhes completos de um evento pelo ID."),
            ("f!evento ping <id>",      "Re-posta o evento com menção ao cargo configurado."),
            ("f!evento deletar <id>",   "Remove um evento. Requer permissão `Gerenciar Eventos`."),
        ]
        for cmd, desc in cmds:
            em.add_field(name=f"`{cmd}`", value=desc, inline=False)
        em.set_footer(**_footer(self.bot.user))
        return em

    def _page_jam(self) -> discord.Embed:
        em = discord.Embed(
            title=f"{Icon.GAMEJAM}  Módulo: Game Jam",
            color=Color.GAMEJAM,
            timestamp=_now_ts(),
        )
        cmds = [
            ("f!jam criar",                              "Wizard completo para criar uma game jam com tema, regras, premiação e banner."),
            ("f!jam ativa",                              "Mostra a game jam em andamento."),
            ("f!jam listar",                             "Lista todas as jams (abertas, em andamento, encerradas)."),
            ("f!jam encerrar <id>",                      "Encerra uma jam. Requer `Gerenciar Eventos`."),
            ('f!jam resultado <id> "1º" "2º" "3º"',     "Posta o pódio final com menção ao cargo. Os argumentos entre aspas são os nomes/menções."),
        ]
        for cmd, desc in cmds:
            em.add_field(name=f"`{cmd}`", value=desc, inline=False)
        em.set_footer(**_footer(self.bot.user))
        return em

    def _page_avisos(self) -> discord.Embed:
        em = discord.Embed(
            title=f"{Icon.AVISO}  Módulo: Avisos",
            color=Color.AVISO,
            timestamp=_now_ts(),
        )
        cmds = [
            ("f!aviso <mensagem>",                    "Aviso padrão com formatação limpa."),
            ("f!aviso urgente <mensagem>",            "Aviso com destaque vermelho de urgência."),
            ("f!aviso embed <título> | <mensagem>",   "Aviso com título personalizado."),
            ("f!aviso rich <mensagem>",               "Aviso com bloco ANSI colorido — máximo impacto visual."),
        ]
        for cmd, desc in cmds:
            em.add_field(name=f"`{cmd}`", value=desc, inline=False)
        em.set_footer(**_footer(self.bot.user))
        return em

    def _page_config(self) -> discord.Embed:
        em = discord.Embed(
            title="⚙️  Módulo: Configuração",
            color=Color.NEUTRO,
            timestamp=_now_ts(),
        )
        em.add_field(
            name="`f!config set <chave> <valor>`",
            value="Define uma configuração. Requer Administrador.",
            inline=False,
        )
        em.add_field(
            name="`f!config show`",
            value="Exibe todas as configurações do servidor.",
            inline=False,
        )
        em.add_field(
            name="`f!config reset`",
            value="Reseta todas as configurações.",
            inline=False,
        )
        chaves = "\n".join([
            "`canal_eventos`   — canal para postar eventos",
            "`canal_gamejam`   — canal exclusivo para jams",
            "`canal_avisos`    — canal de avisos",
            "`cargo_gamedev`   — cargo que pode criar eventos",
            "`cargo_ping_jam`  — cargo mencionado em novas jams",
            "`cargo_ping_evt`  — cargo mencionado em novos eventos",
            "`banner_padrao`   — URL do banner padrão",
        ])
        em.add_field(name="Chaves disponíveis", value=chaves, inline=False)
        em.set_footer(**_footer(self.bot.user))
        return em


async def setup(bot: commands.AutoShardedBot):
    await bot.add_cog(Help(bot))
