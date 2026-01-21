import pyautogui
import time
import cv2
import numpy as np
import os
from ..utils.geometry import normalize_roi, get_safe_random_point

class InputSimulator:
    def __init__(self, config=None):
        # Desabilita o fail-safe para evitar paradas bruscas se o mouse for para o canto
        # CUIDADO: Isso impede que você pare o bot movendo o mouse para o canto!
        pyautogui.FAILSAFE = False
        self.cfg = config or {}
        self.rois = self.cfg.get('rois', {})
        self.move_duration = float(self.cfg.get('input', {}).get('mouse_move_duration', 0.0))
        
        # Preload templates to avoid IO on every click
        assets_dir = self.cfg.get('assets', {}).get('templates_dir', '')
        
        # Fight
        fight_img_name = self.cfg.get('assets', {}).get('fight_image', 'fight.png')
        self.fight_template = None
        if assets_dir and fight_img_name:
            import os
            path = os.path.join(assets_dir, fight_img_name)
            if os.path.exists(path):
                self.fight_template = cv2.imread(path)

        # Pokemon
        poke_img_name = self.cfg.get('assets', {}).get('pokemon_image', 'pokemon.png')
        self.pokemon_template = None
        if assets_dir and poke_img_name:
            import os
            path = os.path.join(assets_dir, poke_img_name)
            if os.path.exists(path):
                self.pokemon_template = cv2.imread(path)

        # Run
        run_img_name = self.cfg.get('assets', {}).get('run_image', 'run.png')
        self.run_template = None
        if assets_dir and run_img_name:
            import os
            path = os.path.join(assets_dir, run_img_name)
            if os.path.exists(path):
                self.run_template = cv2.imread(path)

    def click(self, x, y):
        if self.move_duration and self.move_duration > 0:
            pyautogui.moveTo(x, y, duration=self.move_duration)
            pyautogui.click()
        else:
            pyautogui.click(x, y)

    def press(self, key):
        pyautogui.press(key)
    
    def click_in_slot(self, slot_index):
        """Clica aproximadamente no centro de um dos 4 slots de ataque (0-3)."""
        slot_map = {
            0: 'slot_1',
            1: 'slot_2',
            2: 'slot_3',
            3: 'slot_4',
        }
        key = slot_map.get(slot_index)
        if not key:
            return
        moves_rois = self.rois.get('moves', {})
        coords = moves_rois.get(key)
        
        # Simplificado usando função utilitária
        cx, cy = get_safe_random_point(coords, 0.2)
        
        self.click(cx, cy)

    def click_fight_button(self, screen_img=None):
        """Clica no botão FIGHT usando o template fight.png."""
        self._click_template(self.fight_template, 'fight_threshold', screen_img)


    def click_pokemon_button(self, screen_img=None):
        """Clica no botão POKEMON usando o template pokemon.png."""
        self._click_template(self.pokemon_template, 'pokemon_threshold', screen_img)


    def click_run_button(self, screen_img=None):
        """Clica no botão RUN usando o template run.png."""
        self._click_template(self.run_template, 'run_threshold', screen_img)


    def _click_template(self, template, threshold_key, screen_img=None, margin_pct=0.2):
        """
        Generic helper to find and click a template.
        """
        if template is None:
            return False

        if screen_img is not None:
            screenshot = screen_img
        else:
            screenshot = pyautogui.screenshot()
            screenshot = cv2.cvtColor(np.array(screenshot), cv2.COLOR_RGB2BGR)

        res = cv2.matchTemplate(screenshot, template, cv2.TM_CCOEFF_NORMED)
        _, max_val, _, max_loc = cv2.minMaxLoc(res)

        thresh = float(self.cfg.get('detection', {}).get(threshold_key, 0.85))
        if max_val < thresh:
            return False

        h, w = template.shape[:2]
        x, y = max_loc
        
        # Constrói ROI [x, y, w, h] que será normalizada na função utilitária
        roi = [x, y, w, h]
        cx, cy = get_safe_random_point(roi, margin_pct)

        self.click(cx, cy)
        return True