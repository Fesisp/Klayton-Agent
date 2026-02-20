"""
Controle Remoto via UDP - Transmissor (Máquina Real)
=====================================================

Este script roda na sua máquina física (host) e envia comandos
para o bot rodando na VM via rede UDP.

Uso:
    python remote_controller.py

Configuração:
    1. Descubra o IP da VM: ipconfig (Windows) ou ifconfig (Linux)
    2. Altere VM_IP abaixo para o IP da sua VM
    3. Certifique-se que a porta 5005 está aberta no firewall da VM

Teclas de Controle:
    F1  → IDLE (Ocioso - apenas detecta Shiny)
    F2  → MISSION (Missão - clica Goto/Talk)
    F3  → HUNT (Caça - procura alvos específicos)
    F4  → FOLLOW (Seguir - rastreia personagem)
    F5  → PAUSE (Pausa bot)
    F6  → RESUME (Retoma bot)
    F9  → STOP (Para bot)
    ESC → Sair do controle remoto

Requisitos:
    pip install pynput

Autor: PokeBot v2.3
Data: 2026-02-20
"""

import socket
import time
from pynput import keyboard
from datetime import datetime

# ============================
# CONFIGURAÇÃO
# ============================

# IMPORTANTE: Altere este IP para o IP da sua VM!
# Para descobrir o IP da VM:
#   Windows: ipconfig
#   Linux: ifconfig ou ip addr
VM_IP = "192.168.1.100"  # ← ALTERE AQUI!

# Porta UDP (deve ser a mesma no receptor)
PORT = 5005

# Timeout para confirmação (opcional)
TIMEOUT = 1.0

# ============================
# FUNÇÕES
# ============================

def get_timestamp():
    """Retorna timestamp formatado para logs"""
    return datetime.now().strftime("%H:%M:%S")

def send_command(cmd: str, verbose: bool = True) -> bool:
    """
    Envia comando UDP para o bot na VM
    
    Args:
        cmd: Comando a enviar (IDLE, MISSION, HUNT, etc.)
        verbose: Mostrar mensagem de confirmação
    
    Returns:
        bool: True se enviado com sucesso, False caso contrário
    """
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
            # Define timeout para evitar travamentos
            sock.settimeout(TIMEOUT)
            
            # Envia comando
            message = cmd.encode('utf-8')
            sock.sendto(message, (VM_IP, PORT))
            
            if verbose:
                print(f"[{get_timestamp()}] ✅ Comando enviado: {cmd}")
            
            return True
            
    except socket.timeout:
        print(f"[{get_timestamp()}] ⚠️ Timeout ao enviar {cmd}")
        return False
        
    except socket.error as e:
        print(f"[{get_timestamp()}] ❌ Erro de rede: {e}")
        print(f"   Verifique se:")
        print(f"   1. O IP da VM está correto: {VM_IP}")
        print(f"   2. O bot está rodando na VM")
        print(f"   3. A porta {PORT} está aberta no firewall")
        return False
        
    except Exception as e:
        print(f"[{get_timestamp()}] ❌ Erro inesperado: {e}")
        return False

def test_connection() -> bool:
    """
    Testa conexão com a VM enviando comando PING
    
    Returns:
        bool: True se VM está acessível
    """
    print(f"\n🔍 Testando conexão com VM ({VM_IP}:{PORT})...")
    
    try:
        # Tenta enviar PING
        success = send_command("PING", verbose=False)
        
        if success:
            print(f"✅ VM acessível em {VM_IP}:{PORT}")
            return True
        else:
            print(f"❌ Não foi possível conectar à VM")
            return False
            
    except Exception as e:
        print(f"❌ Erro no teste de conexão: {e}")
        return False

