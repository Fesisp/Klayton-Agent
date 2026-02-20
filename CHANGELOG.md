# 📝 Changelog - PokeBot

## [2.1.0] - 2026-02-20 - Sistema de Estados

### ✨ Novas Funcionalidades

#### Máquina de Estados
- **Novo Enum `BotBehavior`**: IDLE, MISSION, HUNTING
- **3 Modos de Operação**:
  - IDLE: Observação passiva (apenas alerta Shiny)
  - MISSION: Progressão automática de missões
  - HUNTING: Caça direcionada de Pokémon específicos

#### Modo HUNTING
- Movimentação aleatória em área delimitada (`area_bounds`)
- Movimento direcional WASD (quando `area_bounds` é null)
- Fuga automática de Pokémon não-alvo
- Luta apenas contra alvos configurados
- Pausas humanizadas (15% de chance a cada movimento)
- Integração completa com STAB e detecção de HP

#### Sistema de Prioridades
- Prioridade 1: SHINY_FOUND (máxima - para tudo)
- Prioridade 2: IN_BATTLE (sobrepõe comportamento)
- Prioridade 3: EXPLORING (executa comportamento ativo)

### 🔧 Melhorias

#### BotController (`src/core/bot_controller.py`)
- Loop principal reestruturado com sistema de prioridades
- Método `handle_exploring()` renomeado para `handle_mission()` (clareza)
- Novo método `handle_hunting()` para lógica de caça
- Método `handle_battle()` melhorado com verificação de alvos de caça
- Integração com detecção de HP (crítico < 25%, baixo < 30%)
- Logs mais detalhados com estado atual (GameState + BotBehavior)

#### Configuração (`config/settings.yaml`)
- Nova opção `bot.behavior`: "idle", "mission", "hunting"
- Nova seção `hunt`:
  - `target_pokemon`: Lista de alvos
  - `target_ability`: Habilidade específica (futuro)
  - `area_bounds`: Área delimitada [x1, y1, x2, y2]
  - `move_interval`: Intervalo entre movimentos (segundos)

### 📄 Documentação

#### Novos Arquivos
- `docs/STATE_MACHINE.md`: Arquitetura técnica completa
- `docs/MODES_QUICK_GUIDE.md`: Guia prático de uso
- `docs/STATE_SYSTEM_SUMMARY.md`: Resumo de implementação
- `docs/INTEGRATION_EXAMPLES.py`: Exemplos de código

#### Atualizados
- `README.md`: Seção de features expandida
- `README.md`: Quick Start com exemplos de modos

### 🐛 Correções
- Nenhum bug reportado nesta versão

---

## [2.0.0] - 2026-02-20 - Humanização Completa

### ✨ Novas Funcionalidades

#### Movimentação Humanizada
- **Curvas Bezier**: Mouse move em trajetória curva natural
- **Delays Randômicos**: 50-150ms variável antes de clicar
- **Duração Variável**: Movimentos de 200-500ms (configurável)
- **Método `human_click()`**: Substitui cliques instantâneos
- **Método `_bezier_move()`**: Calcula e executa curvas

#### Ações Idle
- **Método `perform_idle_action()`**: Ações aleatórias ocasionais
- Pressionar espaço (simula leitura)
- Mover câmera aleatoriamente
- Pausas contemplativas
- Frequência configurável (padrão: 5% a cada 10s)

#### Chat Handler com IA
- **Novo Módulo**: `src/perception/chat_handler.py`
- **3 Providers Suportados**:
  - Ollama (local, gratuito)
  - Google Gemini (API)
  - OpenAI (API)
- **4 Personalidades**: casual, competitive, friendly, quiet
- **Timing Humanizado**: 2-5s antes de responder
- **Digitação Natural**: Caractere por caractere com delays
- Limite de 50 caracteres para respostas curtas

#### Detecção de HP
- **Método `_get_hp_percentage()`**: Análise de cor HSV
- Detecta verde (>50%), amarelo (25-50%), vermelho (<25%)
- Calcula porcentagem baseado em largura da barra
- Funciona para player e inimigo
- Integrado com `get_battle_info()`

### 🔧 Melhorias

#### Estratégia de Batalha (`src/decision/battle_strategy.py`)
- **Cálculo STAB**: Bônus de 1.5x quando tipo do movimento = tipo do Pokémon
- **Prioridade de Movimentos**: +10 pontos por nível de prioridade
- **Penalização de Accuracy**: Reduz score proporcionalmente
- **Métodos Novos**:
  - `should_use_item(hp_percentage)`: Recomenda item se HP < 25%
  - `should_switch_pokemon(hp_percentage, enemy)`: Recomenda troca se HP < 30%
- Logs detalhados com scores calculados

#### InputSimulator (`src/action/input_simulator.py`)
- Configurações de humanização no `__init__`
- Método `click()` agora usa `human_click()` quando ativado
- Método `_random_camera_move()`: Simula olhar ao redor

#### GameStateDetector (`src/perception/game_state_detector.py`)
- Método `get_battle_info()` retorna HP percentual
- Flags `player_hp_critical` e `player_hp_low`

