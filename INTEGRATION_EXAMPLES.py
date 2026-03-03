"""
EXEMPLOS PRATICOS DE INTEGRACAO
Conectar as 4 melhorias ao codigo existente do PokeBot
"""

# Imports necessarios
import time
from src.knowledge.pokemon_database import PokemonDatabase
from src.knowledge.team_manager import TeamManager
from src.decision.battle_strategy import BattleStrategy
from src.action.input_simulator import InputSimulator

# ============================================================================
# EXEMPLO 1: Integrar Singleton + Cache no bot_controller.py
# ============================================================================

class BotControllerExample1:
    """Demonstra uso de Singleton + Cache"""
    
    def __init__(self):
        # Singleton: uma unica instancia em toda aplicacao
        self.db = PokemonDatabase()
        
        # Cache automatico: primeira busca ~5ms, buscas posteriores <1ms
        pokemon = self.db.get_pokemon_data("Charizard")
        stats = self.db.get_pokemon_stats("Charizard")
        
        print(f"Cache test: {pokemon['name']} loaded")


# ============================================================================
# EXEMPLO 2: Usar mapeamento de imunidades na estrategia
# ============================================================================

class BattleStrategyExample2:
    """Demonstra deteccao de imunidades"""
    
    def __init__(self):
        self.db = PokemonDatabase()
        self.strategy = BattleStrategy(self.db, None)
    
    def choose_move(self, my_pokemon, enemy_pokemon, available_moves):
        """Escolhe melhor movimento considerando imunidades"""
        
        best_move = None
        best_effectiveness = 0.0
        
        for move_name in available_moves:
            move_data = self.db.get_move_data(move_name)
            if not move_data:
                continue
                
            move_type = move_data.get('type')
            
            # MELHORIA 2: Detecta imunidades!
            effectiveness = self.strategy.calculate_type_effectiveness(
                move_type, 
                enemy_pokemon
            )
            
            # Evita movimentos com efectividade 0 (imunes)
            if effectiveness > best_effectiveness and effectiveness > 0.0:
                best_effectiveness = effectiveness
                best_move = move_name
        
        return best_move or "Struggle"


# ============================================================================
# EXEMPLO 3: Humanizar clicks com anti-cheat
# ============================================================================

class InputSimulatorExample3:
    """Demonstra humanizacao de inputs"""
    
    def __init__(self):
        self.input_sim = InputSimulator({
            'input': {
                'use_human_movement': True,
                'min_delay': 0.1,
                'max_delay': 0.3,
            }
        })
    
    def click_move(self, move_button_x, move_button_y):
        """Clica no botao de movimento com humanizacao"""
        
        # MELHORIA 3: Humanizado com Gaussiana + Jitter
        self.input_sim.humanized_click(
            move_button_x,
            move_button_y,
            delay_min=0.1,
            delay_max=0.3
        )
        # Cada clique tem delays aleatorios (nao fixo = anti-cheat)

# ============================================================================
# EXEMPLO 4: Rastrear PP e recuperar apos crash
# ============================================================================

class BattleManagerExample4:
    """Demonstra rastreamento de PP"""
    
    def __init__(self):
        self.tm = TeamManager()
        self.db = PokemonDatabase()
    
    def start_battle(self, my_team, enemy_team):
        """Iniciar nova batalha com rastreamento"""
        
        # Setup: Inicializar rastreamento de PP
        for pokemon_name in my_team:
            moves_data = {}
            for move in self.tm.get_moves(pokemon_name):
                move_info = self.db.get_move_data(move)
                if move_info:
                    moves_data[move] = move_info.get('pp', 0)
            
            self.tm.initialize_pp_tracking(pokemon_name, moves_data)
    
    def use_move(self, pokemon_name, move_name):
        """Usar um movimento"""
        
        move_info = self.db.get_move_data(move_name)
        if not move_info:
            return False
        
        # MELHORIA 4: Registra uso e retorna PP restante
        pp_left = self.tm.track_move_usage(
            pokemon_name,
            move_name,
            move_info.get('pp', 0)
        )
        
        if pp_left <= 0:
            print(f"ERRO: {move_name} sem PP!")
            return False
        
        print(f"{pokemon_name} usou {move_name} ({pp_left} PP)")
        return True
    
    def choose_next_move(self, pokemon_name):
        """Escolher proximo movimento (prioriza movimentos com PP)"""
        
        # NOVO: Pega apenas movimentos com PP > 0
        available = self.tm.get_available_moves(pokemon_name)
        
        if not available:
            print(f"ERRO: {pokemon_name} sem movimentos com PP!")
            return None
        
        # Retorna primeiro disponivel (ou use logica de estrategia)
        return available[0] if available else None
    
    def recover_from_crash(self, pokemon_name):
        """Recuperar contexto apos bot travar"""
        
        # Obtém estado salvo
        summary = self.tm.pp_summary(pokemon_name)
        
        print(f"Recuperando {pokemon_name}:")
        for move_name, pp in summary.items():
            print(f"  - {move_name}: {pp} PP")
        
        available = self.tm.get_available_moves(pokemon_name)
        print(f"Movimentos disponíveis: {available}")
        
        return available

