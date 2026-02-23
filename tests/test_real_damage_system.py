"""
Exemplo de uso do Sistema de Cálculo de Dano Real (v2.5)

Demonstra:
- Estimativa de stats
- Cálculo de dano com fórmula real
- Detecção de priority moves
- Análise de risco/recompensa
"""

from src.knowledge.pokemon_database import PokemonDatabase
from src.knowledge.team_manager import TeamManager
from src.decision.battle_strategy import BattleStrategy

def exemplo_basico():
    """Exemplo 1: Cálculo básico de stats e dano."""
    print("=" * 60)
    print("EXEMPLO 1: Cálculo Básico de Stats e Dano")
    print("=" * 60)
    
    db = PokemonDatabase()
    
    # Estimativa de stats
    print("\n📊 ESTIMATIVA DE STATS:")
    print("-" * 40)
    
    # Pikachu Lv 50
    pikachu_base_speed = 90
    pikachu_speed = db.estimate_stat(pikachu_base_speed, level=50, iv=31, ev=252, nature=1.1)
    print(f"Pikachu Lv50 (Base Speed 90, +Nature):")
    print(f"  → Speed = {pikachu_speed}")
    
    # Snorlax Lv 50
    snorlax_base_speed = 30
    snorlax_speed = db.estimate_stat(snorlax_base_speed, level=50, iv=31, ev=0, nature=0.9)
    print(f"\nSnorlax Lv50 (Base Speed 30, -Nature):")
    print(f"  → Speed = {snorlax_speed}")
    
    # Comparação
    print(f"\n⚡ Pikachu é {pikachu_speed / snorlax_speed:.2f}x mais rápido que Snorlax")


def exemplo_golpes_comuns():
    """Exemplo 2: Golpes comuns e priority moves."""
    print("\n" + "=" * 60)
    print("EXEMPLO 2: Golpes Comuns e Priority Moves")
    print("=" * 60)
    
    db = PokemonDatabase()
    
    # Charizard
    print("\n🔥 CHARIZARD:")
    print("-" * 40)
    common_moves = db.get_common_moves("charizard")
    print(f"Golpes Comuns: {common_moves[:4]}")
    
    priority_moves = db.get_priority_moves("charizard")
    if priority_moves:
        print(f"Priority Moves: {priority_moves}")
    else:
        print("Priority Moves: Nenhum")
    
    # Scizor
    print("\n🦾 SCIZOR:")
    print("-" * 40)
    common_moves = db.get_common_moves("scizor")
    print(f"Golpes Comuns: {common_moves[:4]}")
    
    priority_moves = db.get_priority_moves("scizor")
    if priority_moves:
        print(f"Priority Moves: {priority_moves}")
    else:
        print("Priority Moves: Nenhum")


def exemplo_status_effects():
    """Exemplo 3: Efeitos de status."""
    print("\n" + "=" * 60)
    print("EXEMPLO 3: Efeitos de Status")
    print("=" * 60)
    
    tm = TeamManager()
    db = PokemonDatabase()
    
    # Paralisia
    print("\n⚡ PARALISIA:")
    print("-" * 40)
    
    tm.set_status("pikachu", "PARALYSIS")
    base_speed = 180
    effective_speed = base_speed * 0.5  # Paralisia = -50%
    
    print(f"Pikachu (Base Speed = {base_speed}):")
    print(f"  → Com Paralisia: {effective_speed}")
    print(f"  → Redução: {(1 - 0.5) * 100:.0f}%")
    
    # Queimadura
    print("\n🔥 QUEIMADURA:")
    print("-" * 40)
    
    tm.set_status("machamp", "BURN")
    base_attack = 200
    effective_attack = base_attack * 0.5  # Burn = -50% ataque físico
    
    print(f"Machamp (Base Attack = {base_attack}):")
    print(f"  → Com Queimadura: {effective_attack}")
    print(f"  → Close Combat: ~50% do dano normal")
    
    # Toxic
    print("\n☠️ TOXIC:")
    print("-" * 40)
    
    tm.set_status("blastoise", "TOXIC")
    max_hp = 200
    
    print(f"Blastoise (Max HP = {max_hp}):")
    for turn in range(1, 9):
        toxic_damage = max_hp * (turn / 16)
        remaining_hp = max_hp - sum(max_hp * (t / 16) for t in range(1, turn + 1))
        
        print(f"  Turno {turn}: -{toxic_damage:.1f} HP (Total: {max_hp - remaining_hp:.1f} HP perdidos)")
        
        if remaining_hp <= 0:
            print(f"    ⚠️ MORTE no turno {turn}")
            break


