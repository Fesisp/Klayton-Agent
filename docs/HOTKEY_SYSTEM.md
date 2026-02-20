# 🎮 Sistema de Controle por Hotkeys - PokeBot

## Visão Geral

O PokeBot agora possui um **Sistema de Hotkeys Globais** que permite controlar o bot em tempo real **sem precisar reiniciar** ou alternar janelas. Você pode mudar entre modos, pausar, retomar e até parar o bot usando apenas teclas de atalho.

### ✨ Principais Vantagens

- ✅ **Controle Instantâneo**: Mude modos sem reiniciar
- ✅ **Funciona em Background**: Mesmo com o jogo em foco
- ✅ **Resposta Imediata**: Comandos processados no próximo loop
- ✅ **Totalmente Configurável**: Personalize as teclas no `settings.yaml`
- ✅ **Prioridade de Comandos**: Ordens sobrepõem autonomia

---

## 🎯 Controles Padrão

| Tecla | Comando | Descrição |
|-------|---------|-----------|
| **F1** | IDLE | Para todas ações, apenas observa |
| **F2** | MISSION | Ativa modo Missão (Goto/Talk) |
| **F3** | HUNTING | Ativa modo Caça (alvos específicos) |
| **F4** | FOLLOW | Ativa modo Seguir Personagem |
| **F5** | PAUSE | Pausa o bot temporariamente |
| **F6** | RESUME | Retoma o bot após pausa |
| **F9** | STOP | Para o bot completamente |

---

## 🚀 Como Usar

### 1. Iniciar o Bot

```powershell
python run_bot.py
```

No início, você verá:

```
🎮 Hotkey Listener inicializado
==================================================
🎮 CONTROLES DISPONÍVEIS:
==================================================
  <F1>     → Estado Ocioso (para tudo)
  <F2>     → Estado Missão (segue Goto/Talk)
  <F3>     → Estado Caça (procura alvos)
  <F4>     → Seguir Personagem
  <F5>     → Pausar Bot
  <F6>     → Retomar Bot
  <F9>     → Parar Bot Completamente
==================================================
✅ Hotkey listener ativo! Pressione as teclas para controlar o bot.
[INFO] Bot Iniciado em modo MISSION!
```

### 2. Usar os Controles

**Durante a execução**, pressione qualquer tecla de controle:

#### Exemplo: Mudar para Modo Caça

```
[Você pressiona F3]

🎮 Hotkey detectada: HUNTING
🎣 Bot mudado para estado HUNTING (Caça)
   → Alvos: ['ditto', 'eevee']
```

O bot **imediatamente** muda de comportamento no próximo loop (~1 segundo).

#### Exemplo: Pausar o Bot

```
[Você pressiona F5]

🎮 Hotkey detectada: PAUSE
⏸️ Bot PAUSADO
   → Pressione F6 para retomar
```

O bot **congela** todas ações, mas continua rodando.

#### Exemplo: Seguir seu Personagem

```
[Você pressiona F4]

🎮 Hotkey detectada: FOLLOW
👤 Bot mudado para estado FOLLOW (Seguir)
   → Bot seguirá seu personagem principal
```

Bot começa a detectar seu personagem e segui-lo.

---

## 🎯 Cenários de Uso

### Cenário 1: Você está jogando manualmente e quer ajuda

**Situação**: Você está explorando e quer que o bot apenas alerte se encontrar Shiny.

**Solução**:
1. Inicie o bot normalmente
2. Pressione **F1** (IDLE)
3. Jogue normalmente
4. Se aparecer Shiny → Bot alerta!

---

### Cenário 2: Você quer que o bot faça missões AFK

**Situação**: Precisa sair do PC mas quer que o bot complete missões.

**Solução**:
1. Posicione personagem na área de missão
2. Pressione **F2** (MISSION)
3. Bot clica em Goto/Talk automaticamente
4. Quando voltar, pressione **F5** (PAUSE) para verificar progresso

---

### Cenário 3: Farm de Pokémon específico

**Situação**: Quer caçar Ditto por 30 minutos.

**Solução**:
1. Configure `hunt.target_pokemon: ["ditto"]` no settings.yaml
2. Pressione **F3** (HUNTING)
3. Bot move-se e foge de tudo exceto Ditto
4. Para parar: **F5** (PAUSE) ou **F1** (IDLE)

---

### Cenário 4: Você quer treinar com conta secundária

