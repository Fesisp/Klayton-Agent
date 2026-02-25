# 🔄 Guia de Migração - Refatoração PokeBot v2.6

## ⚡ Resumo Rápido

A refatoração consolidou o código em uma arquitetura mais limpa. Se você está usando o bot normalmente via `python run_bot.py`, **nada muda**. Este guia é para quem modificou o código base.

---

## 📦 Arquivos Deletados

### ❌ `src/action/battle_controller.py`
**Motivo:** Lógica movida para `BattleStrategy`

**Se você importava:**
```python
# ❌ REMOVER
from src.action.battle_controller import BattleController
```

**Solução:** Não é mais necessário. `BotController.handle_battle()` gerencia tudo.

---

## 🔧 APIs Modificadas

### 1. Detecção de HP

#### ❌ API Antiga (Removida)
```python
# Múltiplos métodos confusos
hp_percent = detector._get_hp_percentage(image, 'player_hp_bar')
```

#### ✅ API Nova (Unificada)
```python
# Método único e consistente
hp_ratio = detector.get_hp_ratio_by_pixel(frame, 'player')  # 0.0 a 1.0
hp_percent = round(hp_ratio * 100, 1) if hp_ratio else None
```

**Conversão Automática:**
```python
# Antes
player_hp = self._get_hp_percentage(image, 'player_hp_bar')

# Depois
player_hp_ratio = self.get_hp_ratio_by_pixel(image, 'player')
player_hp = round(player_hp_ratio * 100, 1) if player_hp_ratio else None
```

---

### 2. Modo Follow

#### ❌ API Antiga (Duplicada)
```python
# Dois métodos fazendo a mesma coisa
bot.handle_follow_behavior(frame)  # Versão 1
bot.handle_follow(frame)            # Versão 2
```

#### ✅ API Nova (Consolidada)
```python
# Método único otimizado
bot.handle_follow(frame)  # Template Matching prioritário + OCR fallback
```

**O que mudou:**
- ✅ Template Matching em **escala de cinza** (mais preciso)
- ✅ OCR como **Deep Search** após 3 segundos
- ✅ Detecção de obstáculos via `NavigationHelper`

---

### 3. Sistema Anti-Stuck

#### ❌ API Antiga (Acoplada)
```python
# Métodos privados no BotController
if self._is_stuck_on_obstacle(pos, time):
    self._perform_escape_movement()
```

#### ✅ API Nova (Desacoplada)
```python
# NavigationHelper reutilizável
if self.nav_helper.is_stuck(pos, time):
    self.nav_helper.perform_escape_movement()
```

**Benefícios:**
- ✅ Disponível para MISSION, FOLLOW e HUNTING
- ✅ Configurável via `settings.yaml`
- ✅ Testável independentemente

---

### 4. Turn Counter em Batalha

#### ❌ API Antiga
```python
# Dentro de BattleController (agora deletado)
battle_controller.turn_count += 1
```

#### ✅ API Nova
```python
# Agora em BattleStrategy
strategy.increment_turn()
turn = strategy.get_turn_count()
```

**Métodos Disponíveis:**
```python
strategy.reset_battle_state()       # Reset no início da batalha
strategy.set_current_enemy(name)    # Define inimigo atual
strategy.increment_turn()           # Incrementa contador
strategy.get_turn_count()          # Retorna turno atual
strategy.update_last_action_time() # Atualiza timestamp
```

---

## 🔍 Checklist de Migração

### Para Usuários Normais
- [ ] Nada! Bot funciona igual. Execute: `python run_bot.py`

### Para Desenvolvedores

#### 1. Importações
```bash
# Busque por importações antigas
grep -r "from src.action.battle_controller" .
grep -r "BattleController" .
```
- [ ] Remover importações de `battle_controller.py`

#### 2. Métodos de HP
```bash
# Busque por métodos antigos
grep -r "_get_hp_percentage" .
```
- [ ] Substituir por `get_hp_ratio_by_pixel()`

#### 3. Métodos Follow
```bash
# Busque por chamadas antigas
grep -r "handle_follow_behavior" .
```
- [ ] Renomear para `handle_follow()`

#### 4. Detecção de Obstáculos
```bash
# Busque por métodos privados
grep -r "_is_stuck_on_obstacle" .
grep -r "_perform_escape_movement" .
```
- [ ] Substituir por `nav_helper.is_stuck()` e `nav_helper.perform_escape_movement()`

---

## 🧪 Validação Pós-Migração

### Teste 1: Compilação
```bash
python -m py_compile src/**/*.py
```
**Esperado:** Sem erros

### Teste 2: Importações
```bash
python -c "from src.core.bot_controller import BotController; print('OK')"
```
**Esperado:** `OK`

