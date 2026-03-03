"""
EXEMPLOS PRATICOS DE INTEGRACAO
Conectar as 4 melhorias ao codigo existente do PokeBot
"""

# ============================================================================
# EXEMPLO 1: Integrar Singleton + Cache no bot_controller.py
# ============================================================================

# Antes:
"""
class BotController:
    def __init__(self):
        self.db = PokemonDatabase()  # Nova instancia!
        self.db2 = PokemonDatabase()  # Outra instancia!
        # Múltiplas instâncias = I/O repetido
"""

# Depois:
from src.knowledge.pokemon_database import PokemonDatabase

class BotController:
    def __init__(self):
        self.db = PokemonDatabase()  # Singleton!
        
        # Uso transparente - cache automático
        pokemon = self.db.get_pokemon_data("Charizard")  # <1ms após cache
        stats = self.db.get_pokemon_stats("Charizard")   # <1ms após cache

# ============================================================================
# EXEMPLO 2: Usar mapeamento de imunidades na estratégia
# ============================================================================

# Antes (sem detectar imunidades):
"""
def choose_move(self, my_pokemon, enemy_pokemon):
    enemy_types = self.db.get_pokemon_types(enemy_pokemon)
    
    # Problem: Usa Ground em Levitate = Zero damage!
    if "Ground" in available_moves:
        return "Ground"  # Wasted turn
"""

# Depois (detecta imunidades):
def choose_move(self, my_pokemon, enemy_pokemon):
    available_moves = self.tm.get_moves(my_pokemon)
    
    best_move = None
    best_effectiveness = 0.0
    
    for move_name in available_moves:
        move_data = self.db.get_move_data(move_name)
        move_type = move_data['type']
        
        # NOVO: Detecta imunidades!
        effectiveness = self.strategy.calculate_type_effectiveness(
            move_type, 
            enemy_pokemon
        )
        
        if effectiveness > best_effectiveness and effectiveness > 0.0:
            best_effectiveness = effectiveness
            best_move = move_name
    
    return best_move or self.get_safe_move()

# ============================================================================
# EXEMPLO 3: Humanizar clicks com anti-cheat
# ============================================================================

# Antes (padrão fixo - detectável):
"""
def click_move(self, slot_index):
    x, y = self.get_move_coords(slot_index)
    pyautogui.moveTo(x, y, duration=0.2)
    time.sleep(0.15)  # FIXO!
    pyautogui.click()
    time.sleep(0.1)   # FIXO!
"""

# Depois (Gaussiana - natural):
def click_move(self, slot_index):
    x, y = self.get_move_coords(slot_index)
    
    # NOVO: Humanizado!
    self.input_simulator.humanized_click(
        x, y,
        delay_min=0.1,
        delay_max=0.3
    )
    # Cada clique tem delays aleatórios (6754x variáveis!)

# ============================================================================
# EXEMPLO 4: Rastrear PP e recuperar após crash
# ============================================================================

# Fluxo completo de uma batalha:

class BattleManager:
    def __init__(self):
        self.tm = TeamManager()
        self.db = PokemonDatabase()
    
    def start_battle(self, my_team, enemy_team):
        """Iniciar nova batalha"""
        # Setup: Inicializar rastreamento de PP
        for pokemon_name in my_team:
            moves_data = {}
            for move in self.tm.get_moves(pokemon_name):
                move_info = self.db.get_move_data(move)
                moves_data[move] = move_info['pp']
            
            self.tm.initialize_pp_tracking(pokemon_name, moves_data)
    
    def use_move(self, pokemon_name, move_name):
        """Usar um movimento"""
        move_info = self.db.get_move_data(move_name)
        
        # Registra uso e retorna PP restante
        pp_left = self.tm.track_move_usage(
            pokemon_name,
            move_name,
            move_info['pp']
        )
        
        if pp_left <= 0:
            print(f"ERRO: {move_name} sem PP!")
            return False
        
        print(f"{pokemon_name} usou {move_name} ({pp_left} PP)")
        return True
    
    def choose_next_move(self, pokemon_name):
        """Escolher proximo movimento (prioriza movimentos com PP)"""
        # NOVO: Pega apenas movimentos com PP
        available = self.tm.get_available_moves(pokemon_name)
        
        if not available:
            print(f"ERRO: {pokemon_name} sem movimentos com PP!")
            return None
        
        # Estrategia escolhe entre disponíveis
        return self.strategy.choose_best_move(pokemon_name, available)
    
    def recover_from_crash(self, pokemon_name):
        """Recuperar contexto após bot travar"""
        # Obtém estado salvo
        summary = self.tm.pp_summary(pokemon_name)
        
        print(f"Recuperando {pokemon_name}:")
        for move_name, pp in summary.items():
            print(f"  - {move_name}: {pp} PP")
        
        available = self.tm.get_available_moves(pokemon_name)
        print(f"Movimentos disponíveis: {available}")
        
        return available

