"""
Script de Migração: JSON → SQLite

Converte pokedex_completa.json em banco de dados SQLite otimizado.
Estrutura:
- pokemon: dados base (ID, stats, altura, peso)
- types: tipos de cada Pokemon
- abilities: habilidades de cada Pokemon
- moves: movimentos aprendidos por nível com detalhes completos

Uso:
    python tools/json_to_sqlite.py
"""

import json
import sqlite3
import os
from pathlib import Path

def migrate_to_sqlite():
    project_root = Path(__file__).parent.parent
    json_path = project_root / 'data' / 'pokedex_completa.json'
    db_path = project_root / 'data' / 'pokedex.db'

    print("=" * 70)
    print("🔄 MIGRAÇÃO: JSON → SQLite")
    print("=" * 70)
    
    if not json_path.exists():
        print(f"❌ Erro: {json_path} não encontrado.")
        return False

    print(f"\n📂 Lendo: {json_path}")
    with open(json_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    print(f"   ✅ {len(data)} Pokémons carregados")

    # Remover DB antigo se existir para evitar duplicatas
    if db_path.exists():
        os.remove(db_path)
        print(f"   ✅ Banco anterior removido")

    print(f"\n💾 Criando banco de dados: {db_path}")
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # 1. Criar Tabelas com melhorias
    print("   📋 Criando tabelas...")
    
    cursor.execute('''
        CREATE TABLE pokemon (
            name TEXT PRIMARY KEY,
            id INTEGER UNIQUE NOT NULL,
            hp INTEGER NOT NULL,
            attack INTEGER NOT NULL,
            defense INTEGER NOT NULL,
            sp_attack INTEGER NOT NULL,
            sp_defense INTEGER NOT NULL,
            speed INTEGER NOT NULL,
            height REAL NOT NULL,
            weight REAL NOT NULL
        )
    ''')
    print("      ✅ Tabela 'pokemon' criada")

    cursor.execute('''
        CREATE TABLE types (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            pokemon_name TEXT NOT NULL,
            type TEXT NOT NULL,
            FOREIGN KEY(pokemon_name) REFERENCES pokemon(name),
            UNIQUE(pokemon_name, type)
        )
    ''')
    print("      ✅ Tabela 'types' criada")

    cursor.execute('''
        CREATE TABLE abilities (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            pokemon_name TEXT NOT NULL,
            ability TEXT NOT NULL,
            FOREIGN KEY(pokemon_name) REFERENCES pokemon(name),
            UNIQUE(pokemon_name, ability)
        )
    ''')
    print("      ✅ Tabela 'abilities' criada")

    cursor.execute('''
        CREATE TABLE moves (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            pokemon_name TEXT NOT NULL,
            level INTEGER NOT NULL,
            move_name TEXT NOT NULL,
            power INTEGER,
            accuracy INTEGER,
            type TEXT NOT NULL,
            category TEXT NOT NULL,
            priority INTEGER NOT NULL,
            pp INTEGER NOT NULL,
            FOREIGN KEY(pokemon_name) REFERENCES pokemon(name)
        )
    ''')
    print("      ✅ Tabela 'moves' criada")

    # Criar índices para melhor performance
    print("   🔍 Criando índices...")
    cursor.execute('CREATE INDEX idx_pokemon_id ON pokemon(id)')
    cursor.execute('CREATE INDEX idx_moves_pokemon ON moves(pokemon_name)')
    cursor.execute('CREATE INDEX idx_moves_level ON moves(level)')
    cursor.execute('CREATE INDEX idx_types_pokemon ON types(pokemon_name)')
    cursor.execute('CREATE INDEX idx_abilities_pokemon ON abilities(pokemon_name)')
    print("      ✅ Índices criados")

    # 2. Inserir Dados
    print(f"\n📥 Inserindo dados...")
    total_pokemon = len(data)
    total_moves = 0
    total_types = 0
    total_abilities = 0

    for idx, (name, info) in enumerate(data.items(), 1):
        if idx % 100 == 0:
            print(f"   Processados: {idx}/{total_pokemon}")
        
        # Inserir Pokémon
        try:
            cursor.execute('''
                INSERT INTO pokemon VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                name, info['id'], 
                info['base_stats']['hp'], info['base_stats']['attack'],
                info['base_stats']['defense'], info['base_stats']['sp_attack'],
                info['base_stats']['sp_defense'], info['base_stats']['speed'],
                info['height'], info['weight']
            ))
        except sqlite3.IntegrityError as e:
            print(f"   ⚠️  Erro ao inserir {name}: {e}")
            continue

        # Inserir Tipos
        for t in info.get('tipos', []):
            try:
                cursor.execute('INSERT INTO types (pokemon_name, type) VALUES (?, ?)', 
                             (name, t))
                total_types += 1
            except sqlite3.IntegrityError:
                pass  # Ignorar duplicatas

        # Inserir Habilidades
        for abi in info.get('abilities', []):
            try:
                cursor.execute('INSERT INTO abilities (pokemon_name, ability) VALUES (?, ?)', 
                             (name, abi))
                total_abilities += 1
            except sqlite3.IntegrityError:
                pass  # Ignorar duplicatas

        # Inserir Movimentos (agora em formato OBJETO)
        for level_str, moves_list in info.get('movimientos_por_nivel', {}).items():
            for move in moves_list:
                # Se move é OBJETO (novo formato)
                if isinstance(move, dict):
                    move_name = move.get('name')
                    power = move.get('power')
                    accuracy = move.get('accuracy', 100)
                    move_type = move.get('type', 'Normal')
                    category = move.get('category', 'Status')
                    priority = move.get('priority', 0)
                    pp = move.get('pp', 0)
                # Se move é ARRAY (formato antigo) - compatibilidade
                else:
                    move_name = move[0]
                    power = move[1]
                    accuracy = move[2]
                    move_type = move[3]
                    category = move[4]
                    priority = move[5]
                    pp = move[6]
                
                cursor.execute('''
                    INSERT INTO moves (pokemon_name, level, move_name, power, accuracy, type, category, priority, pp)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (name, int(level_str), move_name, power, accuracy, move_type, category, priority, pp))
                total_moves += 1

    conn.commit()
    conn.close()
    
    # Relatório final
    print("\n" + "=" * 70)
    print("📊 RELATÓRIO DE MIGRAÇÃO")
    print("=" * 70)
    print(f"✅ Pokémons inseridos: {total_pokemon}")
    print(f"✅ Tipos inseridos: {total_types}")
    print(f"✅ Habilidades inseridas: {total_abilities}")
    print(f"✅ Movimentos inseridos: {total_moves}")
    print(f"✅ Banco de dados: {db_path}")
    print(f"   Tamanho: {os.path.getsize(db_path) / 1024 / 1024:.2f} MB")
    print("=" * 70)
    print("✅ MIGRAÇÃO CONCLUÍDA COM SUCESSO!")
    print("=" * 70)
    return True

if __name__ == "__main__":
    migrate_to_sqlite()
