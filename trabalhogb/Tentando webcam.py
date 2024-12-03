import cv2
import numpy as np
from tkinter import Tk, filedialog, Toplevel, Button, Label

# ---------------------------------------
# Configurações iniciais e variáveis globais
# ---------------------------------------

# Carregar adesivos com transparência
adesivos = {
    'oculos': cv2.imread('eyeglasses.png', cv2.IMREAD_UNCHANGED),
    'chapeu': cv2.imread('hat.png', cv2.IMREAD_UNCHANGED),
    'estrela': cv2.imread('star.png', cv2.IMREAD_UNCHANGED),
    'arvore': cv2.imread('arvore.png', cv2.IMREAD_UNCHANGED),
    'alce': cv2.imread('alce.png', cv2.IMREAD_UNCHANGED),
    'nascimento': cv2.imread('nascimento.png', cv2.IMREAD_UNCHANGED),
}

# Verifica se os adesivos foram carregados corretamente
for nome, adesivo in adesivos.items():
    if adesivo is None:
        print(f"Erro ao carregar o adesivo: {nome}")
        exit(1)

# Variáveis globais
indice_adesivo_atual = 0  # Indica o adesivo selecionado
indice_filtro_atual = 0   # Indica o filtro selecionado
historico_acao = []       # Histórico de ações para desfazer alterações
imagem_original = None    # Imagem original carregada pelo usuário
imagem_com_efeitos = None # Imagem com filtros e adesivos aplicados
escala_visualizacao = None # Escala da imagem para ajustar ao quadro de edição
miniaturas = []           # Miniaturas de filtros disponíveis para exibição
usando_webcam = False     # Indica se o programa está usando a webcam
video_writer = None       # Gravador de vídeo para salvar frames da webcam
video_filename = "output.mp4"  # Nome do arquivo de vídeo para salvar

# Dimensões do quadro de edição e elementos da interface
LARGURA_JANELA = 1366
ALTURA_JANELA = 768
LARGURA_FRAME = 768
ALTURA_FRAME = 432
ALTURA_ADESIVOS = 100
ALTURA_BARRA = 100
ALTURA_BOTOES = 50

# Nomes dos filtros disponíveis
nomes_filtros = [
    "Original",             # Filtro 0
    "Escala de Cinza",      # Filtro 1
    "Inversão",             # Filtro 2
    "Desfoque",             # Filtro 3
    "Efeito Tumblr",        # Filtro 4
    "Efeito Prism",         # Filtro 5
    "Vintage",              # Filtro 6
    "Silly Face",           # Filtro 7
    "Kyle+Kendall Slim",    # Filtro 8
    "Filtro Kodak",         # Filtro 9
    "Negativo da Foto"      # Filtro 10
]

# Inicializa classificadores para detecção de rosto, olhos e sorriso
face_classifier = cv2.CascadeClassifier(cv2.data.haarcascades + "haarcascade_frontalface_default.xml")
eye_classifier = cv2.CascadeClassifier(cv2.data.haarcascades + "haarcascade_eye.xml")
smile_classifier = cv2.CascadeClassifier(cv2.data.haarcascades + "haarcascade_smile.xml")

# ---------------------------------------
# Funções auxiliares
# ---------------------------------------

def redimensionar_para_visualizacao(imagem):
    """
    Redimensiona a imagem para caber no quadro de edição, mantendo a proporção.
    """
    global escala_visualizacao
    altura, largura = imagem.shape[:2]
    escala_visualizacao = min(LARGURA_FRAME / largura, ALTURA_FRAME / altura)
    nova_largura = int(largura * escala_visualizacao)
    nova_altura = int(altura * escala_visualizacao)
    return cv2.resize(imagem, (nova_largura, nova_altura))

def aplicar_adesivo(imagem_fundo, adesivo, x, y):
    """
    Aplica um adesivo na posição especificada (x, y) da imagem.
    Suporta adesivos com canal alfa para transparência.
    """
    altura_adesivo, largura_adesivo = adesivo.shape[:2]

    if adesivo.shape[2] == 4:  # Verifica canal alfa
        azul, verde, vermelho, alfa = cv2.split(adesivo)
        adesivo_rgb = cv2.merge((azul, verde, vermelho))
        mascara = alfa
    else:
        adesivo_rgb = adesivo
        mascara = np.ones((altura_adesivo, largura_adesivo), dtype=np.uint8) * 255

    if y + altura_adesivo > imagem_fundo.shape[0] or x + largura_adesivo > imagem_fundo.shape[1]:
        return
    roi = imagem_fundo[y:y + altura_adesivo, x:x + largura_adesivo]
    fundo = cv2.bitwise_and(roi, roi, mask=cv2.bitwise_not(mascara))
    sobreposicao = cv2.add(fundo, adesivo_rgb)
    imagem_fundo[y:y + altura_adesivo, x:x + largura_adesivo] = sobreposicao

