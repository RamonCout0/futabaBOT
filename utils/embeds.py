"""
utils/embeds.py  ·  Biblioteca visual da Futaba Sakura
Todos os embeds do bot passam por aqui — garante consistência.
"""

from __future__ import annotations
import discord
from datetime import datetime, timezone
from typing import Optional


# ═══════════════════════════  PALETA  ═══════════════════════════
class Color:
    """Cores principais da Futaba."""
    EVENTO    = 0x5865F2   # azul discord  — eventos gerais
    GAMEJAM   = 0xFF4B6E   # rosa vibrante — game jam
    AVISO     = 0xFFC300   # âmbar         — avisos
    SUCESSO   = 0x57F287   # verde         — confirmações
    ERRO      = 0xED4245   # vermelho      — erros
    INFO      = 0x00B0F4   # ciano         — info / help
    NEUTRO    = 0x2B2D31   # fundo escuro  — neutro


# ═══════════════════════════  ÍCONES  ═══════════════════════════
class Icon:
    EVENTO      = "🎮"
    GAMEJAM     = "🏆"
    AVISO       = "📢"
    CALENDARIO  = "📅"
    RELOGIO     = "⏰"
    PREMIACAO   = "🥇"
    TEMA        = "🎨"
    EQUIPE      = "👥"
    INSCRICAO   = "📝"
    LINK        = "🔗"
    REGRA       = "📜"
    SUCESSO     = "✅"
    ERRO        = "❌"
    INFO        = "ℹ️"
    CONFETE     = "🎊"
    FOGUETE     = "🚀"
    ESTRELA     = "⭐"
    FOGO        = "🔥"
    DIAMANTE    = "💎"
    CONTROLLER  = "🕹️"
    SPARKLE     = "✨"


# ═══════════════════  SEPARADORES DECORATIVOS  ══════════════════
SEP_LINHA    = "━" * 35
SEP_DUPLO    = "═" * 35
SEP_PONTO    = "· " * 17 + "·"
SEP_ESTRELA  = "✦ " + "─" * 31 + " ✦"


# ═══════════════════════  FOOTER PADRÃO  ════════════════════════
FOOTER_TEXTO = "Futaba Sakura  ·  Comunidade Indie BR"
FOOTER_ICON  = "https://cdn.discordapp.com/embed/avatars/0.png"  # fallback


def _footer(bot_user: Optional[discord.ClientUser] = None) -> dict:
    icon = bot_user.display_avatar.url if bot_user else FOOTER_ICON
    return {"text": FOOTER_TEXTO, "icon_url": icon}


def _now_ts() -> datetime:
    return datetime.now(tz=timezone.utc)


# ═══════════════════  VALIDAÇÃO DE URL DE IMAGEM  ════════════════
_IMG_EXTS = (".png", ".jpg", ".jpeg", ".gif", ".webp")

def _is_image_url(url: Optional[str]) -> bool:
    """Verifica se a URL parece ser um link direto de imagem."""
    if not url:
        return False
    u = url.lower().split("?")[0]   # ignora query string
    return any(u.endswith(ext) for ext in _IMG_EXTS)


# ════════════════════════  BUILDERS  ════════════════════════════

def evento_embed(
    *,
    titulo: str,
    descricao: str,
    data_inicio: str,
    data_fim: str,
    local: str = "Servidor do Discord",
    banner_url: Optional[str] = None,
    organizador: Optional[str] = None,
    vagas: Optional[str] = None,
    link_inscricao: Optional[str] = None,
    extras: Optional[list[tuple[str, str]]] = None,
    bot_user: Optional[discord.ClientUser] = None,
) -> discord.Embed:
    """Embed para eventos gerais."""

    desc = descricao

    em = discord.Embed(
        title=f"{Icon.EVENTO}  {titulo}",
        description=desc,
        color=Color.EVENTO,
        timestamp=_now_ts(),
    )

    if banner_url and _is_image_url(banner_url):
        em.set_image(url=banner_url)
        value=f"```\n{data_inicio}\n```",
        inline=True,
    )
    em.add_field(
        name=f"{Icon.RELOGIO}  Fim",
        value=f"```\n{data_fim}\n```",
        inline=True,
    )
    em.add_field(
        name=f"{Icon.LINK}  Local",
        value=f"```\n{local}\n```",
        inline=True,
    )

    if organizador:
        em.add_field(name=f"{Icon.ESTRELA}  Organizado por", value=organizador, inline=True)
    if vagas:
        em.add_field(name=f"{Icon.EQUIPE}  Vagas", value=f"```{vagas}```", inline=True)
    if link_inscricao:
        em.add_field(name=f"{Icon.INSCRICAO}  Inscrição", value=f"[Clique aqui]({link_inscricao})", inline=True)

    if extras:
        em.add_field(name=SEP_LINHA, value="", inline=False)
        for nome, valor in extras:
            em.add_field(name=nome, value=valor, inline=True)

    em.set_footer(**_footer(bot_user))
    return em


