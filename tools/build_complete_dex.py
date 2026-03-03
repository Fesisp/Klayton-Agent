"""
Script Final: Pokedex Completa 100% PokeAPI (Gen 1-7)

Busca TODOS os dados diretamente da PokeAPI sem depender de arquivos locais.
Processa Pokemon ID 1-809 (Gerações 1-7).

Uso:
    python tools/build_complete_dex.py
"""

import json
import time
import requests
from pathlib import Path

class CompleteDexBuilder:
    def __init__(self):
        self.project_root = Path(__file__).parent.parent
        self.output_path = self.project_root / 'data' / 'pokedex_completa.json'
        self.temp_path = self.project_root / 'data' / 'pokedex_temp.json'
        
        self.request_count = 0
        self.request_timestamp = time.time()
        self.moves_cache = {}
        
    def rate_limit_check(self):
        """Respeita o rate limit de 100 requests/min da PokeAPI."""
        self.request_count += 1
        if self.request_count >= 100:
            elapsed = time.time() - self.request_timestamp
            if elapsed < 60:
                wait_time = 60 - elapsed
                print(f"⏸️  Aguardando {wait_time:.0f}s (rate limit)...")
                time.sleep(wait_time)
            self.request_count = 0
            self.request_timestamp = time.time()
    
    def fetch_pokemon_data(self, pokemon_id):
        """Busca dados completos de um Pokémon na PokeAPI por ID."""
        try:
            self.rate_limit_check()
            url = f"https://pokeapi.co/api/v2/pokemon/{pokemon_id}"
            response = requests.get(url, timeout=15)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            print(f"   ⚠️  Erro ao buscar Pokemon ID {pokemon_id}: {e}")
            return None
    
    def fetch_move_data(self, move_name):
        """Busca dados de um move na PokeAPI."""
        try:
            self.rate_limit_check()
            url = f"https://pokeapi.co/api/v2/move/{move_name}"
            response = requests.get(url, timeout=15)
            response.raise_for_status()
            return response.json()
        except Exception:
            return None
    
    def get_move_data(self, move_name):
        """Obtém dados completos de um move (com cache)."""
        if move_name in self.moves_cache:
            return self.moves_cache[move_name]
        
        api_data = self.fetch_move_data(move_name)
        if api_data:
            move_complete = {
                "power": api_data.get('power'),
                "accuracy": api_data.get('accuracy') if api_data.get('accuracy') else 100,
                "type": api_data['type']['name'].capitalize(),
                "category": api_data['damage_class']['name'].capitalize(),
                "priority": api_data.get('priority', 0),
                "pp": api_data.get('pp', 0)
            }
            self.moves_cache[move_name] = move_complete
            return move_complete
        
        # Fallback
        return {
            "power": None,
            "accuracy": 100,
            "type": "Normal",
            "category": "Status",
            "priority": 0,
            "pp": 0
        }
    
    def save_progress(self, complete_dex, is_final=False):
        """Salva progresso incremental."""
        output = self.output_path if is_final else self.temp_path
        with open(output, 'w', encoding='utf-8') as f:
            json.dump(complete_dex, f, indent=2, ensure_ascii=False)
    
    def build_complete_dex(self):
        """Constrói a Pokedex completa 100% da PokeAPI."""
        
        print("=" * 70)
        print("🔬 CONSTRUÇÃO DA POKEDEX COMPLETA (100% PokeAPI - Gen 1-7)")
        print("=" * 70)
        
        # Carregar progresso anterior se existir
        complete_dex = {}
        start_id = 1
        if self.temp_path.exists():
            with open(self.temp_path, 'r', encoding='utf-8') as f:
                complete_dex = json.load(f)
            if complete_dex:
                last_id = max([data['id'] for data in complete_dex.values()])
                start_id = last_id + 1
            print(f"\n🔄 Retomando do Pokemon ID #{start_id}")
        
        print(f"\n🔄 Processando Pokémons (ID 1-809)...")
        print(f"⏰ Estimativa: ~{(809 - start_id + 1) / 100 * 1:.0f} minutos")
        print()
        
        success_count = len(complete_dex)
        error_count = 0
        errors_list = []
        
        for pokemon_id in range(start_id, 810):  # 1-809
            print(f"[{pokemon_id}/809] ", end="", flush=True)
            
            # Buscar dados completos da API
            api_data = self.fetch_pokemon_data(pokemon_id)
            
            if not api_data:
                print("❌")
                error_count += 1
                errors_list.append(pokemon_id)
                continue
            
            pokemon_name = api_data['name'].replace('-', ' ').title()
            print(f"{pokemon_name}...", end=" ", flush=True)
            
            # Extrair abilities
            abilities = []
            for ability_entry in api_data.get('abilities', []):
                ability_name = ability_entry['ability']['name']
                formatted_ability = ability_name.replace('-', ' ').title()
                abilities.append(formatted_ability)
            
            # Montar entrada completa
            complete_entry = {
                "id": api_data['id'],
                "tipos": [t['type']['name'].capitalize() for t in api_data['types']],
                "abilities": abilities,
                "base_stats": {
                    "hp": api_data['stats'][0]['base_stat'],
                    "attack": api_data['stats'][1]['base_stat'],
                    "defense": api_data['stats'][2]['base_stat'],
                    "sp_attack": api_data['stats'][3]['base_stat'],
                    "sp_defense": api_data['stats'][4]['base_stat'],
                    "speed": api_data['stats'][5]['base_stat']
                },
                "height": round(api_data['height'] / 10, 1),
                "weight": round(api_data['weight'] / 10, 1),
                "movimientos_por_nivel": {}
            }
            
            # Processar movimentos aprendidos por level-up
            for move_entry in api_data.get('moves', []):
                move_name = move_entry['move']['name']
                
                # Procurar método level-up
                for version_detail in move_entry['version_group_details']:
                    if version_detail['move_learn_method']['name'] == 'level-up':
                        level = str(version_detail['level_learned_at'])
                        
                        # Obter dados completos do move
                        move_data = self.get_move_data(move_name)
                        
                        # Adicionar ao nível correspondente
                        if level not in complete_entry["movimientos_por_nivel"]:
                            complete_entry["movimientos_por_nivel"][level] = []
                        
                        move_display_name = move_name.replace('-', ' ').title()
                        complete_entry["movimientos_por_nivel"][level].append({
                            "name": move_display_name,
                            "power": move_data["power"],
                            "accuracy": move_data["accuracy"],
                            "type": move_data["type"],
                            "category": move_data["category"],
                            "priority": move_data["priority"],
                            "pp": move_data["pp"]
                        })
                        break  # Usar apenas a primeira versão encontrada
            
            complete_dex[pokemon_name] = complete_entry
            success_count += 1
            print("✅")
            
            # Salvar progresso a cada 50 Pokemon
            if pokemon_id % 50 == 0:
                self.save_progress(complete_dex, is_final=False)
                print(f"💾 Progresso salvo: {pokemon_id}/809")
        
        # Salvar arquivo final
        print(f"\n💾 Salvando arquivo final em {self.output_path}...")
        self.save_progress(complete_dex, is_final=True)
        
        # Remover arquivo temporário
        if self.temp_path.exists():
            self.temp_path.unlink()
        
        # Relatório
        print("\n" + "=" * 70)
        print("📊 RELATÓRIO FINAL")
        print("=" * 70)
        print(f"✅ Pokémons processados: {success_count}/809")
        print(f"✅ Moves únicos em cache: {len(self.moves_cache)}")
        
        if error_count > 0:
            print(f"\n⚠️  IDs não encontrados ({error_count}):")
            for pid in errors_list[:15]:
                print(f"   - ID {pid}")
            if len(errors_list) > 15:
                print(f"   ... e mais {len(errors_list) - 15}")
        
        # Mostrar exemplo
        if complete_dex:
            sample_name = list(complete_dex.keys())[0]
            sample = complete_dex[sample_name]
            print(f"\n📋 Exemplo ({sample_name}):")
            print(f"   ID: {sample['id']}")
            print(f"   Tipos: {sample['tipos']}")
            print(f"   Abilities: {sample['abilities']}")
            print(f"   Stats: HP={sample['base_stats']['hp']}, "
                  f"Atk={sample['base_stats']['attack']}, "
                  f"Def={sample['base_stats']['defense']}, "
                  f"SpA={sample['base_stats']['sp_attack']}, "
                  f"SpD={sample['base_stats']['sp_defense']}, "
                  f"Spe={sample['base_stats']['speed']}")
            print(f"   Peso: {sample['weight']} kg | Altura: {sample['height']} m")
            print(f"   Total de níveis com moves: {len(sample['movimientos_por_nivel'])}")
            if '1' in sample['movimientos_por_nivel'] and sample['movimientos_por_nivel']['1']:
                move_ex = sample['movimientos_por_nivel']['1'][0]
                print(f"   Move exemplo (nv1): {move_ex['name']} | "
                      f"Power={move_ex['power']} | Acc={move_ex['accuracy']} | "
                      f"Type={move_ex['type']} | Cat={move_ex['category']} | "
                      f"Pri={move_ex['priority']} | PP={move_ex['pp']}")
        
        print(f"\n📁 Arquivo gerado: {self.output_path}")
        print("=" * 70)
        print("✅ POKEDEX COMPLETA CONSTRUÍDA COM SUCESSO!")
        print("=" * 70)
        
        return True

if __name__ == "__main__":
    builder = CompleteDexBuilder()
    builder.build_complete_dex()
