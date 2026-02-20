# Melhorias de Humanização - PokeBot

## Resumo das Implementações

Este documento descreve as melhorias técnicas implementadas para tornar o PokeBot indistinguível de um jogador humano legítimo.

---

## 1. 🎯 Movimentação Humanizada (Curvas Bezier)

### Arquivo: `src/action/input_simulator.py`

### Mudanças Implementadas:

#### A. Sistema de Movimento em Curva Bezier
- **Método `_bezier_move()`**: Move o mouse em uma trajetória curva suave até o alvo
- **Aleatoriedade**: Ponto de controle da curva varia ±20 pixels para movimentos únicos
- **Número de passos**: Entre 15-25 pontos aleatórios na curva para variação natural

#### B. Método `human_click()`
- Substitui cliques instantâneos por sequência humanizada:
  1. Movimento em curva Bezier até o alvo
  2. Delay randômico (50-150ms) antes do clique
  3. Clique
  4. Pequeno delay pós-clique (20-80ms)

#### C. Sistema de Ações Idle
- **Método `perform_idle_action()`**: Executa ações aleatórias periodicamente
- Ações disponíveis:
  - Pressionar espaço (simula leitura)
  - Mover câmera aleatoriamente
  - Pausas contemplativas
- **Frequência**: 5% de chance a cada 10 segundos (configurável)

### Configuração (settings.yaml):
```yaml
input:
  use_human_movement: true      # Ativa/desativa curvas Bezier
  min_delay: 0.05               # Delay mínimo antes de clicar
  max_delay: 0.15               # Delay máximo antes de clicar
  min_move_duration: 0.2        # Duração mínima do movimento
  max_move_duration: 0.5        # Duração máxima do movimento
  idle_action_chance: 0.05      # Chance de ação idle (0-1)
```

### Dependência Nova:
- **scipy**: Biblioteca para interpolação matemática das curvas

---

## 2. 🤖 Chat Handler com IA

### Arquivo: `src/perception/chat_handler.py` (NOVO)

### Funcionalidades:

#### A. Suporte a Múltiplas APIs de LLM
1. **Ollama (Local)** - Recomendado para privacidade
   - Modelos: llama3, mistral, phi3, etc.
   - Sem custo, 100% offline
   
2. **Google Gemini**
   - Modelos: gemini-pro, gemini-1.5-flash
   - Requer API key
   
3. **OpenAI**
   - Modelos: gpt-3.5-turbo, gpt-4
   - Requer API key e paga por uso

#### B. Personalidades Configuráveis
- **Casual**: Jogador relaxado e amigável
- **Competitive**: Focado em estratégia
- **Friendly**: Muito sociável
- **Quiet**: Tímido, respostas curtas

#### C. Timing Humanizado
- Tempo de "leitura" antes de responder: 2-5 segundos (configurável)
- Digitação caractere por caractere com delays variáveis (50-150ms)
- Pausas maiores em espaços e pontuação (1.5-2.5x)

#### D. Controle de Frequência
- `response_chance`: Probabilidade de responder (padrão: 30%)
- Limite de 50 caracteres para respostas curtas e naturais

### Configuração (settings.yaml):
```yaml
chat:
  enabled: false                # Ativar/desativar
  provider: "ollama"            # ollama, gemini, openai
  model: "llama3"               # Modelo específico
  api_key: ""                   # Para Gemini/OpenAI
  base_url: "http://localhost:11434"  # URL do Ollama
  response_chance: 0.3          # 30% de chance de responder
  min_response_time: 2.0        # Mínimo 2s para responder
  max_response_time: 5.0        # Máximo 5s para responder
  personality: "casual"         # Estilo de conversa
```

### Como Usar com Ollama (Gratuito):
```powershell
# 1. Instalar Ollama: https://ollama.ai/download
# 2. Baixar modelo:
ollama pull llama3

# 3. Iniciar servidor (já inicia automaticamente no Windows)
ollama serve

# 4. Ativar no settings.yaml:
chat:
  enabled: true
  provider: "ollama"
  model: "llama3"
```

### Dependência Nova:
- **requests**: Para chamadas HTTP às APIs