**Situação**: Tem 2 contas abertas, quer que o bot siga sua conta principal.

**Solução**:
1. Configure o template do seu personagem (veja abaixo)
2. Pressione **F4** (FOLLOW)
3. Bot detecta e segue seu personagem principal
4. Quando entrar em batalha: bot luta automaticamente
5. Após batalha: volta a seguir

---

## ⚙️ Configuração Avançada

### Personalizar Teclas

Edite `config/settings.yaml`:

```yaml
controls:
  enabled: true
  
  # Use qualquer tecla (formato <tecla>)
  idle_key: "<f1>"
  mission_key: "<f2>"
  hunting_key: "<f3>"
  follow_key: "<f4>"
  pause_key: "<f5>"
  resume_key: "<f6>"
  stop_key: "<f9>"
```

**Teclas disponíveis**:
- Teclas de função: `<f1>` até `<f12>`
- Números: `<1>` até `<0>`
- Letras: `<a>` até `<z>`
- Símbolos: `<space>`, `<enter>`, `<tab>`, etc.
- Combinações: `<ctrl>+<f1>`, `<alt>+<q>`, `<shift>+<f5>`

**Exemplo de customização**:
```yaml
controls:
  idle_key: "<ctrl>+<1>"      # Ctrl+1 para IDLE
  mission_key: "<ctrl>+<2>"   # Ctrl+2 para MISSION
  hunting_key: "<ctrl>+<3>"   # Ctrl+3 para HUNTING
  follow_key: "<ctrl>+<4>"    # Ctrl+4 para FOLLOW
  pause_key: "<space>"        # Espaço para pausar
```

---

## 👤 Sistema de FOLLOW (Seguir Personagem)

### Modo 1: Template Matching (Recomendado)

**Como funciona**: Bot detecta visualmente seu personagem na tela.

#### Setup:

**1. Capture o Sprite do seu Personagem**

Use PrintScreen ou Snipping Tool para capturar **apenas** o sprite do seu personagem:

![Exemplo de sprite](exemplo_sprite.png)

**2. Salve como `player_char.png`**

Salve a imagem em: `assets/templates/player_char.png`

**3. Configure no settings.yaml**

```yaml
follow:
  method: "template"
  player_template: "player_char.png"
  match_threshold: 0.7  # Ajuste se necessário (0-1)
  distance: 50  # Distância mínima em pixels
  check_interval: 1.0  # Verifica a cada 1 segundo
```

**4. Ative o Modo**

Pressione **F4** ou inicie com:
```yaml
bot:
  behavior: "follow"
```

#### Como o Bot se Comporta:

```
[Loop 1]
→ Captura tela
→ Procura player_char.png
→ Encontra em (850, 620)
→ Calcula distância do centro: 95px
→ Distância > 50px → Clica em direção ao personagem

[Loop 2]
→ Captura tela
→ Encontra em (920, 680)
→ Distância: 45px
→ Distância < 50px → Não move (já está perto)

[Loop 3 - Batalha detectada]
→ GameState = IN_BATTLE
→ Pausa Follow temporariamente
→ Luta normalmente com STAB
→ Após batalha → Volta a seguir
```

---

### Modo 2: Party Button (Alternativo)

**Como funciona**: Bot clica no botão "Follow" da party.

#### Setup:

**1. Capture o Botão Follow**

Tire screenshot do botão "Follow" que aparece quando você está em party:

![Exemplo de botão](exemplo_follow_button.png)

**2. Salve como `follow_button.png`**

Salve em: `assets/templates/follow_button.png`

**3. Configure**

```yaml
follow:
  method: "party_button"
  follow_button_template: "follow_button.png"
  button_threshold: 0.75
  check_interval: 2.0  # Clica a cada 2 segundos
```

**Vantagem**: Não precisa capturar sprite do personagem.

**Desvantagem**: Só funciona se estiver em party com outra conta.

---

## 🔄 Sistema de Prioridades com Hotkeys

### Como as Prioridades Funcionam:

