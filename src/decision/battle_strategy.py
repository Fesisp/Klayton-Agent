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
        """Escolhe o melhor movimento baseado em power, tipo e categoria.

        - Usa dados do pokeapi (tipo_id, power, categoria).
        - Aplica multiplicador de eficácia de tipo.
        - Evita golpes puramente de status quando possível.
        """

        enemy_types = self.db.get_pokemon_types(enemy_name)
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

            score = power

            # Eficácia de tipo (se soubermos o type_id do golpe e do inimigo)
            type_mult = self.db.get_type_multiplier(type_id, enemy_types)
            score *= type_mult

            # Penaliza movimentos de status (power 0 em categorias típicas de status/support)
            if power == 0 and category_id in {"1", "2", "3", "5", "10", "11", "12", "13"}:
                score -= 50

            logger.debug(
                f"Avaliação golpe slot {i} '{move_name}': power={power}, type_id={type_id}, "
                f"category_id={category_id}, type_mult={type_mult}, score={score}"
            )

            if score > best_score:
                best_score = score
                best_slot = i

        logger.info(f"Melhor golpe escolhido: slot={best_slot}, score={best_score}")
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