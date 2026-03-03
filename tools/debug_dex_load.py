from pathlib import Path
import json

project_root = Path.cwd()
dex_path = project_root / 'data' / 'dex.json'

print(f'Caminho: {dex_path}')
print(f'Existe? {dex_path.exists()}')

with open(dex_path, 'r', encoding='utf-8') as f:
    dex = json.load(f)

print(f'Total Pokemon: {len(dex)}')
bulb = dex['Bulbasaur']
print(f'\nBulbasaur:')
print(f'  Keys: {list(bulb.keys())}')
print(f'  Tem movimientos_por_nivel? {"movimientos_por_nivel" in bulb}')
moves = bulb.get('movimientos_por_nivel', {})
print(f'  Quantidade de niveis: {len(moves)}')
print(f'  Moves vazio? {len(moves) == 0}')
if moves:
    print(f'  Niveis: {list(moves.keys())[:5]}')
