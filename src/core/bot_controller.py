import time
import cv2
import winsound
import random
from pathlib import Path
from enum import Enum
import ctypes
from loguru import logger
from ..perception.game_state_detector import GameState
from ..utils.geometry import normalize_roi, crop_roi_safe, get_safe_random_point
from ..utils.navigation_helper import NavigationHelper
from ..utils.notifier import NotificationManager


class BotBehavior(Enum):
    """Estados de comportamento do bot."""
    IDLE = 0      # Ocioso - não faz nada, apenas observa
    MISSION = 1   # Seguindo missão (Goto/Talk)
    HUNTING = 2   # Caçando Pokémons específicos
    FOLLOW = 3    # Seguindo personagem principal


class BotController:
    def __init__(self, config, components):
        self.cfg = config
        self.cap = components['screen']
        self.detector = components['detector']
        self.input = components['input']
        self.strategy = components['strategy']
        self.ocr = components['ocr']
        self.team_mgr = components['team_mgr']
        self.strategy.detector = self.detector
        
        # === NOTIFICAÇÕES ===
        self.notifier = NotificationManager(config)
        
        self.running = True
        self.paused = False  # Controle de pausa via hotkey
        self.debug = bool(self.cfg.get('bot', {}).get('debug_mode', False))
        
        # NavigationHelper para detecção de obstáculos
        self.nav_helper = NavigationHelper(self.input, config)
        
        # Máquina de Estados - Comportamento Ativo
        behavior_cfg = self.cfg.get('bot', {}).get('behavior', 'mission').lower()
        if behavior_cfg == 'idle':
            self.behavior = BotBehavior.IDLE
        elif behavior_cfg == 'hunting':
            self.behavior = BotBehavior.HUNTING
        elif behavior_cfg == 'follow':
            self.behavior = BotBehavior.FOLLOW
        else:
            self.behavior = BotBehavior.MISSION
        
        # Configurações de Caça
        hunt_cfg = self.cfg.get('hunt', {})
        self.hunt_target_pokemon = hunt_cfg.get('target_pokemon', [])  # Lista de nomes
        self.hunt_target_ability = hunt_cfg.get('target_ability', None)
        self.hunt_area_bounds = hunt_cfg.get('area_bounds', None)  # [x1, y1, x2, y2]
        self.hunt_move_interval = float(hunt_cfg.get('move_interval', 2.0))
        self.last_hunt_move = 0
        
        # Configurações de Follow (Seguir Personagem)
        follow_cfg = self.cfg.get('follow', {})
        self.follow_distance = int(follow_cfg.get('distance', 50))  # Distância mínima em pixels
        self.follow_method = follow_cfg.get('method', 'template')  # template ou party_button
        self.follow_check_interval = float(follow_cfg.get('check_interval', 1.0))
        self.last_follow_check = 0
        
        # Memória de curto prazo para FOLLOW (última posição vista)
        self.last_seen_pos = None
        self.last_seen_time = 0
        self.follow_lost_target_timeout = float(self.cfg.get('follow_settings', {}).get('lost_target_timeout', 5.0))
        self.follow_player_name = self.cfg.get('follow_settings', {}).get('player_name', None)
        
        # Memória de Alvo: Rastreia última posição conhecida
        self.target_last_known_pos = None
        self.target_last_seen_time = 0
        self.memory_retention = float(self.cfg.get('follow_settings', {}).get('memory_retention', 10.0))  # 10 segundos

        # Tracking de batalha para inferência de velocidade/dano
        self.last_player_hp_percentage = None
        self.last_enemy_hp_percentage = None
        self.last_damage_received = 0
        self.turn_count = 0  # Contador de turnos para Toxic tracking
        
        # === BATTLE CONTEXT v2.5: Tracking Persistente ===
        self.battle_context = {
            'active': False,
            'turn_count': 0,
            'last_player_hp': None,
            'last_enemy_hp': None,
            'last_enemy_name': None
        }
        
        logger.info(f"Bot iniciado em modo: {self.behavior.name} com Motor de Batalha v2.5")
        if self.behavior == BotBehavior.HUNTING:
            logger.info(f"Alvos de caça: {self.hunt_target_pokemon}")
        elif self.behavior == BotBehavior.FOLLOW:
            logger.info(f"Modo Follow ativo - Método: {self.follow_method}")

    def _reset_battle_context(self):
        """Reseta tracking ao sair de batalha."""
        logger.info("🏁 Batalha encerrada. Resetando contexto tático.")
        self.battle_context = {
            'active': False,
            'turn_count': 0,
            'last_player_hp': None,
            'last_enemy_hp': None,
            'last_enemy_name': None
        }
        # Reseta stages de buffs/debuffs
        if hasattr(self.strategy, 'intelligence'):
            self.strategy.intelligence.reset_battle_stages()

    def handle_follow(self, frame):
        """Modo FOLLOW consolidado com Template Matching prioritário e OCR como fallback.
        
        ESTRATÉGIA OTIMIZADA:
        1. Template Matching em escala de cinza (rápido e preciso)
        2. Se falhar: OCR Deep Search após 3 segundos
        3. Memória de última posição conhecida
        4. Detecção de obstáculos via NavigationHelper
        
        Args:
            frame: Frame capturado da tela
        """
        if not self.follow_player_name:
            logger.warning("⚠️ FOLLOW ativo mas player_name não configurado")
            return
        
        current_time = time.time()
        
        # Verificar cooldown de checagem
        if current_time - self.last_follow_check < self.follow_check_interval:
            return
        
        self.last_follow_check = current_time
        
        # === FASE 1: Template Matching (Prioritário) ===
        target_pos = self._follow_by_template_get_pos(frame)
        
        # === FASE 2: OCR Deep Search (Fallback após 3s) ===
        if not target_pos:
            time_since_last_seen = current_time - self.last_seen_time if self.last_seen_time else 999
            
            if time_since_last_seen > 3.0:  # Deep Search após 3 segundos
                if self.debug:
                    logger.debug("[FOLLOW] Template falhou - Ativando OCR Deep Search...")
                target_pos = self.detector.find_player_name(frame, self.follow_player_name)
        
        # === FASE 3: Processamento de Posição ===
        if target_pos:
            # Alvo encontrado - atualiza memória
            self.last_seen_pos = target_pos
            self.last_seen_time = current_time
            self.nav_helper.reset_stuck_detection()
            
            # Calcula distância do centro
            h, w = frame.shape[:2]
            center_x, center_y = w // 2, h // 2
            player_x, player_y = target_pos
            
            distance = ((player_x - center_x)**2 + (player_y - center_y)**2)**0.5
            
            if distance > self.follow_distance:
                # === DETECÇÃO DE OBSTÁCULOS ===
                if self.nav_helper.is_stuck(target_pos, current_time):
                    logger.warning("🚧 Obstáculo detectado! Executando escape...")
                    self.nav_helper.perform_escape_movement()
                    return
                
                # Movimento normal em direção ao alvo
                move_x = center_x + int((player_x - center_x) * 0.7)
                move_y = center_y + int((player_y - center_y) * 0.7)
                
                logger.info(f"👤 [FOLLOW] Seguindo {self.follow_player_name} | dist: {distance:.0f}px")
                self.input.click(move_x, move_y)
                
                walk_time = min(1.5, max(0.3, distance / 500))
                time.sleep(walk_time)
            else:
                if self.debug:
                    logger.debug(f"[FOLLOW] Alvo próximo ({distance:.0f}px < {self.follow_distance}px)")
        
        else:
            # === FASE 4: Memória de Curto Prazo ===
            time_since_last_seen = current_time - self.last_seen_time if self.last_seen_time else 999
            
            if self.last_seen_pos and time_since_last_seen < self.follow_lost_target_timeout:
                logger.info(f"🔍 Alvo perdido - Indo para última posição ({time_since_last_seen:.1f}s)")
                x, y = self.last_seen_pos
                self.input.click(x, y)
                time.sleep(1.0)
            else:
                # Timeout - modo de recuperação
                if time_since_last_seen >= self.follow_lost_target_timeout:
                    logger.warning(f"⏰ Alvo perdido há {time_since_last_seen:.1f}s - Busca de recuperação")
                    self.last_seen_pos = None
                    self._recovery_search()
    
    def run(self):
        """Loop principal do bot."""
        logger.info(f"Bot Iniciado em modo {self.behavior.name}! Pressione Ctrl+C para parar.")
        while self.running:
            try:
                # Verificação de pausa (via hotkey)
                if self.paused:
                    time.sleep(0.5)  # Sleep curto quando pausado
                    continue
                
                img = self.cap.capture()
                game_state = self.detector.detect_state(img)

                if self.debug:
                    logger.debug(f"GameState: {game_state.name} | Behavior: {self.behavior.name}")

                # PRIORIDADE MÁXIMA: Shiny (sobrepõe qualquer estado)
                if game_state == GameState.SHINY_FOUND:
                    self.handle_shiny()
                
                # Modo FOLLOW: Rastreio contínuo de jogador
                if self.behavior == BotBehavior.FOLLOW:
                    self.handle_follow(img)
                    continue

                # PRIORIDADE 2: Batalha (sobrepõe Missão/Caça/Follow, mas não os encerra)
                if game_state == GameState.IN_BATTLE:
                    self.handle_battle(img)
                    continue

                # PRIORIDADE 3: Comportamento Ativo (quando explorando)
                if game_state == GameState.EXPLORING:
                    if self.behavior == BotBehavior.MISSION:
                        self.handle_mission(img)
                    elif self.behavior == BotBehavior.HUNTING:
                        self.handle_hunting(img)
                    elif self.behavior == BotBehavior.FOLLOW:
                        self.handle_follow(img)
                    elif self.behavior == BotBehavior.IDLE:
                        if self.debug:
                            logger.debug("Bot em estado OCIOSO. Aguardando...")
                        # Modo IDLE: não faz absolutamente nada
                        pass
                
                # Intervalo do loop principal (configurável, padrão 1.0s)
                sleep_time = float(self.cfg.get('bot', {}).get('loop_interval', 1.0))
                time.sleep(sleep_time)

            except KeyboardInterrupt:
                logger.info("Interrupção manual (Ctrl+C). Parando...")
                self.running = False
            except Exception as e:
                logger.exception(f"Erro no loop principal: {e}")
                time.sleep(5)  # Espera segura antes de tentar novamente

    def handle_shiny(self):
        logger.critical("SHINY ENCONTRADO! ALARME!")
        
        # Pausa o bot imediatamente
        self.paused = True
        logger.warning("Bot PAUSADO automaticamente devido ao shiny")
        
        # === NOTIFICAÇÃO ENVIADA PARA TELEGRAM/DISCORD ===
        self.notifier.notify_shiny_found("Pokémon Desconhecido", "Local Desconhecido")

        # 1) Toca o alarme padrão do PC (beep) algumas vezes
        for _ in range(10):
            winsound.MessageBeep(winsound.MB_ICONEXCLAMATION)
            time.sleep(0.5)

        # 2) Notificação visual simples via MessageBox do Windows
        try:
            ctypes.windll.user32.MessageBoxW(
                0,
                "Um SHINY foi detectado pelo PokeBot Pro!\n\nBot PAUSADO. Pressione F6 para retomar.",
                "PokeBot Pro - SHINY ENCONTRADO",
                0x00000040,  # MB_ICONINFORMATION
            )
        except Exception as e:
            logger.error(f"Falha ao exibir MessageBox de shiny: {e}")

        # Bot continua rodando mas pausado, aguardando F6 para retomar

    def handle_mission(self, img):
        """Modo MISSION: Segue missões clicando em Talk e Goto."""
        # 1) Verifica se há diálogo (talk.png) antes de qualquer coisa
        talk_tpl = self.detector.templates.get('talk')
        if talk_tpl is not None:
            # If a specific search area is configured, crop the image to that ROI to avoid false positives
            talk_area = self.cfg.get('detection', {}).get('talk_search_area')
            if talk_area:
                search_img = crop_roi_safe(img, talk_area)
                if self.debug:
                    logger.debug(f"Talk search area usada: {talk_area}")
            else:
                search_img = img

            res_talk = cv2.matchTemplate(search_img, talk_tpl, cv2.TM_CCOEFF_NORMED)
            _, max_val_talk, _, _ = cv2.minMaxLoc(res_talk)
            # Use configurable threshold (default 0.95) to avoid confusão com chat
            talk_thresh = self.cfg.get('detection', {}).get('talk_threshold', 0.95)
            if self.debug:
                logger.debug(f"Score talk.png: {max_val_talk:.3f} (threshold={talk_thresh})")
            if max_val_talk > talk_thresh:
                logger.info(f"Ícone de diálogo encontrado (score={max_val_talk:.3f}). Avançando conversa com Espaço...")
                self.input.press('space')
                return

        # 2) Se não tem diálogo, tenta seguir missão via Goto
        goto_tpl = self.detector.templates.get('goto')
        if goto_tpl is None:
            logger.warning("Template 'goto.png' não encontrado ou não carregado.")
            return

        res = cv2.matchTemplate(img, goto_tpl, cv2.TM_CCOEFF_NORMED)
        _, max_val, _, max_loc = cv2.minMaxLoc(res)

        goto_thresh = self.cfg.get('detection', {}).get('goto_threshold', 0.8)

        if self.debug:
            logger.debug(f"Score goto.png: {max_val:.3f} (threshold={goto_thresh})")

        # Antes de clicar em Goto, revalida se não estamos em batalha neste frame
        current_state = self.detector.detect_state(img)
        if current_state == GameState.IN_BATTLE:
            if self.debug:
                logger.debug("Botões de batalha detectados ao tentar clicar em Goto. Cancelando clique.")
            return

        if max_val > goto_thresh:
            logger.info("Botão Goto encontrado. Seguindo missão...")
            # Clica em uma região interna "segura" do botão encontrado (não precisa ser o centro exato)
            h, w = goto_tpl.shape[:2]
            x, y = max_loc

            margin_x = int(0.1 * w)
            margin_y = int(0.1 * h)

            safe_x1 = x + margin_x
            safe_x2 = x + w - margin_x
            safe_y1 = y + margin_y
            safe_y2 = y + h - margin_y

            cx = (safe_x1 + safe_x2) // 2
            cy = (safe_y1 + safe_y2) // 2

            if self.debug:
                logger.debug(f"Clicando em Goto nas coordenadas seguras: ({cx}, {cy}) dentro de [{safe_x1},{safe_y1},{safe_x2},{safe_y2}]")

            self.input.click(cx, cy)
            time.sleep(2) # Espera caminhar
            return

        # 3) Fallback: nenhum talk nem Goto detectado
        # Não faz nada para evitar movimento indesejado
        if self.debug:
            logger.debug("Nenhum talk/goto confiável encontrado. Aguardando próximo ciclo.")
    
    def handle_hunting(self, img):
        """Modo HUNTING: Movimenta-se aleatoriamente em área de caça para encontrar Pokémon específicos."""
        
        # Verificar se passou tempo suficiente desde o último movimento
        current_time = time.time()
        if current_time - self.last_hunt_move < self.hunt_move_interval:
            return
        
        self.last_hunt_move = current_time
        
        # Estratégia de movimentação humanizada para caça
        # 1. Movimento aleatório em área delimitada (se configurada)
        # 2. Simula padrões de caminhada humana (não perfeitamente aleatório)
        
        if self.hunt_area_bounds and len(self.hunt_area_bounds) == 4:
            x1, y1, x2, y2 = self.hunt_area_bounds
            
            # Gera ponto aleatório dentro da área
            target_x = random.randint(x1, x2)
            target_y = random.randint(y1, y2)
            
            if self.debug:
                logger.debug(f"[HUNTING] Movendo para ponto aleatório: ({target_x}, {target_y})")
            
            # Move para o ponto usando movimento humanizado
            self.input.click(target_x, target_y)
            
            # Pequeno delay para simular caminhada
            walk_delay = random.uniform(1.0, 2.5)
            time.sleep(walk_delay)
        else:
            # Sem área definida: movimento direcional aleatório
            directions = ['w', 'a', 's', 'd']  # Cima, Esquerda, Baixo, Direita
            
            # Escolhe direção aleatória
            direction = random.choice(directions)
            
            # Duração variável de movimento
            duration = random.uniform(0.5, 1.5)
            
            if self.debug:
                logger.debug(f"[HUNTING] Movendo na direção '{direction}' por {duration:.2f}s")
            
            # Simula pressionar tecla por tempo variável
            # (PyAutoGUI não suporta keydown nativo, então simulamos com múltiplos press)
            steps = int(duration * 10)  # 10 passos por segundo
            for _ in range(steps):
                self.input.press(direction)
                time.sleep(0.1)
        
        # Ocasionalmente para e olha ao redor (mais humano)
        if random.random() < 0.15:  # 15% de chance
            if self.debug:
                logger.debug("[HUNTING] Pausando para olhar ao redor...")
            self.input.perform_idle_action()
            time.sleep(random.uniform(1.0, 2.0))

    def handle_battle(self, img):
        """
        Pipeline de Batalha Integrado (v2.5)
        Combina: Visão Rápida + Decisão TTK + Inferência de Itens + PP Tracking
        """
        # 1. Inicialização de Contexto e PP Tracking
        if not self.battle_context['active']:
            self.battle_context['active'] = True
            self.battle_context['turn_count'] = 0
            logger.info("⚔️ Nova batalha detectada - Iniciando Motor Tático v2.5")
            
            # --- INÍCIO: INJEÇÃO DA MELHORIA 4 (PP TRACKING) ---
            # Identifica o Pokémon atual (o primeiro da party)
            player_name = self.team_mgr.current_team[0] if self.team_mgr.current_team else None
            if player_name:
                my_moves = self.team_mgr.get_moves(player_name)
                if my_moves:
                    moves_data = {}
                    for move in my_moves:
                        if move:
                            # Busca o PP máximo direto do banco de dados em cache (<1ms)
                            move_info = self.strategy.db.get_move_data(move.strip().lower())
                            if move_info:
                                moves_data[move] = move_info.get('pp', 0)
                    
                    # Inicializa o rastreio na memória do TeamManager
                    self.team_mgr.initialize_pp_tracking(player_name, moves_data)
                    logger.info(f"📊 Rastreamento de PP inicializado para {player_name}: {moves_data}")
            # --- FIM DA INJEÇÃO ---
            
            # Garante menu de luta aberto
            self.input.click_fight_button(img)
            time.sleep(self.cfg.get('battle', {}).get('fight_to_moves_delay', 1.2))
            img = self.cap.capture()

        self.battle_context['turn_count'] += 1
        
        # 2. Percepção Avançada (HP via Pixels HSV, sem OCR lento)
        battle_info = self.detector.get_battle_info(img)
        enemy_name = battle_info.get('enemy_name', '').strip()
        player_name = battle_info.get('player_name', '').strip()
        
        current_player_hp = battle_info.get('player_hp_percentage')
        
        if not player_name or not enemy_name:
            logger.warning("Não foi possível ler nomes na batalha. Tentando novamente...")
            return

        # 3. Inferência de Itens e Dano (record_turn_result)
        # Calcula quanto dano levamos no turno passado para inferir Choice Band/Life Orb
        if self.battle_context['last_player_hp'] is not None and current_player_hp is not None:
            damage_taken = self.battle_context['last_player_hp'] - current_player_hp
            if damage_taken > 0:
                # Passa para a estratégia analisar se o dano condiz com itens ofensivos
                if hasattr(self.strategy, 'record_turn_result'):
                    self.strategy.record_turn_result(
                        i_attacked_first=True,  # Simplificação, idealmente rastrear quem agiu
                        damage_received=damage_taken
                    )
        
        # Atualiza contexto para próximo turno
        self.battle_context['last_player_hp'] = current_player_hp
        self.battle_context['last_enemy_name'] = enemy_name

        # 4. Decisão Tática Baseada em TTK (Time-To-Kill)
        # get_best_action avalia: Status, Risco de Morte, Velocidade e Dano Letal
        tactical_action = self.strategy.get_best_action(player_name, enemy_name)
        
        logger.info(f"🧠 Decisão Tática Turno {self.battle_context['turn_count']}: {tactical_action}")

        # 5. Execução da Ação
        if tactical_action == "SWITCH_TO_RESISTANT" or tactical_action == "SWITCH_MANDATORY":
            self._handle_switch_to_resistant(enemy_name, img)
            
        elif tactical_action == "HEAL":
            success = self._use_healing_move(player_name)
            if not success:
                logger.warning("Falha ao curar, atacando como fallback.")
                self._perform_attack(player_name, enemy_name)
                
        elif tactical_action in ["ATTACK", "BEST_EFFICIENCY_ATTACK"]:
            self._perform_attack(player_name, enemy_name)
            
        else:
            # Fallback seguro - delega para estratégia antiga
            best_slot = self.strategy.get_best_move(player_name, enemy_name)
            if best_slot == -1:
                self._execute_emergency_switch(enemy_name, img)
            else:
                logger.info(f"⚔️ [BATTLE] Atacando slot {best_slot} contra {enemy_name}")
                self.input.click_in_slot(best_slot)

        # Sincroniza contador de turnos da estratégia (clima, estados temporais)
        if hasattr(self.strategy, 'increment_turn'):
            self.strategy.increment_turn()

        # Cooldown entre turnos
        time.sleep(self.cfg.get('battle', {}).get('action_cooldown', 4.0))
    
    def _perform_attack(self, player_name, enemy_name):
        """Executa ataque considerando PP e Humanização Avançada."""
        # Escolhe o melhor slot
        best_slot = self.strategy.get_best_move(player_name, enemy_name)
        
        if best_slot == -1:  # Estratégia pediu troca de emergência
            logger.warning("Estratégia solicitou troca de emergência durante seleção de ataque.")
            self._handle_switch_to_resistant(enemy_name, None)
            return

        # --- INÍCIO: CONSUMO DE PP (MELHORIA 4) ---
        moves = self.team_mgr.get_moves(player_name)
        if moves and 0 <= best_slot < len(moves):
            move_name = moves[best_slot]
            if move_name:
                # Atualiza estado de clima quando usamos golpe de weather
                if hasattr(self.strategy, 'update_weather_from_move'):
                    self.strategy.update_weather_from_move(move_name)

                move_info = self.strategy.db.get_move_data(move_name.strip().lower())
                max_pp = move_info.get('pp', 0) if move_info else 0
                
                # Desconta o PP usado e retorna o quanto sobrou
                pp_left = self.team_mgr.track_move_usage(player_name, move_name, max_pp)
                logger.info(f"⚔️ Usando {move_name} (Slot {best_slot}) - PP Restante: {pp_left}/{max_pp}")
        # --- FIM DO CONSUMO DE PP ---

        # --- INÍCIO: CLIQUE HUMANIZADO (MELHORIA 3) ---
        # Usa humanized_click_in_slot se disponível, senão fallback
        if hasattr(self.input, 'humanized_click_in_slot'):
            self.input.humanized_click_in_slot(best_slot, delay_min=0.1, delay_max=0.3)
        else:
            # Fallback seguro: aplica humanização genérica se o método específico não existir
            logger.debug("Usando fallback de clique genérico (adicione humanized_click_in_slot ao InputSimulator)")
            self.input.click_in_slot(best_slot)
        # --- FIM DO CLIQUE HUMANIZADO ---

    def _use_healing_move(self, player_name):
        """Tenta usar um movimento de cura conhecido."""
        my_moves = self.team_mgr.get_moves(player_name)
        healing_moves = self.strategy.healing_move_names  # Set de nomes de cura
        
        for idx, move in enumerate(my_moves):
            if move and move.lower() in healing_moves:
                logger.info(f"🩹 Executando cura com {move} (Slot {idx})")
                self.input.click_in_slot(idx)
                return True
        return False

    def _handle_switch_to_resistant(self, enemy_name, img):
        """
        Troca para o Pokémon mais resistente ao inimigo atual.
        Analisa tipos e imunidades para escolher o melhor 'tank'.
        """
        logger.info(f"🛡️ Buscando troca defensiva contra {enemy_name}...")
        
        # Garante menu de pokémon aberto
        if img is None:
            img = self.cap.capture()
        self.input.click_pokemon_button(img)
        time.sleep(1.0)
        
        # Obtém tipos do inimigo
        enemy_types = self.strategy.db.get_pokemon_types(enemy_name)
        
        current_team = self.team_mgr.current_team
        best_switch_idx = -1
        best_resistance_score = -1.0
        
        # Avalia cada membro do time (começando do índice 1, pois 0 é o atual)
        for idx, poke_name in enumerate(current_team):
            if idx == 0: continue  # Pula o atual
            if not poke_name: continue
            
            poke_types = self.strategy.db.get_pokemon_types(poke_name)
            
            # Calcula score de resistência (quanto menor o multiplicador, melhor)
            # Imunidade (0.0) ganha score máximo
            total_mult = 1.0
            for e_type in enemy_types:
                mult = self.strategy.db.get_type_multiplier(e_type, poke_types)
                total_mult *= mult
            
            # Score inverso: quanto menor o dano, maior o score
            resistance_score = 1.0 / (total_mult + 0.01)
            
            logger.debug(f"Analisando {poke_name}: Recebe {total_mult}x de dano (Score: {resistance_score:.1f})")
            
            if resistance_score > best_resistance_score:
                best_resistance_score = resistance_score
                best_switch_idx = idx
        
        if best_switch_idx != -1:
            logger.info(f"🔄 Trocando para {current_team[best_switch_idx]} (Slot {best_switch_idx}) - Melhor resistência")
            self._click_party_slot(best_switch_idx)
        else:
            logger.warning("Nenhuma troca favorável encontrada. Voltando para batalha.")
            self.input.press('esc')  # Fecha menu

    def _click_party_slot(self, slot_idx):
        """Clica no slot específico do menu de party com anti-tracking."""
        switch_cfg = self.cfg.get('rois', {}).get('switch_menu', {})
        container = switch_cfg.get('container')
        slot_h = int(switch_cfg.get('slot_height', 30))
        
        norm_container = normalize_roi(container)
        if norm_container:
            x1, y1, x2, _ = norm_container
            slot_y1 = y1 + slot_idx * slot_h
            slot_y2 = slot_y1 + slot_h
            
            # Pega um ponto randômico seguro dentro do slot
            cx, cy = get_safe_random_point([x1, slot_y1, x2, slot_y2], 0.2)
            
            # --- INÍCIO: CLIQUE HUMANIZADO (MELHORIA 3) ---
            if hasattr(self.input, 'humanized_click'):
                # Aplica curva de Bezier e delay Gaussiano
                self.input.humanized_click(cx, cy, delay_min=0.15, delay_max=0.35)
            else:
                self.input.click(cx, cy)
            # --- FIM DO CLIQUE HUMANIZADO ---

    def _execute_emergency_switch(self, enemy_name, img):
        """Executa troca de emergência quando estratégia retorna -1.
        
        Args:
            enemy_name: Nome do inimigo
            img: Frame atual
        """
        logger.critical("🔄 Motor de Risco recomendou TROCA OBRIGATÓRIA!")
        
        try:
            switch_idx = self.strategy.choose_switch_target(enemy_name)
        except Exception as e:
            logger.error(f"Erro ao escolher alvo de troca: {e}")
            return
        
        if switch_idx is None:
            logger.warning("⚠️ Troca recomendada mas nenhum alvo disponível")
            return
        
        logger.info(f"🔄 Executando troca de emergência para slot {switch_idx}")
        
        try:
            # Abre menu de POKEMON
            self.input.click_pokemon_button(img)
            time.sleep(0.6)
            
            # Clica no slot escolhido
            switch_cfg = self.cfg.get('rois', {}).get('switch_menu', {})
            container = switch_cfg.get('container')
            slot_h = int(switch_cfg.get('slot_height', 30))
            
            norm_container = normalize_roi(container)
            if norm_container:
                x1, y1, x2, y2 = norm_container
                slot_y1 = y1 + switch_idx * slot_h
                slot_y2 = slot_y1 + slot_h
                slot_roi = [x1, slot_y1, x2, slot_y2]
                cx, cy = get_safe_random_point(slot_roi, 0.2)
                
                self.input.click(cx, cy)
                time.sleep(self.cfg.get('battle', {}).get('action_cooldown', 2.5))
        except Exception as e:
            logger.error(f"Erro ao executar troca de emergência: {e}")
    
    def _recovery_search(self):
        """Tenta recuperar visão do alvo quando perdido (método auxiliar de FOLLOW)."""
        if self.debug:
            logger.debug("[FOLLOW] Executando busca de recuperação...")
        
        # Opção 1: Girar câmera
        if random.random() < 0.5:
            rotate_key = random.choice(['q', 'e'])
            if self.debug:
                logger.debug(f"[FOLLOW] Girando câmera ({rotate_key})...")
            self.input.press(rotate_key)
            time.sleep(0.3)
        else:
            # Opção 2: Dar pequenos passos aleatórios
            directions = ['w', 'a', 's', 'd']
            direction = random.choice(directions)
            if self.debug:
                logger.debug(f"[FOLLOW] Dando passos ({direction})...")
            for _ in range(3):
                self.input.press(direction)
                time.sleep(0.1)
        
        time.sleep(random.uniform(0.5, 1.0))
    
    def _follow_by_template_get_pos(self, img):
        """Template matching em escala de cinza para detectar personagem seguido.
        
        Returns:
            tuple: (x, y) posição do alvo ou None se não encontrado
        """
        follow_cfg = self.cfg.get('follow', {})
        player_template_name = follow_cfg.get('player_template', 'player_char.png')
        assets_dir = self.cfg.get('assets', {}).get('templates_dir', 'assets/templates/')
        player_template_path = assets_dir + player_template_name
        
        # Carrega template na primeira chamada
        if not hasattr(self, '_player_template'):
            try:
                self._player_template = cv2.imread(player_template_path)
                if self._player_template is None:
                    logger.warning(f"Template de personagem não encontrado: {player_template_path}")
                    return None
            except Exception as e:
                logger.error(f"Erro ao carregar template: {e}")
                return None
        
        if self._player_template is None:
            return None
        
        try:
            # Converte para escala de cinza para melhor precisão
            gray_img = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
            gray_template = cv2.cvtColor(self._player_template, cv2.COLOR_BGR2GRAY)
            
            res = cv2.matchTemplate(gray_img, gray_template, cv2.TM_CCOEFF_NORMED)
            _, max_val, _, max_loc = cv2.minMaxLoc(res)
            
            threshold = float(follow_cfg.get('match_threshold', 0.7))
            
            if max_val >= threshold:
                h, w = self._player_template.shape[:2]
                player_x = max_loc[0] + w // 2
                player_y = max_loc[1] + h // 2
                return (player_x, player_y)
            else:
                if self.debug:
                    logger.debug(f"[FOLLOW] Template score: {max_val:.3f} < {threshold}")
                return None
        
        except Exception as e:
            logger.error(f"Erro no template matching: {e}")
            return None