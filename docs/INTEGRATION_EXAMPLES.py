"""
Exemplo de Integração do Chat Handler no Bot Principal

Este arquivo mostra como integrar o sistema de chat com IA no loop principal do bot.
"""

from src.perception.chat_handler import ChatHandler
from src.action.input_simulator import InputSimulator
from src.perception.game_state_detector import GameStateDetector
from src.core.bot_controller import BotController
import yaml


def exemplo_integracao_chat():
    """Exemplo de como integrar o ChatHandler no bot."""
    
    # 1. Carregar configuração
    with open('config/settings.yaml', 'r', encoding='utf-8') as f:
        config = yaml.safe_load(f)
    
    # 2. Inicializar componentes
    input_sim = InputSimulator(config)
    chat_handler = ChatHandler(config, input_sim)
    
    # 3. No loop principal do bot, adicionar detecção de chat
    # (Pseudo-código - adaptar ao seu bot_controller.py)
    
    # Exemplo de uso:
    if chat_handler.enabled:
        # Supondo que você tenha uma ROI para chat no settings.yaml
        chat_roi = config.get('rois', {}).get('chat_area')
        
        if chat_roi:
            # Recortar área do chat
            chat_img = screen[chat_roi[1]:chat_roi[3], chat_roi[0]:chat_roi[2]]
            
            # Extrair texto com OCR
            chat_text = ocr_engine.extract_text_optimized(
                chat_img,
                whitelist="ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0-9 .,!?",
                invert_for_white_text=True
            )
            
            # Processar e responder se apropriado
            if chat_text:
                chat_handler.handle_detected_chat(chat_text)


def exemplo_uso_acoes_idle():
    """Exemplo de como usar ações idle no loop principal."""
    
    with open('config/settings.yaml', 'r', encoding='utf-8') as f:
        config = yaml.safe_load(f)
    
    input_sim = InputSimulator(config)
    
    # No loop principal, chamar periodicamente:
    # (Isso já verifica internamente se passou tempo suficiente)
    input_sim.perform_idle_action()


def exemplo_uso_deteccao_hp():
    """Exemplo de como usar detecção de HP na batalha."""
    
    with open('config/settings.yaml', 'r', encoding='utf-8') as f:
        config = yaml.safe_load(f)
    
    from src.perception.screen_capture import ScreenCapture
    from src.perception.ocr_engine import OCREngine
    from src.decision.battle_strategy import BattleStrategy
    from src.knowledge.pokemon_database import PokemonDatabase
    from src.knowledge.team_manager import TeamManager
    
    screen_cap = ScreenCapture(config)
    ocr = OCREngine(config)
    detector = GameStateDetector(screen_cap, ocr, config)
    
    db = PokemonDatabase()
    tm = TeamManager()
    strategy = BattleStrategy(db, tm, config)
    
    # Capturar tela
    screen = screen_cap.capture()
    
    # Obter informações de batalha (inclui HP agora)
    battle_info = detector.get_battle_info(screen)
    
    print(f"Player: {battle_info['player_name']}")
    print(f"Player HP: {battle_info['player_hp_percentage']}%")
    print(f"Enemy: {battle_info['enemy_name']}")
    print(f"Enemy HP: {battle_info['enemy_hp_percentage']}%")
    
    # Decidir se deve usar item
    if strategy.should_use_item(battle_info['player_hp_percentage']):
        print("❗ Recomendação: Usar item de cura!")
        # input_simulator.click_bag_button()
        # input_simulator.click_potion()
    
    # Decidir se deve trocar Pokémon
    if strategy.should_switch_pokemon(
        battle_info['player_hp_percentage'],
        battle_info['enemy_name']
    ):
        print("❗ Recomendação: Trocar de Pokémon!")
        # input_simulator.click_pokemon_button()
        # input_simulator.click_in_party_slot(1)


