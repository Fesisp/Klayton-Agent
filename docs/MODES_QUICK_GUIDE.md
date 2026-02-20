# 🎮 Guia Rápido - Modos de Operação

## Troca Rápida de Modo

Edite `config/settings.yaml` e altere apenas uma linha:

```yaml
bot:
  behavior: "hunting"  # Mude aqui: idle, mission, hunting
```

Reinicie o bot:
```powershell
python run_bot.py
```

---

## 🆕 Modo HUNTING - Setup em 3 Passos

### Passo 1: Configurar Alvos

```yaml
hunt:
  target_pokemon:
    - "ditto"      # Adicione os Pokémon que quer caçar
    - "eevee"
```

### Passo 2: Escolher Estratégia de Movimento

**Opção A: Área Delimitada (Recomendado para áreas específicas)**
```yaml
hunt:
  area_bounds: [500, 300, 1400, 900]  # [x1, y1, x2, y2]
  move_interval: 2.0
```

Para encontrar coordenadas:
```powershell
python tools/simple_coord_grabber.py
# Clique: canto superior esquerdo da área
# Clique: canto inferior direito da área
```

**Opção B: Movimento Livre (Recomendado para rotas lineares)**
```yaml
hunt:
  area_bounds: null  # Usa WASD aleatório
  move_interval: 1.5
```

### Passo 3: Ativar Modo

```yaml
bot:
  behavior: "hunting"
```

### Executar:
```powershell
python run_bot.py
```

**Resultado:**
- ✅ Bot se move aleatoriamente
- ✅ Foge de todos exceto alvos
- ✅ Luta contra alvos com STAB
- ✅ Alerta se encontrar Shiny

---

## 📋 Exemplos Práticos

### Exemplo 1: Caçar Ditto em Route 15

**Objetivo:** Encontrar Ditto para breeding

```yaml
bot:
  behavior: "hunting"

hunt:
  target_pokemon: ["ditto"]
  area_bounds: [600, 350, 1350, 850]
  move_interval: 2.0
```

**O que acontece:**
1. Bot clica em pontos aleatórios dentro da área
2. Caminha até lá (provoca encontros)
3. Encontra Rattata → Foge
4. Encontra Pidgey → Foge
5. Encontra Ditto → Luta!

---

### Exemplo 2: Farm de Eevee para Evoluções

**Objetivo:** Capturar múltiplos Eevee

```yaml
bot:
  behavior: "hunting"

hunt:
  target_pokemon: ["eevee"]
  area_bounds: null  # Movimento livre
  move_interval: 1.5
```

**O que acontece:**
1. Bot pressiona W/A/S/D aleatoriamente
2. Encontra qualquer coisa → Foge
3. Encontra Eevee → Luta!

---

### Exemplo 3: Shiny Hunt (Qualquer Pokémon)

**Objetivo:** Apenas encontrar Shiny, não importa qual

```yaml
bot:
  behavior: "hunting"

hunt:
  target_pokemon: []  # Lista vazia = foge de TODOS
  area_bounds: [700, 400, 1250, 800]
  move_interval: 2.0

strategy:
  blacklist: []  # Remove blacklist para não fugir de nada
```

**Configuração alternativa - Modo Mission:**
```yaml
bot:
  behavior: "mission"  # Segue rota enquanto detecta Shiny
```

---

### Exemplo 4: AFK Progressão de História

**Objetivo:** Bot completa missões enquanto você está AFK

```yaml
bot:
  behavior: "mission"
```

**O que acontece:**
1. Clica em Goto quando aparece
2. Conversa com NPCs (Talk)
3. Luta quando encontra inimigos
4. Avança diálogos automaticamente

---

### Exemplo 5: Detecção Passiva de Shiny

**Objetivo:** Você joga, bot apenas alerta Shiny

```yaml
bot:
  behavior: "idle"
```

**O que acontece:**
- Bot NÃO clica em nada
- Você joga normalmente
- Se aparecer Shiny → Alarme!

---

## ⚡ Dicas Rápidas

### Velocidade de Caça
```yaml
# Mais rápido (arriscado - pode parecer bot)
hunt:
  move_interval: 1.0

# Balanceado (recomendado)
hunt:
  move_interval: 2.0

# Mais lento (mais humano)
hunt:
  move_interval: 3.0
```

### Área de Caça Eficiente

