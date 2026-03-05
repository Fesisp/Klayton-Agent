# Sistema de Notificações - PokeBot Pro

## 📱 Visão Geral

O sistema de notificações envia alertas críticos (como **Shiny encontrado**) diretamente para seu celular via **Telegram** ou **Discord**, sem necessidade de WhatsApp ou aprovação manual.

### Canais Suportados

| Canal | Tipo | Custo | Facilidade | Status |
|-------|------|------|-----------|--------|
| **Telegram** | Bot Privado | Grátis | ⭐⭐⭐⭐⭐ | ✅ Recomendado |
| **Discord** | Webhook | Grátis | ⭐⭐⭐⭐ | ✅ Alternativa |

---

## 🚀 Configuração Telegram (RECOMENDADO)

### Passo 1: Criar o Bot no BotFather

1. Abra o **Telegram**
2. Procure por `@BotFather` (usuário oficial do Telegram)
3. Inicie a conversa com `/start`
4. Digite: `/newbot`
5. Escolha um nome para o bot (ex: `PokeBot Notifier`)
6. Escolha um username (deve terminar com `bot`, ex: `pokebot_notifier_bot`)
7. **Copie o TOKEN recebido** (algo como `123456:ABC-DEF1234ghIkl-zyx57W2v1u123ew11`)

### Passo 2: Obter seu Chat ID

1. No Telegram, procure por `@GetIDs Bot` (ou `@userinfobot`)
2. Inicie a conversa
3. Digite `/my_id`
4. **Copie o número recebido** (seu Chat ID)

### Passo 3: Atualizar config/settings.yaml

```yaml
notifications:
  # Cole o TOKEN do bot que você recebeu do BotFather
  telegram_bot_token: "123456:ABC-DEF1234ghIkl-zyx57W2v1u123ew11"
  
  # Cole seu Chat ID pessoal
  telegram_chat_id: "987654321"
  
  # Deixe vazio se não usar Discord
  discord_webhook_url: ""
```

### Passo 4: Testar

```python
from src.utils.notifier import NotificationManager
import yaml

with open('config/settings.yaml') as f:
    config = yaml.safe_load(f)

notifier = NotificationManager(config)
notifier.notify_all("Teste de notificação Telegram!")
```

Você deve receber uma mensagem no Telegram em segundos! ✅

---

## 💬 Configuração Discord (ALTERNATIVA)

### Passo 1: Criar Webhook no Discord

1. Abra seu **servidor Discord**
2. Clique com **botão direito** no canal (ex: `#pokebbot-alerts`)
3. Selecione **Editar Canal**
4. Vá para **Integrações** → **Webhooks**
5. Clique em **Novo Webhook**
6. Dê um nome (ex: `PokeBot`)
7. Clique em **Copiar URL do Webhook**

### Passo 2: Atualizar config/settings.yaml

```yaml
notifications:
  # Deixe vazio se não usar Telegram
  telegram_bot_token: ""
  telegram_chat_id: ""
  
  # Cole a URL completa do webhook
  discord_webhook_url: "https://discord.com/api/webhooks/1234567890/abcdefghijklmnopqrstuvwxyz"
```

### Passo 3: Testar

Você deve ver mensagens aparecendo no canal Discord! ✅

---

## 📋 Exemplos de Uso

### Notificação de Shiny

```python
# Em handle_shiny() do BotController:
self.notifier.notify_shiny_found("Pikachu", "Viridian Forest")
```

**Resultado:**
```
✨ SHINY ENCONTRADO! ✨
Pokémon: PIKACHU
Local: Viridian Forest
Status: Bot pausado aguardando ação
```

### Notificação de Status de Batalha

```python
self.notifier.notify_battle_status("Pikachu", "Tentacruel", 85.5, 42.3)
```

**Resultado:**
```
⚔️ Status de Batalha
Seu: Pikachu (85.5%)
Inimigo: Tentacruel (42.3%)
```

### Notificação de Erro

```python
self.notifier.notify_error("Falha ao capturar HP", "handle_battle()")
```

**Resultado:**
```
❌ ERRO: Falha ao capturar HP
📍 Contexto: handle_battle()
```

---

## ⚙️ Configuração Avançada

### Desabilitar um Canal

Para desabilitar **Telegram** mas manter **Discord**:
```yaml
notifications:
  telegram_bot_token: ""      # Deixar vazio
  telegram_chat_id: ""         # Deixar vazio
  discord_webhook_url: "https://..."
```

### Timeout de Conexão

Se sua conexão de internet é lenta, as notificações têm timeout de **10 segundos**. Isso é suficiente para:
- Redes Wi-Fi normais ✅
- Conexões móveis ✅
- Redes muito lentas (2G) ⚠️ Pode falhar

---

## 🆘 Troubleshooting

### Erro: "Telegram não configurado"

**Solução:** Você deixou `telegram_bot_token` ou `telegram_chat_id` vazios.
- Volte para **Passo 1 e 2** da configuração Telegram

### Erro: "Token inválido"

**Solução:** O token foi copiado incorretamente do BotFather.
- Teste o token manualmente:
  ```bash
  curl -X GET "https://api.telegram.org/bot<SEU_TOKEN>/getMe"
  ```
- Se retornar erro 404, o token é inválido

### Erro: "Chat ID inválido"

**Solução:** O Chat ID foi copiado incorretamente de `@GetIDs Bot`.
- Certifique-se que é apenas **números** (ex: `987654321`)
- Não copie texto adicional

### Notificações não chegam mas sem erro

**Possíveis causas:**
1. Seu bot do Telegram está **bloqueado** - Inicie conversa com seu bot antes de usar
2. Firewall/Proxy bloqueando - Tente com VPN ou rede diferente
3. Token expirado - Delete e recrie o bot no BotFather

### Discord retorna "401 Unauthorized"

**Solução:** A URL do webhook expirou ou foi deletada.
- Crie um novo webhook no canal Discord

---

## 📝 Logs e Debugging

Para ver logs detalhados de notificações:

```python
# Em src/core/bot_controller.py ou main.py
from loguru import logger

# Aumentar nível de verbosidade
logger.remove()  # Remove handler padrão
logger.add("logs/pokebot.log", level="DEBUG")
logger.add(lambda msg: print(msg, end=""), level="DEBUG")
```

Procure por linhas como:
```
✅ Notificação Telegram enviada com sucesso
✅ Notificação Discord enviada com sucesso
⚠️ Falha ao enviar notificação por QUALQUER canal
```

---

## 🔐 Segurança

### Tokens & URLs

- **Nunca** compartilhe seu `telegram_bot_token` ou `telegram_chat_id`
- **Nunca** compartilhe a URL do webhook Discord publicamente
- Se vazar, regenere imediatamente:
  - Telegram: `/revoke` no BotFather
  - Discord: Delete e crie novo webhook

### Privacy

- Mensagens são enviadas aos servidores Telegram/Discord
- Nenhuma informação é armazenada localmente no bot
- Use VPN se desejar privacidade adicional

---

## 📞 Suporte

Dúvidas? Procure por:
- `@BotFather` (Telegram) - Documentação oficial
- Discord Docs - Webhooks Guide
- Issues do repositório PokeBot

---

**Última atualização:** Março 2026  
**Status:** ✅ Funcional e Testado
