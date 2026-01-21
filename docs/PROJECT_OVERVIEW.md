# Visão Geral do Projeto PokeBot-Pro

## Visão Geral

- **Propósito:** `PokeBot-Pro` é um bot para o MMORPG Pokémon (Tibianic-like) que joga “sozinho”: segue missões (Goto), conversa com NPCs, entra em batalhas, luta de forma minimamente inteligente, detecta shinies e para o jogo para você capturar.
- **Arquitetura:** Python + OpenCV + Tesseract + automação de mouse/teclado. Toda lógica de jogo é separada em módulos: captura de tela, percepção (OCR/detecção de estado), decisão, ação (inputs) e conhecimento (time, movimentos, tipos, etc.), configurados via `settings.yaml`.

## Fluxo de Execução Atual

- **Entrada principal:** `PokeBot_Pro/run_bot.py`
  - Faz setup de `sys.path`, carrega `config/settings.yaml` e instancia o núcleo (`src.core.main`).
  - Comandos típicos (no diretório `PokeBot_Pro`):
    ```powershell
    python -m pip install -r requirements.txt
    python run_bot.py
    ```

- **Loop principal:** `BotController.run` em `src/core/bot_controller.py`
  - A cada iteração:
    - Captura frame da tela (`ScreenCapture`).
    - Usa `GameStateDetector.detect_state` para classificar o estado:
      - `SHINY_FOUND` → alarme sonoro e para o bot.
      - `IN_BATTLE` → `handle_battle`.
      - `EXPLORING` → `handle_exploring`.
    - Espera ~0.5s entre iterações.

## Estados e Comportamentos

### 1. Exploração – `handle_exploring`

- Primeiro, procura ícone de diálogo (`talk.png`) numa área configurável (`detection.talk_search_area`):
  - Se detectado com `talk_threshold`, pressiona `space` para avançar textos de NPC.
- Caso contrário, procura botão de missão (`goto.png`):
  - Se score acima de `goto_threshold` e não estiver em batalha naquele frame:
    - Clica numa área “segura” dentro do botão, espera ~2s para o personagem andar.
- Fallback: se não há talk nem goto confiáveis, pressiona `space` ocasionalmente para manter alguma interação.

### 2. Batalha – `handle_battle`

- Confere se continua `IN_BATTLE`; se não, aborta.
- **Passo 1 – focar no menu de golpes:**
  - Clica no botão `FIGHT` via template (`fight.png`) com margem interna, e espera `battle.fight_to_moves_delay` (ex: 1.2s) para garantir que o menu de golpes abriu.
- **Passo 2 – ler quem luta:**
  - Usa `GameStateDetector.get_battle_info`:
    - Recorta ROIs `rois.enemy_name` e `rois.player_name`.
    - Aplica OCR otimizado para texto branco, whitelists de letras.
    - Remove “Lv” e espaços extras.
    - Resulta em `enemy_name` e `player_name` (nome do seu pokémon atual).
- **Passo 3 – decisão de fuga:**
  - Chama `strategy.should_flee(my_pokemon_name, enemy_name)`:
    - Se `True`, clica `RUN` via template (`run.png`), aguarda `battle.action_cooldown` (ex: 4s) e retorna.
- **Passo 4 – decisão de troca:**
  - Chama `strategy.choose_switch_target(enemy_name)`:
    - Se devolve índice:
      - Clica `POKEMON` via template (`pokemon.png`).
      - Recorta `rois.switch_menu.container`.
      - Usa `OCREngine.ocr_party_list` para ler a lista de pokémons.
      - Atualiza `TeamManager.current_team` com esses nomes.
      - Clica no slot escolhido (por índice * `slot_height`).
      - Espera `action_cooldown` e retorna (não ataca nesse tick).
- **Passo 5 – leitura dos golpes:**
  - Assume que menu de golpes está visível.
  - Para cada slot `rois.moves.slot_1..4`:
    - Recorta ROI do botão.
    - Processa com `OCREngine.preprocess_dynamic_background_text` (texto branco em fundo colorido).
    - Chama `OCREngine.extract_text_optimized` com whitelist de letras e espaço.
    - Limpa com `OCREngine.clean_move_name` (regra dos moves: remover PP `/` e números, manter o nome).
    - Monta lista `my_moves`.
  - Chama `TeamManager.save_moves(my_pokemon_name, my_moves)` para persistir golpes conhecidos.
- **Passo 6 – escolha do golpe:**
  - `strategy.get_best_move(my_pokemon_name, enemy_name)`:
    - Usa base de conhecimento (tipos, poder) e golpes conhecidos para selecionar índice do melhor slot (0–3).
  - Loga a escolha e clica no slot com `InputSimulator.click_in_slot`.
  - Espera `battle.action_cooldown` para dar tempo de animação e reaparecimento dos botões.

### 3. Shiny – `handle_shiny`

