import cv2
import numpy as np
from tkinter import Tk, filedialog

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
imagem_para_visualizacao = None  # Imagem redimensionada para visualização
imagem_com_efeitos = None # Imagem com filtros e adesivos aplicados
escala_visualizacao = None # Escala da imagem para ajustar ao quadro de edição
miniaturas = []           # Miniaturas de filtros disponíveis para exibição

# Dimensões do quadro de edição e elementos da interface
LARGURA_FRAME = 960       # Reduzido para 70% do tamanho original
ALTURA_FRAME = 540        # Reduzido para 70% do tamanho original
ALTURA_BARRA = 100        # Altura da barra de filtros
ALTURA_ADESIVOS = 100     # Altura da área de adesivos
ALTURA_BOTOES = 50        # Altura dos botões "Salvar" e "Desfazer"

# Nomes dos filtros disponíveis (filtros removidos: "Pretty Freckles" e "Filtro P&B")
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
    "Filtro Kodak"          # Filtro 9
]

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

    # Separar canais e criar máscara caso o adesivo tenha canal alfa
    if adesivo.shape[2] == 4:  # Verifica canal alfa
        azul, verde, vermelho, alfa = cv2.split(adesivo)
        adesivo_rgb = cv2.merge((azul, verde, vermelho))
        mascara = alfa
    else:
        adesivo_rgb = adesivo
        mascara = np.ones((altura_adesivo, largura_adesivo), dtype=np.uint8) * 255

    # Ajusta posição e evita sobreposição fora da imagem
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
    return imagem


def gerar_miniaturas(imagem):
    """
    Gera miniaturas dos filtros disponíveis para exibição na barra.
    """
    miniaturas = []
    for i in range(len(nomes_filtros)):
        filtro_aplicado = aplicar_filtro(imagem, i)
        miniatura = cv2.resize(filtro_aplicado, (80, 80))
        miniaturas.append(miniatura)
    return miniaturas


def atualizar_janela():
    """
    Atualiza a janela principal com a imagem, área de adesivos e barra de filtros.
    """
    visualizacao = redimensionar_para_visualizacao(imagem_com_efeitos)
    largura_total = visualizacao.shape[1]
    altura_total = visualizacao.shape[0] + ALTURA_ADESIVOS + ALTURA_BARRA
    janela = np.zeros((altura_total, largura_total, 3), dtype=np.uint8)

    # Adiciona área de adesivos
    janela[:ALTURA_ADESIVOS] = desenhar_area_adesivos(largura_total)

    # Adiciona a imagem editada
    janela[ALTURA_ADESIVOS:ALTURA_ADESIVOS + visualizacao.shape[0]] = visualizacao

    # Adiciona a barra de filtros
    janela[ALTURA_ADESIVOS + visualizacao.shape[0]:] = desenhar_barra_de_filtros(largura_total)

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
    x_offset = 10
    for i, miniatura in enumerate(miniaturas):
        largura_disponivel = min(80, largura - x_offset - 10)
        if largura_disponivel <= 0:
            break
        miniatura_redimensionada = cv2.resize(miniatura, (largura_disponivel, 80))
        barra[10:10 + miniatura_redimensionada.shape[0], x_offset:x_offset + miniatura_redimensionada.shape[1]] = miniatura_redimensionada
        if i == indice_filtro_atual:
            cv2.rectangle(barra, (x_offset, 10), (x_offset + miniatura_redimensionada.shape[1], 90), (0, 255, 0), 2)
        x_offset += largura_disponivel + 10
    return barra


def callback_mouse(evento, x, y, flags, parametros):
    """
    Lida com cliques e eventos do mouse na interface.
    """
    global imagem_com_efeitos, historico_acao, indice_adesivo_atual, indice_filtro_atual
    visualizacao_altura = redimensionar_para_visualizacao(imagem_com_efeitos).shape[0]

    if evento == cv2.EVENT_LBUTTONDOWN:
        # Verifica se o clique está na área dos adesivos
        if 0 <= y <= ALTURA_ADESIVOS:
            indice = x // 90
            if indice < len(adesivos):
                indice_adesivo_atual = indice
                atualizar_janela()
        # Verifica se o clique está na imagem para adicionar adesivo
        elif ALTURA_ADESIVOS <= y <= ALTURA_ADESIVOS + visualizacao_altura:
            x_original = int(x / escala_visualizacao)
            y_original = int((y - ALTURA_ADESIVOS) / escala_visualizacao)
            adesivo = list(adesivos.values())[indice_adesivo_atual]
            historico_acao.append(imagem_com_efeitos.copy())
            aplicar_adesivo(imagem_com_efeitos, adesivo, x_original, y_original)
            atualizar_janela()
        # Verifica se o clique está na barra de filtros
        elif ALTURA_ADESIVOS + visualizacao_altura < y <= ALTURA_ADESIVOS + visualizacao_altura + ALTURA_BARRA:
            indice_filtro = x // 90
            if indice_filtro < len(nomes_filtros):
                indice_filtro_atual = indice_filtro
                imagem_com_efeitos = aplicar_filtro(imagem_original, indice_filtro_atual)
                historico_acao.append(imagem_com_efeitos.copy())
                atualizar_janela()

    # Scroll do mouse para trocar adesivo
    elif evento == cv2.EVENT_MOUSEWHEEL:
        if flags > 0:
            indice_adesivo_atual = (indice_adesivo_atual + 1) % len(adesivos)
        else:
            indice_adesivo_atual = (indice_adesivo_atual - 1) % len(adesivos)
        atualizar_janela()


# ---------------------------------------
# Fluxo principal do programa
# ---------------------------------------

def main():
    """
    Executa o programa principal.
    """
    global imagem_com_efeitos, imagem_original, miniaturas, historico_acao

    # Seleciona uma imagem para edição
    Tk().withdraw()
    caminho_imagem = filedialog.askopenfilename(
        title="Selecione uma imagem",
        filetypes=[("Imagens", "*.png *.jpg *.jpeg *.bmp *.tiff *.gif")]
    )
    if not caminho_imagem:
        print("Nenhuma imagem selecionada.")
        exit(1)

    # Carrega a imagem selecionada
    imagem_original = cv2.imread(caminho_imagem)
    if imagem_original is None:
        print("Erro ao carregar a imagem.")
        exit(1)

    # Inicializa a imagem com efeitos e gera miniaturas
    imagem_com_efeitos = imagem_original.copy()
    historico_acao.append(imagem_com_efeitos.copy())
    miniaturas = gerar_miniaturas(imagem_original)

    # Exibe a interface e configura eventos de mouse
    atualizar_janela()
    cv2.setMouseCallback("Editor", callback_mouse)

    # Loop principal para interação do usuário
    while True:
        tecla = cv2.waitKey(1) & 0xFF
        if tecla == 27:  # Tecla ESC para sair
            break

    cv2.destroyAllWindows()


# ---------------------------------------
# Executa o programa
# ---------------------------------------
if __name__ == "__main__":
    main()