def aplicar_filtro(imagem, indice_filtro):
    """
    Aplica um dos filtros predefinidos com base no índice selecionado.
    """
    if indice_filtro == 0:  # Original
        return imagem.copy()
    elif indice_filtro == 1:  # Escala de Cinza
        filtro = cv2.cvtColor(imagem, cv2.COLOR_BGR2GRAY)
        return cv2.cvtColor(filtro, cv2.COLOR_GRAY2BGR)
    elif indice_filtro == 2:  # Inversão
        return cv2.bitwise_not(imagem)
    elif indice_filtro == 3:  # Desfoque
        return cv2.GaussianBlur(imagem, (15, 15), 0)
    elif indice_filtro == 4:  # Efeito Tumblr
        return cv2.applyColorMap(imagem, cv2.COLORMAP_PINK)
    elif indice_filtro == 5:  # Efeito Prism
        return cv2.applyColorMap(imagem, cv2.COLORMAP_RAINBOW)
    elif indice_filtro == 6:  # Vintage
        sepia_filter = np.array([[0.272, 0.534, 0.131],
                                 [0.349, 0.686, 0.168],
                                 [0.393, 0.769, 0.189]])
        imagem_vintage = cv2.transform(imagem, sepia_filter)
        return np.clip(imagem_vintage, 0, 255).astype(np.uint8)
    elif indice_filtro == 7:  # Silly Face
        return cv2.add(imagem, np.full_like(imagem, 30))
    elif indice_filtro == 8:  # Kyle+Kendall Slim
        return cv2.bilateralFilter(imagem, 15, 80, 80)
    elif indice_filtro == 9:  # Filtro Kodak
        lookup_table = np.array([min(i + 20, 255) for i in range(256)]).astype("uint8")
        return cv2.LUT(imagem, lookup_table)
    elif indice_filtro == 10:  # Negativo da Foto
        return cv2.bitwise_not(imagem)
    return imagem

def salvar_imagem(imagem):
    """
    Salva a imagem atual na pasta que o usuário desejar.
    """
    Tk().withdraw()
    caminho_salvar = filedialog.asksaveasfilename(
        title="Salvar imagem como",
        defaultextension=".png",
        filetypes=[("PNG files", "*.png"), ("JPEG files", "*.jpg"), ("All files", "*.*")]
    )
    if caminho_salvar:
        cv2.imwrite(caminho_salvar, imagem)
        print(f"Imagem salva em {caminho_salvar}")

def salvar_frame_webcam(frame):
    """
    Salva um frame capturado da webcam no arquivo de vídeo.
    """
    global video_writer, video_filename
    if video_writer is None:
        # Configuração do codec e do gravador de vídeo
        fourcc = cv2.VideoWriter_fourcc(*'mp4v')
        video_writer = cv2.VideoWriter(video_filename, fourcc, 30, (frame.shape[1], frame.shape[0]))
    video_writer.write(frame)

def desfazer_acao():
    """
    Desfaz a última ação do usuário, caso possível.
    """
    global imagem_com_efeitos, historico_acao
    if len(historico_acao) > 1:
        historico_acao.pop()
        imagem_com_efeitos = historico_acao[-1].copy()
        atualizar_janela()

def gerar_miniaturas(imagem):
    """
    Gera miniaturas dos filtros disponíveis para exibição na barra.
    """
    miniaturas = []
    for i in range(len(nomes_filtros)):
        filtro_aplicado = aplicar_filtro(imagem, i)
        largura_miniatura = LARGURA_JANELA // len(nomes_filtros)
        miniatura = cv2.resize(filtro_aplicado, (largura_miniatura, 80))
        miniaturas.append(miniatura)
    return miniaturas

