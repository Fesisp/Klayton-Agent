# 🚨 EMERGÊNCIA: Credenciais Vazaram no Git

## ⚠️ O QUE ACONTECEU?

Suas credenciais do Telegram e Discord foram **commitadas no Git** e **enviadas ao repositório remoto** (GitHub/GitLab).

**Por que o `.gitignore` não funcionou?**
- `.gitignore` só funciona para arquivos **NOVOS** (não rastreados)
- Se um arquivo já foi commitado ANTES, o `.gitignore` é ignorado
- Você commitou `settings.yaml` com credenciais ANTES de adicionar ao `.gitignore`

---

## 🔥 AÇÕES IMEDIATAS (FAÇA AGORA!)

### 1. REVOGAR CREDENCIAIS COMPROMETIDAS

#### Telegram (URGENTE)
```bash
1. Abra Telegram
2. Procure @BotFather
3. Selecione seu bot
4. Digite: /revoke
5. Confirme
6. Digite: /newbot (para criar novo)
7. Anote o NOVO token
```

#### Discord (URGENTE)
```bash
1. Abra Discord → Seu Servidor
2. Editar Canal → Integrações → Webhooks
3. DELETE o webhook comprometido
4. Crie um NOVO webhook
5. Copie a nova URL
```

### 2. ATUALIZAR settings.yaml LOCAL

Edite `config/settings.yaml` com os NOVOS tokens:

```yaml
notifications:
  telegram_bot_token: "SEU_NOVO_TOKEN_AQUI"
  telegram_chat_id: "SEU_CHAT_ID"  # Este pode manter
  discord_webhook_url: "SUA_NOVA_URL_WEBHOOK"
```

---

## 🧹 LIMPAR HISTÓRICO DO GIT

### Opção 1: Remover do tracking (JÁ FEITO)

```bash
git rm --cached config/settings.yaml
git commit -m "Security: Remove sensitive credentials"
git push --force
```

✅ **Status:** Executado com sucesso!

### Opção 2: Limpar TODO o histórico (mais seguro)

⚠️ **ATENÇÃO:** Isto reescreve o histórico. Use apenas se o repositório for privado ou você for o único colaborador.

```bash
# Instalar BFG Repo-Cleaner (mais rápido que git filter-branch)
# Download: https://rpo.github.io/bfg-repo-cleaner/

# Opção A: Remover arquivo específico
java -jar bfg.jar --delete-files settings.yaml

# Opção B: Substituir credenciais por placeholders
java -jar bfg.jar --replace-text secrets.txt

# Limpar refs
git reflog expire --expire=now --all
git gc --prune=now --aggressive

# Push forçado
git push --force
```

**Arquivo `secrets.txt` (para Opção B):**
```
TELEGRAM_BOT_TOKEN_PATTERN==>TELEGRAM_TOKEN_REMOVED
TELEGRAM_CHAT_ID_PATTERN==>CHAT_ID_REMOVED
https://discord.com/api/webhooks/==>DISCORD_WEBHOOK_REMOVED
```

---

## 🔒 PREVENIR NOVOS VAZAMENTOS

### 1. Verificar .gitignore

```bash
cat .gitignore | Select-String "settings.yaml"
# Output esperado: config/settings.yaml ✅
```

### 2. Testar antes de commit

```bash
# SEMPRE execute antes de git add/commit:
git status --ignored

# settings.yaml deve aparecer como "ignored" ✅
```

### 3. Usar pre-commit hooks

Crie `.git/hooks/pre-commit`:

```bash
#!/bin/sh
# Impede commit de arquivos sensíveis

if git diff --cached --name-only | grep -q "config/settings.yaml"; then
    echo "🚨 ERRO: Tentativa de commit de settings.yaml bloqueada!"
    echo "Este arquivo contém credenciais sensíveis."
    exit 1
fi
```

Torne executável:
```bash
chmod +x .git/hooks/pre-commit  # Linux/Mac
# No Windows, o Git Bash executa automaticamente
```

---

## 📊 VERIFICAR DANOS

### Verificar se foi para o GitHub/GitLab

```bash
# Ver último commit no remoto
git log origin/main --oneline -10

# Procurar por settings.yaml no histórico remoto
git log --all --full-history -- config/settings.yaml
```

### Se apareceu no remoto:

1. **Repositório Privado:** 
   - Risco menor, mas ainda revogue credenciais
   - Apenas colaboradores têm acesso

2. **Repositório Público:**
   - 🚨 RISCO MÁXIMO
   - Bots de scraping podem ter copiado
   - REVOGUE IMEDIATAMENTE
   - Considere deletar o repositório e recriar

---

## ✅ CHECKLIST DE SEGURANÇA

Marque cada item:

- [ ] Revogei token do Telegram (@BotFather → /revoke)
- [ ] Deletei webhook do Discord
- [ ] Criei novas credenciais
- [ ] Atualizei `config/settings.yaml` LOCAL
- [ ] Executei `git rm --cached config/settings.yaml`
- [ ] Fiz commit: `git commit -m "Security: Remove credentials"`
- [ ] Fiz push: `git push --force`
- [ ] Verifiquei que GitHub/GitLab NÃO mostra mais settings.yaml
- [ ] Testei novas credenciais funcionam
- [ ] Configurei pre-commit hook (opcional)
- [ ] Li `docs/SEGURANCA.md` completamente

---

## 📞 SUPORTE

### Se ainda não resolveu:

1. **GitHub:** Settings → Security → Secret scanning alerts
2. **GitLab:** Security & Compliance → Secret Detection
3. **Telegram:** @BotFather → Documentação
4. **Discord:** Criar ticket de suporte

### Se suspeitar de acesso não autorizado:

- Telegram: Verifique `Settings → Privacy → Active Sessions`
- Discord: `User Settings → Authorized Apps`
- GitHub: `Settings → Security Log`

---

**Última atualização:** Março 2026  
**Criado devido a:** Vazamento de credenciais em commit  
**Status:** 🚨 AÇÃO IMEDIATA NECESSÁRIA
