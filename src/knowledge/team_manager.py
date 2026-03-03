import json
from pathlib import Path
from typing import List, Dict, Optional


class TeamManager:
    """Gerencia equipe atual (volátil) e golpes conhecidos (persistente)."""

    def __init__(self):
        # Banco de golpes conhecidos (persistente)
        self.moves_db_path = Path("data/known_moves.json")
        self.current_team: List[str] = []  # Lista volátil, atualizada em tempo real
        self.known_moves: Dict[str, List[str]] = {}  # Dicionário persistente {pokemon_name: [moves]}
        self.outspeeded_last_turn: bool = False
        
        # Sistema de Status (volátil, resetado entre batalhas)
        self.pokemon_status: Dict[str, str] = {}  # {pokemon_name: "BURN", "PARALYSIS", "POISON", etc}
        self.inferred_items: Dict[str, str] = {}  # {pokemon_name: "CHOICE_SCARF", "LIFE_ORB", etc}
        self.survival_turns: Dict[str, int] = {}  # {pokemon_name: turnos_restantes} para Toxic
        
        # ========== MEMÓRIA DE TURNO: Rastreamento de PP ==========
        # Formato: {pokemon_name: {move_name: pp_restante}}
        self.session_pp_usage: Dict[str, Dict[str, int]] = {}
        
        self._load_moves()

    # --------- API nova ---------
    def update_team_from_hud(self, ocr_results_list: List[str]):
        """Atualiza a equipe atual a partir dos nomes lidos no HUD (exploração)."""
        # Limita a 6 slots e normaliza
        self.current_team = [name.lower().strip() for name in ocr_results_list[:6] if name]

    def update_pokemon_moves(self, pokemon_name: str, moves_list: List[str]):
        """Atualiza golpes conhecidos de um pokémon (chamado na batalha)."""
        if not pokemon_name:
            return
        name = pokemon_name.lower().strip()
        if not name:
            return

        # Remove entradas vazias ou muito curtas dos golpes
        cleaned_moves = [m.strip() for m in moves_list if m and m.strip()]

        # Atualiza apenas se algo mudou para evitar escrita desnecessária em disco
        if name not in self.known_moves or self.known_moves[name] != cleaned_moves:
            self.known_moves[name] = cleaned_moves
            self._save_moves()

    def get_moves_for(self, pokemon_name: str) -> List[str]:
        if not pokemon_name:
            return []
        return self.known_moves.get(pokemon_name.lower().strip(), [])

    # --------- Compatibilidade com código existente ---------
    def save_moves(self, pokemon_name: str, moves: List[str]):
        """Wrapper para compatibilidade com código legado (usa API nova)."""
        self.update_pokemon_moves(pokemon_name, moves)

    def get_moves(self, pokemon_name: str) -> List[str]:
        """Wrapper para compatibilidade com BattleStrategy."""
        return self.get_moves_for(pokemon_name)

    def set_outspeeded_last_turn(self, value: bool):
        self.outspeeded_last_turn = bool(value)

    def get_outspeeded_last_turn(self) -> bool:
        return self.outspeeded_last_turn
    
    def set_status(self, pokemon_name: str, status: str):
        """Define o status de um Pokémon (BURN, PARALYSIS, POISON, TOXIC, SLEEP, FREEZE)."""
        if not pokemon_name:
            return
        key = pokemon_name.lower().strip()
        self.pokemon_status[key] = status.upper()
        
        # Se for TOXIC, inicia contador de sobrevivência
        if status.upper() == "TOXIC":
            self.survival_turns[key] = 8  # ~8 turnos até morte
    
    def get_status(self, pokemon_name: str) -> Optional[str]:
        """Retorna o status atual do Pokémon ou None."""
        if not pokemon_name:
            return None
        key = pokemon_name.lower().strip()
        return self.pokemon_status.get(key)
    
    def set_inferred_item(self, pokemon_name: str, item: str):
        """Define item inferido (CHOICE_SCARF, CHOICE_BAND, LIFE_ORB, etc)."""
        if not pokemon_name:
            return
        key = pokemon_name.lower().strip()
        self.inferred_items[key] = item.upper()
    
    def get_inferred_item(self, pokemon_name: str) -> Optional[str]:
        """Retorna item inferido ou None."""
        if not pokemon_name:
            return None
        key = pokemon_name.lower().strip()
        return self.inferred_items.get(key)
    
    def decrease_survival_turns(self, pokemon_name: str):
        """Decrementa contador de sobrevivência (Toxic/Burn)."""
        if not pokemon_name:
            return
        key = pokemon_name.lower().strip()
        if key in self.survival_turns:
            self.survival_turns[key] -= 1
    
    def get_survival_turns(self, pokemon_name: str) -> int:
        """Retorna turnos restantes antes de morte por status."""
        if not pokemon_name:
            return 999
        key = pokemon_name.lower().strip()
        return self.survival_turns.get(key, 999)
    
    def get_max_hp(self, pokemon_name: str) -> int:
        """Retorna HP máximo estimado do Pokémon."""
        stats = self.get_stats(pokemon_name)
        if stats:
            return stats.get('hp', 100)
        return 100  # Default
    
    def get_stats(self, pokemon_name: str) -> Optional[Dict[str, int]]:
        """Retorna stats calculados do Pokémon (HP, Atk, Def, SpA, SpD, Speed).
        
        Por enquanto, retorna stats base multiplicados por um fator de nível.
        No futuro, pode integrar com sistema de tracking de IVs/EVs.
        
        Args:
            pokemon_name: Nome do Pokémon
            
        Returns:
            Dict com keys: hp, attack, defense, special_attack, special_defense, speed
            Ou None se Pokémon não encontrado
        """
        if not pokemon_name:
            return None
        
        # Placeholder: Retorna stats estimados baseados em level 50 médio
        # TODO: Integrar com sistema real de stats tracking
        
        # Por enquanto, assume stats médios para level 50
        # Fórmula simplificada: stat = (base * 2 + 31 + 63) * level / 100 + 5
        # Para level 50: stat ≈ base + 55
        
        # Retorna stats fictícios até implementação completa
        # Na prática, isso deve vir de um banco de dados de stats base + cálculos
        return {
            'hp': 150,  # Placeholder
            'attack': 100,
            'defense': 100,
            'special_attack': 100,
            'special_defense': 100,
            'speed': 100  # Este é o importante para judge_speed_tier
        }
    
    # ========== SISTEMA DE RASTREAMENTO DE PP (Memória de Turno) ==========
    def initialize_pp_tracking(self, pokemon_name: str, moves_data: Dict[str, int]):
        """Inicializa rastreamento de PP para um Pokémon.
        
        Chamado quando um Pokémon entra em batalha ou é capturado.
        
        Args:
            pokemon_name: Nome do Pokémon
            moves_data: Dict {move_name: max_pp}
        """
        if not pokemon_name:
            return
        
        key = pokemon_name.lower().strip()
        if key not in self.session_pp_usage:
            self.session_pp_usage[key] = {}
        
        # Inicializa cada movimento com PP máximo
        for move_name, max_pp in moves_data.items():
            self.session_pp_usage[key][move_name] = max_pp
    
    def track_move_usage(self, pokemon_name: str, move_name: str, max_pp: int = None) -> int:
        """
        Registra o uso de um movimento e retorna PP restante.
        
        FUNÇÃO CRÍTICA: Se o bot travar, ele usa esse rastreamento para 
        saber quais movimentos ainda têm PP.
        
        Args:
            pokemon_name: Nome do Pokémon
            move_name: Nome do movimento
            max_pp: PP máximo (opcional, se não rastreado antes)
            
        Returns:
            int: PP restante após usar o movimento (0 = sem PP)
        """
        if not pokemon_name or not move_name:
            return 0
        
        poke_key = pokemon_name.lower().strip()
        move_key = move_name.lower().strip()
        
        # Inicializa Pokémon se não existe
        if poke_key not in self.session_pp_usage:
            self.session_pp_usage[poke_key] = {}
        
        # Inicializa movimento se não existe
        if move_key not in self.session_pp_usage[poke_key]:
            self.session_pp_usage[poke_key][move_key] = max_pp or 0
        
        # Decrementa PP (nunca nega)
        current_pp = self.session_pp_usage[poke_key][move_key]
        self.session_pp_usage[poke_key][move_key] = max(0, current_pp - 1)
        
        return self.session_pp_usage[poke_key][move_key]
    
    def get_move_pp(self, pokemon_name: str, move_name: str) -> int:
        """Retorna PP restante de um movimento (0 = sem PP)."""
        if not pokemon_name or not move_name:
            return 0
        
        poke_key = pokemon_name.lower().strip()
        move_key = move_name.lower().strip()
        
        return self.session_pp_usage.get(poke_key, {}).get(move_key, 0)
    
    def get_available_moves(self, pokemon_name: str) -> List[str]:
        """
        Retorna lista de movimentos que AINDA TÊM PP.
        
        Crítico para seleção de movimentos quando o bot reinicia em meio a batalha.
        
        Args:
            pokemon_name: Nome do Pokémon
            
        Returns:
            Lista de nomes de movimentos com PP > 0
        """
        if not pokemon_name:
            return []
        
        poke_key = pokemon_name.lower().strip()
        if poke_key not in self.session_pp_usage:
            # Se não há rastreamento, retorna todos os movimentos conhecidos
            return self.get_moves(pokemon_name)
        
        # Filtra apenas movimentos com PP > 0
        available = [
            move_name 
            for move_name, pp in self.session_pp_usage[poke_key].items()
            if pp > 0
        ]
        
        return available or ["struggle"]  # Fallback para Struggle se sem PP
    
    def pp_summary(self, pokemon_name: str) -> Dict[str, int]:
        """Retorna sumário de PP: {move_name: pp_restante}."""
        if not pokemon_name:
            return {}
        
        poke_key = pokemon_name.lower().strip()
        return self.session_pp_usage.get(poke_key, {})
    
    def reset_pp_session(self):
        """Limpa rastreamento de PP (fim de batalha ou nova sessão)."""
        self.session_pp_usage.clear()

    # --------- Persistência interna ---------
    def _load_moves(self):
        if self.moves_db_path.exists():
            with self.moves_db_path.open('r', encoding='utf-8') as f:
                self.known_moves = json.load(f)

    def _save_moves(self):
        self.moves_db_path.parent.mkdir(parents=True, exist_ok=True)
        with self.moves_db_path.open('w', encoding='utf-8') as f:
            json.dump(self.known_moves, f, indent=2, ensure_ascii=False)