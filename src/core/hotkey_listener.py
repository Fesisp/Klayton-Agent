"""
Hotkey Listener - Sistema de controle global por teclas de atalho

Permite mudar o comportamento do bot em tempo real sem precisar reiniciar.
Funciona mesmo quando a janela do jogo está em foco.
"""

from pynput import keyboard
from loguru import logger
from enum import Enum
import threading
import time


class HotkeyCommand(Enum):
    """Comandos disponíveis via hotkeys."""
    IDLE = "idle"
    MISSION = "mission"
    HUNTING = "hunting"
    FOLLOW = "follow"
    PAUSE = "pause"
    RESUME = "resume"
    STOP = "stop"


class HotkeyListener:
    def __init__(self, bot_controller, config=None):
        """
        Inicializa o listener de hotkeys globais.
        
        Args:
            bot_controller: Instância do BotController para enviar comandos
            config: Dicionário de configuração com mapeamento de teclas
        """
        self.bot = bot_controller
        self.cfg = config or {}
        self.controls_cfg = self.cfg.get('controls', {})
        
        # Carrega mapeamento de teclas do config
        self.hotkeys = {
            self.controls_cfg.get('idle_key', '<f1>'): HotkeyCommand.IDLE,
            self.controls_cfg.get('mission_key', '<f2>'): HotkeyCommand.MISSION,
            self.controls_cfg.get('hunting_key', '<f3>'): HotkeyCommand.HUNTING,
            self.controls_cfg.get('follow_key', '<f4>'): HotkeyCommand.FOLLOW,
            self.controls_cfg.get('pause_key', '<f5>'): HotkeyCommand.PAUSE,
            self.controls_cfg.get('resume_key', '<f6>'): HotkeyCommand.RESUME,
            self.controls_cfg.get('stop_key', '<f9>'): HotkeyCommand.STOP,
        }
        
        self.listener = None
        self.running = False
        self.paused = False
        
        logger.info("🎮 Hotkey Listener inicializado")
        self._print_hotkey_map()
    
    def _print_hotkey_map(self):
        """Imprime mapeamento de teclas no console."""
        logger.info("=" * 50)
        logger.info("🎮 CONTROLES DISPONÍVEIS:")
        logger.info("=" * 50)
        
        key_map = {
            HotkeyCommand.IDLE: "Estado Ocioso (para tudo)",
            HotkeyCommand.MISSION: "Estado Missão (segue Goto/Talk)",
            HotkeyCommand.HUNTING: "Estado Caça (procura alvos)",
            HotkeyCommand.FOLLOW: "Seguir Personagem",
            HotkeyCommand.PAUSE: "Pausar Bot",
            HotkeyCommand.RESUME: "Retomar Bot",
            HotkeyCommand.STOP: "Parar Bot Completamente",
        }
        
        for key, command in self.hotkeys.items():
            description = key_map.get(command, "Desconhecido")
            logger.info(f"  {key.upper():<8} → {description}")
        
        logger.info("=" * 50)
    
    def start(self):
        """Inicia o listener em uma thread separada."""
        if self.running:
            logger.warning("Hotkey listener já está rodando")
            return
        
        self.running = True
        
        # Cria listener com callbacks para cada combinação
        hotkey_combinations = {}
        for key, command in self.hotkeys.items():
            # Remove < e > da tecla
            clean_key = key.strip('<>')
            hotkey_combinations[clean_key] = lambda cmd=command: self._on_hotkey(cmd)
        
        # Inicia listener global
        self.listener = keyboard.GlobalHotKeys(hotkey_combinations)
        self.listener.start()
        
        logger.info("✅ Hotkey listener ativo! Pressione as teclas para controlar o bot.")
    
    def stop(self):
        """Para o listener."""
        if not self.running:
            return
        
        self.running = False
        if self.listener:
            self.listener.stop()
        
        logger.info("Hotkey listener parado")
    
    def _on_hotkey(self, command):
        """
        Callback executado quando uma hotkey é pressionada.
        
        Args:
            command: HotkeyCommand correspondente à tecla
        """
        try:
            logger.info(f"🎮 Hotkey detectada: {command.value.upper()}")
            
            if command == HotkeyCommand.IDLE:
                self._set_idle()
            elif command == HotkeyCommand.MISSION:
                self._set_mission()
            elif command == HotkeyCommand.HUNTING:
                self._set_hunting()
            elif command == HotkeyCommand.FOLLOW:
                self._set_follow()
            elif command == HotkeyCommand.PAUSE:
                self._pause_bot()
            elif command == HotkeyCommand.RESUME:
                self._resume_bot()
            elif command == HotkeyCommand.STOP:
                self._stop_bot()
            
        except Exception as e:
            logger.error(f"Erro ao processar hotkey {command}: {e}")
    
    def _set_idle(self):
        """Muda para estado IDLE."""
        from ..core.bot_controller import BotBehavior
        
        if hasattr(self.bot, 'behavior'):
            self.bot.behavior = BotBehavior.IDLE
            logger.info("⏸️ Bot mudado para estado IDLE (Ocioso)")
            logger.info("   → Bot não fará nada, apenas observará")
        else:
            logger.error("BotController não tem atributo 'behavior'")
    
    def _set_mission(self):
        """Muda para estado MISSION."""
        from ..core.bot_controller import BotBehavior
        
        if hasattr(self.bot, 'behavior'):
            self.bot.behavior = BotBehavior.MISSION
            logger.info("🗺️ Bot mudado para estado MISSION (Missão)")
            logger.info("   → Bot seguirá Goto e Talk automaticamente")
        else:
            logger.error("BotController não tem atributo 'behavior'")
    
    def _set_hunting(self):
        """Muda para estado HUNTING."""
        from ..core.bot_controller import BotBehavior
        
        if hasattr(self.bot, 'behavior'):
            self.bot.behavior = BotBehavior.HUNTING
            targets = getattr(self.bot, 'hunt_target_pokemon', [])
            logger.info("🎣 Bot mudado para estado HUNTING (Caça)")
            logger.info(f"   → Alvos: {targets if targets else 'Nenhum configurado'}")
        else:
            logger.error("BotController não tem atributo 'behavior'")
    
    def _set_follow(self):
        """Muda para estado FOLLOW."""
        from ..core.bot_controller import BotBehavior
        
        if hasattr(self.bot, 'behavior'):
            self.bot.behavior = BotBehavior.FOLLOW
            logger.info("👤 Bot mudado para estado FOLLOW (Seguir)")
            logger.info("   → Bot seguirá seu personagem principal")
        else:
            logger.error("BotController não tem atributo 'behavior'")
    
    def _pause_bot(self):
        """Pausa o bot temporariamente."""
        if hasattr(self.bot, 'paused'):
            self.bot.paused = True
            logger.info("⏸️ Bot PAUSADO")
            logger.info("   → Pressione F6 para retomar")
        else:
            logger.error("BotController não tem atributo 'paused'")
    
    def _resume_bot(self):
        """Retoma o bot após pausa."""
        if hasattr(self.bot, 'paused'):
            self.bot.paused = False
            logger.info("▶️ Bot RETOMADO")
        else:
            logger.error("BotController não tem atributo 'paused'")
    
    def _stop_bot(self):
        """Para o bot completamente."""
        if hasattr(self.bot, 'running'):
            self.bot.running = False
            logger.info("🛑 Bot PARADO completamente")
            logger.info("   → Reinicie o script para usar novamente")
        else:
            logger.error("BotController não tem atributo 'running'")
    
    def is_paused(self):
        """Verifica se o bot está pausado."""
        return getattr(self.bot, 'paused', False)


class HotkeyManager:
    """Gerenciador simplificado para integração fácil."""
    
    @staticmethod
    def create_and_start(bot_controller, config):
        """
        Cria e inicia o hotkey listener.
        
        Args:
            bot_controller: Instância do BotController
            config: Configuração do bot
            
        Returns:
            HotkeyListener: Instância do listener
        """
        listener = HotkeyListener(bot_controller, config)
        listener.start()
        return listener
