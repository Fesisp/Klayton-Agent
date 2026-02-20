# 🚀 Guia Rápido - Ativando as Melhorias de Humanização

## Instalação

### 1. Instalar Novas Dependências
```powershell
pip install scipy requests
```
Ou reinstalar tudo:
```powershell
pip install -r requirements.txt
```

### 2. Ajustar Configuração

Edite `config/settings.yaml` e verifique/ajuste estas seções:

#### Movimentação Humanizada (Já ativado por padrão):
```yaml
input:
  use_human_movement: true      # ✅ Curvas Bezier ativadas
  min_delay: 0.05
  max_delay: 0.15
  idle_action_chance: 0.05      # 5% de chance de ação idle
```

#### ROIs de HP (IMPORTANTE - Ajustar para sua resolução):
```yaml
rois:
  player_hp_bar: [1517, 1046, 1732, 1071]  # Coordenadas da barra de HP
  enemy_hp_bar: [57, 33, 272, 58]
```

**Como encontrar as coordenadas certas?**
Use a ferramenta `tools/roi_picker.py`:
```powershell
python tools/roi_picker.py
```

---

## 🤖 (Opcional) Ativando Chat com IA

### Opção 1: Ollama (Gratuito e Local) - RECOMENDADO

#### Passo 1: Instalar Ollama
Baixe de: https://ollama.ai/download

#### Passo 2: Baixar Modelo
```powershell
ollama pull llama3
```
Outros modelos disponíveis:
- `llama3` (4.7 GB) - Melhor balanceamento
- `phi3` (2.3 GB) - Mais leve
- `mistral` (4.1 GB) - Rápido

#### Passo 3: Ativar no settings.yaml
```yaml
chat:
  enabled: true
  provider: "ollama"
  model: "llama3"
  base_url: "http://localhost:11434"
  response_chance: 0.3          # 30% de chance de responder
  personality: "casual"
```

#### Passo 4: Testar
O Ollama já inicia automaticamente no Windows. Para verificar:
```powershell
ollama list
```

### Opção 2: Google Gemini (Requer API Key)

#### Passo 1: Obter API Key
https://makersuite.google.com/app/apikey

#### Passo 2: Configurar
```yaml
chat:
  enabled: true
  provider: "gemini"
  model: "gemini-pro"
  api_key: "SUA_API_KEY_AQUI"
  response_chance: 0.3
  personality: "casual"
```

### Opção 3: OpenAI (Pago)

```yaml
chat:
  enabled: true
  provider: "openai"
  model: "gpt-3.5-turbo"
  api_key: "sk-..."
  response_chance: 0.3
  personality: "casual"
```

---

## 🎮 Executando o Bot

```powershell
python run_bot.py
```

### O Que Esperar:

#### ✅ Movimentação Humanizada Ativa:
- Mouse se move em curvas suaves (não linhas retas)
- Delays variáveis entre cliques (50-150ms)
- Ações idle ocasionais (pressionar espaço, mover câmera)

#### ✅ Detecção de HP Funcionando:
```
[INFO] HP do player: 67.3%
[INFO] HP do inimigo: 45.2%
```

Se aparecer `None`, ajuste as coordenadas em `rois.player_hp_bar` e `rois.enemy_hp_bar`.

#### ✅ STAB e Estratégia Melhorada:
```
[DEBUG] STAB aplicado para 'Thunderbolt' (tipo 13 em [13])
[INFO] Melhor golpe escolhido: slot=2, score=202.50
```

#### ✅ Chat com IA (se ativado):
```
[INFO] Mensagem detectada: whats up?
[INFO] Aguardando 3.47s antes de responder...
[INFO] Resposta enviada: nm just grinding levels
```

---

## 🔧 Troubleshooting

### Problema: "ModuleNotFoundError: No module named 'scipy'"
**Solução:**
```powershell
pip install scipy
```

### Problema: "ModuleNotFoundError: No module named 'requests'"
**Solução:**
```powershell
pip install requests
```

### Problema: HP sempre retorna None
**Causas possíveis:**
1. ROI incorreto (coordenadas erradas)
2. Resolução diferente
3. Cor da barra diferente (UI modificada)

**Solução:**
Use `tools/roi_picker.py` para encontrar as coordenadas corretas da barra de HP.

### Problema: Chat não funciona com Ollama
**Verificar:**
1. Ollama está instalado?
   ```powershell
   ollama --version
   ```
2. Modelo foi baixado?
   ```powershell
   ollama list
   ```
3. Servidor está rodando?
   ```powershell
   # Deve retornar "Ollama is running"
   curl http://localhost:11434
   ```

### Problema: Bot está clicando muito rápido/devagar
**Ajustar em settings.yaml:**
```yaml
input:
  min_move_duration: 0.3  # Aumentar para mais lento
  max_move_duration: 0.7
  min_delay: 0.1          # Aumentar delay
  max_delay: 0.25
```

---

## 📊 Comparação: Antes vs Depois

### ANTES (Bot Óbvio):
- ❌ Mouse se move em linha reta instantaneamente
- ❌ Cliques com timing perfeito (sempre 0.5s)
- ❌ Sempre usa Slot 1, independente de efetividade
- ❌ Nunca faz pausas ou movimentos extras
- ❌ Deixa Pokémon desmaiar (não detecta HP)

### DEPOIS (Humanizado):
- ✅ Mouse se move em curvas naturais
- ✅ Delays randômicos (50-150ms variável)
- ✅ Escolhe melhor golpe com STAB e efetividade
- ✅ Ações idle ocasionais (espaço, câmera)
- ✅ Detecta HP baixo e pode trocar/usar item
- ✅ (Opcional) Conversa naturalmente no chat

---

## 🎯 Próximos Passos Recomendados

1. **Testar em Ambiente Controlado**: 
   - Execute por 30 minutos e observe os logs
   - Verifique se detecção de HP está funcionando
   - Confirme que movimentos estão suaves

2. **Ajustar Personalidade**:
   - Teste diferentes valores de `idle_action_chance`
   - Experimente diferentes `personality` no chat

3. **Otimizar Estratégia**:
   - Ajuste `whitelist` e `blacklist` conforme necessário
   - Monitore escolhas de movimentos nos logs

4. **Adicionar Pausas Programadas**:
   - Implemente sistema de pausas (2-4h a cada 6-8h)
   - Varie horários de jogo

---

## 📞 Suporte

Para dúvidas ou problemas:
1. Verifique os logs em tempo real
2. Confira `docs/HUMANIZATION_FEATURES.md` para detalhes técnicos
3. Ajuste configurações gradualmente

---

**Boa sorte e bom jogo! 🎮✨**
