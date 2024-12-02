import cv2  # Biblioteca para manipulação de imagens e vídeos
import numpy as np  # Biblioteca para operações numéricas
from tkinter import Tk, filedialog  # Interface gráfica para seleção de arquivos

# Carregar stickers com transparência
stickers = {
    'eyeglasses': cv2.imread('eyeglasses.png', cv2.IMREAD_UNCHANGED),
    'hat': cv2.imread('hat.png', cv2.IMREAD_UNCHANGED),
    'star': cv2.imread('star.png', cv2.IMREAD_UNCHANGED),
    'arvore': cv2.imread('arvore.png', cv2.IMREAD_UNCHANGED),
    'alce': cv2.imread('alce.png', cv2.IMREAD_UNCHANGED),
    'nascimento': cv2.imread('nascimento.png', cv2.IMREAD_UNCHANGED),
}

# Verifica se todos os stickers foram carregados corretamente
for name, sticker in stickers.items():
    if sticker is None:
        print(f"Erro ao carregar o sticker: {name}")
        exit(1)

# Variáveis globais
current_sticker_idx = 0  # Índice do sticker atual
current_filter_idx = 0  # Índice do filtro atual
undo_stack = []  # Histórico de estados para desfazer ações
original_image = None  # Imagem original carregada
img_with_effects = None  # Imagem com efeitos aplicados

# Dimensões mínimas da janela
MIN_WIDTH = 800
MIN_HEIGHT = 600

# Função para selecionar imagem
def select_image():
    """Abre uma janela para o usuário selecionar uma imagem do computador."""
    Tk().withdraw()  # Oculta a janela principal do Tkinter
    file_path = filedialog.askopenfilename(
        title="Selecione uma imagem",
        filetypes=[("Imagens", "*.png *.jpg *.jpeg *.bmp *.tiff *.gif")]
    )
    if not file_path:
        print("Nenhuma imagem selecionada. O programa será encerrado.")
        exit(1)
    return file_path

# Função para centralizar a imagem
def center_image(img, min_width, min_height):
    """Centraliza a imagem em um fundo preto com dimensões mínimas de largura e altura."""
    h, w, c = img.shape
    new_h = max(h, min_height)
    new_w = max(w, min_width)

    # Cria um fundo preto com as dimensões mínimas
    centered_frame = np.zeros((new_h, new_w, c), dtype=np.uint8)

    # Calcula as posições para centralizar a imagem
    y_offset = (new_h - h) // 2
    x_offset = (new_w - w) // 2

    # Coloca a imagem centralizada no fundo
    centered_frame[y_offset:y_offset + h, x_offset:x_offset + w] = img
    return centered_frame

# Função para aplicar stickers
def applySticker(background, sticker, x, y):
    """Aplica um sticker na imagem em uma posição específica (x, y)."""
    h, w = sticker.shape[:2]
    b_h, b_w = background.shape[:2]

    # Ajusta a posição caso o sticker ultrapasse os limites da imagem
    if x + w > b_w or y + h > b_h:
        print("Sticker ultrapassa os limites da imagem, ajustando posição...")
        w = min(w, b_w - x)
        h = min(h, b_h - y)
        sticker = sticker[:h, :w]

    # Verifica se o sticker possui transparência
    if sticker.shape[2] == 4:
        b, g, r, a = cv2.split(sticker)
        mask = a.astype(np.uint8)
        sticker = cv2.merge((b, g, r))
    else:
        mask = np.ones(sticker.shape[:2], dtype=np.uint8) * 255

    # Combina o sticker com a região de interesse na imagem de fundo
    roi = background[y:y+h, x:x+w]
    bg_masked = cv2.bitwise_and(roi, roi, mask=cv2.bitwise_not(mask))
    sticker_masked = cv2.bitwise_and(sticker, sticker, mask=mask)
    background[y:y+h, x:x+w] = cv2.add(bg_masked, sticker_masked)
    return background

# Função para aplicar filtros
def applyFilter(img, filter_idx):
    """Aplica filtros predefinidos na imagem com base no índice do filtro."""
    if filter_idx == 0:  # Retorna a imagem original
        return img.copy()
    elif filter_idx == 1:  # Filtro em escala de cinza
        filtered = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        return cv2.cvtColor(filtered, cv2.COLOR_GRAY2BGR)  # Converte de volta para 3 canais
    elif filter_idx == 2:  # Filtro de inversão
        return cv2.bitwise_not(img)
    elif filter_idx == 3:  # Filtro de desfoque
        return cv2.GaussianBlur(img, (15, 15), 0)
    return img

