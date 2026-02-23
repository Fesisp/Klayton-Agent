# 🎯 Guia Rápido - Modo FOLLOW v2.4

## 📋 Pré-requisitos
1. PokeBot Pro v2.4+ instalado
2. Tesseract OCR configurado (para detecção por nome)
3. Template do personagem (opcional, para fallback)

---

## ⚙️ Configuração Inicial

### 1. Configurar Nome do Jogador
Edite `config/settings.yaml`:

```yaml
follow_settings:
  player_name: "Spinola"  # ⚠️ SUBSTITUA pelo seu nick exato do jogo
  min_confidence: 0.7            # Confiança do template matching
  lost_target_timeout: 5.0       # Segundos antes de desistir
  check_interval: 1.0            # Intervalo entre verificações
```

### 2. Verificar ROIs de HP
Certifique-se de que as coordenadas estão corretas:

```yaml
rois:
  hp_player: [1517, 1046, 1732, 1071]  # Barra HP do jogador
  hp_enemy: [57, 33, 272, 58]          # Barra HP do inimigo
```

**💡 Dica:** Use `tools/roi_picker.py` para capturar coordenadas exatas.

---

## 🎮 Como Usar

### Método 1: Hotkey (Recomendado)
1. Inicie o bot: `python run_bot.py`
2. Pressione **F4** para ativar modo FOLLOW
3. O bot começará a seguir automaticamente

### Método 2: Configuração Permanente
Edite `config/settings.yaml`:

```yaml
bot:
  behavior: "follow"  # Modo padrão ao iniciar
```

---

## 🧪 Testando a Detecção

### Teste 1: Detecção de HP
```python
from src.perception.game_state_detector import GameStateDetector
from src.perception.screen_capture import ScreenCapture
import yaml

# Carregar configuração
with open('config/settings.yaml', 'r', encoding='utf-8') as f:
    cfg = yaml.safe_load(f)

# Inicializar
screen = ScreenCapture(cfg)
detector = GameStateDetector(cfg)

# Capturar e testar
img = screen.capture()
hp = detector.get_hp_ratio(img, 'player')
print(f"✅ HP do jogador: {hp * 100:.1f}%")
```

### Teste 2: Detecção de Nome
```python
# Continuando do Teste 1...
pos = detector.find_player_name(img, "FelipeSpinola")
if pos:
    print(f"✅ Jogador encontrado em {pos}")
else:
    print("❌ Jogador não encontrado")
```

### Teste 3: Template Matching
Capture uma imagem do personagem que deseja seguir:

1. Use `tools/roi_picker.py` para capturar sprite
2. Salve como `assets/templates/player_char.png`
3. Configure em `settings.yaml`:

```yaml
follow:
  method: "template"
  player_template: "player_char.png"
  match_threshold: 0.7
```

---

## 🐛 Solução de Problemas

### ❌ "Jogador não encontrado"
**Causas:**
1. Nome configurado incorretamente (case-sensitive!)
2. Jogador fora da área de busca (800x800px)
3. OCR falhou na leitura

**Soluções:**
- Verifique o nome exato no jogo
- Aproxime-se do jogador alvo
- Tente método `template` como fallback

```yaml
follow:
  method: "template"  # Usar template ao invés de OCR
```

### ❌ "Bot fica vibrando"
**Causa:** `follow.distance` muito baixo

**Solução:**
```yaml
follow:
  distance: 100  # Aumentar distância mínima (padrão: 50)
```

### ❌ "Bot perde o alvo muito rápido"
**Causa:** `lost_target_timeout` muito curto

**Solução:**
```yaml
follow_settings:
  lost_target_timeout: 10.0  # Aumentar para 10 segundos
```

### ❌ "Detecção de HP sempre retorna 0%"
**Causa:** ROIs de HP incorretos

**Solução:**
1. Execute `tools/roi_picker.py`
2. Selecione a barra de HP na tela
3. Atualize coordenadas em `settings.yaml`

---

## 📊 Comportamento Esperado

### Estado Normal (Alvo Visível)
```
[INFO] 👤 [FOLLOW] Nome 'FelipeSpinola' encontrado em (800, 600)
[INFO] 👤 [FOLLOW] Movendo para alvo (distância: 120px)
```

### Estado de Memória (Alvo Temporário Invisível)
```
[DEBUG] [FOLLOW] Alvo não visível, usando última posição conhecida
[INFO] 👤 [FOLLOW] Movendo para última posição (780, 590)
```

### Estado de Recuperação (Busca Ativa)
```
[INFO] 🔍 [FOLLOW] Alvo perdido! Tentando recuperar...
[DEBUG] [FOLLOW] Rotacionando câmera para procurar
```

### Estado de Desistência
```
[WARN] ⏱️ [FOLLOW] Timeout de 5.0s atingido, alvo não recuperado
[INFO] [FOLLOW] Retornando ao estado IDLE
```

---

## 🎯 Dicas de Uso

### 1. Multi-Conta (Party)
Se você está em party com outra conta:

```yaml
follow:
  method: "party_button"  # Usa botão "Follow" da UI
  follow_button_template: "follow_button.png"
```

### 2. Movimento Humanizado
O bot já usa movimento humanizado por padrão:
- ✅ Delay aleatório antes de clicar (0.05-0.15s)
- ✅ Movimento em curva Bezier
- ✅ Tempo de caminhada proporcional à distância

### 3. Debug Mode
Para ver logs detalhados:

```yaml
bot:
  debug_mode: true  # Ativa logs DEBUG
```

### 4. Prioridade de Estados
O bot respeita a hierarquia:

1. **SHINY** (máxima prioridade)
2. **BATALHA** (alta prioridade)
3. **FOLLOW** (média prioridade)

**Exemplo:** Se um shiny aparecer durante FOLLOW, o bot para imediatamente.

---

## 📈 Otimização de Performance

### CPU Limitada
```yaml
screen:
  fps: 5  # Reduzir FPS (padrão: 10)

follow_settings:
  check_interval: 2.0  # Aumentar intervalo (padrão: 1.0)
```

### Precisão Máxima
```yaml
follow_settings:
  min_confidence: 0.85  # Aumentar confiança (padrão: 0.7)
  check_interval: 0.5   # Diminuir intervalo (padrão: 1.0)
```

---

## 🔧 Comandos Úteis

### Testar OCR do Tesseract
```powershell
& "C:\Program Files\Tesseract-OCR\tesseract.exe" imagem.png stdout --psm 6
```

### Capturar Screenshot para Debug
```python
python -c "from mss import mss; import cv2; cv2.imwrite('debug.png', mss().grab(mss().monitors[1]))"
```

### Ver Logs em Tempo Real
```powershell
Get-Content logs/pokebot.log -Wait -Tail 20
```

---

## 📞 Suporte

### Logs
Verifique `logs/pokebot.log` para erros detalhados.

### Issues
Reporte bugs com:
1. Versão do PokeBot
2. Conteúdo de `settings.yaml` (sem informações sensíveis)
3. Últimas 50 linhas do log
4. Screenshot do problema (se aplicável)

---

## 📚 Recursos Adicionais

- **Documentação Completa:** `docs/PROJECT_OVERVIEW.md`
- **Changelog:** `docs/CHANGELOG_v2.4.md`
- **Testes:** `tests/test_ocr_and_strategy.py`

---

**Atualizado:** Janeiro 2025  
**Versão:** 2.4.0
