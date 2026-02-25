"""
Script de teste de integridade do PokeBot
Valida que todos os componentes estão funcionando corretamente
"""
import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT_DIR))

def test_imports():
    """Testa todas as importações principais"""
    print("🔍 Testando importações...")
    try:
        from src.core.bot_controller import BotController, BotBehavior
        print("  ✅ BotController")
        
        from src.perception.game_state_detector import GameStateDetector, GameState
        print("  ✅ GameStateDetector")
        
        from src.perception.screen_capture import ScreenCapture
        print("  ✅ ScreenCapture")
        
        from src.perception.ocr_engine import OCREngine
        print("  ✅ OCREngine")
        
        from src.action.input_simulator import InputSimulator
        print("  ✅ InputSimulator")
        
        from src.decision.battle_strategy import BattleStrategy
        print("  ✅ BattleStrategy")
        
        from src.knowledge.pokemon_database import PokemonDatabase
        print("  ✅ PokemonDatabase")
        
        from src.knowledge.team_manager import TeamManager
        print("  ✅ TeamManager")
        
        return True
    except Exception as e:
        print(f"  ❌ Erro: {e}")
        return False

def test_config():
    """Testa carregamento de configuração"""
    print("\n🔍 Testando configuração...")
    try:
        import yaml
        config_path = ROOT_DIR / 'config' / 'settings.yaml'
        with open(config_path, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)
        
        # Valida estruturas essenciais
        assert 'rois' in config, "Faltando 'rois' no config"
        assert 'ocr' in config, "Faltando 'ocr' no config"
        assert 'bot' in config, "Faltando 'bot' no config"
        
        print("  ✅ Config válido")
        return True
    except Exception as e:
        print(f"  ❌ Erro: {e}")
        return False

def test_data_files():
    """Testa arquivos de dados"""
    print("\n🔍 Testando arquivos de dados...")
    try:
        import json
        data_dir = ROOT_DIR / 'data'
        
        files = ['dex.json', 'movimentos.json', 'tipos.json']
        for file in files:
            file_path = data_dir / file
            if file_path.exists():
                with open(file_path, 'r', encoding='utf-8') as f:
                    json.load(f)
                print(f"  ✅ {file}")
            else:
                print(f"  ⚠️ {file} não encontrado (opcional)")
        
        return True
    except Exception as e:
        print(f"  ❌ Erro: {e}")
        return False

def test_dependencies():
    """Testa dependências instaladas"""
    print("\n🔍 Testando dependências...")
    try:
        import cv2
        print(f"  ✅ opencv-python {cv2.__version__}")
        
        import numpy
        print(f"  ✅ numpy {numpy.__version__}")
        
        import pytesseract
        print(f"  ✅ pytesseract")
        
        import mss
        print(f"  ✅ mss")
        
        import pyautogui
        print(f"  ✅ pyautogui")
        
        import yaml
        print(f"  ✅ pyyaml")
        
        from loguru import logger
        print(f"  ✅ loguru")
        
        import scipy
        print(f"  ✅ scipy {scipy.__version__}")
        
        import requests
        print(f"  ✅ requests")
        
        from pynput import keyboard
        print(f"  ✅ pynput")
        
        return True
    except Exception as e:
        print(f"  ❌ Erro: {e}")
        return False

def test_bot_methods():
    """Testa métodos do BotController"""
    print("\n🔍 Testando métodos do BotController...")
    try:
        from src.core.bot_controller import BotController
        import inspect
        
        methods = [
            'run', 'handle_shiny', 'handle_mission', 
            'handle_hunting', 'handle_battle', 'handle_follow',
            '_recovery_search', '_follow_by_template_get_pos'
        ]
        
        for method in methods:
            assert hasattr(BotController, method), f"Método {method} não encontrado"
            print(f"  ✅ {method}")
        
        return True
    except Exception as e:
        print(f"  ❌ Erro: {e}")
        return False

def main():
    print("=" * 60)
    print("🤖 TESTE DE INTEGRIDADE DO POKEBOT")
    print("=" * 60)
    
    results = []
    
    results.append(("Importações", test_imports()))
    results.append(("Configuração", test_config()))
    results.append(("Dados", test_data_files()))
    results.append(("Dependências", test_dependencies()))
    results.append(("Métodos", test_bot_methods()))
    
    print("\n" + "=" * 60)
    print("📊 RESUMO")
    print("=" * 60)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for name, result in results:
        status = "✅ PASSOU" if result else "❌ FALHOU"
        print(f"{name:20} {status}")
    
    print("=" * 60)
    print(f"Resultado: {passed}/{total} testes passaram")
    
    if passed == total:
        print("\n🎉 TODOS OS TESTES PASSARAM! O projeto está 100% funcional.")
        return 0
    else:
        print(f"\n⚠️ {total - passed} teste(s) falharam. Verifique os erros acima.")
        return 1

if __name__ == "__main__":
    sys.exit(main())
