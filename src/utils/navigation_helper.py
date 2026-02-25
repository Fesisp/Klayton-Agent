"""
Navigation Helper - Utilitários de Navegação para o PokeBot

Fornece funcionalidades de detecção de obstáculos e movimentação de escape
que podem ser utilizadas em múltiplos modos (MISSION, FOLLOW, HUNTING).
"""

import time
import random
from loguru import logger


class NavigationHelper:
    """Auxiliar de navegação com detecção anti-stuck e movimentos de escape."""
    
    def __init__(self, input_simulator, config=None):
        """
        Inicializa o NavigationHelper.
        
        Args:
            input_simulator: Instância de InputSimulator para executar comandos
            config: Dicionário de configuração (opcional)
        """
        self.input = input_simulator
        self.cfg = config or {}
        
        # Configurações de detecção de obstáculos
        nav_cfg = self.cfg.get('navigation', {})
        self.stuck_threshold = nav_cfg.get('stuck_threshold', 5.0)  # segundos
        self.stuck_distance_tolerance = nav_cfg.get('stuck_distance_tolerance', 10)  # pixels
        self.escape_cooldown = nav_cfg.get('escape_cooldown', 5.0)  # segundos
        self.max_escape_attempts = nav_cfg.get('max_escape_attempts', 3)
        
        # Estado interno
        self.last_target_pos = None
        self.last_target_time = 0
        self.last_escape_time = 0
        self.escape_attempts = 0
    
    def is_stuck(self, current_target_pos, current_time=None):
        """
        Detecta se o bot está preso no mesmo alvo por muito tempo.
        
        Args:
            current_target_pos: (x, y) posição do alvo atual
            current_time: timestamp atual (opcional, usa time.time() se não fornecido)
            
        Returns:
            bool: True se detectado que está preso, False caso contrário
        """
        if current_time is None:
            current_time = time.time()
        
        # Primeira verificação ou cooldown ativo
        if (current_time - self.last_escape_time) < self.escape_cooldown:
            return False
        
        # Se não há histórico, salva e retorna False
        if self.last_target_pos is None:
            self.last_target_pos = current_target_pos
            self.last_target_time = current_time
            return False
        
        # Calcula distância entre alvo atual e alvo anterior
        dx = current_target_pos[0] - self.last_target_pos[0]
        dy = current_target_pos[1] - self.last_target_pos[1]
        distance = (dx**2 + dy**2)**0.5
        
        # Se alvo mudou significativamente, atualiza referência e não está preso
        if distance > self.stuck_distance_tolerance:
            self.last_target_pos = current_target_pos
            self.last_target_time = current_time
            self.escape_attempts = 0
            return False
        
        # Se alvo está praticamente no mesmo lugar por muito tempo
        time_stuck = current_time - self.last_target_time
        if time_stuck > self.stuck_threshold:
            logger.warning(f"🚧 Obstáculo detectado! Preso por {time_stuck:.1f}s na mesma posição")
            return True
        
        return False
    
    def perform_escape_movement(self):
        """
        Executa sequência de movimentos para escapar de obstáculos.
        
        Estratégia:
        1. Movimentos laterais curtos (WASD)
        2. Incrementa contador de tentativas
        3. Se exceder máximo, realiza movimento mais agressivo
        """
        self.last_escape_time = time.time()
        self.escape_attempts += 1
        
        if self.escape_attempts > self.max_escape_attempts:
            logger.error(f"⚠️ Máximo de tentativas de escape atingido ({self.max_escape_attempts})")
            # Reset após atingir máximo
            self.escape_attempts = 0
            self.last_target_pos = None
            return
        
        logger.info(f"🔄 Tentativa de escape {self.escape_attempts}/{self.max_escape_attempts}")
        
        # Movimentos aleatórios curtos
        directions = ['w', 'a', 's', 'd']
        
        for _ in range(3):  # 3 movimentos rápidos
            direction = random.choice(directions)
            logger.debug(f"   → Movimento: {direction.upper()}")
            
            # Pressiona tecla por tempo curto
            for _ in range(2):  # 2 pulsos por direção
                self.input.press(direction)
                time.sleep(0.1)
            
            time.sleep(0.2)  # Pequena pausa entre direções
        
        # Reset da posição após escape
        self.last_target_pos = None
        logger.info("✅ Sequência de escape concluída")
    
    def reset_stuck_detection(self):
        """Reseta o estado de detecção de obstáculos.
        
        Útil quando o bot muda de modo ou quando um objetivo é alcançado.
        """
        self.last_target_pos = None
        self.last_target_time = 0
        self.escape_attempts = 0
        logger.debug("🔄 Detecção de obstáculos resetada")
    
    def get_stuck_info(self):
        """
        Retorna informações sobre o estado atual de detecção.
        
        Returns:
            dict: Informações de debug sobre stuck detection
        """
        current_time = time.time()
        time_at_target = current_time - self.last_target_time if self.last_target_pos else 0
        
        return {
            'last_target': self.last_target_pos,
            'time_at_target': time_at_target,
            'escape_attempts': self.escape_attempts,
            'cooldown_remaining': max(0, self.escape_cooldown - (current_time - self.last_escape_time))
        }
