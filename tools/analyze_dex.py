import json

# Analisa os 3 arquivos
print("="*60)
print("ANÁLISE COMPARATIVA DOS ARQUIVOS DE DADOS")
print("="*60)

# 1. dex.json
dex = json.load(open('data/dex.json', 'r', encoding='utf-8'))
print(f"\n📁 dex.json")
print(f"   Total: {len(dex)} Pokémon")
bulbasaur = dex.get('Bulbasaur', {})
print(f"   Campos: {list(bulbasaur.keys())}")
print(f"   ✅ Tem tipos? {bool(bulbasaur.get('tipos'))}")
print(f"   ✅ Tem movimentos? {bool(bulbasaur.get('movimentos_por_nivel'))}")
print(f"   ❌ Tem base_stats? {bool(bulbasaur.get('base_stats'))}")

# 2. dex2_completo.json
dex2 = json.load(open('data/dex2_completo.json', 'r', encoding='utf-8'))
print(f"\n📁 dex2_completo.json")
print(f"   Total: {len(dex2)} Pokémon")
first_item = list(dex2.items())[0]
print(f"   Exemplo: {first_item[0]}")
print(f"   Campos: {list(first_item[1].keys())}")
print(f"   ⚠️  Tem tipos? {bool(first_item[1].get('tipos'))}")
print(f"   ⚠️  Tem movimentos? {bool(first_item[1].get('movimentos_por_nivel'))}")
print(f"   ✅ Tem numero? {bool(first_item[1].get('numero'))}")

# 3. pokeapi_pokemon.json
api = json.load(open('data/pokeapi_pokemon.json', 'r', encoding='utf-8'))
print(f"\n📁 pokeapi_pokemon.json")
print(f"   Total: {len(api)} Pokémon")
if api:
    first_api = list(api.items())[0]
    print(f"   Exemplo: {first_api[0]}")
    print(f"   Campos: {list(first_api[1].keys())}")

print("\n" + "="*60)
print("RECOMENDAÇÕES")
print("="*60)

print("""
🎯 ESTRATÉGIA RECOMENDADA:

1. MANTER dex.json como PRINCIPAL
   ✅ Já tem 809 Pokémon completos
   ✅ Tipos funcionam corretamente
   ✅ Movimentos por nível completos
   ❌ Falta apenas base_stats

2. IGNORAR dex2_completo.json
   ⚠️  Dados vazios (tipos=[], movimentos={})
   ⚠️  Nomes com erros ("Ivyssaur" em vez de "Ivysaur")
   ❌ Não agrega valor ao projeto

3. ENRIQUECER dex.json com:
   - Base Stats da PokeAPI (HP, Atk, Def, SpA, SpD, Speed)
   - Priority dos moves (para Quick Attack, etc)
   - Category dos moves (Physical/Special)

4. IMPACTO NO BOT:
   ✅ Cálculos de dano mais precisos
   ✅ Speed tiers corretos
   ✅ Detecção de Burn effect em ataques físicos
   ✅ Previsão de "Can I survive next turn?"
   ✅ TTK (Time to Kill) otimizado

5. AÇÃO:
   Executar script inject_stats.py que:
   - LÊ: dex.json (atual, completo)
   - BUSCA: Base stats da PokeAPI
   - GERA: dex.json enriquecido (backup automático)
""")

print("\n⏱️  TEMPO ESTIMADO: 9-10 minutos (809 Pokémon)")
print("📊 RATE LIMIT: 100 requests/min (PokeAPI)")
