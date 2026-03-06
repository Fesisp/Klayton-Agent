
"""
Chat Handler - Detecção Visual de Mensagens Privadas (PM)
Monitora a tela continuamente para alertar sobre PMs com alta velocidade.
"""

import time
import cv2
from loguru import logger


class ChatHandler:
    """
    Detecta visualmente mensagens privadas (PM) usando template matching.
    Otimizado para alta velocidade com mínima latência.
    """
    
    def __init__(self, detector, config):
        """
        Inicializa o ChatHandler.
        
        Args:
            detector: Instância do GameStateDetector (para acesso aos templates)
            config: Configuração do bot
        """
        self.cfg = config
        self.detector = detector  # Reutiliza templates já carregados
        
        # Configurações de detecção de PM
        chat_cfg = self.cfg.get('chat_detection', {})
        self.check_interval = float(chat_cfg.get('check_interval', 1.5))  # Segundos entre verificações
        self.pm_threshold = float(chat_cfg.get('pm_threshold', 0.85))      # Confiança mínima (85%)
        self.last_check_time = 0
        
        logger.info(f"ChatHandler inicializado - Intervalo: {self.check_interval}s, Threshold: {self.pm_threshold}")

    def check_for_alerts(self, frame):
        """
        Procura visualmente por alertas de Mensagem Privada (PM) na tela.
        
        Usa template matching ultrarrápido para detectar o gatilho visual de PM
        sem processar a imagem inteira (apenas correlação).
        
        Args:
            frame: Frame capturado da tela (numpy array BGR)
            
        Returns:
            bool: True se PM detectado, False caso contrário
        """
        # Controle de taxa: apenas verifica a cada intervalo
        current_time = time.time()
        if current_time - self.last_check_time < self.check_interval:
            return False
            
        self.last_check_time = current_time
        
        # Obtém template de PM do detector
        pm_template = self.detector.templates.get('chat')  # Usa 'chat.png'
        
        if pm_template is None:
            logger.debug("Template 'chat.png' não encontrado em assets/templates/")
            return False

        try:
            # Template matching: encontra correlação máxima na tela
            res = cv2.matchTemplate(frame, pm_template, cv2.TM_CCOEFF_NORMED)
            _, max_val, _, _ = cv2.minMaxLoc(res)
            
            # Verifica se confiança atinge threshold
            if max_val >= self.pm_threshold:
                confianca = max_val * 100
                logger.critical(f"⚠️  MENSAGEM PRIVADA DETECTADA! (Confiança: {confianca:.1f}%)")
                return True
                
            return False
            
        except Exception as e:
            logger.error(f"Erro na detecção de chat: {e}")
            return False

    def reset_timer(self):
        """Reseta o timer para verificação imediata."""
        self.last_check_time = 0
    def generate_response(self, text_detected):