---

## 3. ❤️ Detecção de HP (Barras de Vida)

### Arquivo: `src/perception/game_state_detector.py`

### Mudanças Implementadas:

#### A. Método `_get_hp_percentage()`
- Analisa barras de HP usando detecção de cor (HSV)
- Detecta cores: Verde (>50%), Amarelo (25-50%), Vermelho (<25%)
- Calcula porcentagem baseado na largura da barra preenchida
- Precisão estimada: ±5%

#### B. Método `get_battle_info()` Melhorado
Retorna agora:
```python
{
    "enemy_name": str,
    "player_name": str,
    "player_hp_percentage": float,      # 0-100
    "enemy_hp_percentage": float,       # 0-100
    "player_hp_critical": bool,         # < 25%
    "player_hp_low": bool,              # < 50%
}
```

### Configuração (settings.yaml):
```yaml
rois:
  player_hp_bar: [1517, 1046, 1732, 1071]  # ROI da barra de HP do player
  enemy_hp_bar: [57, 33, 272, 58]          # ROI da barra de HP do inimigo
```

### Aplicação:
- Usado para decidir quando trocar de Pokémon
- Usado para decidir quando usar itens de cura
- Previne que o Pokémon desmaia

---

## 4. 🎲 Sistema de Pesos Melhorado (STAB)

### Arquivo: `src/decision/battle_strategy.py`

### Mudanças Implementadas:

#### A. Cálculo STAB (Same Type Attack Bonus)
- **Bônus de 1.5x** quando o tipo do movimento = tipo do Pokémon
- Exemplo: Charizard usando Flamethrower (Fogo) = 1.5x power

#### B. Novos Fatores de Decisão
1. **Power Base**: Poder do movimento
2. **STAB**: 1.5x se mesmo tipo
3. **Efetividade de Tipo**: 0.25x, 0.5x, 1x, 2x, 4x
4. **Prioridade**: +10 pontos por nível de prioridade (Quick Attack, etc.)
5. **Accuracy**: Penaliza movimentos imprecisos proporcionalmente
6. **Status Moves**: -50 pontos para golpes sem dano

#### C. Fórmula Final
```python
score = power * stab_bonus * type_multiplier * (accuracy/100)
score += priority * 10
score -= 50 if (power == 0 and is_status_move)
```

#### D. Métodos de Decisão de HP
- **`should_use_item(hp_percentage)`**: Recomenda item se HP < 25%
- **`should_switch_pokemon(hp_percentage, enemy)`**: Recomenda troca se HP < 30%

### Exemplo de Escolha:
```
Pokémon: Charizard (Fire/Flying)
Inimigo: Bulbasaur (Grass/Poison)

Movimentos:
1. Flamethrower (Fire, 90 power)
   - STAB: 1.5x
   - Tipo: 2x (Fire vs Grass)
   - Score: 90 * 1.5 * 2 = 270

2. Wing Attack (Flying, 60 power)
   - STAB: 1.5x
   - Tipo: 1x (Flying vs Grass)
   - Score: 60 * 1.5 * 1 = 90

Escolha: Slot 1 (Flamethrower) ✅
```

---

## 5. 📊 Relatório de Mudanças

| Módulo | Mudança | Impacto |
|--------|---------|---------|
| **Percepção** | Implementação de ROI para Barras de HP | Permite uso de itens e trocas estratégicas antes de desmaiar |
| **Decisão** | Sistema de Pesos com STAB | Bot considera efetividade real e bônus de tipo, não apenas slot 1 |
| **Ação** | Randomização de Delay (jitter) | Evita detecção por padrões de tempo perfeitos (ex: 0.5s fixo) |
| **Conhecimento** | Aprendizado de Moveset Persistente | Bot "lembra" golpes mesmo após reiniciar (known_moves.json) |
| **Interface** | Fallback de Interação Humana | Pressionar espaço e mover câmera simula jogador entediado |
| **Chat** | Sistema de Resposta com IA | Bot pode conversar de forma natural (opcional) |

---

## 6. ⚙️ Como Ativar as Melhorias

