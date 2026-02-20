# 🚀 Setup Rápido - Sistema de Hotkeys

**Tempo estimado**: 5-10 minutos

---

## Passo 1: Instalar Dependência

```powershell
pip install pynput
```

**Verificar instalação**:
```powershell
python -c "import pynput; print('✅ OK')"
```

Se der erro, reinstale:
```powershell
pip uninstall pynput
pip install pynput==1.7.6
```

---

## Passo 2: Verificar Configuração

Abra `config/settings.yaml` e verifique:

```yaml
controls:
  enabled: true  # ← Deve estar true
  
  # Teclas padrão (pode personalizar)
  idle_key: "<f1>"
  mission_key: "<f2>"
  hunting_key: "<f3>"
  follow_key: "<f4>"
  pause_key: "<f5>"
  resume_key: "<f6>"
  stop_key: "<f9>"
```

**Pronto!** Hotkeys básicas já funcionam.

---

## Passo 3 (Opcional): Setup do Modo FOLLOW

**Se você NÃO vai usar modo FOLLOW**, pode pular para Passo 4.

### Método 1: Template Matching (Recomendado)

**1. Capture o sprite do seu personagem**

- Abra o jogo
- Use PrintScreen ou Snipping Tool (Win+Shift+S)
- Capture **APENAS** o sprite do personagem (10x10 a 50x50 pixels)

Exemplo:
```
❌ NÃO capture toda a tela
❌ NÃO capture o nome do personagem
✅ APENAS o sprite/modelo do char
```

**2. Salve como PNG**

Salve em: `assets/templates/player_char.png`

**3. Configure no settings.yaml**

```yaml
follow:
  method: "template"
  player_template: "player_char.png"
  match_threshold: 0.7  # Ajuste se necessário
  distance: 50
  check_interval: 1.0
```

### Método 2: Party Button (Alternativo)

**1. Capture o botão "Follow"**

- Entre em uma party
- Capture o botão "Follow" que aparece na interface
- Salve em: `assets/templates/follow_button.png`

**2. Configure**

```yaml
follow:
  method: "party_button"
  follow_button_template: "follow_button.png"
  button_threshold: 0.75
  check_interval: 2.0
```

---

## Passo 4: Testar Hotkeys

**1. Inicie o bot**

```powershell
python run_bot.py
```

**2. Você deve ver**:

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
```

**3. Teste cada tecla**:

| Tecla | Resultado Esperado |
|-------|-------------------|
| F1 | `🎮 Hotkey detectada: IDLE` + bot para |
| F2 | `🎮 Hotkey detectada: MISSION` + bot clica Goto/Talk |
| F3 | `🎮 Hotkey detectada: HUNTING` + bot move aleatório |
| F4 | `🎮 Hotkey detectada: FOLLOW` + bot segue char |
| F5 | `⏸️ Bot PAUSADO` |
| F6 | `▶️ Bot RETOMADO` |
| F9 | Bot para completamente |

---

## 🐛 Problemas Comuns

### Hotkeys não respondem

**Causa**: Permissões ou pynput não instalado.

**Solução**:
1. Execute PowerShell como Administrador
2. Reinstale pynput: `pip install --force-reinstall pynput`
3. Reinicie o bot

---

### Bot não segue personagem (F4)

**Causa**: Template não encontrado ou threshold muito alto.

**Solução**:

1. **Verificar se template existe**:
   ```powershell
   Test-Path "assets/templates/player_char.png"
   ```
   Deve retornar `True`.

2. **Ativar debug**:
   ```yaml
   bot:
     debug_mode: true
   ```

3. **Analisar logs**:
   ```
   [DEBUG] [FOLLOW] Personagem não detectado (score: 0.65)
   ```
   
   Se score está entre 0.6-0.7, reduza threshold:
   ```yaml
   follow:
     match_threshold: 0.6  # Reduzido de 0.7
   ```

4. **Se ainda não funciona**, use método alternativo:
   ```yaml
   follow:
     method: "party_button"
   ```

---

### Mensagem "pynput não encontrado"

**Causa**: Biblioteca não instalada ou ambiente errado.

**Solução**:

1. **Verificar ambiente Python**:
   ```powershell
   python --version
   pip list | Select-String pynput
   ```

2. **Reinstalar**:
   ```powershell
   pip install pynput
   ```

3. **Se usar venv**:
   ```powershell
   .\venv\Scripts\Activate.ps1
   pip install pynput
   ```

---

## ✅ Checklist Final

- [ ] `pynput` instalado e funcionando
- [ ] `controls.enabled: true` no settings.yaml
- [ ] Hotkey listener aparece ao iniciar bot
- [ ] F1-F6 funcionam corretamente
- [ ] (Opcional) Template do personagem capturado
- [ ] (Opcional) F4 segue personagem

**Se todos checados**: Sistema funcionando! 🎉

---

## 📚 Próximos Passos

1. **Leia a documentação completa**: `docs/HOTKEY_SYSTEM.md`
2. **Configure modos avançados**: `docs/STATE_MACHINE.md`
3. **Personalize teclas**: Edite `controls` no settings.yaml

---

## 🎯 Uso Prático

**Exemplo de rotina diária**:

```
1. Iniciar bot: python run_bot.py
2. Modo missão: F2 (completa missões AFK)
3. Pausa para almoço: F5
4. Retomar: F6
5. Trocar para caça: F3 (farm Ditto)
6. Parar ao fim do dia: F9
```

**Tudo sem reiniciar o bot!** 🚀

---

**Versão: 2.2**  
**Data: 2026-02-20**
