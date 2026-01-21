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

    # --------- Persistência interna ---------
    def _load_moves(self):
        if self.moves_db_path.exists():
            with self.moves_db_path.open('r', encoding='utf-8') as f:
                self.known_moves = json.load(f)

    def _save_moves(self):
        self.moves_db_path.parent.mkdir(parents=True, exist_ok=True)
        with self.moves_db_path.open('w', encoding='utf-8') as f:
            json.dump(self.known_moves, f, indent=2, ensure_ascii=False)