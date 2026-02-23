# 🎯 Motor Avançado de Cálculo de Dano e Risco - v2.5

## 📋 Visão Geral

Sistema avançado de **projeção de turnos** que analisa se atacar, curar ou trocar é a melhor decisão com base em:
- ✅ Cálculo de dano esperado do inimigo
- ✅ Análise de velocidade (Speed Tier)
- ✅ Inferência automática de itens (Choice Scarf, Choice Band, Life Orb)
- ✅ Avaliação de risco/recompensa antes de cada decisão

---

## 🧠 Lógica de Decisão

### Prioridade 0: Avaliação de Risco (Nova!)

Antes de escolher qualquer ataque, o bot agora avalia:

```
Se vou morrer no próximo turno E NÃO sou mais rápido:
   └─> SWITCH_PRIORITY (troca obrigatória)

Se HP < 40% E tenho movimento de cura:
   ├─> Sou mais rápido? → HEAL_NOW
   ├─> Aguento o próximo hit? → HEAL_NOW
   └─> Vou morrer curando? → SWITCH_OR_SACRIFICE

Se inimigo HP < 20%:
   └─> ATTACK (finalizar)

Caso contrário:
   └─> ATTACK (continua análise tática normal)
```

---

## 🔧 Novos Métodos

### `calculate_incoming_damage(enemy_poke, my_poke)`

**Descrição:** Projeta quanto dano o inimigo causará no próximo turno.

**Fórmula:**
```python
base_damage = 0.3  # ~30% HP base
estimated_damage = base_damage * type_multiplier

# Ajustes por item inferido:
if enemy_item == "Choice Band": damage *= 1.5
if enemy_item == "Life Orb": damage *= 1.3
```

**Exemplo:**
```python
>>> strategy.calculate_incoming_damage("Pikachu", "Blastoise")
0.6  # 60% de dano esperado (super efetivo)
```

---

### `evaluate_risk_reward(my_poke, enemy_poke)`

**Descrição:** Julga a viabilidade de sobrevivência antes de atacar.

**Retornos:**
- `"SWITCH_PRIORITY"` - Vou morrer, trocar é obrigatório
- `"HEAL_NOW"` - Cura é segura e necessária
- `"SWITCH_OR_SACRIFICE"` - Cura é suicídio, trocar ou aceitar derrota
- `"ATTACK"` - Seguro para atacar

**Exemplo de Log:**
```
⚠️ RISCO CRÍTICO: Vou morrer no próximo turno (HP=35%, Dano esperado=50%)
🔄 Motor de Risco recomendou TROCA OBRIGATÓRIA!
```

---

### Inferência Automática de Itens

#### Como Funciona:
1. **Turno 1:** Bot registra se foi ultrapassado em velocidade
2. **Turno 2:** Compara sua speed com a máxima possível do inimigo
3. **Inferência:** Se foi ultrapassado mas deveria ser mais rápido → Choice Scarf

**Código:**
```python
if last_turn_outspeeded and my_speed > enemy_max_speed:
    enemy_item_inference = "Choice Scarf"
    enemy_speed *= 1.5  # Ajusta cálculos futuros
```

**Exemplo de Log:**
```
⚠️ INFERÊNCIA AUTOMÁTICA: Pikachu detectado com Choice Scarf ou similar!
(Minha speed=120 > Max dele sem item=95)
```

---

## 🎮 Integração com Bot Controller

### Fluxo de Batalha Atualizado

```python
# 1. Estratégia avalia risco ANTES de escolher movimento
best_slot = strategy.get_best_move(my_poke, enemy_name)

# 2. Se retornar -1, significa SWITCH_PRIORITY
if best_slot == -1:
    switch_idx = strategy.choose_switch_target(enemy_name)
    
    # Executa troca de emergência
    input.click_pokemon_button()
    input.click(switch_slot)
    return  # Não ataca, apenas troca
```

---

## 📊 Exemplos Práticos

### Cenário 1: Jolteon vs Pikachu com Choice Scarf

**Situação:**
- Jolteon (Speed 130) vs Pikachu (Speed base 90)
- Jolteon deveria ser mais rápido, mas Pikachu atacou primeiro

**Turno 1:**
```
Speed Tier: Jolteon(130) vs Pikachu(99) = FASTER ⚡
[Pikachu ataca primeiro - inesperado!]
```

**Turno 2:**
```
⚠️ INFERÊNCIA AUTOMÁTICA: Pikachu detectado com Choice Scarf!
Speed Tier: Jolteon(130) vs Pikachu(148) = SLOWER 🐌
```

**Decisão:**
- Bot agora sabe que Pikachu é mais rápido
- Ajusta estratégia para evitar ataques arriscados

