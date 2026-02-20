# 🌐 Controle Remoto via UDP - PokeBot v2.3

## Visão Geral

O **Sistema de Controle Remoto UDP** permite que você controle o bot rodando em uma **Máquina Virtual (VM)** a partir da sua **máquina física (host)** usando apenas teclas de atalho.

### ✨ Por que UDP?

- ✅ **Ultra-Rápido**: Latência de ~1-5ms (vs ~100-500ms de outros métodos)
- ✅ **Sem "Aperto de Mão"**: Não exige conexão estabelecida (fire-and-forget)
- ✅ **Leve**: Pacotes de ~10 bytes por comando
- ✅ **Simples**: Apenas 1 porta UDP aberta
- ✅ **Confiável**: Funciona mesmo com NAT/Bridged/Host-Only networking

### 🆚 Comparação com Outros Métodos

| Método | Latência | Complexidade | Funciona em VM? |
|--------|----------|--------------|-----------------|
| **UDP (Este)** | 1-5ms | Baixa | ✅ Sim |
| Hotkeys Locais | N/A | Baixa | ❌ Não (apenas host) |
| TCP/WebSocket | 50-100ms | Alta | ✅ Sim |
| SSH/RDP + Hotkeys | 100-500ms | Média | ✅ Sim (lento) |
| Compartilhamento de Arquivos | 1-5s | Alta | ✅ Sim (muito lento) |

---

## 🏗️ Arquitetura

```
┌─────────────────────────────────────────────────────────────┐
│                    MÁQUINA FÍSICA (HOST)                    │
│                                                             │
│  ┌─────────────────────────────────────────────────┐       │
│  │   remote_controller.py (Transmissor)            │       │
│  │                                                 │       │
│  │   [Você pressiona F3]                           │       │
│  │         ↓                                       │       │
│  │   Captura tecla (pynput)                        │       │
│  │         ↓                                       │       │
│  │   Envia "HUNT" via UDP                          │       │
│  └─────────────────────────────────────────────────┘       │
│                        │                                    │
└────────────────────────┼────────────────────────────────────┘
                         │ UDP Socket
                         │ (Porta 5005)
                         ↓
┌─────────────────────────────────────────────────────────────┐
│                  MÁQUINA VIRTUAL (VM)                       │
│                                                             │
│  ┌─────────────────────────────────────────────────┐       │
│  │   udp_receiver.py (Receptor)                    │       │
│  │                                                 │       │
│  │   Escuta porta 5005                             │       │
│  │         ↓                                       │       │
│  │   Recebe "HUNT"                                 │       │
│  │         ↓                                       │       │
│  │   Executa callback: bot.behavior = HUNTING      │       │
│  └─────────────────────────────────────────────────┘       │
│                        │                                    │
│  ┌─────────────────────────────────────────────────┐       │
│  │   bot_controller.py (Loop Principal)            │       │
│  │                                                 │       │
│  │   Próximo loop: detecta behavior = HUNTING      │       │
│  │         ↓                                       │       │
│  │   Executa handle_hunting()                      │       │
│  └─────────────────────────────────────────────────┘       │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

**Latência Total**: ~1 segundo (tempo do `loop_interval` do bot)

---

## 🚀 Setup Passo a Passo

### Passo 1: Descobrir IP da VM

**Na VM (Windows)**:
```powershell
ipconfig
```

Procure por:
```
Adaptador Ethernet Ethernet:
   Endereço IPv4. . . . . . . . : 192.168.1.100  ← Este é o IP!
