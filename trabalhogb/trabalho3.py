import cv2
import numpy as np

def applySticker(background, foreground, pos_x=None, pos_y=None):
    """
    Aplica um sticker (foreground) em uma imagem de fundo (background), considerando transparência.
    
    Parameters:
        background (numpy.ndarray): Imagem de fundo (BGR).
        foreground (numpy.ndarray): Sticker (RGBA ou BGR).
        pos_x (int, optional): Posição X do centro do sticker no fundo.
        pos_y (int, optional): Posição Y do centro do sticker no fundo.
    
    Returns:
        numpy.ndarray: Imagem de fundo com o sticker aplicado.
    """
    # Verifica se o sticker tem canal alfa (RGBA) ou não (BGR)
    if foreground.shape[2] == 4:
        b, g, r, a = cv2.split(foreground)  # Separa canais B, G, R e Alpha
    else:
        b, g, r = cv2.split(foreground)  # Separa canais B, G e R
        a = np.ones_like(b) * 255  # Cria canal Alpha totalmente opaco

    # Combina canais BGR para criar o sticker sem o canal Alpha
    sticker = cv2.merge([b, g, r])

    # Dimensões das imagens de fundo e do sticker
    f_rows, f_cols, _ = foreground.shape
    b_rows, b_cols, _ = background.shape

    # Calcula a posição central se não for especificada
    if pos_x is None:
        pos_x = b_cols // 2
    if pos_y is None:
        pos_y = b_rows // 2

    # Define as coordenadas iniciais do sticker na imagem de fundo
    x_start = pos_x - f_cols // 2
    y_start = pos_y - f_rows // 2

    # Limita as coordenadas para garantir que o sticker não ultrapasse as bordas
    bg_x_start = max(0, x_start)
    bg_y_start = max(0, y_start)
    bg_x_end = min(b_cols, x_start + f_cols)
    bg_y_end = min(b_rows, y_start + f_rows)

    # Ajusta as coordenadas do sticker para o recorte correto
    fg_x_start = max(0, -x_start)
    fg_y_start = max(0, -y_start)
    fg_x_end = fg_x_start + (bg_x_end - bg_x_start)
    fg_y_end = fg_y_start + (bg_y_end - bg_y_start)

    # Recorta a região do sticker e sua máscara
    sticker = sticker[fg_y_start:fg_y_end, fg_x_start:fg_x_end]
    mask = a[fg_y_start:fg_y_end, fg_x_start:fg_x_end]
    mask_inv = cv2.bitwise_not(mask)  # Máscara invertida para aplicar no fundo

    # Recorta a região de interesse (ROI) no fundo
    roi = background[bg_y_start:bg_y_end, bg_x_start:bg_x_end]

    # Aplica a máscara na região de fundo e no sticker
    img_bg = cv2.bitwise_and(roi, roi, mask=mask_inv)
    img_fg = cv2.bitwise_and(sticker, sticker, mask=mask)

    # Combina o fundo com o sticker
    res = cv2.add(img_bg, img_fg)
    background[bg_y_start:bg_y_end, bg_x_start:bg_x_end] = res

    return background

# Carrega a imagem de fundo e mantém uma cópia original
img = cv2.imread('baboon.png')
original_img = img.copy()

# Carrega os stickers com canal alpha
stickers = {
    'eyeglasses': cv2.imread('eyeglasses.png', cv2.IMREAD_UNCHANGED),
    'hat': cv2.imread('hat.png', cv2.IMREAD_UNCHANGED),
    'star': cv2.imread('star.png', cv2.IMREAD_UNCHANGED),
    'arvore': cv2.imread('arvore.png', cv2.IMREAD_UNCHANGED),
    'alce': cv2.imread('alce.png', cv2.IMREAD_UNCHANGED),
    'nascimento': cv2.imread('nascimento.png', cv2.IMREAD_UNCHANGED),
}

# Inicializa o primeiro sticker
current_sticker = stickers['eyeglasses']

# Lista de posições dos stickers e histórico de estados da imagem
stickers_positions = []
sticker_applied_regions = [img.copy()]
current_sticker_idx = 0  # Índice do sticker atual

def mouse_click(event, x, y, flags, param):
    """
    Gerencia eventos do mouse para adicionar, remover ou trocar stickers.
    
    Parameters:
        event: Evento do mouse (clique, rolagem).
        x, y: Posições do cursor.
        flags: Indica rolagem do mouse.
        param: Parâmetros adicionais (não usados aqui).
    """
    global img, stickers_positions, sticker_applied_regions, current_sticker, current_sticker_idx

    if event == cv2.EVENT_LBUTTONDOWN:
        # Adiciona o sticker na posição clicada
        img = applySticker(img, current_sticker, x, y)
        stickers_positions.append((x, y))  # Armazena a posição
        sticker_applied_regions.append(img.copy())  # Salva o estado da imagem
        cv2.imshow('image', img)
    
    if event == cv2.EVENT_RBUTTONDOWN and len(sticker_applied_regions) > 1:
        # Remove o sticker mais recente
        sticker_applied_regions.pop()  # Remove o estado mais recente
        img = sticker_applied_regions[-1].copy()  # Recupera o estado anterior
        stickers_positions.pop()  # Remove a posição correspondente
        cv2.imshow('image', img)

    if event == cv2.EVENT_MOUSEWHEEL:
        # Troca de sticker usando o scroll do mouse
        if flags > 0:  # Scroll para cima
            current_sticker_idx = (current_sticker_idx + 1) % len(stickers)
        else:  # Scroll para baixo
            current_sticker_idx = (current_sticker_idx - 1) % len(stickers)
        
        # Atualiza o sticker atual
        current_sticker = list(stickers.values())[current_sticker_idx]
        print(f"Sticker atual: {list(stickers.keys())[current_sticker_idx]}")
        cv2.imshow('image', img)

# Exibe a imagem inicial
cv2.imshow('image', img)

# Configura a função de callback para eventos do mouse
cv2.setMouseCallback('image', mouse_click)

# Loop principal para exibição contínua da imagem
while True:
    key = cv2.waitKey(1) & 0xFF  # Aguarda tecla pressionada
    if key == 27:  # Se "Esc" for pressionado, sai do loop
        break

# Fecha todas as janelas abertas
cv2.destroyAllWindows()