- Detecção via template `shiny.png` em `GameStateDetector._detect_shiny`, com threshold configurável.
- Se detectado:
  - Emite beeps (`winsound.Beep`) repetidos.
  - Seta `self.running = False` para parar o loop; objetivo: você volta ao PC e decide capturar.

## Percepção (OCR e Detecção)

### Captura de Tela

- Arquivo de captura não foi exibido aqui, mas é típico uso de `mss`/`pyautogui` salvando frames em BGR para OpenCV.

### `GameStateDetector` – `src/perception/game_state_detector.py`

- Carrega templates de:
  - `shiny.png`, `talk.png`, `fight.png`, `bag.png`, `pokemon.png`, `run.png` do diretório `assets/templates`.
- **`detect_state(image)`**
  - Primeiro tenta detectar shiny (matchTemplate global).
  - Depois analisa área de batalha (`detection.battle_area` se configurada):
    - Faz template matching para `fight`, `items` (bag), `pokemon`, `run`.
    - Se qualquer botão tiver score ≥ `battle_button_threshold`, considera `IN_BATTLE`.
  - Caso contrário, `EXPLORING`.
- **`get_battle_info(image)`**
  - Recorta `rois.enemy_name` e `rois.player_name`.
  - OCR com `OCREngine.extract_text_optimized` (`invert_for_white_text=True`).
  - Remove `Lv` e retorna nomes limpos.
  - Planejado: adicionar leitura de HP por barra em ROIs de HP, sem depender de OCR (proporção da barra verde).

### `OCREngine` – `src/perception/ocr_engine.py`

- Centraliza todos os fluxos de OCR, com conhecimento de contexto:

#### `extract_text_optimized(image, whitelist, invert_for_white_text)`

- Upscale 2x (INTER_CUBIC).
- Se `invert_for_white_text=True`:
  - Imagem pode ser 1 canal ou BGR.
  - Para BGR: converte para HSV, gera máscara para regiões claras (texto branco), usa essa máscara como imagem para OCR.
- Caso contrário:
  - Converte para GRAY (respeitando 1 canal).
  - Aplica sharpen (kernel 3x3) + threshold adaptativo gaussiano.
- Usa Tesseract com `--psm 7 --oem 1` e `tessedit_char_whitelist` se fornecido.
- Trata erros com log para evitar crash.

#### `preprocess_dynamic_background_text(image)`

- Pensado para texto branco em botões de moves/HUD:
  - Upscale 3x.
  - BGR→HSV, máscara para branco forte.
  - Inverte (texto preto em fundo branco).
  - Adiciona padding branco para não cortar letras.
  - Retorna imagem 1 canal adequada ao Tesseract.

#### `clean_move_name(text)`

- Responsável por “limpar” nomes de golpes específicos:
  - Regra de negócios (planejada / em uso): remover apenas números e `/` (PP), preservar letras, espaços e hífens.
  - Ex.: `"Thunderbolt  23/25"` → `"Thunderbolt"`.
  - Diferente das regras de nome de pokémon (que devem conservar números quando forem parte do nome ou nível, exceto `Lv`).

#### `ocr_party_list(image_roi)`

- OCR especializado para listas de pokémons (HUD e menu de switch):
  - Upscale forte 4x, GRAY, threshold fixo (180).
  - Inverte, erosão leve para melhorar contornos.
  - Tesseract `--psm 6` (várias linhas) com whitelist alfanumérica.
  - Divide em linhas, remove pedaços com “Lv…” e números isolados, retornando nomes limpos.

## Ação (Input)

### `InputSimulator`

- **Clique genérico:** `click(x, y)` (usa `pyautogui` ou similar).
- **Slots de golpes:**
  - `click_in_slot(slot_index)`:
    - Usa ROIs `rois.moves.slot_1..4`.
    - Clica numa região interna do botão com margens (para evitar bordas invisíveis).
- **Botões de batalha:**
  - `click_fight_button()`:
    - Usa template `fight.png` na tela (ou região de batalha).
    - Usa `cv2.matchTemplate` e threshold `detection.fight_threshold`.
    - Clica dentro da caixa do template com margens de segurança.
  - `click_pokemon_button()`:
    - Mesma lógica com `pokemon.png` e `detection.pokemon_threshold`.
  - `click_run_button()`:
    - Mesma lógica com `run.png` e `detection.run_threshold`.
- **Teclado:**
  - `press(key)`:
    - Para avançar texto (`space`), etc.

## Conhecimento (Dados Persistentes)

### `TeamManager` – `src/knowledge/team_manager.py`

- Mantém:
  - `current_team`: lista volátil com equipe atual lida do HUD/menu (nomes em minúsculo).
  - `known_moves`: dict persistente `{pokemon_name: [move1, move2, ...]}` salvo em `data/known_moves.json`.
- Métodos principais:
  - `update_team_from_hud(ocr_results_list)`:
    - Normaliza nomes lidos (lower, strip) e limita a 6.
  - `update_pokemon_moves(pokemon_name, moves_list)` / `save_moves`:
    - Limpa golpes vazios/curtos, atualiza `known_moves` se muda e salva em disco.
  - `get_moves_for` / `get_moves`:
    - Usado pela `BattleStrategy` para saber quais golpes aquele pokémon tem.

