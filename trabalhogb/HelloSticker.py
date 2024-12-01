import numpy as np
import cv2 as cv

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
    sticker = cv.cvtColor(foreground, cv.COLOR_RGBA2BGR)

    # Separar canais do foreground (com alpha)
    b, g, r, a = cv.split(foreground)

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
    mask_inv = cv.bitwise_not(mask)
    roi = background[bg_y_start:bg_y_end, bg_x_start:bg_x_end]

    # Combinar as imagens usando máscaras
    img_bg = cv.bitwise_and(roi, roi, mask=mask_inv)
    img_fg = cv.bitwise_and(sticker, sticker, mask=mask)
    res = cv.add(img_bg, img_fg)

    # Atualizar o fundo com o resultado
    background[bg_y_start:bg_y_end, bg_x_start:bg_x_end] = res

    return background

#-------------------------------------------------------

# Carregar imagens
background = cv.imread('baboon.png')  # Fundo
foreground = cv.imread('eyeglasses.png', cv.IMREAD_UNCHANGED)  # Sticker com canal alpha

# Aplicar sticker no centro da imagem
res = applySticker(background, foreground, 256, 100)

# Exibir resultado
cv.imshow('Resultado', res)
cv.waitKey(0)
cv.destroyAllWindows()
