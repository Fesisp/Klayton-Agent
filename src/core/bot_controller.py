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
        
        self.running = True
        self.paused = False  # Controle de pausa via hotkey
        # Controle de Cooldown para evitar cliques repetidos
        self.last_goto_click = 0
        self.goto_cooldown = 15.0 # Espera 15 segundos antes de clicar de novo
        self.debug = bool(self.cfg.get('bot', {}).get('debug_mode', False))
        
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
        
        logger.info(f"Bot iniciado em modo: {self.behavior.name}")
        if self.behavior == BotBehavior.HUNTING:
            logger.info(f"Alvos de caça: {self.hunt_target_pokemon}")
        elif self.behavior == BotBehavior.FOLLOW:
            logger.info(f"Modo Follow ativo - Método: {self.follow_method}")

    def run(self):
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
                        # Ações idle ocasionais para parecer humano
                        self.input.perform_idle_action()
                
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

        # 1) Toca o alarme padrão do PC (beep) algumas vezes
        for _ in range(10):
            winsound.MessageBeep(winsound.MB_ICONEXCLAMATION)
            time.sleep(0.5)

        # 2) Notificação visual simples via MessageBox do Windows
        try:
            ctypes.windll.user32.MessageBoxW(
                0,
                "Um SHINY foi detectado pelo PokeBot Pro!",
                "PokeBot Pro - SHINY ENCONTRADO",
                0x00000040,  # MB_ICONINFORMATION
            )
        except Exception as e:
            logger.error(f"Falha ao exibir MessageBox de shiny: {e}")

        # Após alertar, para o bot completamente
        self.running = False

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

        # 3) Fallback: nenhum talk nem Goto, mantém leve interação
        if self.debug:
            logger.debug("Nenhum talk/goto confiável encontrado. Fallback: pressionando espaço.")
        self.input.press('space')
    
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
        # Proteção: se por algum motivo a HUD de batalha sumiu, não atacar
        if self.detector.detect_state(img) != GameState.IN_BATTLE:
            if self.debug:
                logger.debug("handle_battle chamado mas estado não é IN_BATTLE. Abortando ações de ataque.")
            return

        # Sempre garantir que o menu de batalha está focado em FIGHT primeiro
        try:
            # Tenta clicar no FIGHT. Se funcionar, espera um pouco para menu aparecer.
            # Idealmente poderia ter um loop verificando se o menu de golpes abriu.
            self.input.click_fight_button(img)
            
            fight_delay = self.cfg.get('battle', {}).get('fight_to_moves_delay', 1.2)
            
            # Pequeno loop de espera ativa (opcional) ou sleep simples
            # Por segurança, mantemos o sleep mas logamos
            if self.debug:
                logger.debug(f"Aguardando {fight_delay}s para menu de golpes abrir...")
            time.sleep(fight_delay)
            
        except Exception as e:
            logger.error(f"Erro ao clicar no FIGHT inicial: {e}")

        # Após o clique em FIGHT e o pequeno delay, captura um novo frame
        # para garantir que o menu de golpes já esteja completamente renderizado.
        img = self.cap.capture()

        # 1. Ler Inimigo
        battle_info = self.detector.get_battle_info(img)
        enemy_name = battle_info.get('enemy_name', '').strip()
        my_pokemon_name = battle_info.get('player_name', '').strip() or "MeuPokemonAtual"
        
        # Informações de HP (se disponíveis)
        player_hp = battle_info.get('player_hp_percentage')
        enemy_hp = battle_info.get('enemy_hp_percentage')

        if self.debug:
            logger.debug(f"Inimigo: '{enemy_name}' | Meu Pokémon: '{my_pokemon_name}'")
            if player_hp is not None:
                logger.debug(f"HP Player: {player_hp}% | HP Inimigo: {enemy_hp}%")
        
        # VERIFICAÇÃO ESPECIAL: Modo HUNTING
        # Se estamos caçando e o Pokémon NÃO é o alvo, fugir imediatamente
        if self.behavior == BotBehavior.HUNTING and self.hunt_target_pokemon:
            enemy_key = enemy_name.lower().strip()
            targets_lower = [t.lower().strip() for t in self.hunt_target_pokemon]
            
            if enemy_key not in targets_lower:
                logger.info(f"[HUNTING] '{enemy_name}' não é alvo de caça. Fugindo...")
                try:
                    self.input.click_run_button(img)
                    time.sleep(self.cfg.get('battle', {}).get('action_cooldown', 2.5))
                    return
                except Exception as e:
                    logger.error(f"Erro ao fugir de não-alvo: {e}")
            else:
                logger.info(f"✨ [HUNTING] ALVO ENCONTRADO: {enemy_name}! Preparando batalha...")

        # 2. Decidir se deve fugir (blacklist padrão, independente do modo)
        try:
            if self.strategy.should_flee(my_pokemon_name, enemy_name):
                logger.info(f"Decisão de FUGIR da batalha contra {enemy_name}.")
                try:
                    self.input.click_run_button(img)
                    time.sleep(self.cfg.get('battle', {}).get('action_cooldown', 2.5))
                    return
                except Exception as e_click:
                    logger.error(f"Erro ao clicar em RUN via template: {e_click}")
        except Exception as e:
            logger.error(f"Erro ao decidir fuga: {e}")
        
        # 3. Verificar se deve usar item de cura (HP crítico)
        if player_hp is not None and self.strategy.should_use_item(player_hp):
            logger.warning(f"❤️ HP crítico ({player_hp}%)! Recomendado usar item de cura.")
            # TODO: Implementar lógica de uso de item via menu BAG
            # self.input.click_bag_button(img)
            # time.sleep(0.5)
            # ... selecionar potion e usar
        
        # 4. Verificar se deve trocar Pokémon (HP baixo)
        if player_hp is not None and self.strategy.should_switch_pokemon(player_hp, enemy_name):
            logger.warning(f"🔄 HP baixo ({player_hp}%)! Recomendado trocar Pokémon.")
            # Lógica de troca já existe abaixo, mas podemos forçar aqui se necessário

        # 3. (opcional) Tentar trocar de Pokémon se houver alguém claramente vantajoso
        try:
            switch_idx = self.strategy.choose_switch_target(enemy_name)
        except Exception as e:
            logger.error(f"Erro ao decidir troca de Pokémon: {e}")
            switch_idx = None

        if switch_idx is not None:
            logger.info(f"Decisão de TROCAR para o slot {switch_idx} da equipe contra {enemy_name}.")
            try:
                # Abre menu de POKEMON pelo botão com ROI/template existente
                self.input.click_pokemon_button(img)
                time.sleep(0.6)

                # Usa menu de troca configurado em rois.switch_menu e OCR especializado
                switch_cfg = self.cfg.get('rois', {}).get('switch_menu', {})
                container = switch_cfg.get('container')
                slot_h = int(switch_cfg.get('slot_height', 30))

                if container and len(container) == 4:
                    x1, y1, x2, y2 = container
                    if x2 <= x1 or y2 <= y1:
                        x, y, w, h = container
                        x1, y1, x2, y2 = int(x), int(y), int(x + w), int(y + h)
                    h_img, w_img = img.shape[:2]
                    x1 = max(0, min(int(x1), w_img - 1))
                    x2 = max(0, min(int(x2), w_img))
                    y1 = max(0, min(int(y1), h_img - 1))
                    y2 = max(0, min(int(y2), h_img))

                    # OCR da lista inteira com método especializado
                    menu_img = img[y1:y2, x1:x2]
                container = switch_cfg.get('container')
                slot_h = int(switch_cfg.get('slot_height', 30))

                norm_container = normalize_roi(container)
                if norm_container:
                    x1, y1, x2, y2 = norm_container
                    
                    # Usa crop_roi_safe se quiser OCR (mas aqui precisamos de Coordenadas Absolutas para Click)
                    # O OCR usa a imagem recortada, o Click usa coordenadas absolutas.
                    
                    # 1. Recorta para OCR
                    menu_img = crop_roi_safe(img, container)
                    
                    # 2. OCR da lista
                    detected_names = self.ocr.ocr_party_list(menu_img)

                    # Atualiza equipe atual com o que foi lido
                    self.team_mgr.update_team_from_hud(detected_names)

                    # Clica na linha correspondente ao índice sugerido (com aleatoriedade segura)
                    idx = max(0, min(int(switch_idx), max(len(detected_names) - 1, 0)))
                    
                    slot_y1 = y1 + idx * slot_h
                    slot_y2 = slot_y1 + slot_h
                    slot_roi = [x1, slot_y1, x2, slot_y2]
                    
                    cx, cy = get_safe_random_point(slot_roi, 0.2)

                    if self.debug:
                        logger.debug(f"Clicando no slot de equipe {idx} em ({cx}, {cy}) para trocar Pokémon. Nomes detectados: {detected_names}")
                    self.input.click(cx, cy)

                    # Pequena espera para animação de troca
                    time.sleep(self.cfg.get('battle', {}).get('action_cooldown', 2.5))

                    # Depois da troca, não ataca neste tick; deixa próxima iteração decidir
                    return
                else:
                    logger.warning("ROI de menu de troca (switch_menu.container) não configurada; não foi possível trocar.")
                    debug_dir.mkdir(parents=True, exist_ok=True)
                    debug_path = debug_dir / f"{my_pokemon_name.lower()}_slot{i}.png"
                    cv2.imwrite(str(debug_path), move_img)
                except Exception as e:
                    logger.error(f"Erro ao salvar imagem de debug do slot {i}: {e}")

            # Pré-processa texto branco em fundo dinâmico (botão de golpe)
            # Usa método migrado para OCREngine
            processed = self.ocr.process_dynamic_background_text(move_img)

            # Apenas letras e espaços nos nomes de golpes
            move_text_raw = self.ocr.extract_text_optimized(
                processed,
                whitelist="ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz ",
                invert_for_white_text=False
            )
            move_text = move_text_raw.replace('\n', ' ').strip()
            move_name = self.ocr.clean_move_name(move_text)
            my_moves.append(move_name)

            if self.debug:
                logger.debug(f"Slot {i}: OCR_bruto='{move_text}' | nome_limpo='{move_name}' ROI={roi_coords}")

        # 6. Salvar o que aprendeu (nome real do Pokémon atual)
        try:
            self.team_mgr.save_moves(my_pokemon_name, my_moves)
            if self.debug:
                logger.debug(f"Golpes salvos para '{my_pokemon_name}': {my_moves}")
        except Exception as e:
            logger.error(f"Erro ao salvar movimentos: {e}")

        # 7. Decidir Ataque usando estratégia
        try:
            best_slot = self.strategy.get_best_move(my_pokemon_name, enemy_name)
        except Exception as e:
            logger.error(f"Erro na estratégia de batalha: {e}")
            best_slot = 0

        if self.debug:
            logger.debug(f"Estratégia escolheu slot {best_slot} para {my_pokemon_name} vs {enemy_name}")

        # 8. Atacar clicando no slot escolhido
        logger.info(f"Atacando slot {best_slot} contra {enemy_name} | Moves: {my_moves}")
        try:
            self.input.click_in_slot(best_slot)
        except Exception as e:
            logger.error(f"Erro ao clicar no slot de ataque: {e}")

        # Espera animação de ataque/botões reaparecerem (mais paciente)
        time.sleep(self.cfg.get('battle', {}).get('action_cooldown', 4.0))
    
    def handle_follow(self, img):
        """Modo FOLLOW: Segue o personagem principal do jogador."""
        
        # Verificar se passou tempo suficiente desde a última verificação
        current_time = time.time()
        if current_time - self.last_follow_check < self.follow_check_interval:
            return
        
        self.last_follow_check = current_time
        
        if self.follow_method == 'template':
            self._follow_by_template(img)
        elif self.follow_method == 'party_button':
            self._follow_by_party_button(img)
        else:
            logger.warning(f"Método de follow desconhecido: {self.follow_method}")
    
    def _follow_by_template(self, img):
        """Segue o personagem principal usando template matching."""
        
        # Carrega template do personagem (se configurado)
        follow_cfg = self.cfg.get('follow', {})
        player_template_name = follow_cfg.get('player_template', 'player_char.png')
        
        assets_dir = self.cfg.get('assets', {}).get('templates_dir', 'assets/templates/')
        player_template_path = assets_dir + player_template_name
        
        # Tenta carregar template
        if not hasattr(self, '_player_template'):
            try:
                self._player_template = cv2.imread(player_template_path)
                if self._player_template is None:
                    logger.warning(f"Template de personagem não encontrado: {player_template_path}")
                    logger.info("💡 Dica: Capture uma imagem do seu personagem e salve como player_char.png")
                    return
            except Exception as e:
                logger.error(f"Erro ao carregar template do personagem: {e}")
                return
        
        if self._player_template is None:
            return
        
        # Procura o personagem na tela
        try:
            res = cv2.matchTemplate(img, self._player_template, cv2.TM_CCOEFF_NORMED)
            _, max_val, _, max_loc = cv2.minMaxLoc(res)
            
            threshold = float(follow_cfg.get('match_threshold', 0.7))
            
            if max_val >= threshold:
                h, w = self._player_template.shape[:2]
                player_x = max_loc[0] + w // 2
                player_y = max_loc[1] + h // 2
                
                # Calcula centro da tela
                screen_h, screen_w = img.shape[:2]
                center_x = screen_w // 2
                center_y = screen_h // 2
                
                # Calcula distância do personagem ao centro
                distance = ((player_x - center_x) ** 2 + (player_y - center_y) ** 2) ** 0.5
                
                if distance > self.follow_distance:
                    if self.debug:
                        logger.debug(f"[FOLLOW] Personagem detectado em ({player_x}, {player_y})")
                        logger.debug(f"[FOLLOW] Distância do centro: {distance:.0f}px (limite: {self.follow_distance}px)")
                    
                    # Clica na direção do personagem
                    # Calcula ponto intermediário para movimento mais natural
                    target_x = center_x + int((player_x - center_x) * 0.7)
                    target_y = center_y + int((player_y - center_y) * 0.7)
                    
                    logger.info(f"👤 [FOLLOW] Seguindo personagem em ({target_x}, {target_y})")
                    self.input.click(target_x, target_y)
                    
                    # Pequeno delay para caminhar
                    time.sleep(random.uniform(0.5, 1.0))
                else:
                    if self.debug:
                        logger.debug(f"[FOLLOW] Personagem próximo (distância: {distance:.0f}px)")
            else:
                if self.debug:
                    logger.debug(f"[FOLLOW] Personagem não detectado (score: {max_val:.3f})")
        
        except Exception as e:
            logger.error(f"Erro ao seguir por template: {e}")
    
    def _follow_by_party_button(self, img):
        """Segue o personagem usando o botão Follow da party."""
        
        # Esta opção assume que existe um botão "Follow" visível na tela
        # quando você está em party com outra conta
        
        follow_cfg = self.cfg.get('follow', {})
        follow_button_template_name = follow_cfg.get('follow_button_template', 'follow_button.png')
        
        assets_dir = self.cfg.get('assets', {}).get('templates_dir', 'assets/templates/')
        follow_button_path = assets_dir + follow_button_template_name
        
        # Tenta carregar template do botão Follow
        if not hasattr(self, '_follow_button_template'):
            try:
                self._follow_button_template = cv2.imread(follow_button_path)
                if self._follow_button_template is None:
                    logger.warning(f"Template do botão Follow não encontrado: {follow_button_path}")
                    logger.info("💡 Dica: Capture uma imagem do botão 'Follow' e salve como follow_button.png")
                    return
            except Exception as e:
                logger.error(f"Erro ao carregar template do botão Follow: {e}")
                return
        
        if self._follow_button_template is None:
            return
        
        # Procura o botão Follow na tela
        try:
            res = cv2.matchTemplate(img, self._follow_button_template, cv2.TM_CCOEFF_NORMED)
            _, max_val, _, max_loc = cv2.minMaxLoc(res)
            
            threshold = float(follow_cfg.get('button_threshold', 0.75))
            
            if max_val >= threshold:
                h, w = self._follow_button_template.shape[:2]
                button_x = max_loc[0] + w // 2
                button_y = max_loc[1] + h // 2
                
                logger.info(f"👤 [FOLLOW] Clicando no botão Follow em ({button_x}, {button_y})")
                self.input.click(button_x, button_y)
                
                # Delay após clicar no botão
                time.sleep(random.uniform(0.3, 0.7))
            else:
                if self.debug:
                    logger.debug(f"[FOLLOW] Botão Follow não detectado (score: {max_val:.3f})")
        
        except Exception as e:
            logger.error(f"Erro ao seguir por botão: {e}")