"""
Compara a realidade dos 3 arquivos JSON
"""
import json
from pathlib import Path

project_root = Path(__file__).parent.parent

# Carregar arquivos
with open(project_root / 'data' / 'dex.json', encoding='utf-8') as f:
    dex = json.load(f)

with open(project_root / 'data' / 'dex2_completo.json', encoding='utf-8') as f:
    dex2 = json.load(f)

# Análise dex.json
sample_dex = list(dex.values())[0]
print("📄 dex.json ORIGINAL:")
print(f"   Total: {len(dex)} Pokemon")
print(f"   Campos: {list(sample_dex.keys())}")
print(f"   ✅ Tem tipos? {len(sample_dex.get('tipos', [])) > 0}")
print(f"   ✅ Tem moves? {len(sample_dex.get('movimientos_por_nivel', {})) > 0}")
print(f"   ❌ Tem base_stats? {'base_stats' in sample_dex}")
print()

# Análise dex2_completo.json (NOVO - gerado pelo script)
sample_dex2 = list(dex2.values())[0]
print("📄 dex2_completo.json GERADO AGORA:")
print(f"   Total: {len(dex2)} Pokemon")
print(f"   Campos: {list(sample_dex2.keys())}")
print(f"   ✅ Tem tipos? {len(sample_dex2.get('tipos', [])) > 0}")
print(f"   ✅ Tem moves? {len(sample_dex2.get('movimientos_por_nivel', {})) > 0}")
print(f"   ✅ Tem base_stats? {'base_stats' in sample_dex2}")
if 'base_stats' in sample_dex2:
    print(f"   Exemplo stats: {sample_dex2['base_stats']}")
print()

print("🔍 CONCLUSÃO:")
print("   O script COPIOU dex.json → dex2_completo.json")
print("   E INJETOU base_stats no arquivo NOVO")
print("   Mas dex.json ORIGINAL permaneceu sem stats")
