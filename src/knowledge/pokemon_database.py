import json
from pathlib import Path
from loguru import logger


class PokemonDatabase:
    """Fornece dados de Pokémon, tipos e golpes para a BattleStrategy.

    Carrega tanto os arquivos legados (dex.json, tipos.json, movimentos.json)
    como os caches da PokeAPI (pokeapi_pokemon.json, pokeapi_moves.json) e
    uma matriz de eficácia de tipos (type_efficacy.json).
    """

    def __init__(self, data_path: str = "data"):
        self.data_dir = Path(data_path)

        # Bases legadas
        self.dex_legacy = self._load_json("dex.json")
        self.types_legacy = self._load_json("tipos.json")
        self.moves_legacy = self._load_json("movimentos.json")

        # Bases derivadas da PokeAPI
        self.pokeapi_pokemon = self._load_json("pokeapi_pokemon.json")
        self.pokeapi_moves = self._load_json("pokeapi_moves.json")
        self.type_efficacy = self._load_json("type_efficacy.json")

    def _load_json(self, filename: str):
        path = self.data_dir / filename
        if not path.exists():
            return {}
        try:
            with path.open("r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Erro ao carregar {filename}: {e}")
            return {}

    # ---------- Tipos / Fraquezas ----------

    def get_pokemon_types(self, pokemon_name: str):
        """Retorna lista de type_ids do Pokémon.

        Usa `pokeapi_pokemon.json` quando disponível, com fallback para `dex.json`.
        """
        if not pokemon_name:
            return []

        key = pokemon_name.strip().lower()
        data = self.pokeapi_pokemon.get(key)
        if data and "types" in data:
            return data["types"]

        # Fallback para dex antigo, tentando variações de nome
        legacy = (
            self.dex_legacy.get(pokemon_name)
            or self.dex_legacy.get(pokemon_name.capitalize())
            or self.dex_legacy.get(pokemon_name.lower())
        )
        if legacy:
            return legacy.get("tipos", [])

        return []

    def get_weaknesses(self, pokemon_name: str):
        """Retorna lista de type_ids ou nomes de tipos aos quais o Pokémon é fraco.

        Se `type_efficacy.json` estiver disponível, calcula a partir da matriz.
        Caso contrário, usa `tipos.json` legado.
        """
        if not pokemon_name:
            return []

        enemy_types = self.get_pokemon_types(pokemon_name)
        if enemy_types and self.type_efficacy:
            weak_to = set()
            for target_type in enemy_types:
                rels = self.type_efficacy.get(str(target_type), {})
                for atk_type, mult in rels.items():
                    try:
                        if float(mult) >= 2.0:
                            weak_to.add(str(atk_type))
                    except (TypeError, ValueError):
                        continue
            return list(weak_to)

        # Fallback para dados legados, se existirem
        legacy = (
            self.dex_legacy.get(pokemon_name)
            or self.dex_legacy.get(pokemon_name.capitalize())
            or self.dex_legacy.get(pokemon_name.lower())
        )
        if legacy:
            weaknesses = set()
            for p_type in legacy.get("tipos", []):
                type_info = self.types_legacy.get(p_type, {})
                weaknesses.update(type_info.get("fraquezas", []))
            return list(weaknesses)

        return []

    def get_type_multiplier(self, move_type_id, enemy_types):
        """Retorna multiplicador total de tipo (float) para um golpe.

        enemy_types é uma lista de type_ids (strings ou ints).
        """
        if not move_type_id or not enemy_types or not self.type_efficacy:
            return 1.0

        rels = self.type_efficacy.get(str(move_type_id), {})
        if not rels:
            return 1.0

        mult = 1.0
        for t in enemy_types:
            try:
                m = float(rels.get(str(t), 1.0) or 1.0)
            except (TypeError, ValueError):
                m = 1.0
            mult *= m

        return mult

    # ---------- Golpes ----------

    def get_move_data(self, move_name: str):
        """Retorna dados de um golpe em formato compatível com BattleStrategy.

        Formato esperado:
        {
            "type_id": <int ou str>,
            "power": <int>,
            "category_id": <int ou str>,
        }

        Tenta primeiro `pokeapi_moves.json` (chave em lower), depois `movimentos.json`
        legado (nome exato ou Title Case). Se nada encontrado, retorna dict vazio.
        """
        if not move_name:
            return {}

        key = move_name.strip().lower()

        # PokeAPI moves
        data = self.pokeapi_moves.get(key)
        if data:
            return {
                "type_id": data.get("type_id"),
                "power": data.get("power", 0),
                "category_id": data.get("category_id"),
            }

        # Fallback: base legada de movimentos
        legacy = self.moves_legacy.get(move_name) or self.moves_legacy.get(move_name.title())
        if legacy:
            return {
                "type_id": legacy.get("type_id") or legacy.get("tipo_id") or legacy.get("tipo"),
                "power": legacy.get("power", 0) or legacy.get("poder", 0),
                "category_id": legacy.get("category_id") or legacy.get("categoria_id") or legacy.get("categoria"),
            }

        logger.debug(f"Dados de golpe não encontrados para '{move_name}'")
        return {}
    
    def get_base_stats(self, pokemon_name: str):
        """Retorna stats base do Pokémon (HP, Attack, Defense, SpA, SpD, Speed).
        
        Args:
            pokemon_name: Nome do Pokémon
            
        Returns:
            Dict com keys: hp, attack, defense, special_attack, special_defense, speed
            Ou None se Pokémon não encontrado
        """
        if not pokemon_name:
            return None
        
        key = pokemon_name.strip().lower()
        
        # Tenta pokeapi_pokemon primeiro
        data = self.pokeapi_pokemon.get(key)
        if data and "stats" in data:
            stats = data["stats"]
            return {
                "hp": stats.get("hp", 0),
                "attack": stats.get("attack", 0),
                "defense": stats.get("defense", 0),
                "special_attack": stats.get("special-attack", 0),
                "special_defense": stats.get("special-defense", 0),
                "speed": stats.get("speed", 0)
            }
        
        # Fallback: dex legacy
        legacy = self.dex_legacy.get(key)
        if legacy and "stats" in legacy:
            stats = legacy["stats"]
            return {
                "hp": stats.get("hp", 0),
                "attack": stats.get("attack", 0),
                "defense": stats.get("defense", 0),
                "special_attack": stats.get("special_attack", 0) or stats.get("special-attack", 0),
                "special_defense": stats.get("special_defense", 0) or stats.get("special-defense", 0),
                "speed": stats.get("speed", 0)
            }
        
        logger.warning(f"Stats base não encontrados para '{pokemon_name}'")
        return None
    
    def estimate_stat(self, base_stat, level, iv=31, ev=252, nature=1.0):
        """Calcula stat real usando a fórmula de Pokémon.
        
        Args:
            base_stat: Stat base do Pokémon
            level: Nível atual
            iv: Individual Value (0-31, padrão 31 = pior caso)
            ev: Effort Value (0-252, padrão 252 = pior caso)
            nature: Multiplicador de nature (1.1 para +, 0.9 para -, 1.0 neutro)
            
        Returns:
            int: Stat calculado
        """
        return int(((base_stat * 2 + iv + (ev // 4)) * level / 100 + 5) * nature)
    
    def estimate_max_stats(self, pokemon_name: str, level: int):
        """Calcula stats máximos possíveis assumindo IVs/EVs perfeitos (Worst-Case Scenario).
        
        Este método é crítico para nunca subestimar o inimigo. Assume:
        - IVs máximos (31)
        - EVs máximos (252)
        - Nature favorável (+10%)
        
        Args:
            pokemon_name: Nome do Pokémon inimigo
            level: Nível do inimigo
            
        Returns:
            Dict com stats máximos: hp, attack, defense, special_attack, special_defense, speed
        """
        base_stats = self.get_base_stats(pokemon_name)
        if not base_stats:
            logger.warning(f"Stats base não encontrados para '{pokemon_name}' - usando valores médios")
            # Valores médios defensivos para não arriscar
            return {
                'hp': 100,
                'attack': 100,
                'defense': 100,
                'special_attack': 100,
                'special_defense': 100,
                'speed': 100
            }
        
        # Calcula com IVs/EVs máximos + nature favorável para cada stat
        return {
            'hp': self.estimate_stat(base_stats['hp'], level, iv=31, ev=252, nature=1.0),  # HP não tem nature
            'attack': self.estimate_stat(base_stats['attack'], level, iv=31, ev=252, nature=1.1),
            'defense': self.estimate_stat(base_stats['defense'], level, iv=31, ev=252, nature=1.1),
            'special_attack': self.estimate_stat(base_stats['special_attack'], level, iv=31, ev=252, nature=1.1),
            'special_defense': self.estimate_stat(base_stats['special_defense'], level, iv=31, ev=252, nature=1.1),
            'speed': self.estimate_stat(base_stats['speed'], level, iv=31, ev=252, nature=1.1)
        }
    
    def get_common_moves(self, pokemon_name: str):
        """Retorna lista de golpes comuns/prováveis que o Pokémon pode ter.
        
        Args:
            pokemon_name: Nome do Pokémon
            
        Returns:
            Lista de nomes de movimentos (strings)
        """
        if not pokemon_name:
            return []
        
        key = pokemon_name.strip().lower()
        
        # Tenta pokeapi_pokemon primeiro
        data = self.pokeapi_pokemon.get(key)
        if data and "moves" in data:
            # Retorna movimentos comuns (primeiros 8)
            return data["moves"][:8]
        
        # Fallback: movimentos genéricos por tipo
        types = self.get_pokemon_types(pokemon_name)
        common_moves = []
        
        if "electric" in types or 10 in types:
            common_moves = ["thunderbolt", "thunder", "volt switch", "wild charge"]
        elif "water" in types or 11 in types:
            common_moves = ["surf", "hydro pump", "scald", "aqua jet"]
        elif "fire" in types or 10 in types:
            common_moves = ["flamethrower", "fire blast", "flare blitz", "fire punch"]
        elif "grass" in types or 12 in types:
            common_moves = ["energy ball", "leaf storm", "giga drain", "wood hammer"]
        elif "fighting" in types or 2 in types:
            common_moves = ["close combat", "aura sphere", "drain punch", "mach punch"]
        else:
            # Movimentos genéricos
            common_moves = ["return", "hyper beam", "body slam", "quick attack"]
        
        return common_moves
    
    def get_priority_moves(self, pokemon_name: str):
        """Retorna lista de golpes de prioridade que o Pokémon pode ter.
        
        Args:
            pokemon_name: Nome do Pokémon
            
        Returns:
            Lista de nomes de movimentos com prioridade > 0
        """
        if not pokemon_name:
            return []
        
        # Lista de movimentos de prioridade comuns
        priority_moves = [
            "quick attack", "aqua jet", "mach punch", "bullet punch",
            "ice shard", "shadow sneak", "vacuum wave", "extreme speed",
            "sucker punch", "accelerock", "water shuriken"
        ]
        
        # Verifica se o Pokémon tem acesso a algum desses
        common_moves = self.get_common_moves(pokemon_name)
        
        return [m for m in priority_moves if m in [cm.lower() for cm in common_moves]]

