"""
╔══════════════════════════════════════════════════════════════╗
║          FUTABA SAKURA  ·  Bot de Eventos Indie              ║
║          Comunidade Brasileira de Gamedevs                   ║
║          Compatible com ShardCloud                           ║
╚══════════════════════════════════════════════════════════════╝
"""

import discord
from discord.ext import commands
import asyncio
import os
import sys
import logging

# ── Configuração de logging leve ────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="[%(asctime)s] %(levelname)s  %(name)s: %(message)s",
    datefmt="%H:%M:%S",
)
log = logging.getLogger("futaba")

# ── Intents mínimos necessários ─────────────────────────────────
intents = discord.Intents.none()
intents.guilds = True
intents.guild_messages = True
intents.message_content = True
intents.members = False   # desativado para economizar RAM


# ── Factory do bot com auto_sharding para ShardCloud ────────────
def create_bot() -> commands.AutoShardedBot:
    bot = commands.AutoShardedBot(
        command_prefix="f!",
        intents=intents,
        help_command=None,              # substituído pelo nosso
        max_messages=None,              # desliga cache de mensagens → menos RAM
        chunk_guilds_at_startup=False,  # não carrega members → menos RAM
        member_cache_flags=discord.MemberCacheFlags.none(),
    )
    return bot


bot = create_bot()


# ── Carga de cogs ────────────────────────────────────────────────
COGS = [
    "cogs.events",
    "cogs.gamejam",
    "cogs.aviso",
    "cogs.config",
    "cogs.help",
]


@bot.event
async def on_ready():
    log.info(f"✅  Futaba online como {bot.user} (shards: {bot.shard_count})")
    await bot.change_presence(
        activity=discord.Activity(
            type=discord.ActivityType.watching,
            name="🎮 game jams & eventos indie",
        )
    )


async def main():
    async with bot:
        for cog in COGS:
            try:
                await bot.load_extension(cog)
                log.info(f"  ↳ cog carregada: {cog}")
            except Exception as e:
                log.error(f"  ✗ falha ao carregar {cog}: {e}")

        token = os.environ.get("DISCORD_TOKEN")
        if not token:
            log.critical("DISCORD_TOKEN não definida. Abortando.")
            sys.exit(1)

        await bot.start(token)


if __name__ == "__main__":
    asyncio.run(main())