def on_press(key):
    """
    Callback executado quando uma tecla é pressionada
    
    Args:
        key: Tecla pressionada (pynput.keyboard.Key)
    """
    try:
        # Comandos de Modo
        if key == keyboard.Key.f1:
            send_command("IDLE")
            print("   → Bot em modo OCIOSO (apenas detecta Shiny)")
            
        elif key == keyboard.Key.f2:
            send_command("MISSION")
            print("   → Bot em modo MISSÃO (clica Goto/Talk)")
            
        elif key == keyboard.Key.f3:
            send_command("HUNT")
            print("   → Bot em modo CAÇA (procura alvos)")
            
        elif key == keyboard.Key.f4:
            send_command("FOLLOW")
            print("   → Bot em modo SEGUIR (rastreia personagem)")
        
        # Comandos de Controle
        elif key == keyboard.Key.f5:
            send_command("PAUSE")
            print("   → Bot PAUSADO")
            
        elif key == keyboard.Key.f6:
            send_command("RESUME")
            print("   → Bot RETOMADO")
            
        elif key == keyboard.Key.f9:
            send_command("STOP")
            print("   → Bot PARADO")
        
        # Sair do controle remoto
        elif key == keyboard.Key.esc:
            print(f"\n[{get_timestamp()}] 🛑 Encerrando controle remoto...")
            return False  # Para o listener
            
    except AttributeError:
        # Tecla não mapeada (ex: letras, números)
        pass

def print_header():
    """Imprime cabeçalho do controle remoto"""
    print("=" * 60)
    print("🎮 CONTROLE REMOTO UDP - PokeBot v2.3")
    print("=" * 60)
    print(f"VM IP: {VM_IP}")
    print(f"Porta: {PORT}")
    print("=" * 60)

def print_controls():
    """Imprime lista de controles disponíveis"""
    print("\n📋 CONTROLES DISPONÍVEIS:")
    print("-" * 60)
    print("  F1  → IDLE (Ocioso - apenas detecta Shiny)")
    print("  F2  → MISSION (Missão - clica Goto/Talk)")
    print("  F3  → HUNT (Caça - procura alvos específicos)")
    print("  F4  → FOLLOW (Seguir - rastreia personagem)")
    print("")
    print("  F5  → PAUSE (Pausar bot)")
    print("  F6  → RESUME (Retomar bot)")
    print("  F9  → STOP (Parar bot completamente)")
    print("")
    print("  ESC → Sair do controle remoto")
    print("-" * 60)

# ============================
# MAIN
# ============================

def main():
    """Função principal do controle remoto"""
    
    # Cabeçalho
    print_header()
    
    # Teste de conexão
    if not test_connection():
        print("\n⚠️ ATENÇÃO: Não foi possível conectar à VM!")
        print("\n📝 VERIFICAÇÃO:")
        print("   1. O bot está rodando na VM?")
        print(f"   2. O IP {VM_IP} está correto?")
        print(f"      (Execute 'ipconfig' na VM para descobrir)")
        print(f"   3. A porta {PORT} está aberta no firewall da VM?")
        print(f"      (Execute: New-NetFirewallRule -DisplayName 'PokeBot UDP' -Direction Inbound -LocalPort {PORT} -Protocol UDP -Action Allow)")
        print("\n   Mesmo assim, você pode tentar usar o controle.")
        print("   Pressione ENTER para continuar ou CTRL+C para sair...")
        
        try:
            input()
        except KeyboardInterrupt:
            print("\n\n👋 Controle remoto cancelado.")
            return
    
    # Lista de controles
    print_controls()
    
    print(f"\n✅ Controle Ativo! Pressione teclas para comandar o bot na VM.")
    print(f"[{get_timestamp()}] Aguardando comandos...\n")
    
    # Inicia listener de teclado
    try:
        # Cria listener com supress=False para permitir retorno False
        listener = keyboard.Listener(on_press=on_press, suppress=False)  # type: ignore
        listener.start()
        listener.join()
            
    except KeyboardInterrupt:
        print(f"\n[{get_timestamp()}] 🛑 Controle interrompido por Ctrl+C")
    
    print(f"\n[{get_timestamp()}] 👋 Controle remoto encerrado.")

if __name__ == "__main__":
    main()
