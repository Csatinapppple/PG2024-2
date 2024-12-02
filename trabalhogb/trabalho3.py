import cv2
import numpy as np
from tkinter import Tk, filedialog

# Carregar stickers com canal alpha
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

current_sticker_idx = 0
current_filter_idx = 0
undo_stack = []  # Histórico de estados para desfazer

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

def applySticker(background, sticker, x, y):
    """Aplica o sticker na imagem na posição (x, y)"""
    h, w = sticker.shape[:2]
    b_h, b_w = background.shape[:2]

    # Ajusta posição se o sticker ultrapassar os limites
    if x + w > b_w or y + h > b_h:
        print("Sticker ultrapassa os limites da imagem, ajustando posição...")
        w = min(w, b_w - x)
        h = min(h, b_h - y)
        sticker = sticker[:h, :w]

    if sticker.shape[2] == 4:
        b, g, r, a = cv2.split(sticker)
        mask = a.astype(np.uint8)  # Garante que a máscara seja 8 bits
        sticker = cv2.merge((b, g, r))
    else:
        mask = np.ones(sticker.shape[:2], dtype=np.uint8) * 255

    roi = background[y:y+h, x:x+w]
    bg_masked = cv2.bitwise_and(roi, roi, mask=cv2.bitwise_not(mask))
    sticker_masked = cv2.bitwise_and(sticker, sticker, mask=mask)
    result = cv2.add(bg_masked, sticker_masked)
    background[y:y+h, x:x+w] = result
    return background

def applyFilter(img, filter_idx):
    """Aplica filtros predefinidos"""
    if filter_idx == 1:
        return cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    elif filter_idx == 2:
        return cv2.bitwise_not(img)
    elif filter_idx == 3:
        return cv2.GaussianBlur(img, (15, 15), 0)
    else:
        return img

def mouse_callback(event, x, y, flags, param):
    global img, current_sticker_idx, undo_stack
    if event == cv2.EVENT_LBUTTONDOWN:
        undo_stack.append(img.copy())
        sticker = list(stickers.values())[current_sticker_idx]
        img = applySticker(img, sticker, x, y)
        cv2.imshow("Editor", img)
    elif event == cv2.EVENT_MOUSEWHEEL:
        current_sticker_idx = (current_sticker_idx + (1 if flags > 0 else -1)) % len(stickers)
        print(f"Sticker atual: {list(stickers.keys())[current_sticker_idx]}")

def main():
    global img, current_filter_idx, undo_stack

    # Seleção da imagem pelo usuário
    image_path = select_image()
    img = cv2.imread(image_path)
    if img is None:
        print("Erro ao carregar a imagem selecionada.")
        exit(1)

    undo_stack.append(img.copy())  # Adiciona a imagem inicial ao histórico
    cv2.imshow("Editor", img)
    cv2.setMouseCallback("Editor", mouse_callback)

    while True:
        key = cv2.waitKey(1) & 0xFF
        if key == 27:
            break
        elif key == ord('s'):
            cv2.imwrite("imagem_editada.png", img)
            print("Imagem salva.")
        elif key == ord('f'):
            current_filter_idx = (current_filter_idx + 1) % 4
            filtered_img = applyFilter(img.copy(), current_filter_idx)
            cv2.imshow("Editor", filtered_img)
        elif key == 26:  # Ctrl + Z
            if len(undo_stack) > 1:
                undo_stack.pop()
                img = undo_stack[-1].copy()
                cv2.imshow("Editor", img)
                print("Desfeito.")

    cv2.destroyAllWindows()

if __name__ == "__main__":
    main()