```

**Na VM (Linux)**:
```bash
ifconfig
# ou
ip addr
```

**Anote o IP** (ex: `192.168.1.100`).

---

### Passo 2: Configurar Firewall da VM

**IMPORTANTE**: A VM deve permitir tráfego UDP na porta 5005.

**Windows (PowerShell como Administrador)**:
```powershell
New-NetFirewallRule -DisplayName "PokeBot UDP" -Direction Inbound -LocalPort 5005 -Protocol UDP -Action Allow
```

**Verificar regra**:
```powershell
Get-NetFirewallRule -DisplayName "PokeBot UDP"
```

**Linux (iptables)**:
```bash
sudo iptables -A INPUT -p udp --dport 5005 -j ACCEPT
```

**Linux (ufw)**:
```bash
sudo ufw allow 5005/udp
```

---

### Passo 3: Configurar Bot na VM

**Editar `config/settings.yaml` na VM**:

```yaml
remote_control:
  enabled: true   # ← Mudar para true
  port: 5005      # Porta UDP (padrão)
```

**Salvar e fechar**.

---

### Passo 4: Iniciar Bot na VM

**Na VM**:
```powershell
cd C:\Path\To\PokeBot
python run_bot.py
```

**Você deve ver**:
```
✅ Receptor UDP criado (porta 5005)
   Comandos registrados: 8
🌐 Servidor UDP iniciado em 0.0.0.0:5005
   Aguardando comandos remotos...
✅ Controle remoto UDP ativo! Use remote_controller.py na máquina host.
```

**Se não aparecer**: Verifique `remote_control.enabled: true` no `settings.yaml`.

---

### Passo 5: Configurar Transmissor na Máquina Física

**Na sua máquina física (host)**:

**1. Edite `tools/remote_controller.py`**:

```python
# Linha 30-35 (aproximadamente)
VM_IP = "192.168.1.100"  # ← ALTERE para o IP da sua VM!
PORT = 5005
```

**2. Instale dependência** (se ainda não tiver):
```powershell
pip install pynput
```

---

### Passo 6: Testar Conexão

**Na máquina física**:
```powershell
cd C:\Path\To\PokeBot
python tools/remote_controller.py
```

**Saída esperada**:
```
============================================================
🎮 CONTROLE REMOTO UDP - PokeBot v2.3
============================================================
VM IP: 192.168.1.100
Porta: 5005
============================================================

🔍 Testando conexão com VM (192.168.1.100:5005)...
[16:45:23] ✅ Comando enviado: PING
✅ VM acessível em 192.168.1.100:5005

📋 CONTROLES DISPONÍVEIS:
------------------------------------------------------------
  F1  → IDLE (Ocioso - apenas detecta Shiny)
  F2  → MISSION (Missão - clica Goto/Talk)
  F3  → HUNT (Caça - procura alvos específicos)
  F4  → FOLLOW (Seguir - rastreia personagem)

  F5  → PAUSE (Pausar bot)
  F6  → RESUME (Retomar bot)
  F9  → STOP (Parar bot completamente)

  ESC → Sair do controle remoto
------------------------------------------------------------

✅ Controle Ativo! Pressione teclas para comandar o bot na VM.
[16:45:23] Aguardando comandos...
```

**Na VM**, você deve ver:
```
📡 Comando recebido de 192.168.0.10: PING
✅ PING recebido de 192.168.0.10
```

**Se tudo OK**: Conexão estabelecida! 🎉

---

## 🎮 Como Usar

### Uso Básico

**1. Inicie o bot na VM**:
```powershell
python run_bot.py
```

**2. Inicie o controlador na máquina física**:
```powershell
python tools/remote_controller.py
```

**3. Pressione teclas para controlar**:

| Tecla | Efeito na VM | Log na VM |
|-------|--------------|-----------|
| **F1** | `bot.behavior = IDLE` | `🎮 Bot mudado para IDLE` |
| **F2** | `bot.behavior = MISSION` | `🎯 Bot mudado para MISSION` |
| **F3** | `bot.behavior = HUNTING` | `🎣 Bot mudado para HUNTING` |
| **F4** | `bot.behavior = FOLLOW` | `👤 Bot mudado para FOLLOW` |
| **F5** | `bot.paused = True` | `⏸️ Bot PAUSADO` |
| **F6** | `bot.paused = False` | `▶️ Bot RETOMADO` |
| **F9** | `bot.running = False` | `🛑 Bot parado` |

---

### Exemplo de Uso Prático

**Cenário**: Você está usando o PC (host) e quer que o bot na VM alterne entre modos.

```
[Máquina Física]
Você está assistindo YouTube no Chrome

