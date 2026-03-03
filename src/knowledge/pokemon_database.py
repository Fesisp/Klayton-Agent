"""
PokemonDatabase: Interface SQLite para Dados de Pokémon

Fornece acesso rápido aos dados da Pokedex via SQLite ao invés de carregar
JSON pesado na memória.

Métodos principais:
- get_pokemon_data(name): Retorna dados completos de um Pokémon
- get_pokemon_moves(name): Retorna apenas movimentos aprendidos
- search_by_type(type_name): Busca Pokémons por tipo
- get_pokemon_stats(name): Retorna base_stats
"""

import sqlite3
from pathlib import Path
from typing import Optional, Dict, List, Any

class PokemonDatabase:
    def __init__(self):
        self.db_path = Path(__file__).parent.parent.parent / 'data' / 'pokedex.db'
        
        if not self.db_path.exists():
            raise FileNotFoundError(f"❌ Banco de dados não encontrado: {self.db_path}")
    
    def _get_connection(self):
        """Cria conexão com o banco de dados."""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def get_pokemon_data(self, name: str) -> Optional[Dict[str, Any]]:
        """
        Busca todos os dados de um Pokémon específico no SQLite.
        
        Args:
            name: Nome do Pokémon (case-insensitive)
        
        Returns:
            Dict com: id, tipos, abilities, base_stats, altura, peso, movimientos_por_nivel
            None se Pokémon não encontrado
        """
        conn = self._get_connection()
        cursor = conn.cursor()

        # Normalizar nome
        normalized_name = name.strip().title()

        # Buscar dados base
        cursor.execute("SELECT * FROM pokemon WHERE name = ?", (normalized_name,))
        row = cursor.fetchone()
        
        if not row:
            conn.close()
            return None

        pokemon = {
            "name": row['name'],
            "id": row['id'],
            "base_stats": {
                "hp": row['hp'],
                "attack": row['attack'],
                "defense": row['defense'],
                "sp_attack": row['sp_attack'],
                "sp_defense": row['sp_defense'],
                "speed": row['speed']
            },
            "height": row['height'],
            "weight": row['weight'],
            "tipos": [],
            "abilities": [],
            "movimientos_por_nivel": {}
        }
        
        # Buscar Tipos
        cursor.execute("SELECT type FROM types WHERE pokemon_name = ? ORDER BY type", 
                      (normalized_name,))
        pokemon['tipos'] = [r['type'] for r in cursor.fetchall()]
        
        # Buscar Habilidades
        cursor.execute("SELECT ability FROM abilities WHERE pokemon_name = ? ORDER BY ability", 
                      (normalized_name,))
        pokemon['abilities'] = [r['ability'] for r in cursor.fetchall()]

        # Buscar Movimentos organizados por nível
        cursor.execute("""
            SELECT level, move_name, power, accuracy, type, category, priority, pp 
            FROM moves 
            WHERE pokemon_name = ? 
            ORDER BY level ASC, move_name ASC
        """, (normalized_name,))
        
        for row in cursor.fetchall():
            level_str = str(row['level'])
            if level_str not in pokemon['movimientos_por_nivel']:
                pokemon['movimientos_por_nivel'][level_str] = []
            
            # Formato OBJETO (novo, recomendado)
            pokemon['movimientos_por_nivel'][level_str].append({
                "name": row['move_name'],
                "power": row['power'],
                "accuracy": row['accuracy'],
                "type": row['type'],
                "category": row['category'],
                "priority": row['priority'],
                "pp": row['pp']
            })
        
        conn.close()
        return pokemon

    def get_pokemon_moves(self, name: str, level: Optional[int] = None) -> Dict[str, List[Dict]]:
        """
        Retorna movimentos aprendidos por um Pokémon.
        
        Args:
            name: Nome do Pokémon
            level: Nível específico (None = todos os níveis)
        
        Returns:
            Dict: {nível: [movimentos]}
        """
        conn = self._get_connection()
        cursor = conn.cursor()
        normalized_name = name.strip().title()

        if level is not None:
            cursor.execute("""
                SELECT level, move_name, power, accuracy, type, category, priority, pp
                FROM moves
                WHERE pokemon_name = ? AND level = ?
                ORDER BY move_name
            """, (normalized_name, level))
        else:
            cursor.execute("""
                SELECT level, move_name, power, accuracy, type, category, priority, pp
                FROM moves
                WHERE pokemon_name = ?
                ORDER BY level ASC, move_name ASC
            """, (normalized_name,))

        moves_by_level = {}
        for row in cursor.fetchall():
            level_str = str(row['level'])
            if level_str not in moves_by_level:
                moves_by_level[level_str] = []
            
            moves_by_level[level_str].append({
                "name": row['move_name'],
                "power": row['power'],
                "accuracy": row['accuracy'],
                "type": row['type'],
                "category": row['category'],
                "priority": row['priority'],
                "pp": row['pp']
            })

        conn.close()
        return moves_by_level

    def get_pokemon_stats(self, name: str) -> Optional[Dict[str, int]]:
        """Retorna apenas os base_stats de um Pokémon."""
        pokemon = self.get_pokemon_data(name)
        return pokemon['base_stats'] if pokemon else None

    def get_pokemon_types(self, name: str) -> List[str]:
        """Retorna tipos de um Pokémon."""
        pokemon = self.get_pokemon_data(name)
        return pokemon['tipos'] if pokemon else []

    def get_pokemon_abilities(self, name: str) -> List[str]:
        """Retorna habilidades de um Pokémon."""
        pokemon = self.get_pokemon_data(name)
        return pokemon['abilities'] if pokemon else []

    def search_by_type(self, type_name: str) -> List[str]:
        """
        Busca todos os Pokémons de um tipo específico.
        
        Args:
            type_name: Nome do tipo (ex: "Fire", "Water")
        
        Returns:
            Lista de nomes de Pokémons
        """
        conn = self._get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT DISTINCT pokemon_name 
            FROM types 
            WHERE type = ? 
            ORDER BY pokemon_name
        """, (type_name.capitalize(),))
        
        results = [r['pokemon_name'] for r in cursor.fetchall()]
        conn.close()
        return results

    def search_by_ability(self, ability_name: str) -> List[str]:
        """Busca Pokémons por habilidade."""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT DISTINCT pokemon_name 
            FROM abilities 
            WHERE ability = ? 
            ORDER BY pokemon_name
        """, (ability_name.capitalize(),))
        
        results = [r['pokemon_name'] for r in cursor.fetchall()]
        conn.close()
        return results

    def search_by_move(self, move_name: str) -> List[str]:
        """Busca Pokémons que podem aprender um move específico."""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT DISTINCT pokemon_name 
            FROM moves 
            WHERE move_name = ? 
            ORDER BY pokemon_name
        """, (move_name,))
        
        results = [r['pokemon_name'] for r in cursor.fetchall()]
        conn.close()
        return results

    def get_all_pokemon(self) -> List[str]:
        """Retorna lista de todos os Pokémons."""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        cursor.execute("SELECT name FROM pokemon ORDER BY id")
        results = [r['name'] for r in cursor.fetchall()]
        conn.close()
        return results

    def get_total_pokemon_count(self) -> int:
        """Retorna total de Pokémons no banco."""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        cursor.execute("SELECT COUNT(*) as count FROM pokemon")
        count = cursor.fetchone()['count']
        conn.close()
        return count

    def validate_pokemon(self, name: str) -> bool:
        """Verifica se um Pokémon existe no banco."""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        normalized_name = name.strip().title()
        cursor.execute("SELECT COUNT(*) as count FROM pokemon WHERE name = ?", 
                      (normalized_name,))
        exists = cursor.fetchone()['count'] > 0
        conn.close()
        return exists


# Exemplo de uso
if __name__ == "__main__":
    db = PokemonDatabase()
    
    print("=" * 70)
    print("🔍 TESTE DA POKEDEX SQLite")
    print("=" * 70)
    
    # Teste 1: Buscar Pokémon completo
    pokemon = db.get_pokemon_data("Bulbasaur")
    if pokemon:
        print(f"\n✅ Pokémon encontrado: {pokemon['name']}")
        print(f"   ID: {pokemon['id']}")
        print(f"   Tipos: {pokemon['tipos']}")
        print(f"   Abilities: {pokemon['abilities']}")
        print(f"   HP: {pokemon['base_stats']['hp']}")
        if pokemon['movimientos_por_nivel'].get('1'):
            move = pokemon['movimientos_por_nivel']['1'][0]
            print(f"   Move Nv1: {move['name']} (Power: {move['power']})")
    
    # Teste 2: Contar total
    total = db.get_total_pokemon_count()
    print(f"\n✅ Total de Pokémons: {total}")
    
    # Teste 3: Buscar por tipo
    fire_types = db.search_by_type("Fire")
    print(f"✅ Pokémons Fire: {len(fire_types)} encontrados")
    if fire_types:
        print(f"   Exemplos: {', '.join(fire_types[:3])}")
    
    print("\n" + "=" * 70)