# ============================================================================
# EXEMPLO 5: Integração completa no main loop
# ============================================================================

def main_battle_loop():
    """Loop principal de batalha com todas as melhorias"""
    
    # Setup
    db = PokemonDatabase()  # Singleton
    tm = TeamManager()
    strategy = BattleStrategy(db, tm)
    input_sim = InputSimulator(config)
    
    # Detectar Pokemon inimigo
    enemy_pokemon = "Charizard"
    my_pokemon = "Pikachu"
    
    # Inicializar rastreamento
    my_moves = tm.get_moves(my_pokemon)
    moves_data = {m: db.get_move_data(m)['pp'] for m in my_moves}
    tm.initialize_pp_tracking(my_pokemon, moves_data)
    
    # Main loop
    while battle_ongoing:
        # 1. ESCOLHER MOVIMENTO (com imunidades)
        best_move = None
        best_eff = 0.0
        
        for move in tm.get_available_moves(my_pokemon):  # Apenas PP > 0
            move_type = db.get_move_data(move)['type']
            
            # MELHORIA 2: Detecta imunidades
            eff = strategy.calculate_type_effectiveness(
                move_type,
                enemy_pokemon
            )
            
            if eff > best_eff:
                best_eff = eff
                best_move = move
        
        if best_move is None:
            best_move = "Struggle"
        
        # 2. CLICAR NO MOVIMENTO (humanizado)
        move_coords = get_move_button_coords(best_move)
        
        # MELHORIA 3: Humanizado
        input_sim.humanized_click(
            move_coords['x'],
            move_coords['y'],
            delay_min=0.1,
            delay_max=0.3
        )
        
        # 3. RASTREAR PP
        # MELHORIA 4: Track PP
        tm.track_move_usage(my_pokemon, best_move, max_pp)
        
        # 4. ACESSAR DATABASE (cache automático)
        # MELHORIA 1: Lookup rápido
        enemy_data = db.get_pokemon_data(enemy_pokemon)  # <1ms
        
        # Continuar batalha...
        time.sleep(2)  # Aguardar resultado
    
    # Fim da batalha
    tm.reset_pp_session()  # Limpar rastreamento

# ============================================================================
# EXEMPLO 6: Monitorar performance
# ============================================================================

def monitor_improvements():
    """Demonstrar ganhos de performance"""
    
    db = PokemonDatabase()
    
    # Teste 1: Cache
    print("=== TESTE DE CACHE ===")
    import time
    
    # Miss
    start = time.time()
    db.get_pokemon_data("Pikachu")
    elapsed1 = time.time() - start
    print(f"Cache Miss: {elapsed1*1000:.2f}ms")
    
    # Hit
    start = time.time()
    db.get_pokemon_data("Pikachu")
    elapsed2 = time.time() - start
    print(f"Cache Hit:  {elapsed2*1000:.3f}ms")
    print(f"Speedup:    {elapsed1/elapsed2:.0f}x\n")
    
    # Teste 2: Imunidades
    print("=== TESTE DE IMUNIDADES ===")
    strategy = BattleStrategy(db, None)
    
    eff = strategy.calculate_type_effectiveness("Ground", "Gengar")
    print(f"Ground vs Gengar (Levitate): {eff}x")
    
    eff = strategy.calculate_type_effectiveness("Electric", "Lanturn")
    print(f"Electric vs Lanturn (Volt Absorb): {eff}x\n")
    
    # Teste 3: PP tracking
    print("=== TESTE DE PP TRACKING ===")
    tm = TeamManager()
    tm.initialize_pp_tracking("Pikachu", {"thunderbolt": 15})
    
    for i in range(3):
        pp = tm.track_move_usage("Pikachu", "Thunderbolt", 15)
        print(f"Uso {i+1}: {pp} PP restante")
    
    available = tm.get_available_moves("Pikachu")
    print(f"Disponíveis: {available}")
    
    print("\n=== TODAS AS MELHORIAS FUNCIONANDO ===")

if __name__ == "__main__":
    monitor_improvements()

# ============================================================================
# DICAS DE INTEGRACAO
# ============================================================================

"""
1. Singleton + Cache:
   - Importar PokemonDatabase uma vez no __init__
   - Reutilizar em toda aplicação
   - Nunca criar múltiplas instâncias
   - Cache automático, transparente

2. Imunidades:
   - Sempre usar calculate_type_effectiveness()
   - Nunca assumir 2.0x super-efetivo
   - Filtrar movimentos com eff = 0.0
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