[Pressiona F2]
→ Transmissor envia "MISSION" via UDP

[VM]
→ Receptor recebe "MISSION"
→ bot.behavior = MISSION
→ Bot começa a clicar Goto/Talk

[15 minutos depois]

[Máquina Física - Pressiona F3]
→ Transmissor envia "HUNT"

[VM]
→ Receptor recebe "HUNT"
→ bot.behavior = HUNTING
→ Bot começa a procurar Ditto

[Sem precisar abrir a VM ou RDP! 🎉]
```

---

## 🔧 Configuração Avançada

### Personalizar Porta UDP

**Se porta 5005 está em uso**, mude para outra:

**Na VM (`settings.yaml`)**:
```yaml
remote_control:
  enabled: true
  port: 6000  # ← Nova porta
```

**Na Máquina Física (`remote_controller.py`)**:
```python
PORT = 6000  # ← Mesma porta
```

**Atualizar firewall**:
```powershell
New-NetFirewallRule -DisplayName "PokeBot UDP" -Direction Inbound -LocalPort 6000 -Protocol UDP -Action Allow
```

---

### Usar com Rede Host-Only ou NAT

**Host-Only (VMware/VirtualBox)**:
- VM tem IP privado (ex: `192.168.56.101`)
- Host acessa diretamente
- **Vantagem**: Isolado da internet
- **Configuração**: Apenas mude `VM_IP` para o IP do adaptador Host-Only

**NAT com Port Forwarding**:
- VM usa NAT para internet
- Host precisa de port forwarding
- **VMware**: VM Settings → Network Adapter → NAT Settings → Add Port Forwarding
  - Host Port: 5005
  - VM Port: 5005
  - Type: UDP
- **VirtualBox**: Settings → Network → Advanced → Port Forwarding
  - Same config
- **Configuração**: `VM_IP = "127.0.0.1"` (localhost)

**Bridged (Recomendado para iniciantes)**:
- VM aparece como dispositivo separado na rede
- Tem IP próprio (ex: `192.168.1.100`)
- Host acessa como outro computador
- **Configuração**: Use IP real da VM

---

### Adicionar Novos Comandos

**1. No receptor (`udp_receiver.py`)**:

```python
# Linha ~150 (dentro de create_udp_receiver)

# Comando customizado: resetar bot
receiver.register_callback("RESET", lambda: bot_controller.reset_state())
```

**2. No transmissor (`remote_controller.py`)**:

```python
# Linha ~90 (dentro de on_press)

elif key == keyboard.Key.f7:
    send_command("RESET")
    print("   → Bot RESETADO")