def inicializar_webcam():
    """
    Inicializa o modo de webcam e configura os elementos para aplicar filtros e adesivos.
    """
    global usando_webcam, imagem_com_efeitos, video_writer
    usando_webcam = True

    # Inicializa a captura de vídeo
    captura = cv2.VideoCapture(0)
    if not captura.isOpened():
        print("Erro ao acessar a webcam.")
        exit(1)

    # Configura o gravador de vídeo (caso necessário)
    video_writer = None

    while True:
        ret, frame = captura.read()
        if not ret:
            print("Erro ao capturar frame da webcam.")
            break

        # Converte o frame para escala de cinza para a detecção
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        gray = cv2.equalizeHist(gray)

        # Realiza a detecção de rostos
        rostos = face_classifier.detectMultiScale(gray, scaleFactor=1.3, minNeighbors=4, minSize=(30, 30))

        # Desenha retângulos ao redor dos rostos detectados
        for (x, y, w, h) in rostos:
            cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 2)

            # Região de interesse para olhos e sorriso dentro do rosto
            roi_gray = gray[y:y + h, x:x + w]
            roi_color = frame[y:y + h, x:x + w]

            # Detecção de olhos
            olhos = eye_classifier.detectMultiScale(roi_gray)
            for (ex, ey, ew, eh) in olhos:
                cv2.rectangle(roi_color, (ex, ey), (ex + ew, ey + eh), (255, 0, 0), 2)

            # Detecção de sorriso
            sorrisos = smile_classifier.detectMultiScale(roi_gray, scaleFactor=1.7, minNeighbors=22)
            for (sx, sy, sw, sh) in sorrisos:
                cv2.rectangle(roi_color, (sx, sy), (sx + sw, sy + sh), (0, 255, 255), 2)

        # Redimensiona o frame para o tamanho do frame view
        frame_redimensionado = redimensionar_para_visualizacao(frame)
        imagem_com_efeitos = frame_redimensionado.copy()

        # Aplica o filtro selecionado no frame da webcam
        imagem_com_efeitos = aplicar_filtro(imagem_com_efeitos, indice_filtro_atual)

        # Atualiza a janela
        atualizar_janela()

        # Salva o frame no arquivo de vídeo (se necessário)
        if video_writer is not None:
            salvar_frame_webcam(frame)

        # Lê a tecla pressionada pelo usuário
        tecla = cv2.waitKey(1) & 0xFF
        if tecla == 27:  # Tecla ESC para sair
            break

    captura.release()
    if video_writer:
        video_writer.release()
    cv2.destroyAllWindows()

def escolher_modo():
    """
    Exibe uma janela inicial para o usuário escolher entre carregar uma imagem ou usar a webcam.
    """
    root = Tk()
    root.title("Escolha o Modo")
    root.geometry("300x150")
    root.resizable(False, False)

    Label(root, text="Escolha o modo de edição:", font=("Arial", 12)).pack(pady=10)

    def carregar_imagem():
        """
        Função chamada quando o usuário escolhe carregar uma imagem.
        """
        root.destroy()
        carregar_imagem_e_iniciar()

    def usar_webcam():
        """
        Função chamada quando o usuário escolhe usar a webcam.
        """
        root.destroy()
        inicializar_webcam()

    Button(root, text="Carregar Imagem", command=carregar_imagem, width=20, height=2).pack(pady=5)
    Button(root, text="Usar Webcam", command=usar_webcam, width=20, height=2).pack(pady=5)

    root.mainloop()

def carregar_imagem_e_iniciar():
    """
    Permite ao usuário carregar uma imagem e inicializa o editor de imagem.
    """
    global imagem_com_efeitos, imagem_original, miniaturas, historico_acao

    Tk().withdraw()
    caminho_imagem = filedialog.askopenfilename(
        title="Selecione uma imagem",
        filetypes=[("Imagens", "*.png *.jpg *.jpeg *.bmp *.tiff *.gif")]
    )
    if not caminho_imagem:
        print("Nenhuma imagem selecionada.")
        return

    imagem_original = cv2.imread(caminho_imagem)
    if imagem_original is None:
        print("Erro ao carregar a imagem.")
        return

    imagem_com_efeitos = imagem_original.copy()
    historico_acao.append(imagem_com_efeitos.copy())
    miniaturas = gerar_miniaturas(imagem_original)

    atualizar_janela()
    cv2.setMouseCallback("Editor", callback_mouse)

    while True:
        tecla = cv2.waitKey(1) & 0xFF
        if tecla == 27:  # Tecla ESC para sair
            break

    cv2.destroyAllWindows()

def atualizar_janela():
    """
    Atualiza a janela principal com a imagem, área de adesivos, barra de filtros e botões.
    """
    visualizacao = redimensionar_para_visualizacao(imagem_com_efeitos)
    largura_total = LARGURA_JANELA
    altura_total = ALTURA_JANELA

    janela = np.zeros((altura_total, largura_total, 3), dtype=np.uint8)

    x_offset_frame = (largura_total - visualizacao.shape[1]) // 2
    y_offset_frame = ALTURA_ADESIVOS

    janela[:ALTURA_ADESIVOS] = desenhar_area_adesivos(largura_total)
    janela[y_offset_frame:y_offset_frame + visualizacao.shape[0], x_offset_frame:x_offset_frame + visualizacao.shape[1]] = visualizacao
    janela[y_offset_frame + visualizacao.shape[0]:y_offset_frame + visualizacao.shape[0] + ALTURA_BARRA] = desenhar_barra_de_filtros(largura_total)
    desenhar_botoes(janela, largura_total, y_offset_frame + visualizacao.shape[0] + ALTURA_BARRA)

    cv2.imshow("Editor", janela)