def exemplo_calculo_dano():
    """Exemplo 4: Cálculo de dano real."""
    print("\n" + "=" * 60)
    print("EXEMPLO 4: Cálculo de Dano Real")
    print("=" * 60)
    
    # Simulação manual da fórmula
    print("\n💥 FÓRMULA DE DANO:")
    print("-" * 40)
    
    level = 50
    power = 90  # Thunderbolt
    atk = 150   # Sp. Attack de Pikachu
    defense = 80  # Sp. Defense de Charizard
    
    # Fórmula base
    damage = (((2 * level / 5 + 2) * power * atk / defense) / 50 + 2)
    
    # Modificadores
    stab = 1.5  # Electric vs Electric type (STAB)
    type_mult = 1.0  # Electric vs Fire/Flying (neutral)
    
    final_damage = damage * stab * type_mult
    
    print(f"Pikachu Lv{level} usa Thunderbolt em Charizard:")
    print(f"  Power: {power}")
    print(f"  Sp.Attack: {atk}")
    print(f"  Sp.Defense: {defense}")
    print(f"\n  Dano Base: {damage:.2f}")
    print(f"  STAB: x{stab}")
    print(f"  Type Multiplier: x{type_mult}")
    print(f"\n  → DANO FINAL: {final_damage:.2f}")
    
    # Com Life Orb
    print("\n🔮 COM LIFE ORB:")
    life_orb_damage = final_damage * 1.3
    print(f"  → DANO FINAL: {life_orb_damage:.2f} (+30%)")


def exemplo_priority_risk():
    """Exemplo 5: Risco de priority move."""
    print("\n" + "=" * 60)
    print("EXEMPLO 5: Risco de Priority Move")
    print("=" * 60)
    
    print("\n⚡ CENÁRIO:")
    print("-" * 40)
    print("Charizard (HP 25%, Speed 200) vs Scizor (HP 80%, Speed 120)")
    print("Scizor tem Bullet Punch (priority +1)")
    
    my_hp = 0.25
    my_speed = 200
    enemy_speed = 120
    
    print(f"\n📊 ANÁLISE:")
    print(f"  Sou mais rápido? {my_speed > enemy_speed} (200 > 120)")
    
    # Priority move estimado
    priority_power = 40
    stab = 1.5  # Bug type Scizor
    type_mult = 2.0  # Bug vs Fire (super-efetivo)
    
    estimated_damage = 0.25 * stab * type_mult  # ~30% HP
    
    print(f"  Dano de Bullet Punch estimado: {estimated_damage * 100:.1f}% HP")
    print(f"  Meu HP atual: {my_hp * 100:.1f}%")
    
    has_risk = my_hp < estimated_damage
    
    print(f"\n⚠️ RISCO DE PRIORITY: {'SIM' if has_risk else 'NÃO'}")
    
    if has_risk:
        print("  → DECISÃO: SWITCH_PRIORITY (fugir imediatamente)")
        print("  → RAZÃO: Priority move ignora velocidade e causa OHKO")


def exemplo_integracao_completa():
    """Exemplo 6: Integração completa do sistema."""
    print("\n" + "=" * 60)
    print("EXEMPLO 6: Integração Completa")
    print("=" * 60)
    
    print("\n🎮 SIMULAÇÃO DE BATALHA:")
    print("-" * 40)
    
    # Setup
    db = PokemonDatabase()
    tm = TeamManager()
    
    # Cenário
    my_poke = "charizard"
    enemy_poke = "blastoise"
    my_hp = 0.35
    enemy_hp = 0.70
    
    print(f"Meu Pokémon: {my_poke.upper()} (HP {my_hp * 100:.0f}%)")
    print(f"Inimigo: {enemy_poke.upper()} (HP {enemy_hp * 100:.0f}%)")
    
    # Velocidade
    print("\n⚡ ANÁLISE DE VELOCIDADE:")
    my_base_stats = db.get_base_stats(my_poke)
    enemy_base_stats = db.get_base_stats(enemy_poke)
    
    if my_base_stats and enemy_base_stats:
        my_speed = db.estimate_stat(my_base_stats['speed'], level=50)
        enemy_speed = db.estimate_stat(enemy_base_stats['speed'], level=50)
        
        print(f"  {my_poke}: {my_speed} speed")
        print(f"  {enemy_poke}: {enemy_speed} speed")
        print(f"  → {'Sou mais rápido' if my_speed > enemy_speed else 'Inimigo é mais rápido'}")
    
    # Golpes
    print(f"\n🎯 GOLPES PROVÁVEIS DE {enemy_poke.upper()}:")
    common_moves = db.get_common_moves(enemy_poke)
    for move in common_moves[:4]:
        move_data = db.get_move_data(move)
        if move_data:
            power = move_data.get('power', 'N/A')
            print(f"  - {move.title()}: {power} BP")
    
    # Decisão
    print("\n🧠 DECISÃO:")
    print(f"  HP crítico? {my_hp < 0.4}")
    print(f"  Inimigo fraco? {enemy_hp < 0.2}")
    print(f"  → Recomendação: {'HEAL ou SWITCH' if my_hp < 0.4 else 'ATTACK'}")


if __name__ == "__main__":
    exemplo_basico()
    exemplo_golpes_comuns()
    exemplo_status_effects()
    exemplo_calculo_dano()
    exemplo_priority_risk()
    exemplo_integracao_completa()
    
    print("\n" + "=" * 60)
    print("✅ Todos os exemplos concluídos!")
    print("=" * 60)
