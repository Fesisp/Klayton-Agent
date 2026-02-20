# Changelog - PokeBot

Todas as mudanças notáveis serão documentadas aqui.

---

## [v2.3.0] - 2026-02-20

### 🌐 Sistema de Controle Remoto via UDP

#### Adicionado
- **Controle Remoto UDP** para controlar bot em VM a partir do host
  - Latência de 1-5ms (ultra-rápido)
  - Não requer RDP ou console da VM
  - Funciona em background

- **Novo Módulo**: `src/core/udp_receiver.py`
  - Servidor UDP que escuta comandos remotos
  - Thread separada para não bloquear loop principal
  - Callbacks thread-safe para cada comando
  - Suporte a PING para teste de conexão

- **Novo Script**: `tools/remote_controller.py`
  - Transmissor UDP rodando na máquina física (host)
  - Captura teclas F1-F9 e envia para VM
  - Teste de conectividade automático
  - Logs detalhados de cada comando

#### Comandos UDP Suportados
- `IDLE`, `MISSION`, `HUNT`/`HUNTING`, `FOLLOW`
- `PAUSE`, `RESUME`, `STOP`
- `PING` (teste de conexão)

#### Configuração

**`config/settings.yaml`**:
```yaml
remote_control:
  enabled: false  # Mude para true na VM
  port: 5005      # Porta UDP
```

**`tools/remote_controller.py`**:
```python
VM_IP = "192.168.1.100"  # IP da VM
PORT = 5005
```

#### Modificado

- **`main.py`**:
  - Integração com `create_udp_receiver()`
  - Inicializa servidor UDP se habilitado
  - Cleanup adequado ao finalizar

#### Documentação

- **Novo**: `docs/REMOTE_CONTROL_UDP.md`
  - Setup completo passo a passo
  - Configuração de firewall (Windows/Linux)
  - Troubleshooting para problemas comuns
  - Comparação com outros métodos de controle
  - Exemplos de logs
  - Casos de uso avançados

### Arquitetura UDP

**Por que UDP?**
- ✅ Ultra-rápido (1-5ms vs 100-500ms de TCP/SSH)
- ✅ Fire-and-forget (sem handshake)
- ✅ Pacotes leves (~10 bytes)
- ✅ Funciona com NAT/Bridged/Host-Only

**Fluxo**:
```
[Host] Tecla F3 → Transmissor → UDP Socket (5005)
  ↓
[VM] Receptor → Callback → bot.behavior = HUNTING
```

### Requisitos

**VM (Receptor)**:
- `remote_control.enabled: true` em `settings.yaml`
- Porta 5005 UDP aberta no firewall
- Bot rodando (`python run_bot.py`)

**Host (Transmissor)**:
- IP da VM configurado em `remote_controller.py`
- `pynput` instalado
- Rede local conectando host e VM

### Setup Rápido

**1. Na VM**:
```powershell
# Abrir porta no firewall
New-NetFirewallRule -DisplayName "PokeBot UDP" -Direction Inbound -LocalPort 5005 -Protocol UDP -Action Allow

# Editar settings.yaml
remote_control:
  enabled: true

# Iniciar bot
python run_bot.py
```

**2. No Host**:
```powershell
# Descobrir IP da VM (executar na VM)
ipconfig  # Anotar IPv4

# Editar remote_controller.py (no host)
VM_IP = "192.168.1.100"  # IP da VM

# Executar controlador
python tools/remote_controller.py
```

**3. Testar**:
- Pressionar qualquer tecla F1-F9
- Ver logs no host e na VM confirmando recebimento

### Impacto

**Ganho de usabilidade**: Controle de VM sem precisar abrir RDP/Console!

**ANTES**: Abrir RDP → Focar janela → Pressionar tecla → Fechar RDP (~20-30s)  
**DEPOIS**: Pressionar tecla no host (~1s)

**Ganho**: **20-30x mais rápido!** 🚀

---

## [v2.2.0] - 2026-02-20

### 🎮 Sistema de Controle por Hotkeys

#### Adicionado
- **Hotkey Listener Global** usando biblioteca `pynput`
  - Funciona mesmo com o jogo em foco (não precisa Alt+Tab)
  - Thread separada para não bloquear loop principal
  - Mapeamento configurável em `settings.yaml`

- **Novo Módulo**: `src/core/hotkey_listener.py`
  - Classe `HotkeyManager` para gerenciar listener
  - Enum `HotkeyCommand` com 7 comandos disponíveis
  - Callbacks thread-safe para mudança de estado

- **Controles Padrão**:
  - F1: Modo IDLE (ocioso)
  - F2: Modo MISSION (missões)
  - F3: Modo HUNTING (caça)
  - F4: Modo FOLLOW (seguir personagem) ← Novo!
  - F5: PAUSE (pausar bot)
  - F6: RESUME (retomar bot)
  - F9: STOP (parar completamente)

#### Modo FOLLOW (Seguir Personagem)

- **Novo Behavior**: `BotBehavior.FOLLOW`
  - Bot segue personagem principal automaticamente
  - Ideal para contas secundárias

