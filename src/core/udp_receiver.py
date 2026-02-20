"""
Receptor de Comandos UDP - Servidor (VM)
=========================================

Este módulo recebe comandos UDP da máquina física e 
altera o comportamento do bot em tempo real.

Funciona em thread separada para não bloquear o loop principal.

Comandos aceitos:
    - IDLE: Modo ocioso
    - MISSION: Modo missão
    - HUNT: Modo caça
    - FOLLOW: Modo seguir
    - PAUSE: Pausar bot
    - RESUME: Retomar bot
    - STOP: Parar bot
    - PING: Teste de conexão

Autor: PokeBot v2.3
Data: 2026-02-20
"""

import socket
import threading
from typing import Optional, Callable
from loguru import logger

# ============================
# CONFIGURAÇÕES
# ============================

DEFAULT_PORT = 5005
DEFAULT_HOST = "0.0.0.0"  # Escuta em todas interfaces de rede
BUFFER_SIZE = 1024

# ============================
# CLASSE UDP RECEIVER
# ============================

class UDPCommandReceiver:
    """
    Servidor UDP que recebe comandos remotos e executa callbacks
    
    Attributes:
        port (int): Porta UDP para escutar
        host (str): IP para bind (0.0.0.0 = todas interfaces)
        running (bool): Flag de controle do servidor
        thread (threading.Thread): Thread do servidor
        sock (socket.socket): Socket UDP
        callbacks (dict): Mapeamento comando → função
    """
    
    def __init__(self, port: int = DEFAULT_PORT, host: str = DEFAULT_HOST):
        """
        Inicializa o receptor UDP
        
        Args:
            port: Porta UDP para escutar (padrão: 5005)
            host: IP para bind (padrão: 0.0.0.0 - todas interfaces)
        """
        self.port = port
        self.host = host
        self.running = False
        self.thread: Optional[threading.Thread] = None
        self.sock: Optional[socket.socket] = None
        
        # Callbacks para cada comando
        self.callbacks: dict[str, Callable] = {}
        
        logger.debug(f"UDPReceiver inicializado (porta: {port})")
    
    def register_callback(self, command: str, callback: Callable):
        """
        Registra callback para um comando específico
        
        Args:
            command: Nome do comando (ex: "IDLE", "MISSION")
            callback: Função a executar quando comando for recebido
        
        Example:
            receiver.register_callback("IDLE", lambda: bot.set_idle())
        """
        self.callbacks[command.upper()] = callback
        logger.debug(f"Callback registrado para comando: {command}")
    
    def _server_loop(self):
        """
        Loop principal do servidor UDP (executado em thread separada)
        
        Escuta por comandos UDP e executa callbacks correspondentes.
        """
        logger.info(f"🌐 Servidor UDP iniciado em {self.host}:{self.port}")
        logger.info("   Aguardando comandos remotos...")
        
        # Cria socket UDP
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        
        try:
            # Bind no endereço e porta
            self.sock.bind((self.host, self.port))
            self.sock.settimeout(1.0)  # Timeout para checar self.running
            
            while self.running:
                try:
                    # Recebe dados (bloqueante com timeout)
                    data, addr = self.sock.recvfrom(BUFFER_SIZE)
                    
                    # Decodifica comando
                    command = data.decode('utf-8').strip().upper()
                    
                    logger.info(f"📡 Comando recebido de {addr[0]}: {command}")
                    
                    # Comando especial: PING (apenas responde)
                    if command == "PING":
                        logger.success(f"✅ PING recebido de {addr[0]}")
                        continue
                    
                    # Executa callback se existir
                    if command in self.callbacks:
                        try:
                            self.callbacks[command]()
                            logger.success(f"✅ Comando {command} executado")
                        except Exception as e:
                            logger.error(f"❌ Erro ao executar callback para {command}: {e}")
                    else:
                        logger.warning(f"⚠️ Comando desconhecido: {command}")
                        logger.debug(f"   Comandos disponíveis: {list(self.callbacks.keys())}")
                
                except socket.timeout:
                    # Timeout normal, apenas continua loop
                    continue
                    
                except Exception as e:
                    logger.error(f"❌ Erro no servidor UDP: {e}")
        
        finally:
            # Cleanup
            if self.sock:
                self.sock.close()
            logger.info("🛑 Servidor UDP encerrado")
    
    def start(self):
        """
        Inicia o servidor UDP em thread separada
        
        Returns:
            bool: True se iniciado com sucesso
        """
        if self.running:
            logger.warning("⚠️ Servidor UDP já está rodando")
            return False
        
        try:
            self.running = True
            self.thread = threading.Thread(
                target=self._server_loop,
                daemon=True,
                name="UDPReceiver"
            )
            self.thread.start()
            
            logger.success(f"✅ Servidor UDP iniciado na porta {self.port}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Erro ao iniciar servidor UDP: {e}")
            self.running = False
            return False
    
    def stop(self):
        """
        Para o servidor UDP
        """
        if not self.running:
            logger.warning("⚠️ Servidor UDP não está rodando")
            return
        
        logger.info("🛑 Parando servidor UDP...")
        self.running = False
        
        # Aguarda thread terminar
        if self.thread and self.thread.is_alive():
            self.thread.join(timeout=2.0)
        
        logger.success("✅ Servidor UDP parado")
    
    def is_running(self) -> bool:
        """
        Verifica se servidor está ativo
        
        Returns:
            bool: True se servidor está rodando
        """
        return bool(self.running and self.thread and self.thread.is_alive())

# ============================
# FACTORY FUNCTION
# ============================

def create_udp_receiver(bot_controller, config: dict) -> Optional[UDPCommandReceiver]:
    """
    Factory function para criar receptor UDP com callbacks do bot
    
    Args:
        bot_controller: Instância do BotController
        config: Dicionário de configuração
    
    Returns:
        UDPCommandReceiver configurado ou None se desabilitado
    
    Example:
        receiver = create_udp_receiver(bot, config)
        if receiver:
            receiver.start()
    """
    # Verifica se está habilitado
    remote_config = config.get('remote_control', {})
    if not remote_config.get('enabled', False):
        logger.info("Controle remoto UDP desabilitado (remote_control.enabled: false)")
        return None
    
    # Obtém porta da config
    port = remote_config.get('port', DEFAULT_PORT)
    
    # Cria receiver
    receiver = UDPCommandReceiver(port=port)
    
    # Registra callbacks para cada comando
    from src.core.bot_controller import BotBehavior
    
    # Comandos de Modo
    receiver.register_callback("IDLE", lambda: setattr(bot_controller, 'behavior', BotBehavior.IDLE))
    receiver.register_callback("MISSION", lambda: setattr(bot_controller, 'behavior', BotBehavior.MISSION))
    receiver.register_callback("HUNT", lambda: setattr(bot_controller, 'behavior', BotBehavior.HUNTING))
    receiver.register_callback("HUNTING", lambda: setattr(bot_controller, 'behavior', BotBehavior.HUNTING))  # Alias
    receiver.register_callback("FOLLOW", lambda: setattr(bot_controller, 'behavior', BotBehavior.FOLLOW))
    
    # Comandos de Controle
    receiver.register_callback("PAUSE", lambda: setattr(bot_controller, 'paused', True))
    receiver.register_callback("RESUME", lambda: setattr(bot_controller, 'paused', False))
    receiver.register_callback("STOP", lambda: setattr(bot_controller, 'running', False))
    
    logger.success(f"✅ Receptor UDP criado (porta {port})")
    logger.info(f"   Comandos registrados: {len(receiver.callbacks)}")
    
    return receiver
