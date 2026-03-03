"""
PokemonDatabase: Interface SQLite com Singleton + LRU Cache

Padrão Singleton garante uma única instância em toda a aplicação.
LRU Cache reduz I/O ao manter dados recentes em memória.

Performance:
- Primeiro acesso: ~5ms (SQLite)
- Acessos posteriores: <1ms (cache)
"""

import sqlite3
from pathlib import Path
from functools import lru_cache
from typing import Optional, Dict, List, Any

class PokemonDatabase:
    """Singleton com LRU Cache para dados de Pokémon."""
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(PokemonDatabase, cls).__new__(cls)
            cls._instance.db_path = Path(__file__).parent.parent.parent / 'data' / 'pokedex.db'
            
            if not cls._instance.db_path.exists():
                raise FileNotFoundError(f"❌ Banco de dados não encontrado: {cls._instance.db_path}")
        
        return cls._instance

    @lru_cache(maxsize=128)
    def get_pokemon_data(self, name: str) -> Optional[Dict[str, Any]]:
        """
        Busca otimizada com LRU Cache.
        
        Primeiras 128 buscas únicas são cacheadas em memória.
        Acessos posteriores retornam em <1ms sem I/O.
        
        Args:
            name: Nome do Pokémon (case-insensitive)
        
        Returns:
            Dict com dados completos ou None
        """
        if not name:
            return None
        
        normalized_name = name.strip().title()
        
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                
                # Buscar dados base
                cursor.execute("SELECT * FROM pokemon WHERE name = ?", (normalized_name,))
                row = cursor.fetchone()
                
                if not row:
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
                
                # Queries em batch para performance
                cursor.execute(
                    "SELECT type FROM types WHERE pokemon_name = ? ORDER BY type", 
                    (normalized_name,)
                )
                pokemon['tipos'] = [r['type'] for r in cursor.fetchall()]
                
                cursor.execute(
                    "SELECT ability FROM abilities WHERE pokemon_name = ? ORDER BY ability", 
                    (normalized_name,)
                )
                pokemon['abilities'] = [r['ability'] for r in cursor.fetchall()]

                # Buscar movimentos organizados por nível
                cursor.execute("""
                    SELECT level, move_name, power, accuracy, type, category, priority, pp 
                    FROM moves 
                    WHERE pokemon_name = ? 
                    ORDER BY level ASC, move_name ASC
                """, (normalized_name,))
                
                moves_by_level = {}
                for row in cursor.fetchall():
                    lvl = str(row['level'])
                    if lvl not in moves_by_level:
                        moves_by_level[lvl] = []
                    
                    # Formato OBJETO (novo)
                    moves_by_level[lvl].append({
                        "name": row['move_name'],
                        "power": row['power'],
                        "accuracy": row['accuracy'],
                        "type": row['type'],
                        "category": row['category'],
                        "priority": row['priority'],
                        "pp": row['pp']
                    })
                
                pokemon['movimientos_por_nivel'] = moves_by_level
                return pokemon
                
        except sqlite3.Error as e:
            print(f"❌ Erro Database: {e}")
            return None

    @lru_cache(maxsize=128)
    def get_pokemon_stats(self, name: str) -> Optional[Dict[str, int]]:
        """Retorna apenas base_stats (cacheado)."""
        pokemon = self.get_pokemon_data(name)
        return pokemon['base_stats'] if pokemon else None

    @lru_cache(maxsize=64)
    def get_pokemon_types(self, name: str) -> List[str]:
        """Retorna tipos de um Pokémon (cacheado)."""
        pokemon = self.get_pokemon_data(name)
        return pokemon['tipos'] if pokemon else []

    @lru_cache(maxsize=64)
    def get_pokemon_abilities(self, name: str) -> List[str]:
        """Retorna habilidades de um Pokémon (cacheado)."""
        pokemon = self.get_pokemon_data(name)
        return pokemon['abilities'] if pokemon else []

    def search_by_type(self, type_name: str) -> List[str]:
        """Busca Pokémons por tipo (não cacheado - resultado dinâmico)."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "SELECT DISTINCT pokemon_name FROM types WHERE type = ? ORDER BY pokemon_name",
                    (type_name.capitalize(),)
                )
                return [r[0] for r in cursor.fetchall()]
        except sqlite3.Error as e:
            print(f"❌ Erro ao buscar por tipo: {e}")
            return []

    def search_by_ability(self, ability_name: str) -> List[str]:
        """Busca Pokémons por habilidade."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "SELECT DISTINCT pokemon_name FROM abilities WHERE ability = ? ORDER BY pokemon_name",
                    (ability_name.capitalize(),)
                )
                return [r[0] for r in cursor.fetchall()]
        except sqlite3.Error as e:
            print(f"❌ Erro ao buscar por habilidade: {e}")
            return []

    def search_by_move(self, move_name: str) -> List[str]:
        """Busca Pokémons que aprendem um move específico."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "SELECT DISTINCT pokemon_name FROM moves WHERE move_name = ? ORDER BY pokemon_name",
                    (move_name,)
                )
                return [r[0] for r in cursor.fetchall()]
        except sqlite3.Error as e:
            print(f"❌ Erro ao buscar por move: {e}")
            return []

    def get_all_pokemon(self) -> List[str]:
        """Retorna lista de todos os Pokémons."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT name FROM pokemon ORDER BY id")
                return [r[0] for r in cursor.fetchall()]
        except sqlite3.Error as e:
            print(f"❌ Erro ao listar Pokémons: {e}")
            return []

    def get_total_pokemon_count(self) -> int:
        """Retorna total de Pokémons."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT COUNT(*) as count FROM pokemon")
                return cursor.fetchone()[0]
        except sqlite3.Error as e:
            print(f"❌ Erro ao contar Pokémons: {e}")
            return 0

    def validate_pokemon(self, name: str) -> bool:
        """Verifica se um Pokémon existe."""
        return self.get_pokemon_data(name) is not None

    def clear_cache(self):
        """Limpa o cache LRU (usar com cuidado!)."""
        self.get_pokemon_data.cache_clear()
        self.get_pokemon_stats.cache_clear()
        self.get_pokemon_types.cache_clear()
        self.get_pokemon_abilities.cache_clear()
        print("✅ Cache limpo")

    def cache_info(self):
        """Retorna informações do cache."""
        return {
            "pokemon_data": self.get_pokemon_data.cache_info(),
            "pokemon_stats": self.get_pokemon_stats.cache_info(),
            "pokemon_types": self.get_pokemon_types.cache_info(),
            "pokemon_abilities": self.get_pokemon_abilities.cache_info()
        }


# Exemplo de uso
if __name__ == "__main__":
    db = PokemonDatabase()
    
    print("=" * 70)
    print("🔍 TESTE: PokemonDatabase com Singleton + LRU Cache")
    print("=" * 70)
    
    # Teste 1: Primeira busca (SQLite)
    print("\n⏱️  Primeira busca - Bulbasaur (do SQLite):")
    import time
    start = time.time()
    pokemon = db.get_pokemon_data("Bulbasaur")
    elapsed = time.time() - start
    print(f"   Tempo: {elapsed*1000:.2f}ms")
    print(f"   ✅ {pokemon['name']} - ID: {pokemon['id']}")
    
    # Teste 2: Segunda busca (cache)
    print("\n⚡ Segunda busca - Bulbasaur (do cache):")
    start = time.time()
    pokemon = db.get_pokemon_data("Bulbasaur")
    elapsed = time.time() - start
    print(f"   Tempo: {elapsed*1000:.3f}ms (muito mais rápido!)")
    
    # Teste 3: Singleton
    print("\n🔐 Teste Singleton:")
    db2 = PokemonDatabase()
    print(f"   db is db2: {db is db2} (mesma instância)")
    
    # Teste 4: Cache info
    print("\n📊 Info do Cache:")
    info = db.cache_info()
    for key, val in info.items():
        print(f"   {key}: hits={val.hits}, misses={val.misses}, size={val.currsize}/{val.maxsize}")
    
    print("\n" + "=" * 70)