### ⚙️ Configuração

#### settings.yaml
- Nova seção `input` com opções de humanização:
  - `use_human_movement`: true/false
  - `min_delay`, `max_delay`
  - `min_move_duration`, `max_move_duration`
  - `idle_action_chance`

- Nova seção `chat`:
  - `enabled`: true/false
  - `provider`: ollama/gemini/openai
  - `model`: nome do modelo
  - `api_key`: chave de API
  - `response_chance`: 0-1
  - `personality`: casual/competitive/friendly/quiet

- ROI adicionada:
  - `player_hp_bar`: Coordenadas da barra de HP do player

### 📦 Dependências

#### Adicionadas
- `scipy`: Interpolação para curvas Bezier
- `requests`: Chamadas HTTP para APIs de LLM

### 📄 Documentação

#### Novos Arquivos
- `docs/HUMANIZATION_FEATURES.md`: Documentação técnica completa
- `docs/QUICK_START.md`: Guia de instalação e uso
- `docs/IMPLEMENTATION_SUMMARY.md`: Resumo de implementação
- `docs/INTEGRATION_EXAMPLES.py`: Exemplos de integração

### 🐛 Correções
- Nenhum bug reportado nesta versão

---

## [1.0.0] - 2026-02-19 - Versão Inicial

### ✨ Funcionalidades Iniciais

#### Core
- Arquitetura MVC (Model-View-Controller)
- Loop principal com detecção de estado
- Sistema de componentes modulares

#### Percepção
- Captura de tela com MSS
- OCR com Tesseract
- Template matching com OpenCV
- Detecção de estados: EXPLORING, IN_BATTLE, SHINY_FOUND
- Detecção de Shiny com alarme sonoro

#### Decisão
- Sistema de estratégia baseado em tipos
- Cálculo de efetividade (multiplicadores)
- Whitelist e blacklist de Pokémon
- Decisão de fuga baseado em matchup

#### Ação
- Simulação de cliques com PyAutoGUI
- Clique em botões de batalha (FIGHT, ITEMS, POKEMON, RUN)
- Clique em slots de movimento
- Clique em botões de navegação (Goto, Talk)

#### Conhecimento
- Database de Pokémon (tipos, stats)
- Database de movimentos (power, tipo, categoria)
- Matriz de efetividade de tipos
- Team Manager (gerenciamento de equipe)
- Persistência de movimentos conhecidos (known_moves.json)

#### Ferramentas
- `roi_picker.py`: Seleção de ROIs
- `simple_coord_grabber.py`: Captura de coordenadas
- `build_pokeapi_jsons.py`: ETL da PokeAPI
- `gerar_dex_completa.py`: Geração de Pokédex

### ⚙️ Configuração
- `config/settings.yaml`: Arquivo de configuração centralizado
- ROIs configuráveis para todos os elementos da UI
- Thresholds de template matching ajustáveis
- Paths de assets e dados configuráveis

### 📦 Dependências Iniciais
- opencv-python
- numpy
- pytesseract
- mss
- pyautogui
- pyyaml
- loguru

### 📄 Documentação Inicial
- `README.md`: Visão geral do projeto
- `docs/PROJECT_OVERVIEW.md`: Arquitetura e design
- `docs/TESTING.md`: Guia de testes

---

## Legenda de Versões

- **[X.Y.Z]** - Formato de versionamento semântico
  - **X**: Versão major (mudanças incompatíveis)
  - **Y**: Versão minor (novas funcionalidades compatíveis)
  - **Z**: Versão patch (correções de bugs)

### Categorias de Mudanças

- ✨ **Novas Funcionalidades**: Features completamente novas
- 🔧 **Melhorias**: Aprimoramentos em funcionalidades existentes
- 🐛 **Correções**: Bugs corrigidos
- 📄 **Documentação**: Mudanças em documentação
- ⚙️ **Configuração**: Mudanças em arquivos de configuração
- 📦 **Dependências**: Mudanças em bibliotecas externas
- ⚠️ **Deprecado**: Funcionalidades que serão removidas
- 🗑️ **Removido**: Funcionalidades removidas

---

## Roadmap Futuro

### v2.2.0 - Captura Automática (Planejado)
- [ ] Novo modo CAPTURE
- [ ] Uso automático de Poké Balls
- [ ] Verificação de IV via OCR
- [ ] Sistema de captura inteligente (HP + status)

### v2.3.0 - Rotas Inteligentes (Planejado)
- [ ] Sistema de waypoints
- [ ] Rotas pré-programadas
- [ ] Detecção de bloqueios/travamentos
- [ ] Otimização automática de rotas

### v3.0.0 - Aprendizado de Máquina (Futuro)
- [ ] Aprendizado por reforço
- [ ] Otimização de estratégia baseada em histórico
- [ ] Detecção de padrões de spawn
- [ ] Adaptação dinâmica de comportamento

---

**Mantido por**: Fesisp  
**Repositório**: https://github.com/Fesisp/PokeBot  
**Licença**: Educational & Research Only
