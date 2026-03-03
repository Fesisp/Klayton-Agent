"""
Debug: Testar processamento de 1 Pokemon
"""
import json
from pathlib import Path

project_root = Path(__file__).parent.parent
dex_path = project_root / 'data' / 'dex.json'

# Carregar dex.json
with open(dex_path, 'r', encoding='utf-8') as f:
    dex_base = json.load(f)

# Pegar Bulbasaur
bulbasaur_data = dex_base['Bulbasaur']

print("Bulbasaur do dex.json:")
print(f"  Tem 'movimientos_por_nivel'? {'movimientos_por_nivel' in bulbasaur_data}")
print(f"  Tipo do campo: {type(bulbasaur_data.get('movimientos_por_nivel'))}")
print(f"  Quantidade de níveis: {len(bulbasaur_data.get('movimientos_por_nivel', {}))}")
print(f"  Níveis: {list(bulbasaur_data.get('movimientos_por_nivel', {}).keys())[:5]}")

# Simular o loop
moves_by_level = bulbasaur_data.get('movimientos_por_nivel', {})
print(f"\nmoves_by_level: {type(moves_by_level)}")
print(f"É vazio? {len(moves_by_level) == 0}")
print(f"Items: {list(moves_by_level.items())[:2]}")

# Simular processamento
movimientos_por_nivel = {}
for level, moves_list in moves_by_level.items():
    print(f"\nProcessando nível {level}:")
    print(f"  Moves: {moves_list}")
    movimientos_por_nivel[level] = []
    for move_info in moves_list:
        print(f"    Move: {move_info}")

print(f"\nResultado final: {len(movimientos_por_nivel)} níveis")
