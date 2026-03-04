import logging
try:
    import pygetwindow as gw
except Exception:
    gw = None


class WindowHandler:
    def __init__(self, window_title="PokeOne"):
        self.window_title = window_title

    def get_window_rect(self):
        """Retorna (x, y, width, height) da janela ativa."""
        if gw is None:
            return None
        try:
            windows = gw.getWindowsWithTitle(self.window_title)
            if windows:
                win = windows[0]
                if win.isMinimized:
                    win.restore()
                return win.left, win.top, win.width, win.height
            return None
        except Exception as e:
            logging.error(f"Erro ao detectar janela: {e}")
            return None

    def get_relative_coords(self, rel_x, rel_y, win_rect):
        """Converte 0.0-1.0 em pixels reais da janela."""
        x_base, y_base, w, h = win_rect
        return int(x_base + (rel_x * w)), int(y_base + (rel_y * h))