### Outros dados

- `data/pokeapi_pokemon.json`, `data/pokeapi_moves.json`, `data/tipos.json`, etc.:
  - Usados pela camada de estratégia/knowledge para entender tipos, efetividade e golpes.

## Configuração

### `config/settings.yaml` (pontos importantes)

- `assets`:
  - `templates_dir`: pasta base de templates.
  - `talk_image`, `goto_image`, `fight_image`, `run_image`, `pokemon_image`, `shiny_image`, etc.
- `detection`:
  - `talk_search_area`: ROI onde procurar `talk.png`.
  - `talk_threshold`, `goto_threshold`, `battle_button_threshold`.
  - Thresholds específicos para `fight`, `run`, `pokemon` se definidos.
  - `battle_area`: ROI para procurar botões de batalha, reduzindo falso-positivo.
- `rois`:
  - `enemy_name`: área do nome do pokémon inimigo.
  - `player_name`: área do nome do seu pokémon.
  - `moves.slot_1..4`: áreas dos botões de golpe.
  - `switch_menu.container`: área com lista de pokémons no menu de troca.
  - `switch_menu.slot_height`: altura aproximada de cada linha (para clique vertical).
  - (potencial futuro) ROIs para barras de HP.
- `battle`:
  - `fight_to_moves_delay`: tempo entre clique em FIGHT e leitura de golpes.
  - `action_cooldown`: tempo mínimo entre ações (ataque, fuga, troca).
- `bot`:
  - `debug_mode`: se `True`, log detalhado (slots, textos OCR, nomes limpos, etc.).

## Decisões Importantes Já Tomadas

- **Separação de contexto na OCR:**
  - Moves vs. lista de pokémon vs. nomes de pokémon têm pipelines diferentes.
  - *Moves:* texto branco em botão → `process_dynamic_background_text` + whitelist de letras.
  - *Lista HUD/menu:* `ocr_party_list` com vários nomes em bloco.
  - *Nomes de pokémon em batalha:* `extract_text_optimized` com foco em texto branco nos HUDs superiores/inferiores.
- **Clique inicial em FIGHT na batalha:**
  - Decidimos sempre clicar em FIGHT ao entrar no `handle_battle` para garantir que o menu de golpes está aberto antes de qualquer leitura ou decisão de golpe.
- **Uso de templates para botões críticos:**
  - RUN, POKEMON e FIGHT são manuseados via `cv2.matchTemplate`, não por coordenadas fixas, para resistir a pequenas mudanças de layout/resolução.
- **Persistência de conhecimento em JSON:**
  - A base de golpes por pokémon não depende exclusivamente da PokeAPI; o bot aprende o que viu em batalha e reaproveita depois.

## Pontos em Aberto / Próximos Passos Naturais

- **Leitura de HP por barras:**
  - Implementar em `GameStateDetector` algo como `get_hp_ratio(side)`:
    - Recortar ROI da barra de HP, contar pixels verdes vs totais, retornar porcentagem.
    - Integrar na `BattleStrategy` para decidir fuga/troca baseado na vida.
- **Refinamento de ROIs e OCR dos moves:**
  - Ajustar ROIs dos slots de golpe conforme screenshots reais.
  - Testar diferentes thresholds/máscaras para texto branco, buscando nomes consistentes (evitar “ee”, “Oe”).
- **Estratégia de batalha mais rica:**
  - Usar não só tipos, mas também:
    - STAB (mesmo tipo do pokémon).
    - Potência base do golpe.
    - Estado do inimigo (possível no futuro).
- **Melhorias de logs/debug:**
  - Já existem logs por slot; manter o `debug_mode` ativo ao calibrar ROIs e OCR.

## Resumo para Quem For Criar Novos Módulos

- A aplicação já:
  - Detecta estado geral (explorando vs batalha vs shiny).
  - Segue a missão (Goto), conversa (talk), entra em batalha.
  - Lê nomes de pokémon em batalha e da equipe.
  - Lê (ainda de forma imperfeita) os nomes dos golpes.
  - Decide fugir, trocar ou atacar com um golpe escolhido por estratégia.
- Se você for adicionar algo novo (por exemplo, leitura de HP, IA de movimento, estatísticas de farming), use esse padrão:
  - **Percepção:** adicionar no `GameStateDetector`/`OCREngine`/ROIs.
  - **Conhecimento:** colocar bancos em `data/` e helpers em `src/knowledge`.
  - **Decisão:** estender `BattleStrategy` ou criar novas classes em `src/decision`.
  - **Ação:** adicionar métodos em `InputSimulator` se precisar de novos cliques/teclas.
  - **Configuração:** tudo o que for dependente de posição/threshold entra em `config/settings.yaml` para evitar hardcode na lógica.
