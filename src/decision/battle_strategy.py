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

        # Força minúsculo para comparação
        self.whitelist = {x.lower() for x in self.whitelist}
        self.blacklist = {x.lower() for x in self.blacklist}

    # ---------------------------------------------------------
    # Escolha de movimento
    # ---------------------------------------------------------
    def get_best_move(self, my_pokemon_name, enemy_name):
        """Escolhe o melhor movimento baseado em power, tipo, categoria e STAB.

        - Usa dados do pokeapi (tipo_id, power, categoria).
        - Aplica multiplicador de eficácia de tipo.
        - Aplica bônus STAB (Same Type Attack Bonus) de 1.5x.
        - Evita golpes puramente de status quando possível.
        - Considera prioridade de movimentos.
        """

        enemy_types = self.db.get_pokemon_types(enemy_name)
        my_types = self.db.get_pokemon_types(my_pokemon_name)
        logger.info(f"Meu Pokémon: {my_pokemon_name} | tipos={my_types}")
        logger.info(f"Inimigo: {enemy_name} | tipos={enemy_types}")

        my_moves = self.tm.get_moves(my_pokemon_name)
        if not my_moves:
            logger.warning("Movimentos desconhecidos. Usando Slot 1.")
            return 0

        best_slot = 0
        best_score = float("-inf")

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

            # Base score é o power do movimento
            score = power

            # 1. STAB (Same Type Attack Bonus): 1.5x se o tipo do movimento é igual ao tipo do Pokémon
            stab_bonus = 1.0
            if type_id in my_types:
                stab_bonus = 1.5
                logger.debug(f"STAB aplicado para '{move_name}' (tipo {type_id} em {my_types})")
            
            score *= stab_bonus

            # 2. Eficácia de tipo (super efetivo, neutro, não muito efetivo)
            type_mult = self.db.get_type_multiplier(type_id, enemy_types)
            score *= type_mult

            # 3. Bônus de prioridade (movimentos com prioridade > 0 são valiosos)
            if priority > 0:
                score += priority * 10  # Bônus adicional para movimentos rápidos

            # 4. Penaliza movimentos de baixa accuracy
            if accuracy < 100:
                score *= (accuracy / 100)

            # 5. Penaliza movimentos de status (power 0 em categorias típicas de status/support)
            if power == 0 and category_id in {"1", "2", "3", "5", "10", "11", "12", "13"}:
                score -= 50

            # 6. Preferência por movimentos físicos vs especiais baseado na categoria
            # Categoria 0 = status, 1 = físico, 2 = especial (depende da implementação)
            # Aqui podemos adicionar lógica futura baseada em stats do Pokémon

            logger.debug(
                f"Avaliação golpe slot {i} '{move_name}': power={power}, type_id={type_id}, "
                f"category_id={category_id}, stab={stab_bonus}, type_mult={type_mult}, "
                f"priority={priority}, accuracy={accuracy}, score={score:.2f}"
            )

            if score > best_score:
                best_score = score
                best_slot = i

        logger.info(f"Melhor golpe escolhido: slot={best_slot}, score={best_score:.2f}")
        return best_slot

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
    
    def should_switch_pokemon(self, player_hp_percentage, enemy_name):
        """
        Decide se deve trocar de Pokémon baseado no HP e matchup.
        
        Args:
            player_hp_percentage: Porcentagem de HP do Pokémon atual (0-100)
            enemy_name: Nome do Pokémon inimigo
            
        Returns:
            bool: True se deve trocar, False caso contrário
        """
        if player_hp_percentage is None:
            return False
        
        # Troca se HP estiver baixo (< 30%) e houver outro Pokémon disponível
        if player_hp_percentage < 30:
            logger.info(f"HP baixo ({player_hp_percentage}%) - recomendando troca de Pokémon")
            return True
        
        # Troca se o matchup for muito desfavorável (futuro: verificar tipos)
        # TODO: Implementar lógica de matchup baseado em tipos
        
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