```

**3. Reiniciar ambos**

---

## 🐛 Troubleshooting

### Problema: "Não foi possível conectar à VM"

**Verificações**:

1. **VM está ligada e bot rodando?**
   ```powershell
   # Na VM
   python run_bot.py
   ```

2. **IP correto?**
   ```powershell
   # Na VM
   ipconfig  # Windows
   ifconfig  # Linux
   ```
   Compare com `VM_IP` no `remote_controller.py`.

3. **Firewall permite porta 5005 UDP?**
   ```powershell
   # Na VM (PowerShell Admin)
   Get-NetFirewallRule -DisplayName "PokeBot UDP"
   ```
   
   Se não existir:
   ```powershell
   New-NetFirewallRule -DisplayName "PokeBot UDP" -Direction Inbound -LocalPort 5005 -Protocol UDP -Action Allow
   ```

4. **Configuração habilitada?**
   
   Na VM, `config/settings.yaml`:
   ```yaml
   remote_control:
     enabled: true  # ← Deve ser true
   ```

5. **Rede entre host e VM funcionando?**
   ```powershell
   # Na máquina física
   ping 192.168.1.100  # IP da VM
   ```
   
   Se não responder: problema de rede (NAT/Bridged/Host-Only).

---

### Problema: Comando enviado mas bot não responde

**Verificações**:

1. **Logs na VM**:
   ```
   📡 Comando recebido de 192.168.0.10: HUNT
   ✅ Comando HUNT executado
   ```
   
   Se **não aparece**: Comando não chegou (firewall).
   
   Se **aparece mas bot não muda**: Callback com erro.

2. **Modo debug na VM**:
   ```yaml
   bot:
     debug_mode: true
   ```
   
   Logs mostrarão:
   ```
   [DEBUG] GameState: EXPLORING | Behavior: HUNTING
   ```

3. **Comando correto?**
   
   Comandos válidos:
   - `IDLE`, `MISSION`, `HUNT`, `HUNTING`, `FOLLOW`
   - `PAUSE`, `RESUME`, `STOP`
   
   **Maiúsculas/minúsculas não importam** (normalizado para uppercase).

---

### Problema: Latência muito alta (>5 segundos)

**Causas possíveis**:

1. **Rede lenta**: 
   - Teste ping: `ping 192.168.1.100`
   - Se >100ms: problema de rede

2. **Loop interval muito alto**:
   ```yaml
   bot:
     loop_interval: 5.0  # ← Reduzir para 1.0
   ```

3. **VM sobrecarregada**:
   - CPU/RAM da VM saturada
   - Feche aplicações desnecessárias

**Solução**:
- Use rede Bridged (mais rápida que NAT)
- Reduza `loop_interval` para 0.5-1.0s
- Aloque mais RAM/CPU para VM

---

### Problema: "Address already in use"

**Causa**: Porta 5005 já está em uso.

**Soluções**:

**Opção 1: Fechar processo usando porta**:
```powershell
# Descobrir quem está usando porta 5005
netstat -ano | findstr :5005

# Matar processo (substitua PID)
taskkill /PID 1234 /F
```

**Opção 2: Mudar porta**:
```yaml
# Na VM (settings.yaml)
remote_control:
  port: 6000  # Nova porta
```

```python
# Na máquina física (remote_controller.py)
PORT = 6000
```

---

## 📊 Comparação: Hotkeys Local vs UDP Remoto

### Sistema Original (v2.2) - Hotkeys Locais

**Arquitetura**:
```
[Você pressiona F3 no teclado físico]
         ↓
[pynput detecta na máquina local]
         ↓
[Callback muda bot.behavior = HUNTING]
```

**Limitação**: Só funciona **na mesma máquina** onde o bot roda.

**Problema com VM**: Quando você pressiona F3 no host, a VM não recebe (a menos que esteja em RDP/Console).

---

### Sistema Novo (v2.3) - UDP Remoto

**Arquitetura**:
```
[Você pressiona F3 no teclado físico - HOST]
         ↓
[pynput detecta no host]
         ↓
[Transmissor envia "HUNT" via UDP → VM]
         ↓
[Receptor na VM recebe "HUNT"]
         ↓