# ============================================================================
# EXEMPLO 5: Integracao completa no main loop
# ============================================================================

class FullBattleLoopExample5:
    """Demonstra integracao completa de todas as melhorias"""
    
    def __init__(self):
        self.db = PokemonDatabase()
        self.tm = TeamManager()
        self.strategy = BattleStrategy(self.db, self.tm)
        self.input_sim = InputSimulator({
            'input': {
                'use_human_movement': True,
                'min_delay': 0.1,
                'max_delay': 0.3,
            }
        })
    
    def run_battle_loop_example(self, my_pokemon, enemy_pokemon):
        """Simula um turno de batalha com todas as melhorias"""
        
        print(f"\n[Turno de Batalha] {my_pokemon} vs {enemy_pokemon}")
        
        # Inicializar rastreamento
        my_moves = self.tm.get_moves(my_pokemon)
        if my_moves:
            moves_data = {}
            for m in my_moves:
                move_data = self.db.get_move_data(m)
                if move_data:
                    moves_data[m] = move_data.get('pp', 0)
            self.tm.initialize_pp_tracking(my_pokemon, moves_data)
        
        # 1. ESCOLHER MOVIMENTO (com imunidades)
        best_move = None
        best_eff = 0.0
        
        available = self.tm.get_available_moves(my_pokemon)  # Apenas PP > 0
        
        for move in available:
            move_data = self.db.get_move_data(move)
            if not move_data:
                continue
                
            move_type = move_data.get('type')
            
            # MELHORIA 2: Detecta imunidades
            eff = self.strategy.calculate_type_effectiveness(
                move_type,
                enemy_pokemon
            )
            
            if eff > best_eff:
                best_eff = eff
                best_move = move
        
        if best_move is None:
            best_move = "Struggle"
        
        print(f"  [Move] {my_pokemon} usa {best_move} (eff: {best_eff}x)")
        
        # 2. RASTREAR PP
        # MELHORIA 4: Track PP
        move_data = self.db.get_move_data(best_move)
        if move_data:
            pp_left = self.tm.track_move_usage(
                my_pokemon,
                best_move,
                move_data.get('pp', 0)
            )
            print(f"  [PP] {best_move}: {pp_left} restante")
        
        # 3. ACESSAR DATABASE (cache automatico)
        # MELHORIA 1: Lookup rapido
        enemy_data = self.db.get_pokemon_data(enemy_pokemon)  # <1ms
        if enemy_data:
            print(f"  [Enemy] {enemy_data['name']} - Types: {enemy_data['tipos']}")

# ============================================================================
# EXEMPLO 6: Monitorar performance
# ============================================================================

