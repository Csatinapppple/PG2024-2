import cv2
import numpy as np
from tkinter import Tk, filedialog, Button, Label

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
video_filename = None     # Nome do arquivo de vídeo para salvar

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

# ---------------------------------------
# Funções auxiliares
# ---------------------------------------

def redimensionar_para_visualizacao(imagem):
    """
    Redimensiona a imagem para caber no quadro de edição, mantendo a proporção.
    """
    global escala_visualizacao
    if imagem is None:
        return None
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
    if imagem is None:
        return None
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

def iniciar_video_writer(frame):
    """
    Inicializa o gravador de vídeo no formato MP4 com codec H264.
    O codec H264 é amplamente suportado e embutido no formato MP4.
    """
    global video_writer, video_filename

    if video_writer is None:
        # Abre uma janela de diálogo para salvar o vídeo
        Tk().withdraw()
        video_filename = filedialog.asksaveasfilename(
            title="Salvar vídeo como",
            defaultextension=".mp4",
            filetypes=[("MP4 files", "*.mp4"), ("All files", "*.*")]
        )
        if video_filename:
            # Define o codec H264 (adequado para arquivos MP4)
            fourcc = cv2.VideoWriter_fourcc(*'avc1')
            # Inicializa o VideoWriter com 30 FPS e as dimensões do frame
            video_writer = cv2.VideoWriter(video_filename, fourcc, 30, (frame.shape[1], frame.shape[0]))
            print(f"Gravando vídeo em: {video_filename}")

def finalizar_video_writer():
    """
    Finaliza e salva o vídeo gravado.
    Certifica-se de que o arquivo seja gravado corretamente.
    """
    global video_writer, video_filename

    if video_writer is not None:
        video_writer.release()
        video_writer = None
        print(f"Vídeo salvo em: {video_filename}")

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
    global miniaturas
    miniaturas = []
    for i in range(len(nomes_filtros)):
        filtro_aplicado = aplicar_filtro(imagem, i)
        largura_miniatura = LARGURA_JANELA // len(nomes_filtros)
        miniatura = cv2.resize(filtro_aplicado, (largura_miniatura, 80))
        miniaturas.append(miniatura)

