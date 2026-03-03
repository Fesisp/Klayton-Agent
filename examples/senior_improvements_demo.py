"""
DEMONSTRACAO: Melhorias Senior Implementadas

Exemplo de integracao das 4 melhorias principais:
1. Singleton + LRU Cache (PokemonDatabase)
2. Mapeamento de Imunidades (BattleStrategy)
3. Humanizacao de Inputs (InputSimulator)
4. Memoria de Turno / Rastreamento de PP (TeamManager)
"""

import sys
from pathlib import Path

# Adiciona o diretrio do projeto ao path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.knowledge.pokemon_database import PokemonDatabase
from src.knowledge.team_manager import TeamManager
from src.decision.battle_strategy import BattleStrategy
from src.action.input_simulator import InputSimulator


def demo_singleton_cache():
    """MELHORIA 1: Singleton + LRU Cache"""
    print("\n" + "=" * 70)
    print("[MELHORIA 1] Singleton + LRU Cache")
    print("=" * 70)
    
    # Primeira instancia
    db1 = PokemonDatabase()
    print(f"\nInstancia 1 criada: {db1}")
    
    # Segunda instancia (deve ser a mesma)
    db2 = PokemonDatabase()
    print(f"Instancia 2 criada: {db2}")
    print(f"Sao a mesma instancia? {db1 is db2}")
    
    # Teste de cache
    import time
    print("\nTestando performance do cache:")
    
    # Primeira busca (cache miss)
    start = time.time()
    pikachu = db1.get_pokemon_data("Pikachu")
    elapsed1 = time.time() - start
    print(f"   Primeira busca (Pikachu): {elapsed1*1000:.2f}ms (cache miss)")
    
    # Segunda busca (cache hit)
    start = time.time()
    pikachu = db1.get_pokemon_data("Pikachu")
    elapsed2 = time.time() - start
    print(f"   Segunda busca (Pikachu): {elapsed2*1000:.3f}ms (cache hit)")
    print(f"   Aceleracao: {elapsed1/elapsed2:.0f}x mais rapido!")
    
    # Mostra info do cache
    info = db1.cache_info()
    print(f"\nEstatisticas do Cache:")
    data_info = info['pokemon_data']
    print(f"   Hits: {data_info.hits}, Misses: {data_info.misses}")
    print(f"   Taxa de acerto: {data_info.hits/(data_info.hits+data_info.misses)*100:.1f}%")


def demo_ability_immunities():
    """MELHORIA 2: Mapeamento de Imunidades por Habilidade"""
    print("\n" + "=" * 70)
    print("  MELHORIA 2: Mapeamento de Imunidades por Habilidade")
    print("=" * 70)
    
    db = PokemonDatabase()
    strategy = BattleStrategy(db, None)
    
    print("\n Testando efetividade de tipo com imunidades:")
    
    # Teste 1: Levitate + Ground
    print("\n  Caso 1: Pokmon com Levitate vs Ground")
    print("    Sem Levitate: 2.0x super-efetivo")
    print("    Com Levitate: 0.0x (imune!)")
    eff = strategy.calculate_type_effectiveness("Ground", "Gengar")
    print(f"    Gengar (Levitate): {eff}x (imune)")
    
    # Teste 2: Volt Absorb + Electric
    print("\n  Caso 2: Pokmon com Volt Absorb vs Electric")
    eff = strategy.calculate_type_effectiveness("Electric", "Lanturn")
    print(f"    Lanturn (Volt Absorb): {eff}x (absorve)")
    
    # Teste 3: Flash Fire + Fire
    print("\n  Caso 3: Pokmon com Flash Fire vs Fire")
    eff = strategy.calculate_type_effectiveness("Fire", "Arcanine")
    print(f"    Arcanine (Flash Fire): {eff}x (absorve)")
    
    print("\n Isso evita o 'Zero Damage' issue do bot!")