- **Dois Métodos de Follow**:
  1. **Template Matching** (recomendado):
     - Detecta sprite do personagem visualmente
     - Configurável via `follow.player_template`
     - Threshold ajustável (padrão: 0.7)
  
  2. **Party Button**:
     - Clica em botão "Follow" da party
     - Para uso em parties ativas

- **Configuração**: `config/settings.yaml`
  ```yaml
  follow:
    method: "template"  # ou "party_button"
    player_template: "player_char.png"
    match_threshold: 0.7
    distance: 50  # pixels
    check_interval: 1.0  # segundos
  ```

#### Sistema de Pausa

- Atributo `paused` em `BotController`
- Hotkeys F5/F6 controlam pausa sem parar thread
- Loop verifica `paused` flag antes de cada ação

#### Modificado

- **`bot_controller.py`**:
  - Enum `BotBehavior` agora tem 4 estados (+ FOLLOW)
  - Método `handle_follow()` com lógica de seguimento
  - Checagem de `paused` no início do loop
  - Método `_follow_by_template()` para detecção visual
  - Método `_follow_by_party_button()` para método alternativo

- **`main.py`**:
  - Integração com `HotkeyManager`
  - Inicializa listener antes do loop principal
  - Cleanup adequado ao finalizar

- **`settings.yaml`**:
  - Nova seção `follow` com configurações
  - Nova seção `controls` com mapeamento de teclas
  - `controls.enabled` para habilitar/desabilitar sistema

#### Dependências

- **Adicionado**: `pynput>=1.7.6` ao `requirements.txt`
  - Necessário para hotkeys globais
  - Funciona em Windows/Linux/Mac

#### Documentação

- **Novo**: `docs/HOTKEY_SYSTEM.md`
  - Guia completo do sistema de hotkeys
  - Exemplos de uso e cenários práticos
  - Troubleshooting para problemas comuns
  - Tutorial de setup do modo FOLLOW

- **Novo**: `docs/QUICK_SETUP_HOTKEYS.md`
  - Setup rápido em 5-10 minutos
  - Checklist de verificação
  - Solução de problemas comuns

### Impacto

**Ganho de produtividade**: 30-60x mais rápido para mudar modos!

**ANTES**: Parar bot → Editar arquivo → Reiniciar (~30-60s)  
**DEPOIS**: Pressionar tecla (~1s)

---

## [v2.1.0] - 2026-02-19

### 🔄 Máquina de Estados e Sistema de Caça

#### Adicionado
- **Enum `BotBehavior`** com 3 estados:
  - IDLE: Observação passiva
  - MISSION: Executa missões automaticamente
  - HUNTING: Procura pokémon específicos

- **Sistema de Prioridades**:
  1. Shiny (máxima prioridade)
  2. Batalha ativa
  3. Behavior configurado

- **Modo HUNTING**:
  - Lista de alvos configurável (`hunt.target_pokemon`)
  - Movimento aleatório inteligente
  - Fuga automática de não-alvos
  - Delimitação de área de caça

#### Modificado
- **`bot_controller.py`**:
  - Método `run()` reestruturado com prioridades
  - Métodos `handle_idle()`, `handle_mission()`, `handle_hunting()`
  - Sistema de detecção de alvos

- **`settings.yaml`**:
  - Seção `hunt` com configurações de caça
  - `bot.behavior` para modo inicial

#### Documentação
- **Novo**: `docs/STATE_MACHINE.md`
- **Novo**: `docs/MODES_QUICK_GUIDE.md`

---

## [v2.0.0] - 2026-02-18

### 🤖 Melhorias de Humanização

#### Adicionado
- **Movimentos Bezier** para mouse natural
- **AI Chat Handler** com 3 provedores (Ollama/Gemini/OpenAI)
- **Detecção de HP** via análise de cores (HSV)
- **Cálculo de STAB** (Same Type Attack Bonus)
- **Ações Idle** aleatórias

#### Novo Módulo
- `src/perception/chat_handler.py`: Respostas naturais via LLM

#### Modificado
- **`input_simulator.py`**:
  - `human_click()` com curvas Bezier
  - `_bezier_move()` para interpolação
  - `perform_idle_action()` com ações variadas

- **`game_state_detector.py`**:
  - `_get_hp_percentage()` via análise HSV
  - Detecção de HP verde/amarelo/vermelho

- **`battle_strategy.py`**:
  - `get_best_move()` com bônus STAB (1.5x)
  - Decisões baseadas em HP
  - `should_use_item()` e `should_switch_pokemon()`

#### Dependências
- **Adicionado**: `scipy>=1.11.0`, `requests>=2.31.0`

#### Documentação
- **Novo**: `docs/HUMANIZATION_FEATURES.md`
- **Novo**: `docs/QUICK_START.md`

---

## [v1.0.0] - 2026-01-15

### 🚀 Versão Inicial

#### Features Base
- Captura de tela com MSS
- OCR com Tesseract
- Detecção de estados (batalha, exploração, menu)
- Sistema de batalha automático
- Detecção de Shiny
- Template matching para UI

#### Estrutura
- Arquitetura MVC
- Módulos: perception, decision, action
- Base de dados de Pokémon e movimentos
- Sistema de gerenciamento de time

---

**Formato baseado em [Keep a Changelog](https://keepachangelog.com/)**