def atualizar_janela():
    """
    Atualiza a janela principal e escreve o frame processado no vídeo se necessário.
    """
    global imagem_com_efeitos, usando_webcam

    if imagem_com_efeitos is None:
        return

    if usando_webcam and video_writer is not None:
        # Grava o frame atual no arquivo de vídeo
        video_writer.write(imagem_com_efeitos)

    # Redimensiona a imagem para exibição
    visualizacao = redimensionar_para_visualizacao(imagem_com_efeitos)
    largura_total = LARGURA_JANELA
    altura_total = ALTURA_JANELA

    # Cria uma janela vazia para montagem
    janela = np.zeros((altura_total, largura_total, 3), dtype=np.uint8)

    # Calcula offsets para centralizar o frame na janela
    x_offset_frame = (largura_total - visualizacao.shape[1]) // 2
    y_offset_frame = ALTURA_ADESIVOS

    # Monta a janela com as áreas de adesivos, frame e barra de filtros
    janela[:ALTURA_ADESIVOS] = desenhar_area_adesivos(largura_total)
    janela[y_offset_frame:y_offset_frame + visualizacao.shape[0], x_offset_frame:x_offset_frame + visualizacao.shape[1]] = visualizacao
    janela[y_offset_frame + visualizacao.shape[0]:y_offset_frame + visualizacao.shape[0] + ALTURA_BARRA] = desenhar_barra_de_filtros(largura_total)
    desenhar_botoes(janela, largura_total, y_offset_frame + visualizacao.shape[0] + ALTURA_BARRA)

    # Exibe a janela montada
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
    global miniaturas
    barra = np.zeros((ALTURA_BARRA, largura, 3), dtype=np.uint8)
    largura_miniatura = largura // len(nomes_filtros)
    x_offset = 0
    for i, miniatura in enumerate(miniaturas):
        if miniatura is not None:
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
    global imagem_com_efeitos, historico_acao, indice_adesivo_atual, indice_filtro_atual
    if imagem_com_efeitos is None:
        return

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
                imagem_com_efeitos = aplicar_filtro(imagem_com_efeitos, indice_filtro_atual)
                historico_acao.append(imagem_com_efeitos.copy())
                atualizar_janela()

        elif y_offset_frame + visualizacao_altura + ALTURA_BARRA <= y <= y_offset_frame + visualizacao_altura + ALTURA_BARRA + ALTURA_BOTOES:
            largura_botoes = 200
            espaco_botoes = 20
            x_salvar = (LARGURA_JANELA // 2) - largura_botoes - espaco_botoes
            x_desfazer = (LARGURA_JANELA // 2) + espaco_botoes

            if x_salvar <= x <= x_salvar + largura_botoes:
                if usando_webcam:
                    iniciar_video_writer(imagem_com_efeitos)
                    finalizar_video_writer()
                else:
                    salvar_imagem(imagem_com_efeitos)
            elif x_desfazer <= x <= x_desfazer + largura_botoes:
                desfazer_acao()

def carregar_imagem_e_iniciar():
    """
    Permite ao usuário carregar uma imagem e inicializa o editor.
    """
    global imagem_original, imagem_com_efeitos, miniaturas, historico_acao

    Tk().withdraw()
    caminho_imagem = filedialog.askopenfilename(
        title="Selecione uma imagem",
        filetypes=[("Imagens", "*.png *.jpg *.jpeg *.bmp *.tiff *.gif")]
    )
    if not caminho_imagem:
        return

    imagem_original = cv2.imread(caminho_imagem)
    if imagem_original is None:
        print("Erro ao carregar a imagem.")
        return

    imagem_com_efeitos = imagem_original.copy()
    historico_acao = [imagem_com_efeitos.copy()]
    gerar_miniaturas(imagem_original)

    cv2.namedWindow("Editor")
    cv2.setMouseCallback("Editor", callback_mouse)
    atualizar_janela()

    while True:
        if cv2.waitKey(1) & 0xFF == 27:  # Tecla ESC para sair
            break

    cv2.destroyAllWindows()

def inicializar_webcam():
    """
    Inicializa a webcam e permite aplicar filtros e adesivos em tempo real.
    """
    global usando_webcam, imagem_com_efeitos, miniaturas

    usando_webcam = True
    captura = cv2.VideoCapture(0)
    if not captura.isOpened():
        print("Erro ao acessar a webcam.")
        return

    cv2.namedWindow("Editor")
    cv2.setMouseCallback("Editor", callback_mouse)

    ret, frame = captura.read()
    if ret:
        gerar_miniaturas(frame)

    while True:
        ret, frame = captura.read()
        if not ret:
            break

        imagem_com_efeitos = aplicar_filtro(frame, indice_filtro_atual)
        atualizar_janela()

        if cv2.waitKey(1) & 0xFF == 27:  # Tecla ESC para sair
            break

    captura.release()
    finalizar_video_writer()
    cv2.destroyAllWindows()

def escolher_modo():
    """
    Exibe uma interface inicial para o usuário escolher entre usar webcam ou carregar uma imagem.
    """
    root = Tk()
    root.title("Escolha o Modo")
    root.geometry("300x150")
    root.resizable(False, False)

    Label(root, text="Escolha o modo de edição:", font=("Arial", 12)).pack(pady=10)
    Button(root, text="Carregar Imagem", command=lambda: [root.destroy(), carregar_imagem_e_iniciar()],
           width=20, height=2).pack(pady=5)
    Button(root, text="Usar Webcam", command=lambda: [root.destroy(), inicializar_webcam()],
           width=20, height=2).pack(pady=5)

    root.mainloop()

def main():
    """
    Executa o programa principal.
    """
    escolher_modo()

if __name__ == "__main__":
    main()