[Callback muda bot.behavior = HUNTING]
```

**Vantagem**: Funciona **entre máquinas diferentes** (Host → VM).

---

### Comparação Prática

| Aspecto | Hotkeys Locais (v2.2) | UDP Remoto (v2.3) |
|---------|----------------------|-------------------|
| **Latência** | ~0ms (instantâneo) | ~1-5ms |
| **Funciona em VM?** | ❌ Não | ✅ Sim |
| **Requer RDP/Console?** | ✅ Sim | ❌ Não |
| **Foco na janela?** | ✅ Necessário | ❌ Não necessário |
| **Rede necessária?** | ❌ Não | ✅ Sim (LAN) |
| **Complexidade** | Baixa | Média |
| **Firewall?** | ❌ Não | ✅ Sim (porta UDP) |

**Conclusão**: Use **Hotkeys Locais** se o bot roda no host. Use **UDP Remoto** se o bot roda em VM.

---

## 🎯 Casos de Uso

### Caso 1: Bot na VM, você trabalha no Host

**Cenário**: Você usa o PC principal para trabalhar/estudar, e o bot roda 24/7 em uma VM em background.

**Solução**:
- Inicie `remote_controller.py` no host
- Pressione F1-F9 para controlar bot na VM
- **Sem precisar abrir RDP ou Console!**

**Vantagem**: Controle total sem tirar foco do trabalho.

---

### Caso 2: Múltiplas VMs rodando bots

**Cenário**: Você tem 3 VMs, cada uma com uma conta diferente farmando.

**Solução**:
- Configure cada VM com porta diferente:
  - VM1: porta 5005
  - VM2: porta 5006
  - VM3: porta 5007
- Crie 3 instâncias do `remote_controller.py` (uma por VM)
- Controle todas simultaneamente!

**Exemplo**:
```powershell
# Terminal 1 - Controla VM1
python remote_controller.py  # VM_IP=192.168.1.100, PORT=5005

# Terminal 2 - Controla VM2
python remote_controller_vm2.py  # VM_IP=192.168.1.101, PORT=5006

# Terminal 3 - Controla VM3
python remote_controller_vm3.py  # VM_IP=192.168.1.102, PORT=5007
```

---

### Caso 3: Controle de outro computador da rede

**Cenário**: Você tem um PC desktop com o bot rodando, e quer controlar do laptop.

**Solução**:
- Descubra IP do PC desktop (ex: `192.168.1.50`)
- No laptop, configure `VM_IP = "192.168.1.50"`
- Execute `remote_controller.py` no laptop
- Controle o bot no desktop remotamente!

**Requisito**: Ambos na mesma rede local (LAN).

---

## 🔒 Segurança

### Considerações

**UDP não é criptografado**: Qualquer um na rede pode:
- Ver comandos sendo enviados
- Enviar comandos falsos

**Mitigação**:

1. **Rede confiável**: Use apenas em LAN privada (não Wi-Fi público)

2. **Firewall**: Permita apenas IP do host:
   ```powershell
   # Windows Firewall (permite apenas 192.168.0.10)
   New-NetFirewallRule -DisplayName "PokeBot UDP" -Direction Inbound -LocalPort 5005 -Protocol UDP -RemoteAddress 192.168.0.10 -Action Allow
   ```

3. **Autenticação** (avançado):
   
   Adicione token secreto:
   
   **Transmissor**:
   ```python
   SECRET = "minha_senha_secreta"
   send_command(f"{SECRET}:{cmd}")
   ```
   
   **Receptor**:
   ```python
   SECRET = "minha_senha_secreta"
   data, addr = sock.recvfrom(1024)
   full_msg = data.decode()
   if full_msg.startswith(f"{SECRET}:"):
       cmd = full_msg.split(":", 1)[1]
       # Executar comando
   else:
       logger.warning("Autenticação falhou!")
   ```

**Para uso casual em rede doméstica**: Segurança padrão é suficiente.

---

## 📝 Logs de Exemplo

### Transmissor (Máquina Física)

```
============================================================
🎮 CONTROLE REMOTO UDP - PokeBot v2.3
============================================================
VM IP: 192.168.1.100
Porta: 5005
============================================================

🔍 Testando conexão com VM (192.168.1.100:5005)...
[16:30:15] ✅ Comando enviado: PING
✅ VM acessível em 192.168.1.100:5005