def gamejam_embed(
    *,
    nome: str,
    edicao: str,
    tema: str,
    descricao: str,
    data_inicio: str,
    data_fim: str,
    premiacao: str,
    regras: list[str],
    link_itch: Optional[str] = None,
    banner_url: Optional[str] = None,
    max_equipe: str = "1–4 pessoas",
    bot_user: Optional[discord.ClientUser] = None,
) -> discord.Embed:
    """Embed visual para Game Jams — o carro-chefe da Futaba."""

    # Regras: cada uma em linha própria com bullet, dentro de um code block
    regras_fmt = "```\n" + "\n".join(f"• {r}" for r in regras) + "\n```"

    desc = (
        f"```ansi\n"
        f"\u001b[1;35m{nome.upper()}\u001b[0m  ·  Edição {edicao}\n"
        f"{'─' * 38}\n"
        f"\u001b[0;36mTema:\u001b[0m  {tema}\n"
        f"```\n"
        f"{descricao}"
    )

    em = discord.Embed(
        title=f"{Icon.GAMEJAM}  {nome}  ·  {edicao}",
        description=desc,
        color=Color.GAMEJAM,
        timestamp=_now_ts(),
    )

    if banner_url and _is_image_url(banner_url):
        em.set_image(url=banner_url)
    em.add_field(
        name=f"{Icon.CALENDARIO}  Período",
        value=(
            f"```\n"
            f"▶  {data_inicio}\n"
            f"⏹  {data_fim}\n"
            f"```"
        ),
        inline=True,
    )
    em.add_field(
        name=f"{Icon.EQUIPE}  Equipe",
        value=f"```\n{max_equipe}\n```",
        inline=True,
    )
    em.add_field(
        name=f"{Icon.TEMA}  Tema",
        value=f"```\n{tema}\n```",
        inline=True,
    )

    # Premiação em destaque
    em.add_field(
        name=SEP_ESTRELA,
        value="\u200b",
        inline=False,
    )
    em.add_field(
        name=f"{Icon.PREMIACAO}  Premiação",
        value=(
            f"```ansi\n"
            f"\u001b[1;33m{premiacao}\u001b[0m\n"
            f"```"
        ),
        inline=False,
    )

    # Regras
    em.add_field(
        name=f"{Icon.REGRA}  Regras",
        value=regras_fmt,
        inline=False,
    )

    if link_itch:
        em.add_field(
            name=f"{Icon.INSCRICAO}  Submissão",
            value=f"[Envie seu jogo no itch.io ↗]({link_itch})",
            inline=False,
        )

    em.set_footer(**_footer(bot_user))
    return em


def aviso_embed(
    *,
    titulo: str,
    mensagem: str,
    urgente: bool = False,
    rodape_extra: Optional[str] = None,
    bot_user: Optional[discord.ClientUser] = None,
) -> discord.Embed:
    """Embed para avisos importantes."""

    prefixo = (
        f"```ansi\n\u001b[1;31m⚠  AVISO URGENTE\u001b[0m\n```\n"
        if urgente
        else f"```ansi\n\u001b[1;33m{Icon.AVISO}  AVISO\u001b[0m\n```\n"
    )

    em = discord.Embed(
        title=f"{Icon.AVISO}  {titulo}",
        description=prefixo + mensagem,
        color=Color.GAMEJAM if urgente else Color.AVISO,
        timestamp=_now_ts(),
    )

    if rodape_extra:
        em.set_footer(text=f"{FOOTER_TEXTO}  ·  {rodape_extra}")
    else:
        em.set_footer(**_footer(bot_user))

    return em


def sucesso_embed(texto: str, bot_user=None) -> discord.Embed:
    em = discord.Embed(
        description=f"{Icon.SUCESSO}  {texto}",
        color=Color.SUCESSO,
    )
    em.set_footer(**_footer(bot_user))
    return em


def erro_embed(texto: str, bot_user=None) -> discord.Embed:
    em = discord.Embed(
        description=f"{Icon.ERRO}  {texto}",
        color=Color.ERRO,
    )
    em.set_footer(**_footer(bot_user))
    return em


def info_embed(titulo: str, texto: str, bot_user=None) -> discord.Embed:
    em = discord.Embed(
        title=f"{Icon.INFO}  {titulo}",
        description=texto,
        color=Color.INFO,
        timestamp=_now_ts(),
    )
    em.set_footer(**_footer(bot_user))
    return em
