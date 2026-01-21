import time
from loguru import logger

class BattleController:
    def __init__(self, input_sim, detector, strategy, team_manager, config):
        self.input = input_sim
        self.detector = detector
        self.strategy = strategy
        self.tm = team_manager
        self.rois = config.get('rois', {})
        
        # Estado interno da batalha
        self.current_enemy = None
        self.turn_count = 0
        self.last_action_time = 0
        self.action_cooldown = config.get('battle', {}).get('action_cooldown', 1.5)

    def reset_battle_state(self):
        """Reseta variáveis quando uma nova batalha começa."""
        self.current_enemy = None
        self.turn_count = 0
        logger.info("Estado de batalha resetado.")

    def execute_turn(self, image):
        """
        Executa um turno completo de batalha:
        1. Identifica contexto (Inimigo, HP).
        2. Atualiza memória de golpes.
        3. Consulta estratégia.
        4. Executa ação (Atacar, Trocar ou Fugir).
        """
        # Verifica cooldown para não spammar cliques
        if time.time() - self.last_action_time < self.action_cooldown:
            return

        logger.info("--- Iniciando Turno ---")

        # 1. Identificar Inimigo (com Cache simples)
        enemy_name = self._get_enemy_name(image)
        if not enemy_name:
            logger.warning("Não foi possível ler o nome do inimigo. Pulando turno.")
            return

        # 2. Identificar Meu Pokémon Ativo e Golpes (e salvar na memória)
        my_pokemon_name = self._get_my_pokemon_name(image)
        self._update_known_moves(image, my_pokemon_name)

        # 3. Verificar Decisão de FUGA
        if self.strategy.should_flee(my_pokemon_name, enemy_name):
            self._perform_run()
            return

        # 4. Verificar Decisão de TROCA
        switch_target_idx = self.strategy.choose_switch_target(enemy_name)
        if switch_target_idx is not None:
            self._perform_switch(switch_target_idx)
            return

        # 5. Decisão de ATAQUE (Padrão)
        best_slot_index = self.strategy.get_best_move(my_pokemon_name, enemy_name)
        self._perform_attack(best_slot_index)

    # ---------------------------------------------------------
    # Métodos de Percepção (Auxiliares)
    # ---------------------------------------------------------
    def _get_enemy_name(self, image):
        # Se já lemos o nome e a tela não mudou drasticamente, retorna o cache
        # (Para simplificar, lemos sempre por enquanto, mas idealmente checaria se mudou)
        enemy_img = self.detector.proc.extract_roi(image, self.rois['enemy_name'])
        enemy_proc = self.detector.proc.process_dynamic_background_text(enemy_img)
        text = self.detector.ocr.read_text(enemy_proc, mode="line")
        
        clean_name = text.split()[0] if text else ""
        # Remove símbolos de gênero se o OCR pegar (ex: "Pikachu♂" -> "Pikachu")
        clean_name = clean_name.replace('♂', '').replace('♀', '')
        
        if clean_name and clean_name != self.current_enemy:
            self.current_enemy = clean_name
            logger.info(f"Novo inimigo detectado: {self.current_enemy}")
            
        return self.current_enemy

    def _get_my_pokemon_name(self, image):
        # Tenta ler o nome do jogador. Se falhar, usa o primeiro do time como fallback
        name_img = self.detector.proc.extract_roi(image, self.rois['player_name'])
        name_proc = self.detector.proc.process_dynamic_background_text(name_img)
        text = self.detector.ocr.read_text(name_proc, mode="line")
        
        clean_name = text.split()[0] if text else ""
        
        if not clean_name and self.tm.current_team:
            # Fallback: assume que é o primeiro da lista
            return self.tm.current_team[0]
        
        return clean_name

    def _update_known_moves(self, image, pokemon_name):
        """Lê os botões de ataque e salva no TeamManager."""
        if not pokemon_name: return

        current_moves = []
        for i in range(1, 5):
            slot_key = f'slot_{i}'
            roi = self.rois['moves'].get(slot_key)
            if not roi: continue

            move_img = self.detector.proc.extract_roi(image, roi)
            # Usa processamento específico para texto branco em fundo colorido
            move_proc = self.detector.proc.process_dynamic_background_text(move_img)
            
            raw_text = self.detector.ocr.read_text(move_proc, mode="block")
            clean_move = self.detector.ocr.clean_move_name(raw_text)
            current_moves.append(clean_move)

        # Atualiza a memória persistente
        # Só atualiza se encontrou algo válido (evita limpar golpes se o OCR falhar)
        if any(current_moves):
            self.tm.save_moves(pokemon_name, current_moves)

    # ---------------------------------------------------------
    # Métodos de Ação (Cliques)
    # ---------------------------------------------------------
    def _perform_attack(self, slot_index):
        """Clica no botão de ataque correspondente."""
        # Se necessário, clica em FIGHT primeiro (depende da UI do jogo)
        # self._ensure_fight_menu_open() 
        
        slot_key = f'slot_{slot_index + 1}'
        roi = self.rois['moves'][slot_key]
        
        # Clica no centro do botão
        cx = (roi[0] + roi[2]) // 2
        cy = (roi[1] + roi[3]) // 2
        
        logger.info(f"Usando Ataque Slot {slot_index + 1}")
        self.input.click(cx, cy)
        self.last_action_time = time.time()
        self.turn_count += 1

    def _perform_run(self):
        """Clica no botão de fugir."""
        roi = self.rois['btn_run']
        cx = (roi[0] + roi[2]) // 2
        cy = (roi[1] + roi[3]) // 2
        
        logger.info("Tentando FUGIR...")
        self.input.click(cx, cy)
        self.last_action_time = time.time()

    def _perform_switch(self, target_index):
        """
        Sequência complexa para trocar de Pokémon:
        1. Clica botão 'Pokémon'.
        2. Clica no slot do Pokémon desejado.
        3. Confirma (se houver botão de 'Shift').
        """
        logger.info(f"Iniciando troca para o Pokémon no índice {target_index}...")
        
        # 1. Clicar no botão de menu Pokémon
        btn_pkmn = self.rois['btn_pokemon']
        self.input.click((btn_pkmn[0]+btn_pkmn[2])//2, (btn_pkmn[1]+btn_pkmn[3])//2)
        time.sleep(1.0) # Espera menu abrir

        # 2. Calcular posição do Pokémon na lista
        # Assume que 'switch_menu' está configurado no settings.yaml
        menu_cfg = self.rois.get('switch_menu', {})
        container = menu_cfg.get('container')
        slot_height = menu_cfg.get('slot_height', 30)

        if container:
            # O índice 0 é o atual, o índice 1 é o próximo, etc.
            # Nota: target_index vem do TeamManager. Se o atual é 0, target é relativo à lista completa.
            
            x_base, y_base, _, _ = container
            # Clica no pokemon alvo
            target_y = y_base + (target_index * slot_height) + (slot_height // 2)
            target_x = x_base + 50 # Um pouco para dentro da esquerda

            self.input.click(target_x, target_y)
            time.sleep(0.5)
            
            # Aqui pode ser necessário um clique extra em "Shift/Switch" se abrir um submenu
            # Por enquanto, assumimos clique direto ou duplo clique
            # self.input.click(target_x, target_y) 
            
        self.last_action_time = time.time() + 2.0 # Cooldown maior para troca