### Teste 3: Execução
```bash
python run_bot.py
```
**Esperado:** Bot inicia normalmente

### Teste 4: Funcionalidades
- [ ] Detecção de batalha funciona
- [ ] Modo FOLLOW funciona
- [ ] Modo MISSION funciona
- [ ] Detecção de shiny funciona

---

## 📝 Exemplos Completos

### Exemplo 1: Usando NavigationHelper em Modo Customizado

```python
from src.utils.navigation_helper import NavigationHelper

class MyCustomMode:
    def __init__(self, input_sim, config):
        self.input = input_sim
        self.nav = NavigationHelper(input_sim, config)
    
    def move_to_target(self, target_pos):
        current_time = time.time()
        
        # Verifica obstáculo
        if self.nav.is_stuck(target_pos, current_time):
            logger.warning("Preso! Escapando...")
            self.nav.perform_escape_movement()
            return False
        
        # Move normalmente
        self.input.click(*target_pos)
        return True
    
    def reset(self):
        self.nav.reset_stuck_detection()
```

### Exemplo 2: Consultando Turn Counter

```python
# Durante batalha
def my_battle_logic(strategy, my_pokemon, enemy):
    # Verifica turno atual
    current_turn = strategy.get_turn_count()
    
    if current_turn == 1:
        # Primeiro turno: ataque conservador
        return strategy.get_best_move(my_pokemon, enemy)
    
    elif current_turn > 5:
        # Batalha longa: considerar fuga
        if strategy.should_flee(my_pokemon, enemy):
            return -1  # Código de fuga
    
    # Turno normal
    return strategy.get_best_move(my_pokemon, enemy)
```

### Exemplo 3: HP Detection Unificado

```python
def check_team_health(detector, frame):
    """Verifica HP de todo o time"""
    player_hp = detector.get_hp_ratio_by_pixel(frame, 'player')
    
    if player_hp is None:
        return "HP não detectado"
    
    if player_hp < 0.25:
        return "CRÍTICO"
    elif player_hp < 0.50:
        return "BAIXO"
    elif player_hp < 0.75:
        return "MÉDIO"
    else:
        return "ALTO"
```

---

## ⚠️ Problemas Comuns

### Problema 1: ImportError de BattleController
```
ImportError: cannot import name 'BattleController' from 'src.action.battle_controller'
```
**Solução:** Remova a importação. Use `BotController.handle_battle()` diretamente.

### Problema 2: AttributeError no detector
```
AttributeError: 'GameStateDetector' object has no attribute '_get_hp_percentage'
```
**Solução:** Use `get_hp_ratio_by_pixel()` em vez de `_get_hp_percentage()`.

### Problema 3: NavigationHelper não encontrado
```
ModuleNotFoundError: No module named 'src.utils.navigation_helper'
```
**Solução:** O arquivo foi criado. Certifique-se de que está na última versão.

### Problema 4: handle_follow_behavior não existe
```
AttributeError: 'BotController' object has no attribute 'handle_follow_behavior'
```
**Solução:** Use `handle_follow()` (sem o sufixo `_behavior`).

---

## 🎯 Configuração do NavigationHelper

### Adicione ao `config/settings.yaml`:

```yaml
# Sistema de Navegação Anti-Stuck
navigation:
  # Tempo em segundos até detectar que está preso
  stuck_threshold: 5.0
  
  # Distância em pixels para considerar "mesmo alvo"
  stuck_distance_tolerance: 10
  
  # Cooldown entre tentativas de escape
  escape_cooldown: 5.0
  
  # Máximo de tentativas antes de desistir
  max_escape_attempts: 3
```

---

## 📞 Suporte

### Erros Persistentes?

1. **Limpe cache Python:**
   ```bash
   find . -type d -name "__pycache__" -exec rm -rf {} +
   ```

2. **Reinstale dependências:**
   ```bash
   pip install -r requirements.txt --force-reinstall
   ```

3. **Verifique versão Python:**
   ```bash
   python --version  # Deve ser 3.8+
   ```

---

## ✅ Checklist Final

Antes de considerar a migração completa:

- [ ] `battle_controller.py` deletado do projeto
- [ ] Nenhum erro de importação
- [ ] Bot inicia sem erros
- [ ] Modo MISSION funciona
- [ ] Modo FOLLOW funciona  
- [ ] Modo HUNTING funciona
- [ ] Detecção de batalha funciona
- [ ] Sistema anti-stuck funciona
- [ ] Tests passam (se houver)

---

**Dúvidas?** Consulte `REFACTORING_REPORT.md` para detalhes técnicos completos.

**Versão:** 2.6.0  
**Data:** 25 de Fevereiro de 2026
