import csv
import json
import os
from pathlib import Path

# === CONFIGURAÇÃO DE CAMINHOS ===
# Ajuste se a pasta pokeapi estiver em outro lugar
POKEAPI_ROOT = Path(__file__).resolve().parents[2] / "pokeapi" / "data" / "v2" / "csv"
OUTPUT_FILE = Path(__file__).resolve().parents[1] / "data" / "dex.json"

def load_csv(filename):
    path = POKEAPI_ROOT / filename
    if not path.exists():
        print(f"ERRO: Arquivo não encontrado: {path}")
        return []
    with open(path, 'r', encoding='utf-8') as f:
        return list(csv.DictReader(f))

def to_title(text):
    """Converte 'solar-beam' para 'Solar Beam'"""
    return text.replace('-', ' ').title()

def save_ordered_compact_dex(pokemon_list, data, output_file):
    """
    Salva o JSON respeitando a ordem da lista (ID) e mantendo formatação compacta.
    """
    print(f"Salvando {len(pokemon_list)} Pokémons em ordem correta...")
    
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write("{\n")
        
        count = 0
        total = len(pokemon_list)
        
        for p_name in pokemon_list:
            p_data = data.get(p_name)
            if not p_data: continue
            
            count += 1
            
            # Cabeçalho do Pokémon
            f.write(f'  "{p_name}": {{\n')
            
            # Tipos (Compacto em uma linha)
            tipos_str = json.dumps(p_data["tipos"], ensure_ascii=False)
            f.write(f'    "tipos": {tipos_str},\n')
            
            # Movimentos (Compacto por nível)
            f.write('    "movimentos_por_nivel": {\n')
            
            moves = p_data["movimentos_por_nivel"]
            # Ordenar níveis numericamente (1, 2, 10...)
            sorted_levels = sorted(moves.keys(), key=lambda x: int(x))
            
            for j, lvl in enumerate(sorted_levels):
                move_list = moves[lvl]
                # Gera lista compacta: [["Tackle", 40], ["Growl", null]]
                move_list_str = json.dumps(move_list, ensure_ascii=False)
                
                # Vírgula se não for o último nível
                comma = "," if j < len(sorted_levels) - 1 else ""
                f.write(f'      "{lvl}": {move_list_str}{comma}\n')
            
            f.write('    }\n')
            
            # Vírgula se não for o último Pokémon do arquivo
            comma = "," if count < total else ""
            f.write(f'  }}{comma}\n')
            
        f.write("}")
    print(f"Arquivo salvo com sucesso em: {output_file}")

def main():
    print("--- Gerando DEX Completa (1-809) Ordenada ---")

    # 1. Carregar CSVs
    print("Carregando CSVs do PokeAPI...")
    pokemon_csv = load_csv("pokemon.csv")
    moves_csv = load_csv("moves.csv")
    types_csv = load_csv("types.csv")
    pokemon_types_csv = load_csv("pokemon_types.csv")
    pokemon_moves_csv = load_csv("pokemon_moves.csv")

    if not pokemon_csv:
        print("Falha: CSVs não encontrados.")
        return

    # 2. Mapeamentos
    print("Criando índices...")
    type_map = {row['id']: to_title(row['identifier']) for row in types_csv}
    
    move_map = {}
    for row in moves_csv:
        power = row['power']
        move_map[row['id']] = {
            "name": to_title(row['identifier']),
            "power": int(power) if power and power != '' else None
        }

    poke_types_map = {}
    for row in pokemon_types_csv:
        pid = row['pokemon_id']
        tid = row['type_id']
        if pid not in poke_types_map: poke_types_map[pid] = []
        poke_types_map[pid].append(type_map.get(tid, "Unknown"))

    # 3. Processar Movimentos
    print("Processando movimentos (pode demorar)...")
    temp_moves = {}
    
    for row in pokemon_moves_csv:
        pid = row['pokemon_id']
        if int(pid) > 809: continue # Limite Gen 7
        
        method = row['pokemon_move_method_id']
        if method != '1': continue # 1 = Level up
        
        ver_group = int(row['version_group_id'])
        level = int(row['level'])
        
        # Corrige Level 0 para 1 (Golpes iniciais)
        if level == 0: level = 1
        
        move_id = row['move_id']

        if pid not in temp_moves: temp_moves[pid] = {}
        if ver_group not in temp_moves[pid]: temp_moves[pid][ver_group] = []
        
        temp_moves[pid][ver_group].append({"lvl": level, "id": move_id})

    # 4. Construir Dados
    final_data = {}
    ordered_names = [] # Para manter a ordem correta (1, 2, 3...)

    for row in pokemon_csv:
        pid = row['id']
        
        # Limite Gen 7
        if int(pid) > 809: break 
        
        # Ignorar formas alternativas (IDs > 10000)
        if int(pid) >= 10000: continue

        # Formatar Nome
        p_name = to_title(row['identifier'])
        if p_name.endswith("-m"): p_name = p_name[:-2] + "♂"
        elif p_name.endswith("-f"): p_name = p_name[:-2] + "♀"
        
        ordered_names.append(p_name)

        # Tipos
        p_types = poke_types_map.get(pid, [])

        # Movimentos (Pegar versão mais recente)
        moves_final = {}
        
        if pid in temp_moves:
            # Pega a geração mais recente disponível para este pokemon
            latest_version = max(temp_moves[pid].keys())
            raw_moves = temp_moves[pid][latest_version]
            
            # Ordena por nível
            raw_moves.sort(key=lambda x: x['lvl'])

            for m in raw_moves:
                lvl_key = str(m['lvl'])
                move_data = move_map.get(m['id'])
                if not move_data: continue

                entry = [move_data['name'], move_data['power']]
                
                if lvl_key not in moves_final:
                    moves_final[lvl_key] = []
                
                # Evita duplicatas
                if entry not in moves_final[lvl_key]:
                    moves_final[lvl_key].append(entry)

        final_data[p_name] = {
            "tipos": p_types,
            "movimentos_por_nivel": moves_final
        }

    # 5. Salvar
    save_ordered_compact_dex(ordered_names, final_data, OUTPUT_FILE)

if __name__ == "__main__":
    main()