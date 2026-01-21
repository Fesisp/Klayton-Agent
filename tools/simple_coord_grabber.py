import time
import pyautogui
from loguru import logger


def main():
    logger.info("Ferramenta simples de captura de coordenadas iniciada.")
    logger.info("Você terá 3 segundos para posicionar o mouse.")
    time.sleep(3)

    logger.info("Capturando coordenadas. Pressione Ctrl+C para sair.")

    try:
        while True:
            x, y = pyautogui.position()
            print(f"Posição atual do mouse: x={x}, y={y}")
            time.sleep(0.5)
    except KeyboardInterrupt:
        logger.info("Encerrando captura de coordenadas.")


if __name__ == "__main__":
    main()
