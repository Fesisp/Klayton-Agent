# 🎮 Sistema de Máquina de Estados - PokeBot

## Visão Geral

O PokeBot agora utiliza um sistema de **Máquina de Estados** que separa:
- **GameState**: Estado detectado do jogo (EXPLORING, IN_BATTLE, SHINY_FOUND)
- **BotBehavior**: Comportamento ativo do bot (IDLE, MISSION, HUNTING)

Esta separação permite que o bot tenha diferentes "modos de operação" enquanto reage apropriadamente aos eventos do jogo.

---

## 📊 Arquitetura

### GameState (Estado do Jogo)
Detectado pelo `GameStateDetector` através de visão computacional:

| Estado | Descrição | Detecção |
|--------|-----------|----------|
| `EXPLORING` | Jogador explorando o mundo | Ausência de botões de batalha |
| `IN_BATTLE` | Em combate ativo | Presença de botões FIGHT/ITEMS/POKEMON/RUN |
| `SHINY_FOUND` | Shiny detectado | Template matching com `shiny.png` |

### BotBehavior (Comportamento do Bot)
Definido pelo usuário no `settings.yaml`:

| Comportamento | Descrição | Quando Usar |
|---------------|-----------|-------------|
| `IDLE` | Ocioso - Apenas observa | Quando você quer que o bot não interfira |
| `MISSION` | Segue missões (clica Goto/Talk) | Modo padrão para progressão na história |
| `HUNTING` | Caça Pokémon específicos | Quando procura por espécies raras ou shinies |

---

## 🔄 Sistema de Prioridades

O loop principal do bot funciona com o seguinte sistema de prioridades:

```
┌─────────────────────────────────────┐
│  PRIORIDADE 1: SHINY ENCONTRADO     │ ← Maior prioridade
│  → Para o bot imediatamente         │
│  → Alerta sonoro + notificação      │
└─────────────────────────────────────┘
            ↓ (se não é shiny)
┌─────────────────────────────────────┐
│  PRIORIDADE 2: BATALHA ATIVA        │
│  → Sobrepõe qualquer comportamento  │
│  → Executa handle_battle()          │
│  → Aplica lógica de caça se HUNTING │
└─────────────────────────────────────┘
            ↓ (se explorando)
┌─────────────────────────────────────┐
│  PRIORIDADE 3: COMPORTAMENTO ATIVO  │
│  → IDLE: Apenas ações idle          │
│  → MISSION: Clica Goto/Talk         │
│  → HUNTING: Move-se procurando      │
└─────────────────────────────────────┘
```

### Exemplo de Fluxo:

**Cenário: Bot em modo HUNTING procurando Ditto**

1. **Loop 1-5**: Estado EXPLORING + Behavior HUNTING
   - Bot move-se aleatoriamente pela área de caça
   - Pressiona WASD ou clica em pontos aleatórios
   
2. **Loop 6**: Encontro selvagem inicia → Estado IN_BATTLE
   - OCR detecta "Rattata" como inimigo
   - Rattata não está em `hunt.target_pokemon`
   - Bot clica RUN automaticamente
   
3. **Loop 7-10**: Volta a EXPLORING
   - Continua movimentação de caça
   
4. **Loop 11**: Novo encontro → Estado IN_BATTLE
   - OCR detecta "Ditto" 
   - Ditto está em `hunt.target_pokemon`
   - Bot luta normalmente com estratégia STAB

---

## 🎯 Modo IDLE (Ocioso)

### Quando Usar:
- Você quer jogar manualmente mas manter o bot observando
- Quer detecção de Shiny em background
- Testando configurações sem interferência

### Comportamento:
```yaml
bot:
  behavior: "idle"
```

**O que o bot faz:**
- ✅ Detecta Shiny e alerta
- ✅ Executa ações idle ocasionais (parecer humano)
- ❌ NÃO clica em Goto/Talk
- ❌ NÃO move o personagem
- ❌ NÃO luta (mas detecta batalhas)

**Log típico:**
```
[DEBUG] GameState: EXPLORING | Behavior: IDLE
[DEBUG] Bot em estado OCIOSO. Aguardando...
```

---

## 🗺️ Modo MISSION (Missão)

### Quando Usar:
- Progressão normal da história
- Completar quests
- Modo padrão de operação

