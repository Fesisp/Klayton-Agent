import cv2
import numpy as np
import pytesseract
from loguru import logger
import re
import os
from difflib import get_close_matches


class OCREngine:
    def __init__(self, tesseract_path):
        if not os.path.exists(tesseract_path):
            logger.error(f"Tesseract não encontrado em: {tesseract_path}")
        pytesseract.pytesseract.tesseract_cmd = tesseract_path
        
        # Carrega moves conhecidos de data/known_moves.json
        self.known_moves = []
        try:
            base_dir = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
            known_path = os.path.join(base_dir, "data", "known_moves.json")
            if os.path.exists(known_path):
                import json
                with open(known_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                
                # Extrai nomes únicos
                moves_set = set()
                for moves in data.values():
                    if isinstance(moves, list):
                        for m in moves:
                            if isinstance(m, str) and m:
                                moves_set.add(m)
                self.known_moves = list(moves_set)
        except Exception as e:
            logger.error(f"Erro ao carregar known_moves.json: {e}")
            self.known_moves = []

    def process_dynamic_background_text(self, image):
        """Isola texto branco brilhante em fundo colorido (botões de moves / HUD).
        Migrado de ImageProcessor.
        """
        if image is None or image.size == 0:
            return image

        # Upscaling (3x) com interpolação cúbica
        h, w = image.shape[:2]
        img_big = cv2.resize(image, (w * 3, h * 3), interpolation=cv2.INTER_CUBIC)

        # Converter para HSV
        hsv = cv2.cvtColor(img_big, cv2.COLOR_BGR2HSV)

        # Filtro de branco: baixa saturação, alto valor
        lower_white = np.array([0, 0, 140])
        upper_white = np.array([180, 60, 255])
        mask = cv2.inRange(hsv, lower_white, upper_white)

        # Pequena limpeza de ruído e leve engrossamento
        kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (2, 2))
        mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel)

        # Inverte para texto preto em fundo branco
        inverted = cv2.bitwise_not(mask)
        inverted = cv2.erode(inverted, kernel, iterations=1)

        # Padding branco para o Tesseract não cortar letras
        final_img = cv2.copyMakeBorder(
            inverted, 20, 20, 20, 20, cv2.BORDER_CONSTANT, value=(255, 255, 255)
        )
        return final_img

    def extract_text_optimized(self, image, whitelist=None, invert_for_white_text=False):
        """Extrai texto com pré-processamento forte e suporte a texto branco.

        - Faz upscale para melhorar fontes pequenas.
        - Aplica sharpen + binarização.
        - Quando ``invert_for_white_text`` é True, destaca texto branco/brilhante.
        - Aceita ``whitelist`` de caracteres para melhorar precisão.
        """
        try:
            if image is None or image.size == 0:
                return ""

            # Upscale para melhorar leitura de fontes pequenas
            img_big = cv2.resize(image, None, fx=2, fy=2, interpolation=cv2.INTER_CUBIC)

            if invert_for_white_text:
                # Converter para HSV e pegar apenas regiões bem claras (texto branco)
                # img_big pode ser BGR (3 canais) ou já estar em escala de cinza (1 canal)
                if len(img_big.shape) == 2 or img_big.shape[2] == 1:
                    # Já é 1 canal: usa diretamente como máscara base
                    ocr_img = img_big
                else:
                    hsv = cv2.cvtColor(img_big, cv2.COLOR_BGR2HSV)
                    lower_white = np.array([0, 0, 200])
                    upper_white = np.array([255, 60, 255])
                    mask = cv2.inRange(hsv, lower_white, upper_white)
                    ocr_img = mask
            else:
                # Modo genérico: escala de cinza
                if len(img_big.shape) == 2 or img_big.shape[2] == 1:
                    gray = img_big
                else:
                    gray = cv2.cvtColor(img_big, cv2.COLOR_BGR2GRAY)

                # Sharpen leve para destacar bordas do texto
                kernel = np.array([[0, -1, 0],
                                   [-1, 5, -1],
                                   [0, -1, 0]])
                sharp = cv2.filter2D(gray, -1, kernel)
                # Binarização adaptativa
                ocr_img = cv2.adaptiveThreshold(
                    sharp, 255,
                    cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
                    cv2.THRESH_BINARY,
                    11,
                    2
                )

            # Configuração do Tesseract
            config = "--psm 7 --oem 1"
            if whitelist:
                config += f" -c tessedit_char_whitelist={whitelist}"

            text = pytesseract.image_to_string(ocr_img, config=config)
            return text.strip()
        except Exception as e:
            logger.error(f"Erro no OCR Otimizado: {e}")
            return ""

    def read_text(self, processed_image, mode: str = "line") -> str:
        """Lê texto de uma imagem já pré-processada.

        mode="line": nomes (Charmeleon, Caterpie)
        mode="block": textos em duas linhas (golpes com PP, etc.)
        """
        try:
            psm = 7 if mode == "line" else 6
            config = (
                f"--oem 1 --psm {psm} "
                "-c tessedit_char_whitelist="
                "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789- "
            )
            text = pytesseract.image_to_string(processed_image, config=config)
            return text.strip()
        except Exception as e:
            logger.error(f"Erro no OCR (read_text): {e}")
            return ""


    def clean_move_name(self, text: str) -> str:
        """Normaliza o nome do golpe extraído pelo OCR.

        - Remove PP e lixo do texto do golpe (ex: 'Ember 23/25' -> 'Ember').
        - Aplica uma correção leve usando similaridade com golpes conhecidos
          para corrigir erros comuns de OCR (ex: 'SanadAttack' -> 'Sand Attack').
        """
        if not text:
            return ""

        # Pega apenas letras, espaços e hífen do início, ignorando números e '/'
        match = re.match(r"([a-zA-Z\s\-]+)", text)
        if not match:
            return ""

        clean = match.group(1).strip()
        if len(clean) < 3:
            return ""

        # Correção de similaridade com base na lista de golpes conhecidos (já carregada no init)
        if self.known_moves:
            try:
                # Tenta casar o texto limpo com algum golpe conhecido
                candidates = get_close_matches(clean, self.known_moves, n=1, cutoff=0.8)
                if candidates:
                    return candidates[0]
            except Exception as e:
                logger.error(f"Erro ao tentar corrigir nome de golpe via similaridade: {e}")

        return clean

    def ocr_party_list(self, image_roi):
        """OCR especializado para listas de equipe (texto branco em fundo escuro).

        Usado para ler nomes de Pokémon tanto no HUD quanto no menu de troca.
        """
        try:
            if image_roi is None or image_roi.size == 0:
                return []

            # 1. Upscaling forte para fontes pequenas
            img_big = cv2.resize(
                image_roi,
                None,
                fx=4,
                fy=4,
                interpolation=cv2.INTER_NEAREST,
            )

            # 2. Binarização focada em texto claro
            gray = cv2.cvtColor(img_big, cv2.COLOR_BGR2GRAY)
            _, binary = cv2.threshold(gray, 180, 255, cv2.THRESH_BINARY)

            # 3. Inversão (texto preto em fundo branco)
            inverted = cv2.bitwise_not(binary)

            # 4. Afinar ruído / engrossar traços do texto
            kernel = np.ones((2, 2), np.uint8)
            inverted = cv2.erode(inverted, kernel, iterations=1)

            # 5. Tesseract configurado para bloco de texto (várias linhas)
            config = (
                "--psm 6 "
                "-c tessedit_char_whitelist="
                "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789"
            )

            text = pytesseract.image_to_string(inverted, config=config)

            # 6. Limpeza das linhas
            names = [line.strip() for line in text.split("\n") if line.strip()]

            clean_names = []
            for line in names:
                parts = line.split()
                # Remove partes com Lv, números isolados etc.
                name_parts = [p for p in parts if not p.startswith("Lv")]
                if name_parts:
                    clean_names.append(" ".join(name_parts))

            return clean_names
        except Exception as e:
            logger.error(f"Erro no OCR de lista de equipe: {e}")
            return []