```
┌─────────────────────────────────────────┐
│  PRIORIDADE 0: COMANDO MANUAL (Hotkey)  │ ← Nova!
│  → Muda self.behavior imediatamente     │
└─────────────────────────────────────────┘
            ↓
┌─────────────────────────────────────────┐
│  PRIORIDADE 1: SHINY DETECTADO          │
│  → Para tudo e alerta                   │
└─────────────────────────────────────────┘
            ↓
┌─────────────────────────────────────────┐
│  PRIORIDADE 2: BATALHA ATIVA            │
│  → Executa handle_battle()              │
│  → Retorna ao behavior anterior         │
└─────────────────────────────────────────┘
            ↓
┌─────────────────────────────────────────┐
│  PRIORIDADE 3: BEHAVIOR ATIVO           │
│  → IDLE, MISSION, HUNTING ou FOLLOW     │
└─────────────────────────────────────────┘
```

### Exemplo Prático:

**Situação**: Bot está em modo HUNTING procurando Ditto.

```
[Loop 1-5]
Behavior: HUNTING
→ Bot move-se aleatoriamente
→ Encontra Rattata
→ Foge (não é alvo)

[Você pressiona F4 - FOLLOW]
🎮 Hotkey detectada: FOLLOW
👤 Bot mudado para FOLLOW

[Loop 6]
Behavior: FOLLOW  ← Mudou!
→ Bot procura seu personagem
→ Encontra e clica
→ Segue você

[Encontro aleatório - Batalha inicia]
GameState: IN_BATTLE
→ Pausa FOLLOW temporariamente
→ Luta normalmente

[Batalha termina]
GameState: EXPLORING
Behavior: FOLLOW  ← Continua!
→ Volta a seguir você
```

---

## 🎮 Fluxo de Controle Completo

### Inicialização:

```
[main.py]
→ Carrega config
→ Inicializa componentes
→ Cria BotController
→ Inicia HotkeyListener (thread separada)
→ Executa bot.run()
```

### Durante Execução:

```
[Thread Principal - Bot Loop]
while running:
    if paused:  ← Verifica flag de pausa
        sleep(0.5)
        continue
    
    capture_screen()
    detect_state()
    
    if SHINY:
        alert()
    elif BATTLE:
        fight()
    else:
        if IDLE: idle()
        elif MISSION: goto/talk()
        elif HUNTING: hunt()
        elif FOLLOW: follow()  ← Novo!
    
    sleep(loop_interval)

[Thread Secundária - Hotkey Listener]
while running:
    listen_for_hotkeys()
    
    on_hotkey_pressed:
        bot.behavior = new_behavior  ← Muda flag
        # No próximo loop, bot usa novo behavior
```

### Quando você pressiona uma Hotkey:

```
[Tecla F3 pressionada]
↓
[HotkeyListener detecta]
↓
[Callback _on_hotkey() executado]
↓
[bot.behavior = BotBehavior.HUNTING]
↓
[Log: "🎣 Bot mudado para HUNTING"]
↓
[Thread principal continua loop]
↓
[Próxima iteração usa novo behavior]
```

**Latência**: ~1 segundo (tempo do `loop_interval`)

---

## 🐛 Troubleshooting

### Hotkeys não funcionam

**Verificar**:
1. `controls.enabled` está `true`?
2. Biblioteca `pynput` está instalada?
   ```powershell
   pip install pynput
   ```
3. Executa como Administrador (Windows)?

**Solução**:
```powershell
# Reinstalar pynput
pip uninstall pynput
pip install pynput

# Executar como admin
# Botão direito em PowerShell → "Executar como Administrador"
python run_bot.py
```

---

### Bot não segue personagem (modo FOLLOW)

**Verificar**:
1. Template `player_char.png` existe?
2. Template tem boa qualidade (não pixelado)?
3. `match_threshold` não está muito alto?

**Solução**:
```yaml
follow:
  match_threshold: 0.6  # Reduzir para 0.5-0.6
  
bot:
  debug_mode: true  # Ver logs de detecção
```

Logs úteis:
```
[DEBUG] [FOLLOW] Personagem não detectado (score: 0.43)
```

Se score está perto do threshold (ex: 0.65 vs 0.7), reduza o threshold.

---

### Bot segue objeto errado

**Causa**: Template muito genérico (match com outros sprites)

**Solução**:
1. Capture template mais específico (com parte única do seu char)
2. Aumente `match_threshold` para 0.8-0.9
3. Use método `party_button` ao invés de `template`

---

### Pausa não funciona

**Verificar**:
```yaml
controls:
  enabled: true  # Deve estar true
  pause_key: "<f5>"  # Tecla correta?
```

**Teste**:
```
[Pressione F5]

🎮 Hotkey detectada: PAUSE  ← Deve aparecer
⏸️ Bot PAUSADO
```

