import cv2  # Manipulação de imagens e vídeos
import numpy as np  # Operações numéricas
from tkinter import Tk, filedialog, Button, Label  # Interface gráfica
import threading  # Execução paralela para webcam

# Carregamento de stickers com transparência
stickers = {
    'eyeglasses': cv2.imread('eyeglasses.png', cv2.IMREAD_UNCHANGED),
    'hat': cv2.imread('hat.png', cv2.IMREAD_UNCHANGED),
    'star': cv2.imread('star.png', cv2.IMREAD_UNCHANGED),
    'arvore': cv2.imread('arvore.png', cv2.IMREAD_UNCHANGED),
    'alce': cv2.imread('alce.png', cv2.IMREAD_UNCHANGED),
    'nascimento': cv2.imread('nascimento.png', cv2.IMREAD_UNCHANGED),
}

# Verificação do carregamento dos stickers
for name, sticker in stickers.items():
    if sticker is None:
        print(f"Erro ao carregar o sticker: {name}")
        exit(1)

# Variáveis globais
current_sticker_idx = 0  # Índice do sticker
current_filter_idx = 0  # Índice do filtro
undo_stack = []  # Histórico para desfazer
stickers_positions = []  # Posições de stickers na webcam
face_classifier = cv2.CascadeClassifier(cv2.data.haarcascades + "haarcascade_frontalface_default.xml")

mode = ""  # Modo atual: 'imagem' ou 'webcam'

# Função para abrir janela de seleção de imagem
def select_image():
    """Abre janela para selecionar imagem do computador."""
    Tk().withdraw()
    file_path = filedialog.askopenfilename(
        title="Selecione uma imagem",
        filetypes=[("Imagens", "*.png *.jpg *.jpeg *.bmp *.tiff *.gif")]
    )
    if not file_path:
        print("Nenhuma imagem selecionada.")
        exit(1)
    return file_path

# Função para aplicar stickers
def applySticker(background, sticker, x, y):
    """Aplica sticker na posição (x, y)."""
    h, w = sticker.shape[:2]
    b_h, b_w = background.shape[:2]

    # Ajuste de limites para não sair da tela
    if x + w > b_w or y + h > b_h:
        w = min(w, b_w - x)
        h = min(h, b_h - y)
        sticker = sticker[:h, :w]

    if sticker.shape[2] == 4:
        b, g, r, a = cv2.split(sticker)
        mask = a.astype(np.uint8)
        sticker = cv2.merge((b, g, r))
    else:
        mask = np.ones(sticker.shape[:2], dtype=np.uint8) * 255

    roi = background[y:y+h, x:x+w]
    bg_masked = cv2.bitwise_and(roi, roi, mask=cv2.bitwise_not(mask))
    sticker_masked = cv2.bitwise_and(sticker, sticker, mask=mask)
    background[y:y+h, x:x+w] = cv2.add(bg_masked, sticker_masked)
    return background

# Função para aplicar filtros
def applyFilter(img, filter_idx):
    """Aplica filtros predefinidos."""
    if filter_idx == 1:
        return cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    elif filter_idx == 2:
        return cv2.bitwise_not(img)
    elif filter_idx == 3:
        return cv2.GaussianBlur(img, (15, 15), 0)
    return img

# Função para callback de stickers
def mouse_callback(event, x, y, flags, param):
    """Callback para eventos do mouse."""
    global img, current_sticker_idx, undo_stack
    if event == cv2.EVENT_LBUTTONDOWN:
        undo_stack.append(img.copy())
        sticker = list(stickers.values())[current_sticker_idx]
        stickers_positions.append((x, y, sticker))  # Armazena posição
        img = applySticker(img, sticker, x, y)
        cv2.imshow("Editor", img)
    elif event == cv2.EVENT_MOUSEWHEEL:
        current_sticker_idx = (current_sticker_idx + (1 if flags > 0 else -1)) % len(stickers)
        print(f"Sticker atual: {list(stickers.keys())[current_sticker_idx]}")

# Função para capturar imagens da webcam
def capture_from_webcam():
    """Captura imagens da webcam, permitindo filtros e stickers persistentes."""
    global img, current_filter_idx, stickers_positions
    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        print("Erro ao acessar a webcam.")
        exit(1)

    while True:
        ret, frame = cap.read()
        if not ret:
            break

        # Aplica stickers em todas as capturas
        for (x, y, sticker) in stickers_positions:
            frame = applySticker(frame, sticker, x, y)

        frame = applyFilter(frame, current_filter_idx)
        cv2.imshow("Editor", frame)

        key = cv2.waitKey(1) & 0xFF
        if key == 27:  # Esc para sair
            break
        elif key == ord('s'):
            cv2.imwrite("webcam_frame.png", frame)
            print("Frame salvo.")
        elif key == ord('f'):
            current_filter_idx = (current_filter_idx + 1) % 4
        elif key == ord('c'):
            cv2.setMouseCallback("Editor", mouse_callback)

    cap.release()
    cv2.destroyAllWindows()

# Interface gráfica para escolha de modo
def create_interface():
    """Interface gráfica inicial."""
    root = Tk()
    root.title("Escolha a Fonte")

    Label(root, text="Escolha a fonte da imagem:").pack()

    def start_image_mode():
        root.destroy()
        global mode
        mode = 'imagem'
        image_path = select_image()
        start_image_editor(image_path)

    def start_webcam_mode():
        root.destroy()
        global mode
        mode = 'webcam'
        threading.Thread(target=capture_from_webcam).start()

    Button(root, text="Selecionar Imagem", command=start_image_mode).pack(pady=10)
    Button(root, text="Webcam", command=start_webcam_mode).pack(pady=10)

    root.mainloop()

# Função para edição de imagem
def start_image_editor(image_path):
    """Edita imagem selecionada com filtros e stickers."""
    global img, undo_stack
    img = cv2.imread(image_path)
    if img is None:
        print("Erro ao carregar a imagem selecionada.")
        exit(1)
    undo_stack.append(img.copy())
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
            img = applyFilter(undo_stack[-1].copy(), current_filter_idx)
            cv2.imshow("Editor", img)
        elif key == 26:
            if len(undo_stack) > 1:
                undo_stack.pop()
                img = undo_stack[-1].copy()
                cv2.imshow("Editor", img)
                print("Desfeito.")
    cv2.destroyAllWindows()

if __name__ == "__main__":
    create_interface()