### Comportamento:
```yaml
bot:
  behavior: "mission"
```

**O que o bot faz:**
- ✅ Detecta e clica em `talk.png` (NPCs)
- ✅ Detecta e clica em `goto.png` (próximo objetivo)
- ✅ Avança diálogos com Espaço
- ✅ Luta quando encontra inimigos
- ✅ Foge de Pokémon na blacklist
- ✅ Detecta Shiny

**Fluxo de Decisão:**
```python
if detectar talk.png:
    pressionar espaço (avançar diálogo)
elif detectar goto.png:
    clicar no botão Goto
else:
    pressionar espaço (fallback)
```

**Log típico:**
```
[INFO] Ícone de diálogo encontrado. Avançando conversa com Espaço...
[INFO] Botão Goto encontrado. Seguindo missão...
```

---

## 🎣 Modo HUNTING (Caça)

### Quando Usar:
- Caçar Pokémon específicos (ex: Ditto, Eevee)
- Farm de Pokémon raros
- Caça de Shiny direcionada

### Comportamento:
```yaml
bot:
  behavior: "hunting"

hunt:
  target_pokemon:
    - "ditto"
    - "eevee"
  area_bounds: null
  move_interval: 2.0
```

**O que o bot faz:**

#### Durante Exploração:
1. **Move-se aleatoriamente** para provocar encontros
2. **Duas estratégias de movimento:**
   - **Com `area_bounds` definida**: Clica em pontos aleatórios dentro da área
   - **Sem `area_bounds`**: Usa teclas WASD em direções aleatórias

3. **Simulação humana:**
   - Duração variável de movimento (0.5-1.5s)
   - Pausas ocasionais (15% de chance)
   - Olha ao redor (`perform_idle_action`)

#### Durante Batalha:
```python
if pokemon_encontrado NOT IN target_pokemon:
    FUGIR imediatamente (click RUN)
else:
    LUTAR normalmente com estratégia STAB
```

### Exemplo de Configuração:

**Caça com Área Delimitada:**
```yaml
hunt:
  target_pokemon: ["chansey", "larvitar"]
  area_bounds: [500, 300, 1400, 900]  # Retângulo de caça
  move_interval: 2.0  # Move a cada 2 segundos
```

**Caça com Movimento Direcional:**
```yaml
hunt:
  target_pokemon: ["ditto"]
  area_bounds: null  # Usa WASD
  move_interval: 1.5  # Move a cada 1.5 segundos
```

**Log típico:**
```
[DEBUG] [HUNTING] Movendo para ponto aleatório: (850, 620)
[INFO] [HUNTING] 'Rattata' não é alvo de caça. Fugindo...
[INFO] ✨ [HUNTING] ALVO ENCONTRADO: Ditto! Preparando batalha...
```

---

## ⚙️ Configuração Completa

### settings.yaml

```yaml
bot:
  name: "PokeBot Pro Unified"
  enabled: true
  debug_mode: true
  loop_interval: 1.0
  behavior: "hunting"  # idle, mission, hunting

hunt:
  # Lista de alvos (bot foge de qualquer outro)
  target_pokemon:
    - "ditto"
    - "eevee"
    - "chansey"
  
  # Habilidade específica (futuro)
  target_ability: null
  
  # Área de caça [x1, y1, x2, y2]
  # null = usa movimento WASD aleatório
  area_bounds: null
  
  # Intervalo entre movimentos (segundos)
  move_interval: 2.0

strategy:
  # Pokémon para fugir SEMPRE (independente do modo)
  blacklist:
    - "magikarp"
    - "caterpie"
```

---

## 🔍 Como Determinar `area_bounds`

Use a ferramenta `tools/simple_coord_grabber.py`:

```powershell
python tools/simple_coord_grabber.py
```

**Passos:**
1. Posicione o jogo na tela
2. Clique no canto superior esquerdo da área de caça
3. Clique no canto inferior direito
4. Copie as coordenadas: `[x1, y1, x2, y2]`

**Exemplo:**
```
Clique 1: (520, 310)
Clique 2: (1380, 890)
→ area_bounds: [520, 310, 1380, 890]
```

---

## 📈 Comparação de Modos