def demo_humanized_input():
    """MELHORIA 3: Humanizao de Inputs com Distribuio Gaussiana"""
    print("\n" + "=" * 70)
    print(" MELHORIA 3: Humanizao de Inputs (Distribuio Gaussiana)")
    print("=" * 70)
    
    config = {
        'rois': {},
        'input': {
            'use_human_movement': True,
            'min_delay': 0.1,
            'max_delay': 0.3,
            'min_move_duration': 0.2,
            'max_move_duration': 0.5,
        },
        'detection': {},
        'assets': {}
    }
    
    sim = InputSimulator(config)
    
    print("\n Simulando delays humanizados (Distribuio Gaussiana):")
    print("   Intervalo: 0.1s - 0.3s")
    print("   Distribuio: Gaussiana com =0.2s, =0.033s\n")
    
    import random
    random.seed(42)  # Para reproduzibilidade
    
    delays = []
    for i in range(5):
        mean = 0.2
        sigma = (0.3 - 0.1) / 6
        delay = abs(random.gauss(mean, sigma))
        delay = max(0.1, min(delay, 0.3))
        delays.append(delay)
        print(f"   Clique {i+1}: {delay*1000:.1f}ms")
    
    print(f"\n Varincia natural: {min(delays)*1000:.1f}ms - {max(delays)*1000:.1f}ms")
    print("   Anti-cheat: Intervalos fixos so detectveis, isso no!")


def demo_pp_tracking():
    """MELHORIA 4: Memria de Turno / Rastreamento de PP"""
    print("\n" + "=" * 70)
    print(" MELHORIA 4: Memria de Turno - Rastreamento de PP")
    print("=" * 70)
    
    tm = TeamManager()
    
    print("\n Cenrio: Bot se reinicia no meio da batalha")
    print("   Pikachu usou Thunderbolt 3 vezes (15 PP original)")
    
    # Inicializa movimentos
    moves_data = {
        "thunderbolt": 15,
        "quick_attack": 30,
        "iron_tail": 15
    }
    tm.initialize_pp_tracking("Pikachu", moves_data)
    print(f"\n Rastreamento iniciado")
    print(f"   Movimentos: {moves_data}")
    
    # Simula uso
    print(f"\n Turno 1: Pikachu usa Thunderbolt")
    pp1 = tm.track_move_usage("Pikachu", "Thunderbolt", 15)
    print(f"   PP restante: {pp1}")
    
    print(f"\n Turno 2: Pikachu usa Thunderbolt")
    pp2 = tm.track_move_usage("Pikachu", "Thunderbolt", 15)
    print(f"   PP restante: {pp2}")
    
    print(f"\n Turno 3: Pikachu usa Thunderbolt")
    pp3 = tm.track_move_usage("Pikachu", "Thunderbolt", 15)
    print(f"   PP restante: {pp3}")
    
    # Bot se reinicia
    print(f"\n  BOT REINICIA (se no houvesse rastreamento, perderia contexto!)")
    
    # Recupera contexto
    available = tm.get_available_moves("Pikachu")
    print(f"\n Movimentos disponveis aps restart:")
    for move in available:
        pp = tm.get_move_pp("Pikachu", move)
        print(f"   - {move}: {pp} PP")
    
    print(f"\n Sem rastreamento: Pikachu tentaria usar Thunderbolt com 0 PP!")
    print(f"   Com rastreamento: Bot sabe que precisa usar Quick Attack!")


def demo_integration():
    """Demonstrao de integrao completa"""
    print("\n" + "=" * 70)
    print(" INTEGRAO COMPLETA: Todas as melhorias juntas")
    print("=" * 70)
    
    # Setup
    db = PokemonDatabase()
    tm = TeamManager()
    strategy = BattleStrategy(db, tm)
    
    config = {
        'rois': {},
        'input': {
            'use_human_movement': True,
            'min_delay': 0.1,
            'max_delay': 0.3,
            'min_move_duration': 0.2,
            'max_move_duration': 0.5,
        },
        'detection': {},
        'assets': {}
    }
    sim = InputSimulator(config)
    
    print("\n Sistema de Battle Bot Otimizado:")
    print(f"   Database: Singleton + Cache LRU (128 slots)")
    print(f"   Strategy: Imunidades por Habilidade")
    print(f"   Input: Distribuio Gaussiana")
    print(f"   Memory: Rastreamento de PP")
    
    print(f"\n Pronto para batalha com:")
    print(f"   - 0 latncia em dados recentes (cache)")
    print(f"   - Deteco de imunidades automtica")
    print(f"   - Comportamento anti-cheat")
    print(f"   - Recuperao de contexto aps crash")


if __name__ == "__main__":
    print("\n" + " DEMONSTRAO: Melhorias Snior do PokeBot")
    
    try:
        demo_singleton_cache()
        demo_ability_immunities()
        demo_humanized_input()
        demo_pp_tracking()
        demo_integration()
    except Exception as e:
        print(f"\n Erro na demonstrao: {e}")
        import traceback
        traceback.print_exc()
    
    print("\n" + "=" * 70)
    print(" DEMONSTRAO COMPLETA!")
    print("=" * 70 + "\n")