# Função para desenhar o menu sobre a imagem
def draw_menu(img):
    """Desenha o menu de instruções diretamente sobre a imagem."""
    instructions = [
        "Teclas de Atalho:",
        "'F' - Aplicar filtro",
        "'C' - Alterar sticker (scroll do mouse)",
        "Clique esquerdo - Adicionar sticker",
        "'S' - Salvar imagem",
        "Ctrl + Z - Desfazer",
        "ESC - Sair"
    ]

    # Adiciona o menu no rodapé da imagem
    h, w, _ = img.shape
    overlay = img.copy()
    cv2.rectangle(overlay, (0, h - 100), (w, h), (0, 0, 0), -1)  # Fundo preto semitransparente
    alpha = 0.6
    img = cv2.addWeighted(overlay, alpha, img, 1 - alpha, 0)

    # Adiciona o texto das instruções
    y0 = h - 80
    dy = 20
    for i, line in enumerate(instructions):
        y = y0 + i * dy
        cv2.putText(img, line, (10, y), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1, cv2.LINE_AA)

    return img

# Callback para eventos do mouse
def mouse_callback(event, x, y, flags, param):
    """Callback para manipulação de eventos do mouse, como adicionar stickers."""
    global img_with_effects, current_sticker_idx, undo_stack
    if event == cv2.EVENT_LBUTTONDOWN:
        undo_stack.append(img_with_effects.copy())
        sticker = list(stickers.values())[current_sticker_idx]
        img_with_effects = applySticker(img_with_effects, sticker, x, y)
        img_with_menu = draw_menu(img_with_effects.copy())
        cv2.imshow("Editor", img_with_menu)
    elif event == cv2.EVENT_MOUSEWHEEL:
        current_sticker_idx = (current_sticker_idx + (1 if flags > 0 else -1)) % len(stickers)
        print(f"Sticker atual: {list(stickers.keys())[current_sticker_idx]}")

# Função principal
def main():
    """Função principal que controla o fluxo do programa."""
    global img_with_effects, original_image, current_filter_idx, undo_stack

    # Seleciona a imagem
    image_path = select_image()
    original_image = cv2.imread(image_path)
    if original_image is None:
        print("Erro ao carregar a imagem selecionada.")
        exit(1)

    # Centraliza a imagem se for menor que as dimensões mínimas
    original_image = center_image(original_image, MIN_WIDTH, MIN_HEIGHT)
    img_with_effects = original_image.copy()
    undo_stack.append(img_with_effects.copy())  # Salva o estado inicial

    # Adiciona o menu e exibe
    img_with_menu = draw_menu(img_with_effects.copy())
    cv2.imshow("Editor", img_with_menu)
    cv2.setMouseCallback("Editor", mouse_callback)

    while True:
        key = cv2.waitKey(1) & 0xFF
        if key == 27:  # ESC para sair
            break
        elif key == ord('s'):  # Salvar imagem
            cv2.imwrite("imagem_editada.png", img_with_effects)
            print("Imagem salva.")
        elif key == ord('f'):  # Aplicar filtro
            current_filter_idx = (current_filter_idx + 1) % 4
            img_with_effects = applyFilter(original_image, current_filter_idx)
            img_with_menu = draw_menu(img_with_effects.copy())
            cv2.imshow("Editor", img_with_menu)
        elif key == 26:  # Ctrl + Z (Desfazer)
                if len(undo_stack) > 1:
                    undo_stack.pop()
                    img_with_effects = undo_stack[-1].copy()
                    img_with_menu = draw_menu(img_with_effects.copy())
                    cv2.imshow("Editor", img_with_menu)
                    print("Desfeito.")
                else:
                    print("Nada para desfazer.")
        elif key == ord('c'):  # Alterar o sticker atual usando o scroll do mouse
                current_sticker_idx = (current_sticker_idx + 1) % len(stickers)
                print(f"Sticker atual: {list(stickers.keys())[current_sticker_idx]}")
                img_with_menu = draw_menu(img_with_effects.copy())
                cv2.imshow("Editor", img_with_menu)

    cv2.destroyAllWindows()  # Fecha todas as janelas ao sair


if __name__ == "__main__":
    main()