📋 CONTROLES DISPONÍVEIS:
------------------------------------------------------------
  F1  → IDLE (Ocioso - apenas detecta Shiny)
  F2  → MISSION (Missão - clica Goto/Talk)
  F3  → HUNT (Caça - procura alvos específicos)
  F4  → FOLLOW (Seguir - rastreia personagem)

  F5  → PAUSE (Pausar bot)
  F6  → RESUME (Retomar bot)
  F9  → STOP (Parar bot completamente)

  ESC → Sair do controle remoto
------------------------------------------------------------

✅ Controle Ativo! Pressione teclas para comandar o bot na VM.
[16:30:15] Aguardando comandos...

[16:30:45] ✅ Comando enviado: MISSION
   → Bot em modo MISSÃO (clica Goto/Talk)

[16:35:12] ✅ Comando enviado: HUNT
   → Bot em modo CAÇA (procura alvos)

[16:40:33] ✅ Comando enviado: PAUSE
   → Bot PAUSADO

[16:41:05] ✅ Comando enviado: RESUME
   → Bot RETOMADO

[16:45:00] 🛑 Encerrando controle remoto...
[16:45:00] 👋 Controle remoto encerrado.
```

---

### Receptor (VM)

```
[INFO] Bot Iniciado em modo MISSION!
✅ Receptor UDP criado (porta 5005)
   Comandos registrados: 8
🌐 Servidor UDP iniciado em 0.0.0.0:5005
   Aguardando comandos remotos...
✅ Controle remoto UDP ativo! Use remote_controller.py na máquina host.

[16:30:15] 📡 Comando recebido de 192.168.0.10: PING
[16:30:15] ✅ PING recebido de 192.168.0.10

[16:30:45] 📡 Comando recebido de 192.168.0.10: MISSION
[16:30:45] ✅ Comando MISSION executado
🎯 Bot mudado para estado MISSION (Missão)

[16:35:12] 📡 Comando recebido de 192.168.0.10: HUNT
[16:35:12] ✅ Comando HUNT executado
🎣 Bot mudado para estado HUNTING (Caça)

[16:40:33] 📡 Comando recebido de 192.168.0.10: PAUSE
[16:40:33] ✅ Comando PAUSE executado
⏸️ Bot PAUSADO
   → Pressione F6 para retomar

[16:41:05] 📡 Comando recebido de 192.168.0.10: RESUME
[16:41:05] ✅ Comando RESUME executado
▶️ Bot RETOMADO
```

---

## ✅ Checklist de Setup

- [ ] IP da VM descoberto (`ipconfig` ou `ifconfig`)
- [ ] Firewall da VM configurado (porta 5005 UDP)
- [ ] `settings.yaml` na VM: `remote_control.enabled: true`
- [ ] `remote_controller.py` editado com IP correto
- [ ] `pynput` instalado na máquina física
- [ ] Bot iniciado na VM (`python run_bot.py`)
- [ ] Controlador iniciado no host (`python tools/remote_controller.py`)
- [ ] Teste de PING bem-sucedido
- [ ] Comandos F1-F9 funcionando

**Se todos checados**: Sistema funcionando! 🎉

---

## 🚀 Conclusão

O **Sistema de Controle Remoto UDP v2.3** leva o PokeBot para o próximo nível:

### Principais Benefícios:
- ✅ **Controle de VM sem RDP**: Comandos instantâneos do host
- ✅ **Ultra-Baixa Latência**: 1-5ms (UDP é ~10x mais rápido que TCP)
- ✅ **Setup Simples**: Apenas 1 porta UDP + 2 scripts
- ✅ **Escalável**: Controle múltiplas VMs simultaneamente
- ✅ **Não-Intrusivo**: Funciona em background sem tirar foco

### Casos de Uso:
- Bot rodando em VM enquanto você trabalha no host
- Múltiplas contas em VMs diferentes controladas de um lugar
- Controle de PC desktop a partir de laptop na mesma rede

**Use com sabedoria! 🎮✨**

---

**Versão**: 2.3.0  
**Data**: 2026-02-20  
**Requisitos**: Python 3.8+, pynput, rede local (LAN)
