import sqlite3
from pathlib import Path
from functools import lru_cache


class PokemonDatabase:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(PokemonDatabase, cls).__new__(cls)
            cls._instance.db_path = Path(__file__).parent.parent.parent / 'data' / 'pokedex.db'
        return cls._instance

    @lru_cache(maxsize=64)
    def get_pokemon_data(self, name):
        """Busca otimizada no SQLite com persistência de tipos e habilidades."""
        if not name:
            return None
        name = name.capitalize()

        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()

                cursor.execute("SELECT * FROM pokemon WHERE name = ?", (name,))
                row = cursor.fetchone()
                if not row:
                    return None
                pokemon = dict(row)

                cursor.execute("SELECT type FROM types WHERE pokemon_name = ?", (name,))
                pokemon['tipos'] = [r[0] for r in cursor.fetchall()]

                cursor.execute("SELECT ability FROM abilities WHERE pokemon_name = ?", (name,))
                pokemon['abilities'] = [r[0] for r in cursor.fetchall()]

                cursor.execute("SELECT * FROM moves WHERE pokemon_name = ?", (name,))
                moves_rows = cursor.fetchall()

                moves_by_level = {}
                for m in moves_rows:
                    lvl = str(m['level'])
                    if lvl not in moves_by_level:
                        moves_by_level[lvl] = []
                    moves_by_level[lvl].append([
                        m['move_name'], m['power'], m['accuracy'],
                        m['type'], m['category'], m['priority'], m['pp']
                    ])

                pokemon['movimientos_por_nivel'] = moves_by_level
                return pokemon
        except sqlite3.Error as e:
            print(f"Critico Database: {e}")
            return None

    def get_all_pokemon_names(self):
        """Retorna todos os nomes oficiais para validação de OCR."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT name FROM pokemon")
                return [r[0] for r in cursor.fetchall()]
        except sqlite3.Error:
            return []

