import json

with open('data/dex.json', 'r', encoding='utf-8') as f:
    dex = json.load(f)

bulb = dex['Bulbasaur']
keys = list(bulb.keys())

print('Keys detalhadas:')
for k in keys:
    print(f'  Key: {repr(k)}')
    print(f'  Type: {type(bulb[k]).__name__}')
    if k == 'movimientos_por_nivel' or 'movimiento' in k:
        print(f'  ** Esta é a key de moves!')
        print(f'  Conteudo: {type(bulb[k])} com {len(bulb[k])} itens')
    print()

# Tentar acessar diretamente
print('\nTentando acessar:')
print(f'  bulb["movimientos_por_nivel"]: {bulb.get("movimientos_por_nivel", "NAO ENCONTRADO")}')
print(f'  bulb[keys[1]]: {type(bulb[keys[1]])} com {len(bulb[keys[1]])} itens')