def desenhar_area_adesivos(largura):
    """
    Desenha a área horizontal com miniaturas de adesivos.
    """
    area = np.zeros((ALTURA_ADESIVOS, largura, 3), dtype=np.uint8)
    x_offset = 10
    for i, (nome, adesivo) in enumerate(adesivos.items()):
        adesivo_redimensionado = cv2.resize(adesivo[:, :, :3], (80, 80))
        area[10:90, x_offset:x_offset + 80] = adesivo_redimensionado
        if i == indice_adesivo_atual:
            cv2.rectangle(area, (x_offset, 10), (x_offset + 80, 90), (0, 255, 0), 2)
        x_offset += 90
    return area

def desenhar_barra_de_filtros(largura):
    """
    Desenha a barra horizontal com miniaturas dos filtros.
    """
    barra = np.zeros((ALTURA_BARRA, largura, 3), dtype=np.uint8)
    largura_miniatura = largura // len(nomes_filtros)
    x_offset = 0
    for i, miniatura in enumerate(miniaturas):
        miniatura_redimensionada = cv2.resize(miniatura, (largura_miniatura, 80))
        barra[10:90, x_offset:x_offset + largura_miniatura] = miniatura_redimensionada
        if i == indice_filtro_atual:
            cv2.rectangle(barra, (x_offset, 10), (x_offset + largura_miniatura, 90), (0, 255, 0), 2)
        x_offset += largura_miniatura
    return barra

def desenhar_botoes(janela, largura, y_offset):
    """
    Desenha os botões "Salvar" e "Desfazer" abaixo da barra de filtros.
    """
    botao_largura = 200
    botao_altura = ALTURA_BOTOES
    espaco = 20

    x_salvar = (largura // 2) - botao_largura - espaco
    x_desfazer = (largura // 2) + espaco

    cv2.rectangle(janela, (x_salvar, y_offset), (x_salvar + botao_largura, y_offset + botao_altura), (200, 200, 200), -1)
    cv2.putText(janela, "Salvar", (x_salvar + 50, y_offset + 35), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 0, 0), 2)

    cv2.rectangle(janela, (x_desfazer, y_offset), (x_desfazer + botao_largura, y_offset + botao_altura), (200, 200, 200), -1)
    cv2.putText(janela, "Desfazer", (x_desfazer + 35, y_offset + 35), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 0, 0), 2)

def callback_mouse(evento, x, y, flags, parametros):
    """
    Lida com cliques e eventos do mouse na interface.
    """
    global imagem_com_efeitos, historico_acao, indice_adesivo_atual, indice_filtro_atual, usando_webcam
    visualizacao_altura = redimensionar_para_visualizacao(imagem_com_efeitos).shape[0]
    x_offset_frame = (LARGURA_JANELA - LARGURA_FRAME) // 2
    y_offset_frame = ALTURA_ADESIVOS

    if evento == cv2.EVENT_LBUTTONDOWN:
        if 0 <= y <= ALTURA_ADESIVOS:
            indice = x // 90
            if indice < len(adesivos):
                indice_adesivo_atual = indice
                atualizar_janela()

        elif y_offset_frame <= y <= y_offset_frame + visualizacao_altura:
            x_original = int((x - x_offset_frame) / escala_visualizacao)
            y_original = int((y - y_offset_frame) / escala_visualizacao)
            adesivo = list(adesivos.values())[indice_adesivo_atual]
            historico_acao.append(imagem_com_efeitos.copy())
            aplicar_adesivo(imagem_com_efeitos, adesivo, x_original, y_original)
            atualizar_janela()

        elif y_offset_frame + visualizacao_altura < y <= y_offset_frame + visualizacao_altura + ALTURA_BARRA:
            indice_filtro = x // (LARGURA_JANELA // len(nomes_filtros))
            if indice_filtro < len(nomes_filtros):
                indice_filtro_atual = indice_filtro
                imagem_com_efeitos = aplicar_filtro(imagem_original, indice_filtro_atual)
                historico_acao.append(imagem_com_efeitos.copy())
                atualizar_janela()

        elif y_offset_frame + visualizacao_altura + ALTURA_BARRA <= y <= y_offset_frame + visualizacao_altura + ALTURA_BARRA + ALTURA_BOTOES:
            largura_botoes = 200
            espaco_botoes = 20
            x_salvar = (LARGURA_JANELA // 2) - largura_botoes - espaco_botoes
            x_desfazer = (LARGURA_JANELA // 2) + espaco_botoes

            if x_salvar <= x <= x_salvar + largura_botoes:
                salvar_imagem(imagem_com_efeitos)
            elif x_desfazer <= x <= x_desfazer + largura_botoes:
                desfazer_acao()

def main():
    """
    Executa o programa principal, permitindo ao usuário escolher entre usar webcam ou carregar imagem.
    """
    escolher_modo()

if __name__ == "__main__":
    main()