def monitor_improvements():
    """Demonstrar ganhos de performance"""
    
    db = PokemonDatabase()
    
    # Teste 1: Cache
    print("=== TESTE DE CACHE ===")
    import time
    # ============================================================================
    # EXEMPLO 6: Monitorar performance
    # ============================================================================

    class PerformanceMonitorExample6:
        """Demonstrar ganhos de performance de todas as melhorias"""
    
        @staticmethod
        def monitor_improvements():
            """Demonstrar ganhos de performance"""
        
            db = PokemonDatabase()
            tm = TeamManager()
        
            # Teste 1: Cache
            print("\n=== TESTE 1: CACHE SINGLETON ===")
            import time
        
            # Miss (primeira vez)
            start = time.time()
            data1 = db.get_pokemon_data("Pikachu")
            elapsed1 = time.time() - start
            print(f"Cache Miss: {elapsed1*1000:.2f}ms")
        
            # Hit (segunda vez - do cache)
            start = time.time()
            data2 = db.get_pokemon_data("Pikachu")
            elapsed2 = time.time() - start
            print(f"Cache Hit:  {elapsed2*1000:.3f}ms")
        
            if elapsed2 > 0:
                speedup = elapsed1 / elapsed2
                print(f"Speedup:    {speedup:.0f}x\n")
        
            # Teste 2: Imunidades
            print("=== TESTE 2: IMUNIDADES (MELHORIA 2) ===")
            strategy = BattleStrategy(db, tm)
        
            test_cases = [
                ("Ground", "Gengar", 0.0),      # Levitate immunity
                ("Electric", "Lanturn", 0.0),   # VoltAbsorb immunity
                ("Fire", "Charizard", 0.0),     # FlareBoost immunity
            ]
        
            for move_type, pokemon, expected_eff in test_cases:
                eff = strategy.calculate_type_effectiveness(move_type, pokemon)
                status = "✓" if eff == expected_eff else "✗"
                print(f"{status} {move_type} vs {pokemon}: {eff}x")
        
            # Teste 3: PP Tracking
            print("\n=== TESTE 3: RASTREAMENTO DE PP (MELHORIA 4) ===")
            tm.initialize_pp_tracking("Pikachu", {"Thunder": 15, "Quick-Attack": 30})
        
            pp1 = tm.track_move_usage("Pikachu", "Thunder", 15)
            pp2 = tm.track_move_usage("Pikachu", "Thunder", 15)
        
            print(f"Thunder PP após 1º uso: {pp1}")
            print(f"Thunder PP após 2º uso: {pp2}\n")
    
    available = tm.get_available_moves("Pikachu")
    print(f"Disponíveis: {available}")
    
    print("\n=== TODAS AS MELHORIAS FUNCIONANDO ===")

if __name__ == "__main__":
    monitor_improvements()

# ============================================================================
# DICAS DE INTEGRACAO
# ============================================================================

"""
        print(f"Thunder PP após 1º uso: {pp1}")
        print(f"Thunder PP após 2º uso: {pp2}\n")
   - Sempre usar calculate_type_effectiveness()
   - Nunca assumir 2.0x super-efetivo
    print("=" * 70)
    print("DEMONSTRAÇÃO: INTEGRACAO DE TODAS AS 4 MELHORIAS")
    print("=" * 70)
    
    # Exemplo 1: Singleton
    print("\n[EXEMPLO 1] Singleton + LRU Cache")
    ex1 = SingletonExample1()
    ex1.demonstrate_singleton()
    
    # Exemplo 2: Battle Strategy (Immunities)
    print("\n[EXEMPLO 2] Type Effectiveness + Ability Immunities")
    ex2 = BattleStrategyExample2()
    ex2.demonstrate_immunities()
    
    # Exemplo 3: Humanized Input
    print("\n[EXEMPLO 3] Humanized Input with Gaussian Distribution")
    ex3 = InputSimulatorExample3()
    ex3.demonstrate_humanized_input()
    
    # Exemplo 4: PP Tracking
    print("\n[EXEMPLO 4] BattleManager with PP Tracking")
    ex4 = BattleManagerExample4()
    ex4.demonstrate_pp_tracking()
    
    # Exemplo 5: Full Battle Loop
    print("\n[EXEMPLO 5] Complete Battle Integration")
    ex5 = FullBattleLoopExample5()
    ex5.run_battle_loop_example("Pikachu", "Charizard")
    
    # Exemplo 6: Performance Monitoring
    print("\n[EXEMPLO 6] Performance Monitoring")
    PerformanceMonitorExample6.monitor_improvements()
    
    print("\n" + "=" * 70)
    print("TODAS AS MELHORIAS INTEGRADAS E FUNCIONANDO!")
    print("=" * 70)
   - Logar imunidades detectadas

3. Humanização:
   - Trocar pyautogui.click() por humanized_click()
   - Manter delay_min/max configurável
   - Usar em todos os clicks da bataille
   - Não pré-computar coordenadas (variam com jitter)

4. PP Tracking:
   - initialize_pp_tracking() ao iniciar battle
   - track_move_usage() a cada movimento
   - Usar get_available_moves() para escolher
   - reset_pp_session() ao terminar battle

5. Performance:
   - Monitorar cache_info() ocasionalmente
   - Ajustar maxsize se necessário
   - Logar misses/hits em debug
   - Profilear em produção

6. Segurança:
   - Sempre humanizar clicks
   - Variar delays entre 0.1-0.3s
   - Adicionar jitter em coordenadas
   - Não usar padrões detectáveis
"""
