import cv2
import numpy as np

def applySticker(background, foreground, pos_x=None, pos_y=None):
    """
    Cola um sticker (foreground) com canal alpha em um fundo (background),
    ajustando posição pelo centro e cortando se ultrapassar as bordas.

    Parameters:
        background: numpy.ndarray
            Imagem de fundo (BGR).
        foreground: numpy.ndarray
            Imagem do sticker (RGBA, com canal alpha).
        pos_x: int
            Posição X do centro do sticker no fundo.
        pos_y: int
            Posição Y do centro do sticker no fundo.

    Returns:
        numpy.ndarray
            Imagem final com o sticker aplicado.
    """
    # Converter o sticker para BGR
    sticker = cv2.cvtColor(foreground, cv2.COLOR_RGBA2BGR)

    # Separar canais do foreground (com alpha)
    b, g, r, a = cv2.split(foreground)

    # Dimensões das imagens
    f_rows, f_cols, _ = foreground.shape
    b_rows, b_cols, _ = background.shape

    # Ajustar pos_x e pos_y para serem o centro background
    if pos_x is None:
        pos_x = b_cols // 2
    if pos_y is None:
        pos_y = b_rows // 2

    # Coordenadas do sticker ajustadas para o centro
    x_start = pos_x - f_cols // 2
    y_start = pos_y - f_rows // 2

    # Calcula os cortes para evitar extrapolação das bordas
    bg_x_start = max(0, x_start)
    bg_y_start = max(0, y_start)
    bg_x_end = min(b_cols, x_start + f_cols)
    bg_y_end = min(b_rows, y_start + f_rows)

    fg_x_start = max(0, -x_start)
    fg_y_start = max(0, -y_start)
    fg_x_end = fg_x_start + (bg_x_end - bg_x_start)
    fg_y_end = fg_y_start + (bg_y_end - bg_y_start)

    # Recorta as regiões de sobreposição
    sticker = sticker[fg_y_start:fg_y_end, fg_x_start:fg_x_end]
    mask = a[fg_y_start:fg_y_end, fg_x_start:fg_x_end]
    mask_inv = cv2.bitwise_not(mask)
    roi = background[bg_y_start:bg_y_end, bg_x_start:bg_x_end]

    # Combinar as imagens usando máscaras
    img_bg = cv2.bitwise_and(roi, roi, mask=mask_inv)
    img_fg = cv2.bitwise_and(sticker, sticker, mask=mask)
    res = cv2.add(img_bg, img_fg)

    # Atualizar o fundo com o resultado
    background[bg_y_start:bg_y_end, bg_x_start:bg_x_end] = res

    return background

# Função para remover o sticker
def removeSticker(background, sticker_pos, foreground, original_image):
    """
    Remove o sticker da imagem substituindo a área onde ele estava pela área original.
    
    Parameters:
        background: numpy.ndarray
            Imagem de fundo (BGR).
        sticker_pos: tuple
            Posição (x, y) onde o sticker foi colocado.
        foreground: numpy.ndarray
            Imagem do sticker com canal alpha.
        original_image: numpy.ndarray
            Imagem original para restaurar as regiões removidas.
    
    Returns:
        numpy.ndarray
            Imagem com o sticker removido.
    """
    f_rows, f_cols, _ = foreground.shape
    x, y = sticker_pos
    
    # Coordenadas do sticker ajustadas para o centro
    x_start = x - f_cols // 2
    y_start = y - f_rows // 2

    # Dimensões da imagem de fundo
    b_rows, b_cols, _ = background.shape

    # Ajuste para evitar ultrapassar as bordas da imagem
    x_start = max(0, x_start)
    y_start = max(0, y_start)

    x_end = min(b_cols, x_start + f_cols)
    y_end = min(b_rows, y_start + f_rows)

    # Restaurar a região onde o sticker estava com a imagem original
    background[y_start:y_end, x_start:x_end] = original_image[y_start:y_end, x_start:x_end]
    
    return background

# Função para tratar o clique do mouse
def mouse_click(event, x, y, flags, param):
    global img, stickers_positions, original_img
    
    # Se o botão esquerdo for clicado, adicionar o sticker
    if event == cv2.EVENT_LBUTTONDOWN:
        # Adicionar sticker e armazenar a posição
        img = applySticker(img, foreground, x, y)
        stickers_positions.append((x, y))  # Armazenar a posição
        cv2.imshow('image', img)
    
    # Se o botão direito for clicado, remover o sticker
    if event == cv2.EVENT_RBUTTONDOWN and stickers_positions:
        # Remover o sticker mais recente
        last_position = stickers_positions.pop()  # Remove a última posição
        img = removeSticker(img, last_position, foreground, original_img)  # Remover sticker na posição
        cv2.imshow('image', img)

