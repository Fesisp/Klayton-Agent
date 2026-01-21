def normalize_roi(roi_coords):
    """
    Normaliza coordenadas de região de interesse (ROI).
    Aceita lista/tupla de 4 números.
    Tenta inferir se é [x1, y1, x2, y2] ou [x, y, w, h].
    Retorna (x1, y1, x2, y2) como inteiros.
    """
    if not roi_coords or len(roi_coords) != 4:
        return None

    x1, y1, x2, y2 = map(int, roi_coords)

    # Heurística: se x2 <= x1 ou y2 <= y1, assume formato [x, y, w, h]
    if x2 <= x1 or y2 <= y1:
        w, h = x2, y2 # O que foi lido nos slots 3 e 4
        x, y = x1, y1 # O que foi lido nos slots 1 e 2
        x1 = x
        y1 = y
        x2 = x + w
        y2 = y + h
        
    return x1, y1, x2, y2

def crop_roi_safe(image, roi_coords):
    """
    Recorta uma ROI da imagem de forma segura (respeitando bordas).
    Aceita [x1,y1,x2,y2] ou [x,y,w,h].
    """
    coords = normalize_roi(roi_coords)
    if not coords:
        return image
    
    x1, y1, x2, y2 = coords
    h_img, w_img = image.shape[:2]
    
    # Clamp (garante que está dentro da imagem)
    x1 = max(0, min(x1, w_img - 1))
    x2 = max(0, min(x2, w_img))
    y1 = max(0, min(y1, h_img - 1))
    y2 = max(0, min(y2, h_img))
    
    if x2 <= x1 or y2 <= y1:
        return image # Retorna original se recorte for inválido
        
    return image[y1:y2, x1:x2]


def get_safe_random_point(roi_coords, margin_pct=0.2):
    """
    Retorna um ponto (x, y) aleatório seguro dentro de uma ROI.
    """
    import random
    coords = normalize_roi(roi_coords)
    if not coords:
        return 0, 0
    
    x1, y1, x2, y2 = coords
    w = x2 - x1
    h = y2 - y1
    
    margin_x = int(margin_pct * w)
    margin_y = int(margin_pct * h)
    
    safe_x1 = x1 + margin_x
    safe_x2 = x2 - margin_x
    safe_y1 = y1 + margin_y
    safe_y2 = y2 - margin_y
    
    if safe_x2 <= safe_x1 or safe_y2 <= safe_y1:
        cx = x1 + w // 2
        cy = y1 + h // 2
    else:
        cx = random.randint(safe_x1, safe_x2)
        cy = random.randint(safe_y1, safe_y2)
        
    return cx, cy
