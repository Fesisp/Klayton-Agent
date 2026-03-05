# 🛡️ Sistema de Proteção contra Vazamento de Credenciais

## ✅ Status: ATIVO E FUNCIONAL

Seu repositório agora tem **3 camadas de proteção** contra vazamento de credenciais:

---

## 🔒 Camada 1: `.gitignore`

**O que faz:** Impede que arquivos sensíveis sejam rastreados pelo Git

**Arquivos protegidos:**
- `config/settings.yaml` ← Suas credenciais reais
- `config/secrets.yaml`
- `.env`
- `*.db`, `*.sqlite` (bancos com senhas)
- `*.key`, `*.pem` (chaves privadas)

**Como verificar:**
```bash
git status --ignored
# config/settings.yaml deve aparecer em "Ignored files"
```

---

## 🚫 Camada 2: Pre-commit Hook

**O que faz:** Bloqueia commits automaticamente se detectar:
- Arquivos sensíveis no staging
- Padrões de tokens/API keys
- Credenciais em arquivos YAML

**Localização:** `.git/hooks/pre-commit`

**Como funciona:**
```bash
git add config/settings.yaml  # Tenta adicionar arquivo bloqueado
git commit -m "test"          # ❌ BLOQUEADO automaticamente!

# Output:
# ❌ ERRO: Tentativa de commit bloqueada!
# 📁 Arquivo bloqueado: config/settings.yaml
```

**Testado:** ✅ Funcionando (validou commit anterior)

---

## 🔍 Camada 3: Validador Python

**O que faz:** Script manual para validação detalhada

**Uso:**
```bash
# Antes de qualquer commit importante:
python tools/check_secrets.py
```

**O que verifica:**
1. ✅ Arquivos bloqueados (settings.yaml, .env, etc)
2. ✅ Padrões de tokens (Telegram, Discord, OpenAI, GitHub, AWS)
3. ✅ Credenciais em YAMLs (valores reais vs placeholders)

**Exemplo de uso:**
```bash
$ git add docs/exemplo.md
$ python tools/check_secrets.py

🔍 Verificando segurança do commit...
📁 Arquivos a commitar: 1
   - docs/exemplo.md

🔍 Verificando arquivos bloqueados...
✅ Nenhum arquivo bloqueado

🔍 Verificando padrões de credenciais...
✅ Nenhum padrão suspeito

🔍 Verificando YAMLs...
✅ YAMLs parecem seguros

============================================================
✅ SEGURO - Nenhuma credencial detectada!
============================================================
```

---

## 📋 Workflow Recomendado

### Antes de cada commit:

```bash
# 1. Verificar status
git status --ignored

# 2. Adicionar apenas arquivos seguros
git add src/ docs/ tools/

# 3. NUNCA adicionar:
# ❌ git add config/settings.yaml
# ❌ git add .env

# 4. (Opcional) Validar manualmente
python tools/check_secrets.py

# 5. Commit (pre-commit hook valida automaticamente)
git commit -m "Sua mensagem"

# 6. Push
git push origin main
```

---

## 🚨 Se o Pre-commit Bloqueou

### Erro: "Arquivo bloqueado"

```bash
❌ ERRO: Tentativa de commit bloqueada!
📁 Arquivo bloqueado: config/settings.yaml
```

**Solução:**
```bash
git reset HEAD config/settings.yaml  # Remove do staging
git status                           # Confirmar remoção
```

### Erro: "Credencial detectada"

```bash
❌ ERRO: Credencial detectada no commit!
🔑 Padrão encontrado que parece ser um token/API key
```

**Solução:**
1. Abra o arquivo mencionado
2. Substitua credenciais reais por placeholders:
   ```yaml
   telegram_bot_token: "YOUR_TOKEN_HERE"
   discord_webhook_url: "YOUR_WEBHOOK_URL_HERE"
   ```
3. `git add <arquivo>` novamente
4. Tente commitar

---

## 🔧 Manutenção

### Atualizar padrões de secrets

Edite `tools/check_secrets.py` e adicione em `SECRET_PATTERNS`:

```python
SECRET_PATTERNS = {
    'novo_servico': r'seu_pattern_regex_aqui',
    # ...
}
```

### Adicionar novos arquivos bloqueados

Edite `.gitignore` e adicione:

```
# Seus novos arquivos sensíveis
config/nova_config.yaml
secrets/
```

Edite `tools/check_secrets.py` em `BLOCKED_FILES`:

```python
BLOCKED_FILES = [
    'config/settings.yaml',
    'config/nova_config.yaml',  # Novo
]
```

---

## ✅ Checklist de Segurança

Antes de fazer push público:

- [ ] `config/settings.yaml` está no `.gitignore`
- [ ] Pre-commit hook está instalado (`.git/hooks/pre-commit`)
- [ ] `python tools/check_secrets.py` retorna ✅ SEGURO
- [ ] `git status --ignored` mostra settings.yaml como ignorado
- [ ] Nenhum arquivo em `config/` está no staging (exceto `.example.yaml`)

---

## 📞 Suporte

### Histórico ainda tem credenciais antigas?

Siga: `docs/EMERGENCIA_VAZAMENTO.md`

### Pre-commit não está funcionando?

```bash
# Verificar se existe
ls -la .git/hooks/pre-commit

# Tornar executável (Linux/Mac)
chmod +x .git/hooks/pre-commit

# Windows: Git Bash executa automaticamente
```

### Forçar commit ignorando validação (NÃO RECOMENDADO)

```bash
git commit --no-verify -m "mensagem"
```

⚠️ **Apenas use em emergência!**

---

## 🎯 Resumo

| Camada | Status | Automático | Eficácia |
|--------|--------|------------|----------|
| `.gitignore` | ✅ Ativo | Sim | 🟢 Alta |
| Pre-commit hook | ✅ Ativo | Sim | 🟢 Alta |
| Validador Python | ✅ Ativo | Manual | 🟢 Alta |

**Proteção Total:** 🛡️🛡️🛡️ (Tripla camada)

---

**Última atualização:** Março 2026  
**Status:** ✅ Totalmente configurado e testado  
**Próximo vazamento esperado:** ❌ NUNCA MAIS