Se não aparece, hotkey listener não está ativo.

---

## 📊 Comparação: Antes vs Depois

### ANTES (v2.1):
```yaml
# Para mudar modo:
1. Parar bot (Ctrl+C)
2. Editar settings.yaml
3. Salvar
4. Reiniciar bot
5. Esperar carregar

Total: ~30-60 segundos
```

### DEPOIS (v2.2):
```
# Para mudar modo:
1. Pressionar F3 (HUNTING)

Total: ~1 segundo
```

**Ganho de produtividade**: 30-60x mais rápido! 🚀

---

## 🎯 Casos de Uso Avançados

### Caso 1: Farm Intercalado

**Objetivo**: Alternar entre caça de Ditto e Eevee.

**Solução**:
```yaml
# Setup inicial
hunt:
  target_pokemon: ["ditto"]  # Começa com Ditto

# Durante execução:
[Farm Ditto por 15 min]
→ Pressiona F5 (PAUSE)
→ Edita settings.yaml: target_pokemon: ["eevee"]
→ Pressiona F6 (RESUME)
→ Bot automaticamente recarrega config
→ Farm Eevee por 15 min
```

---

### Caso 2: Seguir + Auto Batalha

**Objetivo**: Bot segue você, mas luta sozinho quando encontra inimigo.

**Configuração**:
```yaml
bot:
  behavior: "follow"

follow:
  method: "template"
  player_template: "player_char.png"
  distance: 50
```

**Resultado**:
- Você controla movimento principal
- Bot te segue de perto
- Quando batalha inicia: bot assume e luta
- Após batalha: volta a seguir

**Uso**: Ideal para treinar conta secundária!

---

### Caso 3: Pausa para Diálogos Importantes

**Situação**: Bot está em modo MISSION mas você quer controlar diálogos importantes.

**Solução**:
```
[Bot clicando em Talk/Goto]

[Diálogo importante aparece]
→ Pressiona F5 (PAUSE)
→ Lê e escolhe opção manualmente
→ Confirma escolha
→ Pressiona F6 (RESUME)
→ Bot continua missão
```

---

## 📝 Logs de Exemplo

### Mudança de Modo Bem-Sucedida:

```
[INFO] Bot rodando em modo: MISSION
[DEBUG] GameState: EXPLORING | Behavior: MISSION
[INFO] Botão Goto encontrado. Seguindo missão...

🎮 Hotkey detectada: HUNTING
🎣 Bot mudado para estado HUNTING (Caça)
   → Alvos: ['ditto', 'eevee']

[DEBUG] GameState: EXPLORING | Behavior: HUNTING
[DEBUG] [HUNTING] Movendo para ponto aleatório: (850, 620)
```

### Modo Follow Funcionando:

```
🎮 Hotkey detectada: FOLLOW
👤 Bot mudado para estado FOLLOW (Seguir)
   → Bot seguirá seu personagem principal

[DEBUG] [FOLLOW] Personagem detectado em (920, 680)
[DEBUG] [FOLLOW] Distância do centro: 95px (limite: 50px)
[INFO] 👤 [FOLLOW] Seguindo personagem em (736, 562)
[DEBUG] [FOLLOW] Personagem próximo (distância: 42px)
```

### Pausa e Retomada:

```
[INFO] ⚔️ Batalha: Pikachu vs Rattata

🎮 Hotkey detectada: PAUSE
⏸️ Bot PAUSADO
   → Pressione F6 para retomar

[... bot congela ...]

🎮 Hotkey detectada: RESUME
▶️ Bot RETOMADO

[INFO] Atacando slot 1 contra Rattata
```

---

## 🚀 Conclusão

O Sistema de Hotkeys transforma o PokeBot em uma **ferramenta flexível e responsiva**:

### Benefícios:
- ✅ Controle total em tempo real
- ✅ Sem necessidade de reiniciar
- ✅ Trabalha em background
- ✅ Prioridade de comandos respeitada
- ✅ Modo FOLLOW para contas secundárias

### Próximos Passos:
1. Instalar dependência: `pip install pynput`
2. Configurar templates (se usar FOLLOW)
3. Personalizar teclas (opcional)
4. Testar controles durante execução

**Use com sabedoria! 🎮✨**

---

**Versão: 2.2 - Sistema de Hotkeys**  
**Data: 2026-02-20**
