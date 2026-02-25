# 🚀 Guia Rápido - PokeBot

## Início Rápido

### 1. Executar o Bot
```bash
python run_bot.py
```

### 2. Controles Principais

| Tecla | Ação |
|-------|------|
| **F1** | Modo Ocioso (bot para tudo) |
| **F2** | Modo Missão (segue Goto/Talk) |
| **F3** | Modo Caça (procura Pokémon) |
| **F4** | Seguir Personagem |
| **F5** | Pausar Bot ⏸️ |
| **F6** | Retomar Bot ▶️ |
| **F9** | Encerrar Bot 🛑 |
| **Ctrl+C** | Encerrar Bot (alternativo) |

---

## 🎯 Comportamentos do Bot

### 🎮 Modo MISSION (Padrão)
- Detecta e clica em botões "Goto"
- Avança diálogos automaticamente (Talk)
- Ideal para: Seguir questas e missões

### 🎯 Modo HUNTING
- Movimenta-se aleatoriamente em área definida
- Procura Pokémon específicos
- Ideal para: Farmar encontros

### 👤 Modo FOLLOW
- Segue personagem principal
- Mantém distância configurável
- Ideal para: Multi-char leveling

### ⏸️ Modo IDLE
- Bot observa mas não age
- Útil para pausas temporárias

---

## ⚔️ Durante Batalhas

O bot automaticamente:
1. ✅ Detecta quando entra em batalha
2. ✅ Escolhe o melhor golpe baseado em tipos
3. ✅ Troca Pokémon se necessário
4. ✅ Foge de batalhas indesejadas (configurável)
5. ✅ Detecta status do inimigo (se templates configurados)

---

## ✨ Detecção de Shiny

Quando detecta um shiny:
1. 🚨 **Alarme sonoro** toca 10 vezes
2. 💬 **Janela de alerta** aparece
3. ⏸️ **Bot pausa automaticamente**
4. ▶️ Pressione **F6** para retomar quando capturar

---

## ⚙️ Configuração Básica

### Alterar Modo do Bot
Edite `config/settings.yaml`:
```yaml
bot:
  behavior: "mission"  # Opções: mission, hunting, follow, idle
```

### Ajustar Velocidade
```yaml
bot:
  loop_interval: 1.0  # Segundos entre cada ciclo (diminuir = mais rápido)
```

### Debug Mode
```yaml
bot:
  debug_mode: true  # Ativa logs detalhados
```

---

## 🐛 Resolução de Problemas

### Bot não responde aos controles
- Verifique se o jogo está em foco
- Tente usar **Ctrl+C** para parar
- Reinicie o bot

### Bot se move aleatoriamente
- Certifique-se que está em modo correto (F1 para parar)
- Verifique se há botão "Goto" na tela

### Batalhas não detectadas
- Verifique templates em `assets/templates/`
- Ajuste thresholds em `config/settings.yaml`
- Ative debug_mode para ver scores de detecção

### Shiny não detectado
- Verifique se `shiny.png` existe em `assets/templates/`
- Threshold padrão: 0.6 (ajustável em config)

---

## 📊 Logs

Logs são salvos em:
```
logs/pokebot_YYYY-MM-DD_HH-MM-SS.log
```

Para ver logs em tempo real:
```bash
tail -f logs/pokebot_*.log  # Linux/Mac
Get-Content logs\pokebot_*.log -Wait  # Windows PowerShell
```

---

## 🆘 Parada de Emergência

Se algo der errado:
1. **Ctrl+C** no terminal
2. **F9** (se hotkeys funcionando)
3. **Mover mouse para canto superior esquerdo** (failsafe do PyAutoGUI - DESABILITADO por padrão)
4. **Alt+Tab** para sair do jogo

---

## 💡 Dicas

### Para Missões
- Use modo **MISSION** (F2)
- Bot clicará automaticamente em Goto
- Diálogos são avançados com Espaço

### Para Caça de Shiny
- Use modo **HUNTING** (F3)
- Configure área de caça em `settings.yaml`
- Bot fugirá de batalhas normais
- Pausará automaticamente ao detectar shiny

### Para Seguir Outro Jogador
- Use modo **FOLLOW** (F4)
- Configure cor do personagem em `settings.yaml`
- Ajuste distância de seguimento

---

## 📝 Checklist Antes de Usar

- [ ] Python 3.13+ instalado
- [ ] Todas as dependências instaladas (`requirements.txt`)
- [ ] Tesseract OCR instalado e configurado
- [ ] Templates em `assets/templates/`
- [ ] ROIs configuradas em `config/settings.yaml`
- [ ] Jogo em modo janela (não fullscreen)
- [ ] Resolução do jogo compatível com ROIs

---

## 🎓 Tutoriais

### Configurar ROIs
```bash
python tools/roi_picker.py
```
Clique nos cantos das áreas que deseja capturar.

### Testar OCR
```bash
python tests/test_ocr_and_strategy.py
```

### Detectar Shiny
```bash
python tests/test_shiny_detection.py
```

---

**Versão:** 2.5.3  
**Última atualização:** 23/02/2026

Para mais informações, consulte `PROJECT_STATUS.md` ou `docs/PROJECT_OVERVIEW.md`.
