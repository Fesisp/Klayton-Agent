from loguru import logger


class BattleStrategy:
    def __init__(self, db, team_manager, config=None):
        self.db = db
        self.tm = team_manager
        self.config = config or {}

        # Carrega estratégia do config.yaml ou usa defaults
        strategy_cfg = self.config.get('strategy', {})
        self.whitelist = set(strategy_cfg.get('whitelist', ["chansey", "blissey"]))
        self.blacklist = set(strategy_cfg.get('blacklist', ["magikarp", "caterpie"]))

        healing_moves_default = [
            "recover", "roost", "synthesis", "moonlight", "morning sun",
            "softboiled", "milk drink", "slack off", "rest", "wish"
        ]
        self.healing_move_names = {
            m.lower() for m in strategy_cfg.get('healing_move_names', healing_moves_default)
        }
        self.healing_category_ids = {
            str(x) for x in strategy_cfg.get('healing_category_ids', [])
        }

        # Força minúsculo para comparação
        self.whitelist = {x.lower() for x in self.whitelist}
        self.blacklist = {x.lower() for x in self.blacklist}
        
        # Tracking de turnos para inferência de itens
        self.current_enemy_level = 50  # Default, atualizado via set_enemy_level()
        self.enemy_outspeeded_me_last_turn = False  # Tracking de velocidade
        self.enemy_item_inference = None  # "Choice Scarf", "Choice Band", "Life Orb", etc
        self.expected_damage_last_turn = 0  # Dano esperado do último turno
        self.actual_damage_last_turn = 0  # Dano real recebido
        self.last_turn_outspeeded = False  # Flag para inferência de velocidade
        self.my_speed_stat = 0  # Velocidade calculada do meu Pokémon
        self.enemy_max_possible_speed = 0  # Velocidade máxima possível do inimigo
        
        # Detecção de HP do detector (será injetado externamente)
        self.detector = None
        
        # Turn Counter (movido de BattleController)
        self.turn_count = 0
        self.current_enemy = None
        self.last_action_time = 0

    # ---------------------------------------------------------
    # Cálculos de Speed Tier
    # ---------------------------------------------------------
    def calculate_speed(self, base_speed, level, iv=31, ev=252, nature=1.1):
        """Cálculo real da fórmula de velocidade de Pokémon.
        
        Args:
            base_speed: Velocidade base do Pokémon
            level: Nível do Pokémon
            iv: Individual Value (0-31, padrão 31)
            ev: Effort Value (0-252, padrão 252)
            nature: Multiplicador de nature (1.1 para +, 0.9 para -, 1.0 neutro)
            
        Returns:
            int: Velocidade calculada
        """
        return int(((base_speed * 2 + iv + (ev // 4)) * level / 100 + 5) * nature)
    
    # ---------------------------------------------------------
    # Cálculo de Efetividade de Tipo com Imunidades por Habilidade
    # ---------------------------------------------------------
    def calculate_type_effectiveness(self, move_type: str, target_pokemon: str) -> float:
        """
        Calcula efetividade de tipo considerando IMUNIDADES POR HABILIDADE.
        
        Algumas abilities garantem imunidade a certos tipos:
        - Levitate: Imune a Ground
        - Water Absorb: Absorve Water (0.0x damage)
        - Volt Absorb: Absorve Electric (0.0x damage)
        - Flash Fire: Absorve Fire (0.0x damage)
        - Filter/Solid Rock: Reduz super-efetivos para 1.5x
        - Dry Skin: Water causa dano regenerativo
        
        Args:
            move_type: Tipo do golpe (ex: "Fire", "Water", "Electric")
            target_pokemon: Nome do Pokémon alvo
            
        Returns:
            float: Multiplicador de efetividade (0.0, 0.5, 1.0, 1.5, 2.0, 4.0)
        """
        target_data = self.db.get_pokemon_data(target_pokemon)
        if not target_data:
            return 1.0
        
        abilities = target_data.get('abilities', [])
        move_type_normalized = move_type.capitalize() if move_type else ""
        
        # ========== IMUNIDADES ABSOLUTAS (0.0x) ==========
        if "Levitate" in abilities and move_type_normalized == "Ground":
            logger.info(f"🛡️  {target_pokemon} com Levitate é imune a Ground")
            return 0.0
        
        if "Water Absorb" in abilities and move_type_normalized == "Water":
            logger.info(f"💧 {target_pokemon} com Water Absorb absorve Water")
            return 0.0
        
        if "Volt Absorb" in abilities and move_type_normalized == "Electric":
            logger.info(f"⚡ {target_pokemon} com Volt Absorb absorve Electric")
            return 0.0
        
        if "Flash Fire" in abilities and move_type_normalized == "Fire":
            logger.info(f"🔥 {target_pokemon} com Flash Fire absorve Fire")
            return 0.0
        
        if "Dry Skin" in abilities and move_type_normalized == "Water":
            logger.info(f"💦 {target_pokemon} com Dry Skin recebe dano reduzido de Water")
            return 0.5
        
        if "Motor Drive" in abilities and move_type_normalized == "Electric":
            logger.info(f"⚡ {target_pokemon} com Motor Drive é imune a Electric")
            return 0.0
        
        if "Storm Drain" in abilities and move_type_normalized == "Water":
            logger.info(f"💧 {target_pokemon} com Storm Drain absorve Water")
            return 0.0
        
        # ========== REDUÇÃO DE SUPER-EFETIVOS (1.5x ao invés de 2.0x) ==========
        if "Filter" in abilities or "Solid Rock" in abilities:
            base_effectiveness = self._get_base_type_effectiveness(move_type_normalized, target_pokemon)
            if base_effectiveness >= 2.0:
                logger.info(f"🛡️  {target_pokemon} com Filter/Solid Rock reduz super-efetivo (2.0x → 1.5x)")
                return 1.5
        
        # ========== EFETIVIDADE PADRÃO DE TIPO ==========
        return self._get_base_type_effectiveness(move_type_normalized, target_pokemon)
    
    def _get_base_type_effectiveness(self, move_type: str, target_pokemon: str) -> float:
        """
        Lógica base de efetividade de tipo (0.5x, 1.0x, 2.0x).
        Usa o tipo_chart.json se disponível, caso contrário retorna 1.0.
        
        Args:
            move_type: Tipo do golpe normalizado
            target_pokemon: Nome do Pokémon alvo
            
        Returns:
            float: Multiplicador base sem considerar habilidades
        """
        target_types = self.db.get_pokemon_types(target_pokemon)
        if not target_types:
            return 1.0
        
        # Tenta usar tipo_chart.json se carregado
        if hasattr(self, 'type_chart'):
            effectiveness = self.type_chart.get(move_type, {}).get(target_types[0], 1.0)
            # Se o Pokémon tem dois tipos, aplica o multiplicador mais favorável
            if len(target_types) > 1:
                eff2 = self.type_chart.get(move_type, {}).get(target_types[1], 1.0)
                effectiveness *= eff2
            return effectiveness
        
        # Fallback: retorna 1.0 (neutra)
        logger.debug(f"Type chart não carregado - retornando efetividade 1.0x para {move_type}")
        return 1.0
    
    def calculate_real_damage(self, enemy_name, enemy_level, my_poke):
        """Calcula o dano MÁXIMO possível considerando Worst-Case Scenario.
        
        FILOSOFIA: Nunca subestimar o inimigo. Assume IVs/EVs máximos, itens ofensivos
        e aplica corretamente os modificadores de status (Burn, Sleep, Paralysis).
        
        MODIFICADORES:
        - Burn: Corta Ataque Físico em 50% ANTES do cálculo
        - Choice Band/Specs: 1.5x no dano
        - Life Orb: 1.3x no dano
        - Paralysis: Velocidade reduzida a 50% (tratado em get_effective_speed)
        - Sleep/Freeze: Inimigo não ataca (retorna 0)
        
        Args:
            enemy_name: Nome do Pokémon inimigo
            enemy_level: Nível do inimigo
            my_poke: Nome do meu Pokémon
            
        Returns:
            float: Dano máximo absoluto em HP
        """
        # 1. VERIFICAÇÃO DE STATUS INCAPACITANTE
        enemy_status = self.tm.get_status(enemy_name)
        if enemy_status in ["SLEEP", "FREEZE"]:
            logger.info(f"💤 {enemy_name} está {enemy_status} - Não atacará")
            return 0.0
        
        # 2. WORST-CASE: Stats máximos do inimigo (IVs/EVs perfeitos)
        enemy_stats = self.db.estimate_max_stats(enemy_name, enemy_level)
        
        # 3. Stats do meu Pokémon (defesas)
        my_stats = self.tm.get_stats(my_poke)
        if not my_stats:
            logger.warning(f"Stats de {my_poke} não encontrados")
            return 0.0
        
        # 4. MODIFICADOR DE BURN (aplicado ANTES do cálculo)
        atk_mod = 0.5 if enemy_status == "BURN" else 1.0
        if enemy_status == "BURN":
            logger.info(f"🔥 {enemy_name} queimado - Ataque físico reduzido 50%")
        
        # 5. INFERÊNCIA DE ITENS
        item = self.tm.get_inferred_item(enemy_name)
        item_mod = 1.0
        if item == "CHOICE":
            item_mod = 1.5
            logger.info(f"⚔️ {enemy_name} aparenta ter Choice Band/Specs (1.5x dano)")
        elif item == "LIFE_ORB":
            item_mod = 1.3
            logger.info(f"💎 {enemy_name} aparenta ter Life Orb (1.3x dano)")
        
        # 6. ANÁLISE DE GOLPES PROVÁVEIS
        max_damage = 0.0
        best_move = ""
        possible_moves = self.db.get_common_moves(enemy_name)
        
        for move_name in possible_moves:
            move_data = self.db.get_move_data(move_name)
            if not move_data:
                continue
            
            power = float(move_data.get('power', 0) or 0)
            if power == 0:
                continue  # Ignora golpes de status
            
            category = str(move_data.get('category_id', ''))
            move_type = str(move_data.get('type_id', ''))
            
            # Seleciona stats corretos (físico vs especial)
            if category == '1':  # Físico
                atk = enemy_stats['attack'] * atk_mod  # Burn aplicado aqui!
                defense = my_stats.get('defense', 100)
            elif category == '2':  # Especial
                atk = enemy_stats['special_attack']  # Burn não afeta especial
                defense = my_stats.get('special_defense', 100)
            else:
                continue
            
            # STAB (Same Type Attack Bonus)
            enemy_types = self.db.get_pokemon_types(enemy_name)
            stab = 1.5 if move_type in [str(t) for t in enemy_types] else 1.0
            
            # Type Effectiveness
            my_types = self.db.get_pokemon_types(my_poke)
            type_mult = self.db.get_type_multiplier(move_type, my_types)
            
            # FÓRMULA OFICIAL DE DANO (Game Freak)
            damage = (((2 * enemy_level / 5 + 2) * power * atk / defense) / 50 + 2)
            final_damage = damage * stab * type_mult * item_mod
            
            if final_damage > max_damage:
                max_damage = final_damage
                best_move = move_name
        
        if max_damage > 0:
            logger.info(f"⚠️ Pior cenário: {enemy_name} pode causar {max_damage:.1f} HP com {best_move}")
        
        return max_damage
    
    def calculate_effective_hp_post_turn(self, my_poke, enemy_dmg_ratio):
        """Calcula se o Pokémon sobrevive ao golpe + dano residual de status.
        
        FILOSOFIA: Morte Inesperada NUNCA mais acontece.
        O bot considera Burn/Toxic/Poison como dano GARANTIDO no fim do turno.
        Se HP efetivo pós-turno <= 0, é matematicamente impossível sobreviver.
        
        FÓRMULA:
        HP_efetivo = HP_atual - Dano_do_golpe - Dano_residual
        
        DANO RESIDUAL:
        - BURN: 1/16 (6.25%) do HP máximo por turno
        - POISON: 1/8 (12.5%) do HP máximo por turno
        - TOXIC: (N/16) onde N = turnos em campo (progressivo)
        
        Args:
            my_poke: Nome do meu Pokémon
            enemy_dmg_ratio: Dano do golpe inimigo em % (0.0 a 1.0)
            
        Returns:
            bool: True se sobrevive, False se morte é inevitável
        """
        if not self.detector:
            logger.warning("Detector não configurado - assumindo sobrevivência")
            return True
        
        # HP atual do meu Pokémon
        my_hp_ratio = self.detector.get_hp_ratio(self.detector.last_frame, 'player') if self.detector.last_frame is not None else None
        if my_hp_ratio is None:
            my_hp_ratio = 1.0  # Fallback: assume HP cheio
        
        status = self.tm.get_status(my_poke)
        residual_dmg_ratio = 0.0
        
        # Calcula dano residual baseado no status
        if status == "BURN" or status == "POISON":
            residual_dmg_ratio = 1.0 / 16.0  # 6.25% para Burn
            if status == "POISON":
                residual_dmg_ratio = 1.0 / 8.0  # 12.5% para Poison regular
            logger.debug(f"🔥 Dano residual de {status}: {residual_dmg_ratio*100:.1f}%")
        
        elif status == "TOXIC":
            # Dano progressivo: N/16 onde N = turnos
            turns_toxic = 8 - self.tm.get_survival_turns(my_poke)  # Turnos decorridos
            residual_dmg_ratio = turns_toxic / 16.0
            logger.debug(f"☠️ Dano residual de TOXIC (turno {turns_toxic}): {residual_dmg_ratio*100:.1f}%")
        
        # HP efetivo após golpe + status
        effective_hp = my_hp_ratio - enemy_dmg_ratio - residual_dmg_ratio
        
        if effective_hp <= 0:
            logger.critical(f"💀 MORTE INEVITÁVEL: HP atual {my_hp_ratio*100:.0f}% - Dano {enemy_dmg_ratio*100:.0f}% - Status {residual_dmg_ratio*100:.0f}% = {effective_hp*100:.0f}%")
            return False
        
        logger.info(f"✅ Sobrevivência confirmada: HP efetivo pós-turno = {effective_hp*100:.0f}%")
        return True
    
    def evaluate_danger_table(self, my_poke, enemy_poke, my_current_hp_ratio=1.0):
        """Tabela de Perigo: Decisões inteligentes baseadas em Status + Priority.
        
        LÓGICA DE DECISÃO:
        1. SLEEP: Se em Sleep e vulnerável (dano > 30% HP), TROCAR imediatamente
           + PREVENÇÃO DE SETUP BAIT: Se inimigo está se buffando, trocar!
        2. BURN: Se sou físico e queimado, considerar troca ou golpe especial/status
        3. PARALYSIS: Recalcular velocidade (50%) e verificar se perco speed tier
        4. PRIORITY THREAT: Mesmo sendo mais rápido, se Quick Attack me mata, TROCAR
        5. TOXIC: Se sobrevivência < 3 turnos, TROCAR antes de morrer
        
        Args:
            my_poke: Nome do meu Pokémon
            enemy_poke: Nome do Pokémon inimigo
            my_current_hp_ratio: HP atual em % (0.0 a 1.0)
            
        Returns:
            str: "SWITCH_IMMEDIATE" (perigo crítico)
                 "SWITCH_ADVISED" (recomendado trocar)
                 "ATTACK" (seguro atacar)
                 "HEAL" (curar é erro matemático)
        """
        my_status = self.tm.get_status(my_poke)
        my_max_hp = self.tm.get_max_hp(my_poke)
        my_current_hp = my_max_hp * my_current_hp_ratio
        
        # 1. SLEEP: Vulnerabilidade crítica + PREVENÇÃO DE SETUP BAIT
        if my_status == "SLEEP":
            damage = self.calculate_real_damage(enemy_poke, self.current_enemy_level, my_poke)
            damage_ratio = damage / my_max_hp if my_max_hp > 0 else 0
            
            # CRÍTICO: Detecta se inimigo está se BUFFANDO (usando você como escada)
            if self.detector and hasattr(self.detector, 'detect_enemy_action_category'):
                enemy_action = self.detector.detect_enemy_action_category()
                if enemy_action == "STATUS_BUFF":
                    logger.critical("🚨 INIMIGO SE BUFFANDO DURANTE SEU SONO! Forçando troca para interromper Setup.")
                    return "SWITCH_IMMEDIATE"
            
            if damage_ratio > 0.3:  # Mais de 30% do HP
                logger.warning(f"😴 SLEEP + dano alto ({damage_ratio*100:.0f}%) = TROCAR AGORA")
                return "SWITCH_IMMEDIATE"
        
        # 2. BURN: Verificar se sou atacante físico
        if my_status == "BURN":
            my_moves = self.tm.get_moves(my_poke)
            physical_moves = 0
            total_attacking_moves = 0
            
            for move in my_moves:
                move_data = self.db.get_move_data(move)
                if move_data and move_data.get('power', 0) > 0:
                    total_attacking_moves += 1
                    if str(move_data.get('category_id', '')) == '1':  # Físico
                        physical_moves += 1
            
            if total_attacking_moves > 0:
                physical_ratio = physical_moves / total_attacking_moves
                if physical_ratio > 0.6:  # Mais de 60% físico
                    logger.warning(f"🔥 Queimado e {physical_ratio*100:.0f}% físico = TROCAR RECOMENDADO")
                    return "SWITCH_ADVISED"
        
        # 3. PARALYSIS: Recalcular speed tier
        if my_status == "PARALYSIS":
            my_speed = self.get_effective_speed(my_poke, is_player=True)
            enemy_speed = self.get_effective_speed(enemy_poke, is_player=False)
            
            if enemy_speed > my_speed:
                logger.info(f"⚡ Paralisia fez eu perder Speed Tier ({my_speed} vs {enemy_speed})")
                # Verifica se isso me torna vulnerável a OHKO
                damage = self.calculate_real_damage(enemy_poke, self.current_enemy_level, my_poke)
                if damage >= my_current_hp:
                    logger.warning(f"⚡ Perdi velocidade + OHKO risk = TROCAR")
                    return "SWITCH_IMMEDIATE"
        
        # 4. PRIORITY THREAT (CRÍTICO: mesmo sendo mais rápido!)
        priority_moves = self.db.get_priority_moves(enemy_poke)
        if priority_moves:
            for move_name in priority_moves:
                move_data = self.db.get_move_data(move_name)
                if not move_data or not move_data.get('power', 0):
                    continue
                
                # Calcula dano do priority move
                enemy_stats = self.db.estimate_max_stats(enemy_poke, self.current_enemy_level)
                my_stats = self.tm.get_stats(my_poke)
                
                category = str(move_data.get('category_id', ''))
                if category == '1':  # Físico
                    atk = enemy_stats['attack']
                    defense = my_stats.get('defense', 100)
                elif category == '2':  # Especial
                    atk = enemy_stats['special_attack']
                    defense = my_stats.get('special_defense', 100)
                else:
                    continue
                
                power = move_data.get('power', 0)
                damage = (((2 * self.current_enemy_level / 5 + 2) * power * atk / defense) / 50 + 2)
                
                if damage >= my_current_hp:
                    logger.warning(f"🎯 {enemy_poke} tem {move_name} (priority) que me mata = TROCAR")
                    return "SWITCH_IMMEDIATE"
        
        # 5. TOXIC: Contador de sobrevivência
        if my_status == "TOXIC":
            turns_left = self.tm.get_survival_turns(my_poke)
            if turns_left < 3:
                logger.warning(f"☠️ Toxic - apenas {turns_left} turnos restantes = TROCAR")
                return "SWITCH_ADVISED"
        
        # 6. CURAR É ERRO MATEMÁTICO?
        # Se o dano do inimigo é menor que 25% do meu HP, curar é desperdício
        damage = self.calculate_real_damage(enemy_poke, self.current_enemy_level, my_poke)
        damage_ratio = damage / my_max_hp if my_max_hp > 0 else 0
        
        if damage_ratio < 0.25 and my_current_hp_ratio > 0.5:
            return "HEAL"  # Flag para NÃO curar (inimigo muito fraco)
        
        return "ATTACK"
    
    def judge_speed_tier(self, my_poke, enemy_name):
        """Julga se o bot é mais rápido que o inimigo.
        
        Considera o pior cenário: Inimigo com IV 31, EV 252 e Nature +10%.
        Também infere se inimigo tem Choice Scarf baseado em turnos anteriores.
        
        Args:
            my_poke: Nome do Pokémon do jogador
            enemy_name: Nome do Pokémon inimigo
            
        Returns:
            bool: True se o jogador é mais rápido, False caso contrário
        """
        # Obter velocidade do jogador
        my_stats = self.tm.get_stats(my_poke)
        if not my_stats or 'speed' not in my_stats:
            logger.warning(f"Stats de velocidade não encontrados para {my_poke}")
            return False  # Assume pior caso
        
        my_speed = my_stats['speed']
        self.my_speed_stat = my_speed  # Armazena para inferência
        
        # Obter velocidade base do inimigo
        enemy_stats = self.db.get_base_stats(enemy_name)
        if not enemy_stats or 'speed' not in enemy_stats:
            logger.warning(f"Stats base não encontrados para {enemy_name}")
            return False  # Assume pior caso
        
        enemy_base_speed = enemy_stats['speed']
        
        # Calcula velocidade máxima possível do inimigo (pior caso)
        enemy_max_speed = self.calculate_speed(
            enemy_base_speed, 
            self.current_enemy_level,
            iv=31, 
            ev=252, 
            nature=1.1
        )
        self.enemy_max_possible_speed = enemy_max_speed  # Armazena para inferência
        
        # Inferência de Item: Se fomos ultrapassados no último turno
        # mas nossa velocidade é maior que a máxima dele, ele deve ter Choice Scarf
        if self.last_turn_outspeeded and self.my_speed_stat > self.enemy_max_possible_speed:
            self.enemy_item_inference = "Choice Scarf"
            enemy_max_speed = int(enemy_max_speed * 1.5)
            logger.warning(
                f"⚠️ INFERÊNCIA AUTOMÁTICA: {enemy_name} detectado com Choice Scarf ou similar! "
                f"(Minha speed={self.my_speed_stat} > Max dele sem item={self.enemy_max_possible_speed})"
            )
        elif self.enemy_outspeeded_me_last_turn:
            if my_speed > enemy_max_speed:
                self.enemy_item_inference = "Choice Scarf"
                enemy_max_speed = int(enemy_max_speed * 1.5)  # Choice Scarf = 1.5x speed
                logger.warning(
                    f"⚠️ INFERÊNCIA: {enemy_name} provavelmente tem Choice Scarf! "
                    f"(Speed ajustado: {enemy_max_speed})"
                )
        
        is_faster = my_speed > enemy_max_speed
        
        logger.info(
            f"Speed Tier: {my_poke}({my_speed}) vs {enemy_name}({enemy_max_speed}) = "
            f"{'FASTER ⚡' if is_faster else 'SLOWER 🐌'}"
        )
        
        return is_faster
    
    def set_enemy_level(self, level):
        """Atualiza o nível do inimigo para cálculos de speed tier."""
        self.current_enemy_level = level
    
    def calculate_incoming_damage(self, enemy_poke, my_poke):
        """Calcula dano máximo que o inimigo pode causar no próximo turno.
        
        Usa fórmula OFICIAL DA GAME FREAK considerando:
        - Stats (Attack, Sp.Attack, Defense, Sp.Defense)
        - STAB (Same Type Attack Bonus)
        - Type Effectiveness
        - Status (Burn reduz ataque físico em 50%)
        - Itens inferidos (Choice Band/Specs, Life Orb)
        - Multiplicadores dinâmicos de campo
        
        Args:
            enemy_poke: Nome do Pokémon inimigo
            my_poke: Nome do Pokémon do jogador
            
        Returns:
            float: Razão de dano esperado (0.0 a 1.0+)
        """
        # Obter stats
        my_stats = self.tm.get_stats(my_poke)
        enemy_base_stats = self.db.get_base_stats(enemy_poke)
        
        if not my_stats or not enemy_base_stats:
            return 0.3  # Fallback para estimativa antiga
        
        # Estimar stats do inimigo (PIOR CENÁRIO: IV 31, EV 252, +Nature)
        enemy_level = self.current_enemy_level
        enemy_atk = self.db.estimate_stat(enemy_base_stats['attack'], enemy_level, iv=31, ev=252, nature=1.1)
        enemy_spa = self.db.estimate_stat(enemy_base_stats['special_attack'], enemy_level, iv=31, ev=252, nature=1.1)
        
        # --- APLICAÇÃO DE STATUS NO INIMIGO ---
        enemy_status = self.tm.get_status(enemy_poke)
        if enemy_status == "BURN":
            # Burn reduz dano físico em 50% (aplicado ANTES do cálculo)
            enemy_atk *= 0.5
            if self.debug:
                logger.debug(f"🔥 {enemy_poke} está queimado: Atk {enemy_atk*2:.0f} → {enemy_atk:.0f}")
        
        max_damage_ratio = 0.0
        best_move_name = ""
        
        # Analisa golpes prováveis do inimigo
        possible_moves = self.db.get_common_moves(enemy_poke)
        
        for move_name in possible_moves:
            move_data = self.db.get_move_data(move_name)
            if not move_data:
                continue
            
            power = float(move_data.get('power', 0) or 0)
            if power == 0:
                continue  # Ignora movimentos de status
            
            # Determina categoria (físico vs especial)
            category_id = str(move_data.get('category_id', '1'))
            is_special = category_id == '2'
            category_name = 'special' if is_special else 'physical'
            
            # Seleção de Stats Ofensivos/Defensivos
            atk_stat = enemy_spa if is_special else enemy_atk
            def_stat = my_stats['special_defense'] if is_special else my_stats['defense']
            
            # --- FÓRMULA OFICIAL DA GAME FREAK ---
            # Damage = (((2 * Level / 5 + 2) * Power * Atk / Def) / 50 + 2)
            damage = (((2 * enemy_level / 5 + 2) * power * atk_stat / def_stat) / 50 + 2)
            
            # --- MULTIPLICADORES DE CAMPO E TIPO ---
            enemy_types = self.db.get_pokemon_types(enemy_poke)
            my_types = self.db.get_pokemon_types(my_poke)
            move_type = move_data.get('type_id')
            
            # STAB (Same Type Attack Bonus)
            stab = 1.5 if move_type in enemy_types else 1.0
            
            # Type Effectiveness
            type_mult = self.db.get_type_multiplier(move_type, my_types)
            
            # --- INFERÊNCIA DE ITENS (MULTIPLICADORES DINÂMICOS) ---
            item_mult = 1.0
            inferred_item = self.tm.get_inferred_item(enemy_poke)
            
            if inferred_item == "CHOICE_SPECS" and is_special:
                item_mult = 1.5
            elif inferred_item == "CHOICE_BAND" and not is_special:
                item_mult = 1.5
            elif inferred_item == "LIFE_ORB":
                item_mult = 1.3
            
            # Dano final
            final_damage = damage * stab * type_mult * item_mult
            
            # Converte para razão do HP máximo
            max_hp = my_stats.get('hp', 100)
            damage_ratio = final_damage / max_hp
            
            if damage_ratio > max_damage_ratio:
                max_damage_ratio = damage_ratio
                best_move_name = move_name
                if self.debug:
                    logger.debug(
                        f"💥 {move_name} ({category_name}): {final_damage:.1f} dmg ({damage_ratio*100:.1f}% HP) "
                        f"[Pwr={power}, STAB={stab}, Type={type_mult}, Item={item_mult}]"
                    )
        
        # Clamp entre 0.1 e 2.0 (2.0 = OHKO)
        max_damage_ratio = max(0.1, min(2.0, max_damage_ratio))
        
        logger.info(
            f"💥 Dano máximo de {enemy_poke}: {max_damage_ratio*100:.1f}% HP "
            f"(Melhor golpe: {best_move_name or 'N/A'})"
        )
        
        return max_damage_ratio
    
    def calculate_perfect_damage(self, enemy_name, enemy_level, my_poke):
        """Calcula o dano PERFEITO considerando Burn, Itens e Status.
        
        Versão aprimorada que integra:
        - Burn reduzindo ataque físico em 50%
        - Inferência de itens (Choice Band/Specs, Life Orb)
        - STAB e type effectiveness
        - Seleção correta de stats ofensivos/defensivos
        
        Args:
            enemy_name: Nome do Pokémon inimigo
            enemy_level: Nível do inimigo
            my_poke: Nome do meu Pokémon
            
        Returns:
            float: Dano máximo em HP absoluto
        """
        # Obter stats estimados do inimigo (pior cenário)
        enemy_base_stats = self.db.get_base_stats(enemy_name)
        if not enemy_base_stats:
            logger.warning(f"Stats de {enemy_name} não encontrados")
            return 0.0
        
        enemy_stats = {
            'attack': self.db.estimate_stat(enemy_base_stats['attack'], enemy_level, iv=31, ev=252, nature=1.1),
            'sp_attack': self.db.estimate_stat(enemy_base_stats['special_attack'], enemy_level, iv=31, ev=252, nature=1.1),
            'defense': self.db.estimate_stat(enemy_base_stats['defense'], enemy_level, iv=31, ev=252, nature=1.1),
            'sp_defense': self.db.estimate_stat(enemy_base_stats['special_defense'], enemy_level, iv=31, ev=252, nature=1.1),
        }
        
        my_stats = self.tm.get_stats(my_poke)
        if not my_stats:
            logger.warning(f"Stats de {my_poke} não encontrados")
            return 0.0
        
        # --- AJUSTE DE STATUS NO INIMIGO ---
        enemy_status = self.tm.get_status(enemy_name)
        atk_mod = 0.5 if enemy_status == "BURN" else 1.0  # Burn corta Atk Físico em 50%
        
        if enemy_status == "BURN":
            logger.info(f"🔥 {enemy_name} queimado - Ataque físico reduzido 50%")
        
        max_damage = 0.0
        best_move = ""
        
        # Analisa todos os golpes prováveis
        possible_moves = self.db.get_common_moves(enemy_name)
        
        for move_name in possible_moves:
            move_data = self.db.get_move_data(move_name)
            if not move_data:
                continue
            
            power = float(move_data.get('power', 0) or 0)
            if power == 0:
                continue  # Ignora movimentos de status
            
            # Determina categoria (físico vs especial)
            category_id = str(move_data.get('category_id', '1'))
            is_special = category_id == '2'
            category_name = 'special' if is_special else 'physical'
            
            # --- SELEÇÃO DE STATS CORRETA ---
            if is_special:
                atk = enemy_stats['sp_attack']  # Especial não é afetado por Burn
                defn = my_stats['special_defense']
            else:
                atk = enemy_stats['attack'] * atk_mod  # Físico afetado por Burn
                defn = my_stats['defense']
            
            # --- FÓRMULA DE DANO REAL (GAME FREAK) ---
            damage = (((2 * enemy_level / 5 + 2) * power * atk / defn) / 50 + 2)
            
            # --- MULTIPLICADORES (STAB + TIPAGEM) ---
            enemy_types = self.db.get_pokemon_types(enemy_name)
            my_types = self.db.get_pokemon_types(my_poke)
            move_type = move_data.get('type_id')
            
            # STAB (Same Type Attack Bonus)
            stab = 1.5 if move_type in enemy_types else 1.0
            
            # Type Effectiveness
            type_mult = self.db.get_type_multiplier(move_type, my_types)
            
            # Dano com STAB e type
            final_damage = damage * stab * type_mult
            
            # --- INFERÊNCIA DE ITEM ---
            inferred_item = self.tm.get_inferred_item(enemy_name)
            
            if inferred_item == "CHOICE_BAND" and not is_special:
                final_damage *= 1.5
                if self.debug:
                    logger.debug(f"📦 Choice Band inferido - Dano físico +50%")
            elif inferred_item == "CHOICE_SPECS" and is_special:
                final_damage *= 1.5
                if self.debug:
                    logger.debug(f"📦 Choice Specs inferido - Dano especial +50%")
            elif inferred_item == "LIFE_ORB":
                final_damage *= 1.3
                if self.debug:
                    logger.debug(f"📦 Life Orb inferido - Dano +30%")
            
            if final_damage > max_damage:
                max_damage = final_damage
                best_move = move_name
                
                if self.debug:
                    logger.debug(
                        f"💥 {move_name} ({category_name}): {final_damage:.1f} dmg "
                        f"[Pwr={power}, STAB={stab}, Type={type_mult}, Status={atk_mod}]"
                    )
        
        if best_move:
            logger.info(
                f"🎯 Dano perfeito de {enemy_name}: {max_damage:.1f} HP "
                f"(Melhor golpe: {best_move})"
            )
        
        return max_damage
    
    def calculate_move_damage(self, attacker_poke, move_name, defender_poke, is_attacker_player=False):
        """Calcula dano de um golpe específico.
        
        Args:
            attacker_poke: Nome do Pokémon atacante
            move_name: Nome do movimento
            defender_poke: Nome do Pokémon defensor
            is_attacker_player: True se atacante é o jogador
            
        Returns:
            float: Dano absoluto (HP)
        """
        move_data = self.db.get_move_data(move_name)
        if not move_data:
            return 0.0
        
        power = float(move_data.get('power', 0) or 0)
        if power == 0:
            return 0.0
        
        # Stats
        if is_attacker_player:
            attacker_stats = self.tm.get_stats(attacker_poke)
            attacker_level = 50  # Assumindo level padrão
            atk = attacker_stats.get('attack', 100)
            spa = attacker_stats.get('special_attack', 100)
        else:
            attacker_base = self.db.get_base_stats(attacker_poke)
            attacker_level = self.current_enemy_level
            atk = self.db.estimate_stat(attacker_base['attack'], attacker_level)
            spa = self.db.estimate_stat(attacker_base['special_attack'], attacker_level)
        
        defender_stats = self.tm.get_stats(defender_poke) if is_attacker_player else self.db.get_base_stats(defender_poke)
        
        # Categoria
        category_id = str(move_data.get('category_id', '1'))
        is_special = category_id == '2'
        
        atk_stat = spa if is_special else atk
        def_stat = defender_stats.get('special_defense' if is_special else 'defense', 100)
        
        # Fórmula
        damage = (((2 * attacker_level / 5 + 2) * power * atk_stat / def_stat) / 50 + 2)
        
        # Modificadores
        attacker_types = self.db.get_pokemon_types(attacker_poke)
        defender_types = self.db.get_pokemon_types(defender_poke)
        move_type = move_data.get('type_id')
        
        stab = 1.5 if move_type in attacker_types else 1.0
        type_mult = self.db.get_type_multiplier(move_type, defender_types)
        
        return damage * stab * type_mult
    
    def check_priority_threat(self, enemy_poke, my_poke, my_hp_raw):
        """Verifica se o inimigo possui golpes de prioridade que podem finalizar.
        
        Args:
            enemy_poke: Nome do Pokémon inimigo
            my_poke: Nome do Pokémon do jogador
            my_hp_raw: HP atual em valor absoluto
            
        Returns:
            bool: True se há ameaça de priority move letal
        """
        priority_moves = self.db.get_priority_moves(enemy_poke)
        
        if not priority_moves:
            return False
        
        for move_name in priority_moves:
            # Calcula dano real do priority move
            priority_dmg = self.calculate_move_damage(
                enemy_poke, move_name, my_poke, is_attacker_player=False
            )
            
            if priority_dmg >= my_hp_raw:
                logger.warning(
                    f"⚡ AMEAÇA DE PRIORITY: {enemy_poke} pode usar {move_name} "
                    f"({priority_dmg:.1f} dmg vs {my_hp_raw:.1f} HP) - LETAL!"
                )
                return True
        
        return False
    
    def check_priority_risk(self, enemy_poke, my_hp_ratio):
        """Verifica se o inimigo tem golpes de prioridade que podem finalizar o bot.
        
        Args:
            enemy_poke: Nome do Pokémon inimigo
            my_hp_ratio: Razão de HP atual (0.0 a 1.0)
            
        Returns:
            bool: True se há risco de priority move fatal
        """
        priority_moves = self.db.get_priority_moves(enemy_poke)
        
        if not priority_moves:
            return False
        
        # Estima dano médio de priority moves (base 40 power)
        # Quick Attack, Aqua Jet, Mach Punch = 40 BP
        # Extreme Speed = 80 BP
        avg_priority_power = 40
        
        # Estimativa simplificada: ~20-30% HP de dano
        estimated_priority_damage = 0.25  # 25% HP
        
        # Considera STAB e type effectiveness
        enemy_types = self.db.get_pokemon_types(enemy_poke)
        my_types = self.db.get_pokemon_types(self.tm.current_team[0] if self.tm.current_team else "")
        
        if enemy_types and my_types:
            # Usa primeiro tipo como proxy
            type_mult = self.db.get_type_multiplier(enemy_types[0], my_types)
            estimated_priority_damage *= type_mult
        
        # Se HP está baixo o suficiente para morrer de priority
        if my_hp_ratio < estimated_priority_damage:
            logger.warning(
                f"⚡ RISCO DE PRIORITY MOVE: {enemy_poke} pode ter {priority_moves[0]}! "
                f"(HP={my_hp_ratio*100:.1f}% vs Dano estimado={estimated_priority_damage*100:.1f}%)"
            )
            return True
        
        return False
    
    def get_effective_speed(self, pokemon_name, is_player=True):
        """Calcula velocidade efetiva considerando status e itens.
        
        Args:
            pokemon_name: Nome do Pokémon
            is_player: True se é o jogador, False se é inimigo
            
        Returns:
            int: Velocidade efetiva
        """
        # Obter velocidade base
        if is_player:
            stats = self.tm.get_stats(pokemon_name)
            base_speed = stats['speed'] if stats else 100
        else:
            base_stats = self.db.get_base_stats(pokemon_name)
            if base_stats:
                # Calcula com pior cenário
                base_speed = self.db.estimate_stat(
                    base_stats['speed'], 
                    self.current_enemy_level,
                    iv=31, ev=252, nature=1.1
                )
            else:
                base_speed = 100
        
        # Aplica modificações de status
        status = self.tm.get_status(pokemon_name)
        if status == "PARALYSIS":
            base_speed *= 0.5  # Paralisia reduz speed em 50%
        
        # Aplica modificações de itens
        item = self.tm.get_inferred_item(pokemon_name)
        if item == "CHOICE_SCARF":
            base_speed *= 1.5
        
        return int(base_speed)
    
    def evaluate_status_risk(self, pokemon_name):
        """Avalia risco de status e recomenda ação.
        
        Args:
            pokemon_name: Nome do Pokémon
            
        Returns:
            str: "RISK_ACCEPTABLE", "SWITCH_MANDATORY", "CHECK_SPEED_TIER", "OK"
        """
        status = self.tm.get_status(pokemon_name)
        
        if not status or status == "OK":
            return "OK"
        
        if status == "SLEEP":
            # Sleep dura 1-3 turnos no PokeOne/MMOs
            turns_asleep = self.tm.get_survival_turns(pokemon_name)
            
            if turns_asleep >= 2:
                # Chance alta de acordar no próximo turno
                logger.info(
                    f"😴 {pokemon_name} dormindo há {turns_asleep} turnos - "
                    f"Provável acordar em breve"
                )
                return "RISK_ACCEPTABLE"
            else:
                # Risco de ser "Setup Bait" (inimigo usa Swords Dance, etc)
                logger.warning(
                    f"😴 {pokemon_name} dormindo há {turns_asleep} turno(s) - "
                    f"RISCO DE SETUP!"
                )
                return "SWITCH_MANDATORY"
        
        if status == "PARALYSIS":
            # Paralisia reduz velocidade em 50% e tem 25% de chance de não agir
            logger.warning(
                f"⚡ {pokemon_name} paralisado - Velocidade reduzida 50%, "
                f"25% chance de falha por turno"
            )
            # A IA deve recalcular Speed Tier imediatamente
            return "CHECK_SPEED_TIER"
        
        if status == "FREEZE":
            # Freeze é permanente até usar golpe de fogo ou descongelar (20%/turno)
            logger.critical(
                f"❄️ {pokemon_name} congelado - 20% chance de descongelar por turno"
            )
            return "SWITCH_MANDATORY"
        
        if status == "TOXIC":
            # Toxic progressivo - verificar turnos restantes
            survival_turns = self.tm.get_survival_turns(pokemon_name)
            if survival_turns <= 2:
                logger.critical(
                    f"☠️ {pokemon_name} com Toxic crítico - {survival_turns} turnos restantes!"
                )
                return "SWITCH_MANDATORY"
            else:
                logger.info(
                    f"☠️ {pokemon_name} com Toxic - {survival_turns} turnos restantes"
                )
                return "RISK_ACCEPTABLE"
        
        return "OK"
    
    def evaluate_best_move(self, my_poke, enemy_poke):
        """Decisão avançada integrando Sleep, Priority Awareness e Speed Tiering.
        
        Pipeline completo:
        1. Gestão de Sleep (se dormindo e vulnerável, trocar)
        2. Cálculo de velocidade efetiva (considera paralisia)
        3. Priority Awareness (mesmo rápido, inimigo pode ter priority)
        4. Decisão final: sobrevivência vs ataque
        
        Args:
            my_poke: Nome do meu Pokémon
            enemy_poke: Nome do Pokémon inimigo
            
        Returns:
            str: "SWITCH_PRIORITY", "SWITCH_ACTION", "OPTIMAL_ATTACK"
        """
        # Obter HP atual
        my_hp = 0.5
        if self.detector:
            detected_hp = self.detector.get_hp_ratio(
                self.detector.cap.capture(), 'player'
            )
            if detected_hp is not None:
                my_hp = detected_hp
        
        # Calcular dano que vou receber (versão perfeita)
        incoming_dmg_raw = self.calculate_perfect_damage(
            enemy_poke, self.current_enemy_level, my_poke
        )
        
        # Converte para razão
        my_stats = self.tm.get_stats(my_poke)
        my_max_hp = my_stats.get('hp', 100) if my_stats else 100
        incoming_dmg_ratio = incoming_dmg_raw / my_max_hp
        
        logger.info(
            f"🧠 Evaluate Best Move: HP={my_hp*100:.0f}%, "
            f"Dano esperado={incoming_dmg_ratio*100:.0f}%"
        )
        
        # --- 1. GESTÃO DE SLEEP (SONO) ---
        my_status = self.tm.get_status(my_poke)
        if my_status == "SLEEP":
            # Se estou dormindo e o inimigo tira >30% de dano: TROCAR
            if incoming_dmg_ratio > 0.3:
                logger.critical(
                    f"😴 DORMINDO + DANO ALTO ({incoming_dmg_ratio*100:.0f}%) - "
                    f"RISCO DE SETUP!"
                )
                return "SWITCH_PRIORITY"
            
            # TODO: Detectar enemy buffing (Swords Dance, Dragon Dance)
            # if self.detector.detect_enemy_buffing():
            #     return "SWITCH_PRIORITY"
        
        # --- 2. CÁLCULO DE VELOCIDADE (SPEED TIERING) ---
        # Considera 50% de redução se paralisado
        my_speed = self.get_effective_speed(my_poke, is_player=True)
        enemy_speed = self.get_effective_speed(enemy_poke, is_player=False)
        
        logger.info(
            f"⚡ Speed: Meu={my_speed} vs Inimigo={enemy_speed} "
            f"({'Mais rápido' if my_speed > enemy_speed else 'Mais lento'})"
        )
        
        # --- 3. PRIORITY AWARENESS ---
        # Mesmo se eu for mais rápido, ele pode me matar com Quick Attack?
        has_priority_risk = False
        
        # Verifica se inimigo tem priority moves
        enemy_priority_moves = self.db.get_priority_moves(enemy_poke)
        if enemy_priority_moves:
            # Estima dano de priority (geralmente ~40% do dano normal)
            priority_dmg_estimate = incoming_dmg_ratio * 0.4
            
            if priority_dmg_estimate >= my_hp:
                has_priority_risk = True
                logger.warning(
                    f"⚡ PRIORITY RISK: {enemy_poke} pode ter {enemy_priority_moves[0]} "
                    f"(dano estimado {priority_dmg_estimate*100:.0f}% vs HP {my_hp*100:.0f}%)"
                )
        
        # --- 4. DECISÃO FINAL: SOBREVIVÊNCIA VS ATAQUE ---
        i_act_first = my_speed > enemy_speed and not has_priority_risk
        
        # Se eu não ajo primeiro e vou morrer
        if not i_act_first and incoming_dmg_ratio >= my_hp:
            logger.critical(
                f"💀 MORTE IMINENTE: Não ajo primeiro e dano é letal "
                f"({incoming_dmg_ratio*100:.0f}% >= {my_hp*100:.0f}%)"
            )
            
            # Verifica se posso matar com priority antes
            if self.can_kill_with_priority(my_poke, enemy_poke):
                logger.info(
                    f"⚡ CONTRA-ATAQUE VIÁVEL: Posso matar com priority!"
                )
                return "OPTIMAL_ATTACK"  # Mata com priority
            else:
                logger.critical(
                    f"🔄 SEM CONTRA-ATAQUE: Trocar Pokémon"
                )
                return "SWITCH_ACTION"
        
        # Se chegou aqui, é seguro atacar
        logger.info(f"⚔️ Situação controlada - Ataque ótimo")
        return "OPTIMAL_ATTACK"
    
    def evaluate_risk_reward(self, my_poke, enemy_poke):
        """Julga se vale a pena atacar, curar ou trocar/fugir.
        
        ATUALIZADO com:
        - Cálculo de dano real
        - Análise de priority moves
        - Consideração de status (Paralisia, Toxic)
        
        Returns:
            str: "SWITCH_PRIORITY", "HEAL_NOW", "ATTACK", ou "SWITCH_OR_SACRIFICE"
        """
        # Obter HP atual
        my_hp = 0.5  # Default
        enemy_hp = 0.5
        
        if self.detector:
            my_hp_result = self.detector.get_hp_ratio(
                self.detector.cap.capture(), 'player'
            )
            enemy_hp_result = self.detector.get_hp_ratio(
                self.detector.cap.capture(), 'enemy'
            )
            
            if my_hp_result is not None:
                my_hp = my_hp_result
            if enemy_hp_result is not None:
                enemy_hp = enemy_hp_result
        
        # Calcula velocidade EFETIVA (com status e itens)
        my_speed = self.get_effective_speed(my_poke, is_player=True)
        enemy_speed = self.get_effective_speed(enemy_poke, is_player=False)
        i_am_faster = my_speed > enemy_speed
        
        # Verifica risco de priority move
        has_priority_risk = self.check_priority_risk(enemy_poke, my_hp)
        
        # Calcula dano que vou receber (fórmula real)
        estimated_enemy_damage = self.calculate_incoming_damage(enemy_poke, my_poke)
        
        # REGRA DE OURO: Morte iminente
        # Se vou morrer antes de agir (inimigo mais rápido OU priority)
        if (not i_am_faster or has_priority_risk) and estimated_enemy_damage >= my_hp:
            logger.critical(
                f"⚠️ RISCO CRÍTICO: Morte iminente! "
                f"(HP={my_hp*100:.1f}%, Dano esperado={estimated_enemy_damage*100:.1f}%, "
                f"Faster={'Sim' if i_am_faster else 'Não'}, Priority={'Sim' if has_priority_risk else 'Não'})"
            )
            
            # TODO: Verificar se temos priority move que mata o inimigo
            # Se temos e mata, atacar ao invés de trocar
            
            return "SWITCH_PRIORITY"
        
        # Verifica Toxic/Poison (morte gradual)
        my_status = self.tm.get_status(my_poke)
        if my_status == "TOXIC":
            survival_turns = self.tm.get_survival_turns(my_poke)
            if survival_turns <= 2:
                logger.warning(
                    f"☠️ TOXIC CRÍTICO: Apenas {survival_turns} turnos restantes!"
                )
                return "SWITCH_PRIORITY"
        
        # Julgamento de cura inteligente
        if my_hp < 0.4:
            # Verifica se temos movimento de cura
            my_moves = self.tm.get_moves(my_poke)
            has_healing = any(
                move and move.strip().lower() in self.healing_move_names
                for move in my_moves if move
            )
            
            if has_healing:
                # Só cura se for mais rápido OU aguentar o hit
                if i_am_faster or (my_hp - estimated_enemy_damage > 0.1):
                    logger.info(
                        f"💊 CURA VIÁVEL: HP={my_hp*100:.1f}%, "
                        f"{'Mais rápido' if i_am_faster else f'Aguenta hit ({(my_hp-estimated_enemy_damage)*100:.1f}% sobra)'}"
                    )
                    return "HEAL_NOW"
                else:
                    logger.warning(
                        f"⚠️ CURA INVIÁVEL: Vou morrer tentando curar "
                        f"(HP={my_hp*100:.1f}%, Dano={estimated_enemy_damage*100:.1f}%)"
                    )
                    return "SWITCH_OR_SACRIFICE"
        
        # Se inimigo está quase morto, sempre ataca
        if enemy_hp < 0.2:
            logger.info(f"🎯 FINALIZAR: Inimigo com HP crítico ({enemy_hp*100:.1f}%)")
            return "ATTACK"
        
        return "ATTACK"
    
    def check_if_any_move_kos(self, enemy_poke):
        """Verifica se algum golpe do bot pode causar KO no inimigo.
        
        Args:
            enemy_poke: Nome do Pokémon inimigo
            
        Returns:
            bool: True se existe possibilidade de KO
        """
        if not self.tm.current_team:
            return False
        
        my_poke = self.tm.current_team[0]
        my_moves = self.tm.get_moves(my_poke)
        
        if not my_moves:
            return False
        
        # Estima HP do inimigo (assume HP cheio se não detectado)
        enemy_hp_ratio = 1.0
        if self.detector:
            detected_hp = self.detector.get_hp_ratio(
                self.detector.cap.capture(), 'enemy'
            )
            if detected_hp is not None:
                enemy_hp_ratio = detected_hp
        
        # Calcula HP absoluto
        enemy_base_stats = self.db.get_base_stats(enemy_poke)
        if enemy_base_stats:
            enemy_max_hp = self.db.estimate_stat(
                enemy_base_stats['hp'], 
                self.current_enemy_level
            )
            enemy_current_hp = enemy_max_hp * enemy_hp_ratio
        else:
            enemy_current_hp = 100  # Fallback
        
        # Testa cada golpe
        for move_name in my_moves:
            if not move_name:
                continue
            
            damage = self.calculate_move_damage(
                my_poke, move_name, enemy_poke, is_attacker_player=True
            )
            
            if damage >= enemy_current_hp:
                logger.info(
                    f"🎯 {move_name} pode causar KO! "
                    f"({damage:.1f} dmg vs {enemy_current_hp:.1f} HP)"
                )
                return True
        
        return False
    
    def get_best_action(self, my_poke, enemy_poke):
        """Decisão tática avançada baseada em TTK (Time To Kill).
        
        Substituímos HP fixo por cálculo de turnos para nocaute.
        Se o inimigo tira 60% e você não mata ele no próximo turno,
        curar é um erro matemático - prefere troca.
        
        Args:
            my_poke: Nome do Pokémon do jogador
            enemy_poke: Nome do Pokémon inimigo
            
        Returns:
            str: "ATTACK", "HEAL", "SWITCH_TO_RESISTANT", "BEST_EFFICIENCY_ATTACK"
        """
        # Obter HP atual (absoluto)
        my_hp_ratio = 0.5
        if self.detector:
            detected_hp = self.detector.get_hp_ratio(
                self.detector.cap.capture(), 'player'
            )
            if detected_hp is not None:
                my_hp_ratio = detected_hp
        
        my_stats = self.tm.get_stats(my_poke)
        my_max_hp = my_stats.get('hp', 100) if my_stats else 100
        my_hp_raw = my_max_hp * my_hp_ratio
        
        # Calcular dano que vou receber
        enemy_dmg_ratio = self.calculate_incoming_damage(enemy_poke, my_poke)
        enemy_dmg = my_max_hp * enemy_dmg_ratio
        
        # 1. VERIFICAR STATUS CRÍTICO
        status_risk = self.evaluate_status_risk(my_poke)
        if status_risk == "SWITCH_MANDATORY":
            logger.critical(
                f"🚨 Status crítico detectado - TROCA OBRIGATÓRIA!"
            )
            return "SWITCH_TO_RESISTANT"
        
        # 2. ANÁLISE DE VELOCIDADE (considerando Status e Itens)
        my_speed = self.get_effective_speed(my_poke, is_player=True)
        enemy_speed = self.get_effective_speed(enemy_poke, is_player=False)
        i_outspeed = my_speed > enemy_speed
        
        # 3. RISCO DE PRIORITY: Mesmo sendo mais rápido, ele pode me finalizar?
        if i_outspeed and self.check_priority_threat(enemy_poke, my_poke, my_hp_raw):
            logger.critical(
                f"⚡ PRIORITY THREAT DETECTADA - Inimigo age primeiro!"
            )
            i_outspeed = False  # O inimigo agirá primeiro com prioridade
        
        # 4. ANÁLISE DE VANTAGEM TÁTICA
        can_ko_enemy = self.check_if_any_move_kos(enemy_poke)
        
        # --- CENÁRIO: Inimigo tira mais de 50% HP ---
        if enemy_dmg > (my_max_hp * 0.5):
            logger.warning(
                f"⚠️ Inimigo causa {enemy_dmg_ratio*100:.1f}% HP - DANO ALTO!"
            )
            
            if can_ko_enemy and i_outspeed:
                logger.info(
                    f"🎯 FINALIZAÇÃO VIÁVEL - Sou mais rápido e posso KO!"
                )
                return "ATTACK"  # Finaliza antes de levar o hit
            
            # Se ele é mais rápido e me mata no próximo hit
            if not i_outspeed and enemy_dmg >= my_hp_raw:
                logger.critical(
                    f"💀 MORTE IMINENTE - Inimigo mais rápido e causa OHKO!"
                )
                return "SWITCH_TO_RESISTANT"  # Troca para resistente
        
        # 5. USO DE MOVIMENTOS DE SUPORTE/CURA
        if my_hp_raw < (enemy_dmg + 10):  # Margem de segurança de 10 HP
            my_moves = self.tm.get_moves(my_poke)
            has_healing = any(
                move and move.strip().lower() in self.healing_move_names
                for move in my_moves if move
            )
            
            if has_healing and i_outspeed:
                logger.info(
                    f"💊 CURA TÁTICA - HP crítico mas sou mais rápido"
                )
                return "HEAL"
            elif has_healing and not i_outspeed:
                logger.warning(
                    f"⚠️ CURA INVIÁVEL - Vou morrer antes de curar"
                )
                return "SWITCH_TO_RESISTANT"
        
        # 6. DECISÃO PADRÃO: MELHOR ATAQUE
        logger.info(f"⚔️ Ataque padrão - Situação controlada")
        return "BEST_EFFICIENCY_ATTACK"
    
    def record_turn_result(self, i_attacked_first, damage_received=0, damage_expected=0):
        """Registra resultado do turno para inferência de itens.
        
        Args:
            i_attacked_first: True se o jogador atacou primeiro
            damage_received: Dano real recebido
            damage_expected: Dano esperado (baseado em cálculos)
        """
        self.enemy_outspeeded_me_last_turn = not i_attacked_first
        self.last_turn_outspeeded = not i_attacked_first  # Atualiza flag de inferência
        self.actual_damage_last_turn = damage_received
        self.expected_damage_last_turn = damage_expected
        
        # Inferência de Choice Band / Life Orb
        if damage_expected > 0 and damage_received > 0:
            damage_ratio = damage_received / damage_expected
            
            if damage_ratio >= 1.45:  # ~1.5x damage
                if self.enemy_item_inference != "Choice Band":
                    self.enemy_item_inference = "Choice Band"
                    logger.warning(
                        f"⚠️ INFERÊNCIA: Inimigo provavelmente tem Choice Band! "
                        f"(Dano: {damage_received} vs esperado: {damage_expected})"
                    )
            elif damage_ratio >= 1.25:  # ~1.3x damage
                if self.enemy_item_inference != "Life Orb":
                    self.enemy_item_inference = "Life Orb"
                    logger.warning(
                        f"⚠️ INFERÊNCIA: Inimigo provavelmente tem Life Orb! "
                        f"(Dano: {damage_received} vs esperado: {damage_expected})"
                    )
    
    # ---------------------------------------------------------
    # Escolha de movimento (com árvore de prioridades táticas)
    # ---------------------------------------------------------
    def get_best_move(self, my_pokemon_name, enemy_name):
        """Escolhe o melhor movimento baseado em árvore de prioridades táticas.

        Hierarquia de Prioridades:
        0. AVALIAÇÃO DE RISCO: Calcula se troca/cura é necessária antes de atacar
        1. SOBREVIVÊNCIA: HP < 40% e tem golpe de cura → Usar cura
        2. CHECKMATE: Algum golpe causa OHKO → Usar o mais preciso
        3. IMUNIDADE: Inimigo imune ao golpe → Ignorar completamente
        4. SPEED & DANGER: Sou mais lento e posso morrer → Considerar troca
        5. INFERÊNCIA: Inimigo "lockado" em golpe fraco → Bufar/atacar
        6. DAMAGE OUTPUT: Maximizar dano (STAB + Type + Priority)
        """

        enemy_types = self.db.get_pokemon_types(enemy_name)
        my_types = self.db.get_pokemon_types(my_pokemon_name)
        logger.info(f"Meu Pokémon: {my_pokemon_name} | tipos={my_types}")
        logger.info(f"Inimigo: {enemy_name} | tipos={enemy_types}")

        my_moves = self.tm.get_moves(my_pokemon_name)
        if not my_moves:
            logger.warning("Movimentos desconhecidos. Usando Slot 1.")
            return 0
        
        # PRIORIDADE 0: AVALIAÇÃO DE RISCO (antes de tudo)
        risk_assessment = self.evaluate_risk_reward(my_pokemon_name, enemy_name)
        
        if risk_assessment == "SWITCH_PRIORITY":
            logger.critical(
                "🔄 AVALIAÇÃO DE RISCO: TROCA OBRIGATÓRIA detectada! "
                "(Bot controller deve processar troca)"
            )
            # Retorna -1 para sinalizar que troca é necessária
            # O bot_controller deve checar isso e chamar choose_switch_target()
            return -1
        
        # Obter HP atual (se detector disponível)
        my_hp_ratio = 1.0
        if self.detector:
            hp = self.detector.get_hp_ratio(self.detector.cap.capture(), 'player')
            if hp is not None:
                my_hp_ratio = hp
        
        # PRIORIDADE 1: SOBREVIVÊNCIA (HP < 40% e tem golpe de cura)
        if my_hp_ratio < 0.4:
            for i, move_name in enumerate(my_moves):
                if not move_name:
                    continue

                move_key = move_name.strip().lower()
                move_data = self.db.get_move_data(move_key)
                category_id = (
                    str(move_data.get("category_id"))
                    if move_data and move_data.get("category_id") is not None
                    else None
                )

                if move_key in self.healing_move_names or (
                    category_id and category_id in self.healing_category_ids
                ):
                    logger.critical(
                        f"🩹 PRIORIDADE 1 - SOBREVIVÊNCIA: HP crítico ({my_hp_ratio*100:.1f}%), "
                        f"usando {move_name}!"
                    )
                    return i
        
        # Análise de movimentos para prioridades 2-6
        move_analysis = []
        
        for i, move_name in enumerate(my_moves):
            if not move_name:
                continue

            move_key = move_name.strip().lower()
            move_data = self.db.get_move_data(move_key)
            if not move_data:
                logger.debug(f"Dados não encontrados para golpe '{move_name}'")
                continue

            power = float(move_data.get("power", 0) or 0)
            type_id = move_data.get("type_id")
            category_id = str(move_data.get("category_id")) if move_data.get("category_id") is not None else None
            priority = int(move_data.get("priority", 0) or 0)
            accuracy = float(move_data.get("accuracy", 100) or 100)
            
            # PRIORIDADE 3: IMUNIDADE (multiplicador 0.0)
            type_mult = self.db.get_type_multiplier(type_id, enemy_types)
            if type_mult == 0.0:
                logger.debug(f"❌ Ignorando '{move_name}' - inimigo é IMUNE (tipo {type_id})")
                continue  # Pula completamente movimentos inúteis
            
            # Calcula STAB
            stab_bonus = 1.5 if type_id in my_types else 1.0
            
            # Dano base
            base_damage = power * stab_bonus * type_mult
            
            # PRIORIDADE 2: CHECKMATE (OHKO)
            # Assume que se dano base > 150, provavelmente é OHKO
            can_ohko = base_damage >= 150
            
            move_analysis.append({
                'slot': i,
                'name': move_name,
                'power': power,
                'type_id': type_id,
                'category_id': category_id,
                'priority': priority,
                'accuracy': accuracy,
                'type_mult': type_mult,
                'stab': stab_bonus,
                'base_damage': base_damage,
                'can_ohko': can_ohko
            })
        
        if not move_analysis:
            logger.warning("Nenhum movimento viável encontrado. Usando Slot 1.")
            return 0
        
        # PRIORIDADE 2: CHECKMATE - Escolhe OHKO mais preciso
        ohko_moves = [m for m in move_analysis if m['can_ohko']]
        if ohko_moves:
            # Ordena por accuracy (mais preciso primeiro)
            best_ohko = max(ohko_moves, key=lambda m: m['accuracy'])
            logger.critical(
                f"💀 PRIORIDADE 2 - CHECKMATE: {best_ohko['name']} pode causar OHKO! "
                f"(Dano base: {best_ohko['base_damage']:.1f}, Accuracy: {best_ohko['accuracy']}%)"
            )
            return best_ohko['slot']
        
        # PRIORIDADE 4: SPEED & DANGER
        # Verifica se somos mais lentos e estamos em perigo
        i_am_faster = self.judge_speed_tier(my_pokemon_name, enemy_name)
        if not i_am_faster and my_hp_ratio < 0.7:
            logger.warning(
                f"⚠️ PRIORIDADE 4 - SPEED & DANGER: Somos mais lentos e HP < 70%. "
                f"Considere trocar Pokémon!"
            )
            # Não retorna aqui, mas sinaliza que troca pode ser necessária
        
        # PRIORIDADE 5: INFERÊNCIA DE ITEM
        if self.enemy_item_inference == "Choice Scarf" or self.enemy_item_inference == "Choice Band":
            logger.info(
                f"💡 PRIORIDADE 5 - INFERÊNCIA: Inimigo tem {self.enemy_item_inference}, "
                f"está 'lockado' em um movimento."
            )
            # Favorece movimentos defensivos/setup se inimigo está lockado em golpe fraco
            # (Implementação futura: detectar se último golpe inimigo foi fraco)
        
        # PRIORIDADE 6: DAMAGE OUTPUT (Padrão)
        # Calcula score final para cada movimento
        for move in move_analysis:
            score = move['base_damage']
            
            # Bônus de prioridade
            if move['priority'] > 0:
                score += move['priority'] * 20
            
            # Penaliza baixa accuracy
            if move['accuracy'] < 100:
                score *= (move['accuracy'] / 100)
            
            # Penaliza movimentos de status
            if move['power'] == 0:
                score -= 50
            
            move['final_score'] = score
            
            logger.debug(
                f"Slot {move['slot']} '{move['name']}': power={move['power']}, "
                f"type_mult={move['type_mult']}, stab={move['stab']}, "
                f"priority={move['priority']}, accuracy={move['accuracy']}, "
                f"score={score:.2f}"
            )
        
        # Escolhe movimento com maior score
        best_move = max(move_analysis, key=lambda m: m['final_score'])
        
        logger.info(
            f"⚔️ PRIORIDADE 6 - DAMAGE OUTPUT: Melhor golpe escolhido: "
            f"slot={best_move['slot']} '{best_move['name']}' (score={best_move['final_score']:.2f})"
        )
        
        return best_move['slot']

    # ---------------------------------------------------------
    # Decisão de fuga
    # ---------------------------------------------------------
    def should_flee(self, my_pokemon_name, enemy_name):
        """Decide se deve fugir.

        Nova regra (simplificada conforme pedido):
        - Fugir APENAS se o inimigo estiver na blacklist.
        - Caso contrário, nunca fugir (independente de matchup).
        """
        enemy_key = (enemy_name or "").strip().lower()
        if not enemy_key:
            return False

        if enemy_key in self.blacklist:
            logger.info(f"{enemy_name} está na BLACKLIST – fugindo da batalha.")
            return True

        return False
    
    # ---------------------------------------------------------
    # Decisão de cura/troca baseado em HP
    # ---------------------------------------------------------
    def should_use_item(self, player_hp_percentage):
        """
        Decide se deve usar um item de cura baseado no HP atual.
        
        Args:
            player_hp_percentage: Porcentagem de HP do Pokémon atual (0-100)
            
        Returns:
            bool: True se deve usar item, False caso contrário
        """
        if player_hp_percentage is None:
            return False
        
        # Usa item se HP estiver crítico (< 25%)
        if player_hp_percentage < 25:
            logger.info(f"HP crítico ({player_hp_percentage}%) - recomendando uso de item")
            return True
        
        return False
    
    def should_switch_pokemon(self, my_poke, enemy_name, player_hp_percentage=None):
        """Decide se deve trocar de Pokémon baseado em HP, speed tier e matchup.
        
        Args:
            my_poke: Nome do Pokémon atual do jogador
            enemy_name: Nome do Pokémon inimigo
            player_hp_percentage: Porcentagem de HP do Pokémon atual (0-100)
            
        Returns:
            bool: True se deve trocar, False caso contrário
        """
        if not my_poke or not enemy_name:
            return False
        
        # Obter HP atual
        my_hp_ratio = 0.7
        if player_hp_percentage is not None:
            my_hp_ratio = player_hp_percentage / 100
        elif self.detector:
            hp = self.detector.get_hp_ratio(self.detector.cap.capture(), 'player')
            if hp is not None:
                my_hp_ratio = hp
        
        my_types = self.db.get_pokemon_types(my_poke)
        enemy_types = self.db.get_pokemon_types(enemy_name)
        
        if not my_types or not enemy_types:
            return False
        
        enemy_type = enemy_types[0] if enemy_types else None
        if enemy_type:
            type_disadvantage = self.db.get_type_multiplier(enemy_type, my_types)
        else:
            type_disadvantage = 1.0
        
        i_am_faster = self.judge_speed_tier(my_poke, enemy_name)
        
        if not i_am_faster and type_disadvantage > 1.0:
            if my_hp_ratio < 0.7:
                logger.warning(
                    f"🔄 TROCA RECOMENDADA: Inimigo mais rápido + vantagem de tipo "
                    f"({type_disadvantage}x) + HP < 70% ({my_hp_ratio*100:.1f}%)"
                )
                return True
        
        if my_hp_ratio < 0.3:
            logger.warning(f"🔄 TROCA RECOMENDADA: HP crítico ({my_hp_ratio*100:.1f}%)")
            return True
        
        if type_disadvantage >= 2.0:
            logger.warning(
                f"🔄 TROCA RECOMENDADA: Matchup muito desfavorável "
                f"({type_disadvantage}x weakness)"
            )
            return True
        
        return False

    # ---------------------------------------------------------
    # Decisão de troca (esqueleto, depende de integração com HUD)
    # ---------------------------------------------------------
    def choose_switch_target(self, enemy_name):
        """Escolhe um alvo de troca na equipe atual.

        Por enquanto, usa apenas nomes da equipe do TeamManager e procura
        o primeiro que tenha pelo menos um golpe com multiplicador > 1.0.
        Retorna o índice na lista current_team, ou None se não vale trocar.
        """
        team = getattr(self.tm, "current_team", [])
        if not team:
            return None

        enemy_types = self.db.get_pokemon_types(enemy_name)
        if not enemy_types:
            return None

        for idx, poke_name in enumerate(team):
            moves = self.tm.get_moves(poke_name)
            if not moves:
                continue
            for move_name in moves:
                move_key = move_name.strip().lower()
                move_data = self.db.get_move_data(move_key)
                if not move_data:
                    continue
                type_id = move_data.get("type_id")
                mult = self.db.get_type_multiplier(type_id, enemy_types)
                if mult > 1.0:
                    logger.info(
                        f"Troca sugerida: {poke_name} (slot {idx}) tem golpe super efetivo contra {enemy_name}."
                    )
                    return idx

        return None
    
    def reset_battle_state(self):
        """Reseta variáveis de estado de batalha (movido de BattleController)."""
        self.current_enemy = None
        self.turn_count = 0
        self.last_action_time = 0
        self.enemy_outspeeded_me_last_turn = False
        self.enemy_item_inference = None
        self.expected_damage_last_turn = 0
        self.actual_damage_last_turn = 0
        logger.info("Estado de batalha resetado.")
    
    def increment_turn(self):
        """Incrementa o contador de turnos."""
        self.turn_count += 1
        logger.debug(f"Turno {self.turn_count} iniciado")
    
    def get_turn_count(self):
        """Retorna o contador atual de turnos."""
        return self.turn_count
    
    def set_current_enemy(self, enemy_name):
        """Define o inimigo atual e reseta se for um novo inimigo."""
        if enemy_name != self.current_enemy:
            logger.info(f"Novo inimigo detectado: {enemy_name}")
            self.reset_battle_state()
            self.current_enemy = enemy_name
    
    def update_last_action_time(self):
        """Atualiza o timestamp da última ação de batalha."""
        import time
        self.last_action_time = time.time()
