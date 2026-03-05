# 🔐 Configuração de Segurança - PokeBot

## ⚠️ DADOS SENSÍVEIS PROTEGIDOS

Seu arquivo `config/settings.yaml` contém **credenciais sigilosas** (tokens Telegram, chat IDs, webhooks Discord) e **NÃO é commitado** no repositório Git.

```
.gitignore → ignora config/settings.yaml ✅
```

---

## 📋 Setup Inicial

### Passo 1: Copiar arquivo de exemplo

```bash
cd config/
cp settings.example.yaml settings.yaml
```

### Passo 2: Preencer credenciais

Edite `config/settings.yaml` e adicione:

```yaml
notifications:
  telegram_bot_token: "8572655546:AAEnpu9oX65UfW7FEV9zzHgmymZdC4_NSsw"  # Seu token
  telegram_chat_id: "2142471792"                                        # Seu chat ID
  discord_webhook_url: "https://discord.com/api/webhooks/..."          # Sua URL
```

### Passo 3: Verificar (IMPORTANTE)

Após editar, verifique que o arquivo está ignorado:

```bash
git status
```

**Esperado:** `config/settings.yaml` NÃO apareça na lista

**Se aparecer:** ⚠️ Ele foi commitado antes. Remova com:

```bash
git rm --cached config/settings.yaml
git commit -m "Remove sensitive settings.yaml from tracking"
git push
```

---

## 🚨 Se suas credenciais vazarem

### Telegram
1. Abra `@BotFather` no Telegram
2. Selecione seu bot
3. Escolha `/revoke` para gerar novo token
4. Atualize `settings.yaml`

### Discord
1. Vá ao canal → Integrações → Webhooks
2. Delete o webhook comprometido
3. Crie um novo webhook
4. Copie a nova URL para `settings.yaml`

---

## ✅ Arquivos Protegidos

| Arquivo | Status | Motivo |
|---------|--------|--------|
| `config/settings.yaml` | 🔒 Ignorado | Contém tokens/IDs |
| `config/settings.example.yaml` | ✅ Commitado | Template (sem dados) |
| `.gitignore` | ✅ Commitado | Define o que ignorar |
| `src/utils/notifier.py` | ✅ Commitado | Código público |

---

## 🔍 Verificar integridade

Para garantir que nenhum secret foi commitado:

```bash
# Procurar por possíveis tokens no histórico
git log --all -S "telegram_bot_token" --oneline

# Procurar por URLs de webhook
git log --all -S "discord.com/api/webhooks" --oneline
```

Se encontrar alguma coisa, execute:

```bash
# Remover arquivo do histórico (CUIDADO - reescreve histórico)
git filter-branch --tree-filter 'rm -f config/settings.yaml' HEAD
```

---

## 📝 Regras de Ouro

✅ **SEMPRE:**
- [ ] Use `settings.example.yaml` como referência
- [ ] Mantenha `settings.yaml` local (nunca commit)
- [ ] Verifique `.gitignore` contém `config/settings.yaml`

❌ **NUNCA:**
- [ ] Commite `settings.yaml` com credenciais reais
- [ ] Compartilhe tokens/IDs em issues/PRs
- [ ] Deixe credenciais em arquivos de código

---

## 🤖 Rotina de Segurança

**A cada nova credencial:**
1. Atualize apenas `config/settings.yaml` (ignorado)
2. Teste com `src/utils/notifier.py`
3. Verifique que `git status` não mostra `settings.yaml`
4. Faça push com confiança ✅

---

**Última atualização:** Março 2026  
**Status:** 🔐 Seguro