### Passo 1: Instalar Dependências
```powershell
pip install -r requirements.txt
```

### Passo 2: Configurar settings.yaml
```yaml
# Ativar movimentação humanizada
input:
  use_human_movement: true
  idle_action_chance: 0.05

# Configurar ROIs de HP (ajustar para sua resolução)
rois:
  player_hp_bar: [1517, 1046, 1732, 1071]
  enemy_hp_bar: [57, 33, 272, 58]

# (Opcional) Ativar chat com IA
chat:
  enabled: false  # Mude para true se quiser
  provider: "ollama"
  model: "llama3"
```

### Passo 3: Testar
```powershell
python run_bot.py
```

---

## 7. 🔒 Considerações Anti-Detecção

### O Que Foi Implementado:
✅ Movimentos em curva (não lineares)  
✅ Delays randômicos entre ações  
✅ Ações idle espontâneas  
✅ Variação de tempo de resposta  
✅ Digitação humanizada (velocidade variável)  
✅ Decisões baseadas em lógica real (STAB, tipos, HP)  

### O Que AINDA Pode Ser Detectado:
⚠️ Tempo de jogo contínuo (bots jogam 24/7)  
⚠️ Padrões de movimento no mapa (mesma rota repetida)  
⚠️ Velocidade de reação perfeita a eventos visuais  
⚠️ Ausência de erros humanos (misclicks, teclas erradas)  

### Recomendações Adicionais:
1. **Não jogue 24/7**: Faça pausas de 2-4 horas a cada 6-8 horas
2. **Varie rotas**: Não repita exatamente o mesmo caminho
3. **Simule AFK**: Pare ocasionalmente por 1-2 minutos
4. **Erre propositalmente**: Clique em lugares errados às vezes (futuro)
5. **Use VPN/Proxy**: Evite bans por IP se reiniciar muitas contas

---

## 8. 📝 Logs de Exemplo

### Com STAB e Tipos:
```
[INFO] Meu Pokémon: Charizard | tipos=[10, 3]  # Fire, Flying
[INFO] Inimigo: Bulbasaur | tipos=[12, 4]      # Grass, Poison
[DEBUG] STAB aplicado para 'Flamethrower' (tipo 10 em [10, 3])
[DEBUG] Avaliação golpe slot 0 'Flamethrower': power=90, stab=1.5, type_mult=2.0, score=270.00
[DEBUG] Avaliação golpe slot 1 'Wing Attack': power=60, stab=1.5, type_mult=1.0, score=90.00
[INFO] Melhor golpe escolhido: slot=0, score=270.00
```

### Com Detecção de HP:
```
[INFO] HP do player: 23.5% (CRÍTICO!)
[INFO] HP crítico (23.5%) - recomendando uso de item
```

### Com Chat IA:
```
[INFO] Mensagem detectada: hey how are you?
[INFO] Aguardando 3.24s antes de responder...
[INFO] Resposta enviada: good bro just hunting shinies hbu
```

---

## 9. 🚀 Melhorias Futuras Sugeridas

1. **Padrões de Erro Humano**:
   - Misclicks ocasionais (5% de chance de clicar em lugar errado)
   - Teclas erradas no chat (typos)
   
2. **Detecção de Contexto**:
   - Ler mensagens de sistema (level up, item encontrado)
   - Reagir a eventos específicos
   
3. **Aprendizado por Reforço**:
   - Melhorar estratégia baseado em vitórias/derrotas
   - Adaptar timing baseado em desempenho

4. **Integração com Captcha**:
   - Notificar usuário quando captcha aparece
   - Pausar bot automaticamente

---

## 10. 📚 Referências

- **Curvas Bezier**: https://en.wikipedia.org/wiki/B%C3%A9zier_curve
- **STAB Pokemon**: https://bulbapedia.bulbagarden.net/wiki/Same-type_attack_bonus
- **Ollama**: https://ollama.ai/
- **Scipy Interpolate**: https://docs.scipy.org/doc/scipy/reference/interpolate.html

---

**Desenvolvido com ❤️ para PokeBot**  
*Versão: 2.0 - Humanização Completa*
