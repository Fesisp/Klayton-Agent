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
