#!/usr/bin/env python3
"""
Interactive ROI/coordinate picker.

Usage:
  - Run: `python tools/roi_picker.py`
  - Draw rectangles with left mouse: click-drag-release.
  - After releasing, press `n` to give a name to the ROI and store it.
  - Press `s` to save all collected ROIs to a JSON/YAML file (default: `rois_collected.json`).
  - Press `c` to clear last ROI, `C` to clear all, `q` or ESC to quit.

The script will try to use `mss` for fast screenshots, falling back to `pyautogui`.
It will print coordinates in both formats: [x,y,w,h] and [x1,y1,x2,y2].

This is a lightweight tool intended to help you pick areas to paste into `config/settings.yaml`.
"""

import json
import os
import argparse
import cv2
import numpy as np

try:
    import mss
    _HAS_MSS = True
except Exception:
    _HAS_MSS = False

try:
    import pyperclip
    _HAS_CLIP = True
except Exception:
    _HAS_CLIP = False

try:
    import pyautogui
    _HAS_PYA = True
except Exception:
    _HAS_PYA = False


class ROIPicker:
    def __init__(self, output_path=None, window_name='ROI Picker'):
        self.output_path = output_path or 'rois_collected.json'
        self.window_name = window_name
        self.rois = []  # list of dicts: {name, x,y,w,h, x1,y1,x2,y2}
        self.drawing = False
        self.start = (0, 0)
        self.end = (0, 0)
        self.img = None
        self.display_img = None

    def grab_screen(self):
        if _HAS_MSS:
            with mss.mss() as sct:
                monitor = sct.monitors[1]
                sct_img = sct.grab(monitor)
                img = np.array(sct_img)
                # mss returns BGRA
                if img.shape[2] == 4:
                    img = cv2.cvtColor(img, cv2.COLOR_BGRA2BGR)
                return img
        elif _HAS_PYA:
            img = pyautogui.screenshot()
            img = cv2.cvtColor(np.array(img), cv2.COLOR_RGB2BGR)
            return img
        else:
            raise RuntimeError('No screenshot backend found. Install `mss` or `pyautogui`.')

    def mouse_callback(self, event, x, y, flags, param):
        if event == cv2.EVENT_LBUTTONDOWN:
            self.drawing = True
            self.start = (x, y)
            self.end = (x, y)
        elif event == cv2.EVENT_MOUSEMOVE and self.drawing:
            self.end = (x, y)
            self.update_display()
        elif event == cv2.EVENT_LBUTTONUP:
            self.drawing = False
            self.end = (x, y)
            self.update_display()
            self.store_last_roi()

    def update_display(self):
        self.display_img = self.img.copy()
        cv2.rectangle(self.display_img, self.start, self.end, (0, 255, 0), 2)
        self.show_instructions()

    def show_instructions(self):
        text_lines = [
            'Left-drag: draw ROI | n: name last | s: save | c: clear last | C: clear all | q/ESC: quit',
            f'Collected: {len(self.rois)}'
        ]
        y = 20
        for line in text_lines:
            cv2.putText(self.display_img, line, (10, y), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1, cv2.LINE_AA)
            y += 20

    def store_last_roi(self):
        x1, y1 = self.start
        x2, y2 = self.end
        x_min = min(x1, x2)
        y_min = min(y1, y2)
        x_max = max(x1, x2)
        y_max = max(y1, y2)
        w = x_max - x_min
        h = y_max - y_min

        if w <= 0 or h <= 0:
            print('ROI inválida (zero width/height) - ignorando')
            return

        roi = {
            'name': f'roi_{len(self.rois)+1}',
            'xywh': [int(x_min), int(y_min), int(w), int(h)],
            'coords': [int(x_min), int(y_min), int(x_max), int(y_max)]
        }
        self.rois.append(roi)
        print('ROI armazenada:', roi)

    def name_last(self):
        if not self.rois:
            print('Nenhuma ROI para nomear')
            return
        name = input('Nome para a última ROI: ').strip()
        if name:
            self.rois[-1]['name'] = name
            print('Renomeada para', name)

    def clear_last(self):
        if self.rois:
            removed = self.rois.pop()
            print('Removida ROI:', removed)
        else:
            print('Nenhuma ROI para remover')

    def clear_all(self):
        self.rois = []
        print('Todas as ROIs removidas')

    def save(self):
        data = {roi['name']: roi['xywh'] for roi in self.rois}
        with open(self.output_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        print(f'Salvo {len(self.rois)} ROIs em {self.output_path}')
        print('Also printing alternate format [x1,y1,x2,y2]:')
        alt = {roi['name']: roi['coords'] for roi in self.rois}
        print(json.dumps(alt, indent=2, ensure_ascii=False))
        if _HAS_CLIP:
            try:
                pyperclip.copy(json.dumps(data))
                print('(copied [x,y,w,h] JSON to clipboard)')
            except Exception:
                pass

    def run(self):
        print('Capturando tela...')
        self.img = self.grab_screen()
        self.display_img = self.img.copy()
        cv2.namedWindow(self.window_name, cv2.WINDOW_NORMAL)
        cv2.setMouseCallback(self.window_name, self.mouse_callback)

        while True:
            self.show_instructions()
            cv2.imshow(self.window_name, self.display_img)
            key = cv2.waitKey(20) & 0xFF
            if key == ord('q') or key == 27:
                break
            elif key == ord('n'):
                self.name_last()
            elif key == ord('s'):
                self.save()
            elif key == ord('c'):
                self.clear_last()
            elif key == ord('C'):
                self.clear_all()
            elif key == ord('r'):
                # Refresh screenshot
                self.img = self.grab_screen()
                self.display_img = self.img.copy()

        cv2.destroyAllWindows()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--out', '-o', help='Output JSON file', default='rois_collected.json')
    args = parser.parse_args()

    picker = ROIPicker(output_path=args.out)
    try:
        picker.run()
    except Exception as e:
        print('Erro:', e)


if __name__ == '__main__':
    main()
