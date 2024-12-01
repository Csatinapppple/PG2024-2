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
            Imagem do sticker (RGBA ou BGR).
        pos_x: int
            Posição X do centro do sticker no fundo.
        pos_y: int
            Posição Y do centro do sticker no fundo.
    
    Returns:
        numpy.ndarray
            Imagem final com o sticker aplicado.
    """
    # Verifica se o foreground possui 4 canais (RGBA) ou apenas 3 canais (BGR)
    if foreground.shape[2] == 4:  # RGBA
        b, g, r, a = cv2.split(foreground)
    else:  # BGR (sem transparência)
        b, g, r = cv2.split(foreground)
        a = np.ones_like(b) * 255  # Canal alpha totalmente opaco (255)

    # Converter o sticker para BGR
    sticker = cv2.merge([b, g, r])

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

# Carregar a imagem de fundo
img = cv2.imread('baboon.png')  # Imagem de fundo
original_img = img.copy()  # Guardar uma cópia da imagem original para restaurar

# Definir os stickers disponíveis (troque pelos seus stickers desejados)
stickers = {
    'eyeglasses': cv2.imread('eyeglasses.png', cv2.IMREAD_UNCHANGED),
    'hat': cv2.imread('hat.png', cv2.IMREAD_UNCHANGED),
    'star': cv2.imread('star.png', cv2.IMREAD_UNCHANGED),
    'elce': cv2.imread('elce.png', cv2.IMREAD_UNCHANGED),
    'nascimento': cv2.imread('nascimento.png', cv2.IMREAD_UNCHANGED),
    # Adicione mais stickers conforme necessário
}

# Inicializar o sticker atual com o primeiro sticker da lista
current_sticker = stickers['eyeglasses']

# Lista para armazenar as posições dos stickers
stickers_positions = []

# Variável para controlar o índice do sticker atual
current_sticker_idx = 0

# Função para tratar o clique do mouse e rolagem do scroll
def mouse_click(event, x, y, flags, param):
    global img, stickers_positions, original_img, current_sticker, current_sticker_idx
    
    # Se o botão esquerdo for clicado, adicionar o sticker
    if event == cv2.EVENT_LBUTTONDOWN:
        # Adicionar sticker e armazenar a posição
        img = applySticker(img, current_sticker, x, y)
        stickers_positions.append((x, y))  # Armazenar a posição
        cv2.imshow('image', img)
    
    # Se o botão direito for clicado, remover o sticker
    if event == cv2.EVENT_RBUTTONDOWN and stickers_positions:
        # Remover o sticker mais recente
        last_position = stickers_positions.pop()  # Remove a última posição
        img = removeSticker(img, last_position, current_sticker, original_img)  # Remover sticker na posição
        cv2.imshow('image', img)

    # Detectar a rotação do scroll do mouse
    if event == cv2.EVENT_MOUSEWHEEL:
        if flags > 0:  # Scroll para cima
            current_sticker_idx = (current_sticker_idx + 1) % len(stickers)
        else:  # Scroll para baixo
            current_sticker_idx = (current_sticker_idx - 1) % len(stickers)
        
        # Atualizar o sticker atual
        current_sticker = list(stickers.values())[current_sticker_idx]
        print(f"Sticker atual: {list(stickers.keys())[current_sticker_idx]}")
        cv2.imshow('image', img)

# Exibir a imagem inicial
cv2.imshow('image', img)

# Definir a função de callback para o mouse
cv2.setMouseCallback('image', mouse_click)

# Esperar até que uma tecla seja pressionada
while True:
    key = cv2.waitKey(1) & 0xFF  # Aguardar tecla pressionada
    if key == 27:  # ESC
        break

    # Atualizar a imagem
    cv2.imshow('image', img)

# Fechar todas as janelas
cv2.destroyAllWindows()