---

### Cenário 2: HP Crítico - Decidir entre Curar ou Trocar

**Situação:**
- Meu HP: 35%
- Inimigo: Machamp (tipo Fighting)
- Tenho: Roost (cura)
- Sou mais lento

**Análise:**
```python
my_hp = 0.35
estimated_damage = 0.5  # ~50% (super efetivo)
i_am_faster = False

# Avaliar cura:
if my_hp - estimated_damage > 0.1:  # 0.35 - 0.5 = -0.15 ❌
    return "HEAL_NOW"
else:
    return "SWITCH_OR_SACRIFICE"  # ✅ Escolhido
```

**Decisão:**
```
⚠️ CURA INVIÁVEL: Vou morrer tentando curar (HP=35%, Dano=50%)
🔄 Motor de Risco recomendou TROCA OBRIGATÓRIA!
```

---

### Cenário 3: Inimigo Quase Morto - Finalizar

**Situação:**
- Meu HP: 20%
- Inimigo HP: 15%
- Sou mais lento

**Análise:**
```python
if enemy_hp < 0.2:  # 15% < 20% ✅
    return "ATTACK"  # Finaliza mesmo em risco
```

**Decisão:**
```
🎯 FINALIZAR: Inimigo com HP crítico (15%)
⚔️ PRIORIDADE 6 - DAMAGE OUTPUT: Thunderbolt (score=180.5)
```

---

## 🔄 Comparação: Antes vs Depois

### ❌ Antes (v2.4)
```python
# Escolhia ataque mais forte, sem considerar risco
best_move = max(moves, key=lambda m: m.power * m.type_mult)
```

**Problemas:**
- ✗ Tentava curar mesmo que fosse morrer no processo
- ✗ Não detectava quando trocar era melhor que atacar
- ✗ Ignorava velocidade do inimigo

### ✅ Depois (v2.5)
```python
# Avalia risco ANTES de escolher movimento
risk = evaluate_risk_reward(my_poke, enemy_poke)

if risk == "SWITCH_PRIORITY":
    return -1  # Sinaliza troca obrigatória
    
if risk == "HEAL_NOW":
    return healing_move_slot
    
# Continua com análise tática normal...
```

**Melhorias:**
- ✓ Projeta se vai sobreviver ao próximo turno
- ✓ Só cura quando é seguro
- ✓ Detecta quando trocar salva o Pokémon
- ✓ Infere itens automaticamente

---

## 🛠️ Configuração

### Ajustar Thresholds de Risco

Edite `src/decision/battle_strategy.py`:

```python
# Linha ~240
if my_hp < 0.4:  # Mudar para 0.3 (30%) se preferir curas mais conservadoras
    # Lógica de cura...

# Linha ~260
if enemy_hp < 0.2:  # Mudar para 0.3 (30%) para finalizar mais cedo
    return "ATTACK"
```

### Adicionar Healing Moves Custom

Em `config/settings.yaml`:

```yaml
strategy:
  healing_move_names:
    - recover
    - roost
    - giga drain  # Adicionar aqui
    - drain punch
```

---

## 📈 Performance

### Tempo de Processamento
- **Avaliação de Risco:** ~5-10ms
- **Cálculo de Dano:** ~2-5ms
- **Inferência de Item:** ~1ms (apenas quando detectado)

**Total:** ~10-15ms adicional por turno (aceitável)

---

## 🐛 Troubleshooting

### "Estratégia escolheu slot -1"
**Causa:** Motor de risco detectou SWITCH_PRIORITY mas bot controller não processou.

**Solução:** Verifique se o código de troca de emergência está ativo em `handle_battle()`.

### "Stats de velocidade não encontrados"
**Causa:** `pokemon_database.py` não tem `get_base_stats()` implementado.

**Solução:** O método já foi adicionado nesta versão. Verifique se `data/pokeapi_pokemon.json` existe.

### "Inimigo sempre detectado com Choice Scarf"
**Causa:** `last_turn_outspeeded` não está sendo resetado entre batalhas.

**Solução:** Adicione reset no início de `handle_battle()`:
```python
self.strategy.last_turn_outspeeded = False
self.strategy.enemy_item_inference = None
```

---

## 🎓 Próximos Passos

### v2.6 - Sugestões Futuras
- [ ] Cálculo de dano real (base stats + level + IVs)
- [ ] Detecção de status (paralisia reduz speed em 50%)
- [ ] Weather/Terrain effects (Rain Dance, Electric Terrain)
- [ ] Predição de movimentos do inimigo (padrões)

---

**Atualizado:** Fevereiro 2026  
**Versão:** 2.5.0  
**Status:** ✅ Testável