def exemplo_loop_completo():
    """Exemplo de loop principal com todas as melhorias integradas."""
    
    import time
    import yaml
    from loguru import logger
    
    # Carregar config
    with open('config/settings.yaml', 'r', encoding='utf-8') as f:
        config = yaml.safe_load(f)
    
    # Inicializar componentes (simplificado)
    from src.perception.screen_capture import ScreenCapture
    from src.perception.ocr_engine import OCREngine
    from src.perception.game_state_detector import GameStateDetector, GameState
    from src.action.input_simulator import InputSimulator
    from src.decision.battle_strategy import BattleStrategy
    from src.knowledge.pokemon_database import PokemonDatabase
    from src.knowledge.team_manager import TeamManager
    from src.perception.chat_handler import ChatHandler
    
    screen_cap = ScreenCapture(config)
    ocr = OCREngine(config)
    detector = GameStateDetector(screen_cap, ocr, config)
    input_sim = InputSimulator(config)
    
    db = PokemonDatabase()
    tm = TeamManager()
    strategy = BattleStrategy(db, tm, config)
    chat_handler = ChatHandler(config, input_sim)
    
    logger.info("🤖 Bot iniciado com todas as melhorias de humanização!")
    
    while True:
        try:
            # 1. Capturar tela
            screen = screen_cap.capture()
            
            # 2. Detectar estado do jogo
            state = detector.detect_state(screen)
            
            # 3. Ação idle ocasional (se não estiver em batalha)
            if state == GameState.EXPLORING:
                input_sim.perform_idle_action()
            
            # 4. Processar batalha
            if state == GameState.IN_BATTLE:
                battle_info = detector.get_battle_info(screen)
                
                logger.info(f"⚔️ Batalha: {battle_info['player_name']} vs {battle_info['enemy_name']}")
                logger.info(f"HP: Player={battle_info['player_hp_percentage']}% | Enemy={battle_info['enemy_hp_percentage']}%")
                
                # Verificar se deve fugir
                if strategy.should_flee(battle_info['player_name'], battle_info['enemy_name']):
                    logger.info("🏃 Fugindo da batalha!")
                    input_sim.click_run_button()
                    time.sleep(2)
                    continue
                
                # Verificar se deve usar item
                if strategy.should_use_item(battle_info['player_hp_percentage']):
                    logger.warning("❤️ HP crítico! Usando item de cura...")
                    # Implementar lógica de usar item aqui
                    time.sleep(1)
                    continue
                
                # Verificar se deve trocar Pokémon
                if strategy.should_switch_pokemon(
                    battle_info['player_hp_percentage'],
                    battle_info['enemy_name']
                ):
                    logger.warning("🔄 HP baixo! Trocando Pokémon...")
                    # Implementar lógica de troca aqui
                    time.sleep(1)
                    continue
                
                # Escolher e usar melhor movimento
                best_move = strategy.get_best_move(
                    battle_info['player_name'],
                    battle_info['enemy_name']
                )
                
                logger.info(f"🎯 Usando movimento no slot {best_move}")
                
                # Clicar em Fight
                input_sim.click_fight_button(screen)
                time.sleep(0.5)
                
                # Clicar no movimento escolhido
                input_sim.click_in_slot(best_move)
                
                # Esperar turno terminar
                time.sleep(3)
            
            # 5. Processar chat (se ativado)
            if chat_handler.enabled and state == GameState.EXPLORING:
                # TODO: Implementar detecção de mensagens no chat
                # chat_text = extrair_texto_do_chat(screen)
                # chat_handler.handle_detected_chat(chat_text)
                pass
            
            # 6. Sleep do loop principal
            time.sleep(config.get('bot', {}).get('loop_interval', 1.0))
            
        except KeyboardInterrupt:
            logger.info("🛑 Bot parado pelo usuário")
            break
        except Exception as e:
            logger.error(f"❌ Erro no loop principal: {e}")
            time.sleep(5)


if __name__ == "__main__":
    # Executar exemplo
    print("=== Exemplo de Detecção de HP ===")
    exemplo_uso_deteccao_hp()
    
    print("\n=== Exemplo de Ações Idle ===")
    exemplo_uso_acoes_idle()
    
    # Para testar o loop completo, descomente:
    # exemplo_loop_completo()
