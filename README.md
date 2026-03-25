# 🌸 Futaba Sakura — Bot de Eventos Indie

> Bot de Discord para agendamento de eventos, avisos e Game Jams  
> Feito para a comunidade brasileira de gamedevs indie

---

## ✨ Funcionalidades

| Módulo | Comandos | Descrição |
|--------|----------|-----------|
| 🎮 Eventos | `f!evento criar/listar/info/ping/deletar` | Wizard interativo + lembretes automáticos |
| 🏆 Game Jam | `f!jam criar/ativa/listar/resultado/encerrar` | Embeds visuais com pódio e premiação |
| 📢 Avisos | `f!aviso / urgente / embed / rich` | Formatação ANSI + blocos decorativos |
| ⚙️ Config | `f!config set/show/reset` | Configuração por servidor |
| ❓ Help | `f!help [módulo]` | Ajuda detalhada por módulo |

---

## 🚀 Deploy no ShardCloud

1. Faça upload da pasta `futaba/` no painel do ShardCloud
2. Defina a variável de ambiente `DISCORD_TOKEN` no painel
3. Defina o arquivo de entrada como `start.py`
4. Python version: **3.11+**
5. Clique em Deploy ✅

**Dependências:**
```
discord.py>=2.4.0
```
*(Instala automaticamente via `requirements.txt`)*

---

## ⚙️ Configuração Inicial

Após o bot entrar no servidor, use como admin:

```
f!config set canal_eventos   <ID do canal>
f!config set canal_gamejam   <ID do canal>
f!config set canal_avisos    <ID do canal>
f!config set cargo_ping_jam  <ID do cargo>
f!config set cargo_ping_evt  <ID do cargo>
f!config set cargo_gamedev   <ID do cargo>
```

---

## 🏆 Criando uma Game Jam

```
f!jam criar
```
O wizard irá perguntar:
- Nome e edição
- Tema
- Descrição
- Data de início e fim
- Premiação
- Regras (separadas por `;`)
- Tamanho da equipe
- Link do itch.io
- Banner (URL de imagem)

Para postar o resultado com pódio:
```
f!jam resultado JAM-XXXXX "Nome do 1º" "Nome do 2º" "Nome do 3º"
```

---

## 📁 Estrutura

```
futaba/
├── futaba.py          # Entry point + criação do bot
├── start.py           # Compatível ShardCloud
├── requirements.txt
├── .env.example
├── cogs/
│   ├── events.py      # Módulo de eventos
│   ├── gamejam.py     # Módulo de game jams
│   ├── aviso.py       # Módulo de avisos
│   ├── config.py      # Configuração por servidor
│   └── help.py        # Help customizado
└── utils/
    ├── embeds.py      # Biblioteca visual (cores, ícones, builders)
    └── storage.py     # Persistência JSON leve (economia de RAM)
```

---

## 💾 Economia de RAM

- `max_messages=None` — sem cache de mensagens
- `chunk_guilds_at_startup=False` — sem carregamento de membros
- `MemberCacheFlags.none()` — sem cache de membros
- `Intents` mínimos — apenas o necessário
- Storage JSON com lazy-load e flush assíncrono

---

## 🔒 Permissões necessárias no Discord

- `Send Messages`
- `Embed Links`
- `Read Message History`
- `Add Reactions`
- `Mention Everyone` *(para pings de cargo)*

---

*Futaba Sakura · Gatuno de Estrelas*