| Aspecto | IDLE | MISSION | HUNTING |
|---------|------|---------|---------|
| Move personagem | ❌ | ❌* | ✅ |
| Clica Goto | ❌ | ✅ | ❌ |
| Clica Talk | ❌ | ✅ | ❌ |
| Luta em batalha | ❌** | ✅ | ✅*** |
| Foge de não-alvos | ❌ | ❌ | ✅ |
| Detecta Shiny | ✅ | ✅ | ✅ |

*Apenas via Goto  
**Detecta mas não age  
***Apenas contra alvos

---

## 🎯 Casos de Uso

### 1. Farm de Shiny Ditto
```yaml
bot:
  behavior: "hunting"

hunt:
  target_pokemon: ["ditto"]
  area_bounds: [600, 400, 1200, 800]
  move_interval: 2.0
```

Bot move-se aleatoriamente na área. Quando encontra:
- **Rattata/Pidgey/etc**: Foge automaticamente
- **Ditto**: Luta normalmente
- **Shiny qualquer**: PARA E ALERTA

### 2. Progressão de História (AFK)
```yaml
bot:
  behavior: "mission"
```

Bot segue Goto, conversa com NPCs, luta quando necessário.

### 3. Detecção de Shiny Passiva
```yaml
bot:
  behavior: "idle"
```

Você joga manualmente, bot apenas observa e alerta se aparecer shiny.

---

## 🛠️ Desenvolvimento Futuro

### Melhorias Planejadas:

1. **Detecção de Habilidade**
   - OCR da tela de sumário após batalha
   - Verificar se Pokémon tem `hunt.target_ability`
   - Capturar apenas se for a habilidade desejada

2. **Modo CAPTURE**
   - Novo comportamento para capturar automaticamente
   - Uso inteligente de Poké Balls
   - Verificação de IV (se possível via OCR)

3. **Rotas Pré-Programadas**
   - `area_bounds` com múltiplos pontos de interesse
   - Rotação entre áreas
   - Detecção de bloqueios/travamentos

4. **Aprendizado de Spawn**
   - Registrar onde cada Pokémon foi encontrado
   - Otimizar área de caça baseado em dados

---

## 🔧 Troubleshooting

### Bot não se move em modo HUNTING
**Verificar:**
- `behavior` está como `"hunting"`?
- `move_interval` não está muito alto?
- Logs mostram `[HUNTING]`?

**Solução:**
```yaml
bot:
  behavior: "hunting"  # Verificar escrita correta
hunt:
  move_interval: 1.5  # Reduzir se necessário
```

### Bot não foge de não-alvos
**Verificar:**
- OCR está lendo nome do Pokémon corretamente?
- Nome está em minúsculas em `target_pokemon`?

**Solução:**
Adicione debug:
```yaml
bot:
  debug_mode: true
```

Veja logs:
```
[DEBUG] Inimigo: 'Rattata' | Meu Pokémon: 'Pikachu'
[INFO] [HUNTING] 'Rattata' não é alvo de caça. Fugindo...
```

### Bot trava em área
**Possível causa:** Personagem encostou em parede

**Solução:** Ajuste `area_bounds` para evitar obstáculos, ou use movimento direcional (`area_bounds: null`)

---

## 📚 API de Referência

### Métodos do BotController

```python
class BotController:
    def handle_mission(self, img):
        """Modo MISSION: Clica Talk e Goto."""
        
    def handle_hunting(self, img):
        """Modo HUNTING: Move-se aleatoriamente procurando alvos."""
        
    def handle_battle(self, img):
        """Batalha: Verifica alvos de caça e aplica estratégia."""
```

### Enums

```python
class BotBehavior(Enum):
    IDLE = 0      # Ocioso
    MISSION = 1   # Missão
    HUNTING = 2   # Caça
```

---

## 🎉 Conclusão

O sistema de estados permite que o PokeBot seja flexível e adaptável:

- **IDLE**: Observação passiva
- **MISSION**: Automação de progressão
- **HUNTING**: Farm direcionado

Todos os modos mantêm:
- ✅ Detecção de Shiny
- ✅ Movimentação humanizada
- ✅ Estratégia STAB inteligente
- ✅ Sistema de prioridades robusto

**Use com sabedoria e responsabilidade!** 🎮✨

---

**Versão: 2.1 - Sistema de Estados**  
**Data: 2026-02-20**
