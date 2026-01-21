import json
import os
from pathlib import Path

from loguru import logger


"""
Script para gerar JSONs de apoio ao bot a partir do repo Fesisp/pokeapi.

Estrutura esperada do diretório (ajuste se seu clone estiver em outro caminho):

PokeBot_Pro/
  tools/
    build_pokeapi_jsons.py
  ..
../pokeapi/   <- clone de https://github.com/Fesisp/pokeapi
  data/
    pokemon.json
    moves.json

Se seus arquivos tiverem outro formato/nome, ajuste as constantes abaixo.
"""

# Caminho relativo padrão para o clone do pokeapi
POKEAPI_ROOT = Path(__file__).resolve().parents[2] / "pokeapi"
DATA_DIR = Path(__file__).resolve().parents[1] / "data"

# Fontes reais no repo pokeapi (CSV em data/v2/csv)
CSV_DIR = POKEAPI_ROOT / "data" / "v2" / "csv"
POKEMON_SOURCE = CSV_DIR / "pokemon.csv"
MOVES_SOURCE = CSV_DIR / "moves.csv"
POKEMON_TYPES_SOURCE = CSV_DIR / "pokemon_types.csv"
MOVE_META_SOURCE = CSV_DIR / "move_meta.csv"
TYPE_EFFICACY_SOURCE = CSV_DIR / "type_efficacy.csv"

POKEMON_OUT = DATA_DIR / "pokeapi_pokemon.json"
MOVES_OUT = DATA_DIR / "pokeapi_moves.json"


def load_csv(path: Path):
    import csv

    if not path.exists():
        logger.error(f"Arquivo não encontrado: {path}")
        return None

    with path.open("r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        return list(reader)


def build_pokemon_index(pokemon_rows, pokemon_types_rows):
    """Constrói índice de Pokémon com tipos básicos a partir dos CSVs oficiais."""

    # Mapa id -> nome
    id_to_name = {row["id"]: row["identifier"] for row in pokemon_rows}

    # tipos por id (até 2 tipos)
    types_by_id = {}
    for row in pokemon_types_rows:
        pid = row["pokemon_id"]
        type_id = row["type_id"]
        types_by_id.setdefault(pid, []).append(type_id)

    # Precisaríamos mapear type_id -> nome de tipo; para simplificar aqui, guardamos apenas ids numéricos
    index = {}
    for pid, name in id_to_name.items():
        types = types_by_id.get(pid, [])
        index[name] = {
            "types": types,
        }
    return index


def build_moves_index(move_rows, move_meta_rows):
    """Constrói índice de golpes a partir dos CSVs oficiais (moves + move_meta)."""

    # move_id -> meta
    meta_by_move_id = {row["move_id"]: row for row in move_meta_rows}

    index = {}
    for row in move_rows:
        move_id = row["id"]
        name = row["identifier"]
        meta = meta_by_move_id.get(move_id, {})

        move_type = row.get("type_id")  # id numérico; pode ser mapeado para nome depois
        power = meta.get("power") or 0
        accuracy = meta.get("accuracy") or 100
        category = meta.get("meta_category_id") or "unknown"

        # converter power/accuracy para int se possível
        try:
            power = int(power) if power not in (None, "") else 0
        except ValueError:
            power = 0
        try:
            accuracy = int(accuracy) if accuracy not in (None, "") else 100
        except ValueError:
            accuracy = 100

        index[name] = {
            "type_id": move_type,
            "power": power,
            "accuracy": accuracy,
            "category_id": category,
        }
    return index


def main():
    logger.info(f"Usando repo pokeapi em: {POKEAPI_ROOT}")
    if not POKEAPI_ROOT.exists():
        logger.error("Diretório pokeapi não encontrado. Clone https://github.com/Fesisp/pokeapi como pasta irmã de PokeBot_Pro.")
        return

    DATA_DIR.mkdir(parents=True, exist_ok=True)

    pokemon_rows = load_csv(POKEMON_SOURCE)
    moves_rows = load_csv(MOVES_SOURCE)
    pokemon_types_rows = load_csv(POKEMON_TYPES_SOURCE)
    move_meta_rows = load_csv(MOVE_META_SOURCE)

    if None in (pokemon_rows, moves_rows, pokemon_types_rows, move_meta_rows):
        logger.error("Falha ao carregar CSVs fonte do pokeapi.")
        return

    pokemon_index = build_pokemon_index(pokemon_rows, pokemon_types_rows)
    moves_index = build_moves_index(moves_rows, move_meta_rows)

    with POKEMON_OUT.open("w", encoding="utf-8") as f:
        json.dump(pokemon_index, f, ensure_ascii=False, indent=2)
    logger.info(f"Salvo índice de Pokémon em {POKEMON_OUT}")

    with MOVES_OUT.open("w", encoding="utf-8") as f:
        json.dump(moves_index, f, ensure_ascii=False, indent=2)
    logger.info(f"Salvo índice de golpes em {MOVES_OUT}")


if __name__ == "__main__":
    main()