**Pequena (farm concentrado):**
```yaml
area_bounds: [700, 450, 1100, 750]  # 400x300px
```

**Média (balanceado):**
```yaml
area_bounds: [500, 300, 1400, 900]  # 900x600px
```

**Grande (rota longa):**
```yaml
area_bounds: [300, 200, 1600, 1000]  # 1300x800px
```

### Combinando com Humanização

```yaml
input:
  use_human_movement: true
  idle_action_chance: 0.05  # 5% de pausas

hunt:
  move_interval: 2.0  # Combinado = muito humano
```

---

## 🎯 Escolhendo o Modo Certo

| Objetivo | Modo | Configuração |
|----------|------|--------------|
| Caçar Pokémon específico | HUNTING | `target_pokemon` preenchido |
| Farm de Shiny genérico | HUNTING | `target_pokemon: []` |
| Completar missões AFK | MISSION | Padrão |
| Apenas alertar Shiny | IDLE | Sem configuração extra |
| Testar configurações | IDLE | Debug ativo |

---

## 🔄 Fluxo de Trabalho Típico

### Manhã: Farm de Shiny Ditto
```yaml
bot:
  behavior: "hunting"
hunt:
  target_pokemon: ["ditto"]
```

### Tarde: Progressão de História
```yaml
bot:
  behavior: "mission"
```

### Noite: Caça de Eevee
```yaml
bot:
  behavior: "hunting"
hunt:
  target_pokemon: ["eevee"]
```

---

## ⚠️ Avisos Importantes

### HUNTING Mode:
- ⚠️ Foge de TODOS exceto alvos
- ⚠️ Pode gastar muitos repels se configurado
- ⚠️ Certifique-se que nomes estão corretos (minúsculas)

### MISSION Mode:
- ⚠️ Pode travar se Goto sumir da tela
- ⚠️ Monitore diálogos importantes (escolhas)

### IDLE Mode:
- ⚠️ Bot NÃO joga por você
- ⚠️ Apenas observa e alerta

---

## 📝 Template de Configuração

Copie e cole no seu `settings.yaml`:

```yaml
# ===== CONFIGURAÇÃO RÁPIDA =====

bot:
  behavior: "hunting"  # MUDE AQUI: idle, mission, hunting

hunt:
  # Pokémon que você QUER encontrar
  target_pokemon:
    - "ditto"
    - "eevee"
  
  # Área de caça (null = movimento livre)
  area_bounds: null  # Ex: [500, 300, 1400, 900]
  
  # Velocidade (segundos entre movimentos)
  move_interval: 2.0

strategy:
  # Pokémon que SEMPRE foge (em qualquer modo)
  blacklist:
    - "magikarp"

# ===== FIM DA CONFIGURAÇÃO =====
```

---

## 🚀 Comando Único para Testar

```powershell
# 1. Editar settings.yaml (use seu editor favorito)
notepad config/settings.yaml

# 2. Executar bot
python run_bot.py

# 3. Parar bot
Ctrl+C
```

---

## 📊 Logs de Sucesso

### HUNTING Funcionando:
```
[INFO] Bot iniciado em modo: HUNTING
[INFO] Alvos de caça: ['ditto', 'eevee']
[DEBUG] [HUNTING] Movendo para ponto aleatório: (850, 620)
[INFO] [HUNTING] 'Rattata' não é alvo de caça. Fugindo...
[INFO] ✨ [HUNTING] ALVO ENCONTRADO: Ditto! Preparando batalha...
```

### MISSION Funcionando:
```
[INFO] Bot iniciado em modo: MISSION
[INFO] Botão Goto encontrado. Seguindo missão...
[INFO] Ícone de diálogo encontrado. Avançando conversa com Espaço...
```

### IDLE Funcionando:
```
[INFO] Bot iniciado em modo: IDLE
[DEBUG] Bot em estado OCIOSO. Aguardando...
[CRITICAL] SHINY ENCONTRADO! ALARME!  ← SE APARECER SHINY
```

---

## 🎓 Conclusão

Agora você tem **3 modos poderosos**:

1. **IDLE**: Vigilância passiva
2. **MISSION**: Automação completa
3. **HUNTING**: Caça direcionada

**Mude entre eles editando apenas 1 linha no settings.yaml!**

Use conforme sua necessidade e **bom jogo!** 🎮✨

---

**Versão: 2.1**  
**Última atualização: 2026-02-20**
