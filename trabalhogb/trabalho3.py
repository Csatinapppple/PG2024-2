import cv2  # Biblioteca para manipulação de imagens e vídeos
import numpy as np  # Biblioteca para operações numéricas
from tkinter import Tk, filedialog  # Interface gráfica para seleção de arquivos

# Carregar adesivos (stickers) com transparência
adesivos = {
    'oculos': cv2.imread('eyeglasses.png', cv2.IMREAD_UNCHANGED),
    'chapeu': cv2.imread('hat.png', cv2.IMREAD_UNCHANGED),
    'estrela': cv2.imread('star.png', cv2.IMREAD_UNCHANGED),
    'arvore': cv2.imread('arvore.png', cv2.IMREAD_UNCHANGED),
    'alce': cv2.imread('alce.png', cv2.IMREAD_UNCHANGED),
    'nascimento': cv2.imread('nascimento.png', cv2.IMREAD_UNCHANGED),
}

# Verifica se todos os adesivos foram carregados corretamente
for nome, adesivo in adesivos.items():
    if adesivo is None:
        print(f"Erro ao carregar o adesivo: {nome}")
        exit(1)

# Variáveis globais
indice_adesivo_atual = 0
indice_filtro_atual = 0
historico_acao = []
imagem_original = None
imagem_para_visualizacao = None
imagem_com_efeitos = None
escala_visualizacao = None

# Dimensões do frame de visualização
LARGURA_FRAME = 800
ALTURA_FRAME = 600

# Lista de nomes dos filtros para exibição
nomes_filtros = [
    "Original", "Escala de Cinza", "Inversão", "Desfoque", "Clarendon",
    "Efeito Tumblr", "Efeito Prism", "Pretty Freckles", "Vintage",
    "Silly Face", "Kyle+Kendall Slim", "Filtro P&B", "Filtro Kodak"
]

# Função para selecionar uma imagem
def selecionar_imagem():
    Tk().withdraw()
    caminho_arquivo = filedialog.askopenfilename(
        title="Selecione uma imagem",
        filetypes=[("Imagens", "*.png *.jpg *.jpeg *.bmp *.tiff *.gif")]
    )
    if not caminho_arquivo:
        print("Nenhuma imagem selecionada. O programa será encerrado.")
        exit(1)
    return caminho_arquivo

# Função para redimensionar a imagem para o quadro de visualização
def redimensionar_para_visualizacao(imagem):
    global escala_visualizacao
    altura, largura = imagem.shape[:2]
    escala_visualizacao = min(LARGURA_FRAME / largura, ALTURA_FRAME / altura)
    nova_largura = int(largura * escala_visualizacao)
    nova_altura = int(altura * escala_visualizacao)
    return cv2.resize(imagem, (nova_largura, nova_altura))

# Função para aplicar um adesivo na imagem
def aplicar_adesivo(imagem_fundo, adesivo, posicao_x, posicao_y):
    altura_adesivo, largura_adesivo = adesivo.shape[:2]
    altura_fundo, largura_fundo = imagem_fundo.shape[:2]

    if posicao_x + largura_adesivo > largura_fundo or posicao_y + altura_adesivo > altura_fundo:
        largura_adesivo = min(largura_adesivo, largura_fundo - posicao_x)
        altura_adesivo = min(altura_adesivo, altura_fundo - posicao_y)
        adesivo = adesivo[:altura_adesivo, :largura_adesivo]

    if adesivo.shape[2] == 4:
        azul, verde, vermelho, alfa = cv2.split(adesivo)
        mascara = alfa.astype(np.uint8)
        adesivo = cv2.merge((azul, verde, vermelho))
    else:
        mascara = np.ones(adesivo.shape[:2], dtype=np.uint8) * 255

    area_interesse = imagem_fundo[posicao_y:posicao_y + altura_adesivo, posicao_x:posicao_x + largura_adesivo]
    fundo_mascarado = cv2.bitwise_and(area_interesse, area_interesse, mask=cv2.bitwise_not(mascara))
    adesivo_mascarado = cv2.bitwise_and(adesivo, adesivo, mask=mascara)
    imagem_fundo[posicao_y:posicao_y + altura_adesivo, posicao_x:posicao_x + largura_adesivo] = cv2.add(fundo_mascarado, adesivo_mascarado)
    return imagem_fundo

# Função para aplicar filtros predefinidos
def aplicar_filtro(imagem, indice_filtro):
    if indice_filtro == 0:
        return imagem.copy()
    elif indice_filtro == 1:
        filtro = cv2.cvtColor(imagem, cv2.COLOR_BGR2GRAY)
        return cv2.cvtColor(filtro, cv2.COLOR_GRAY2BGR)
    elif indice_filtro == 2:
        return cv2.bitwise_not(imagem)
    elif indice_filtro == 3:
        return cv2.GaussianBlur(imagem, (15, 15), 0)
    elif indice_filtro == 4:
        return cv2.addWeighted(imagem, 1.2, cv2.GaussianBlur(imagem, (15, 15), 0), -0.2, 0)
    elif indice_filtro == 5:
        return cv2.applyColorMap(imagem, cv2.COLORMAP_PINK)
    elif indice_filtro == 6:
        return cv2.applyColorMap(imagem, cv2.COLORMAP_RAINBOW)
    elif indice_filtro == 7:
        return cv2.cvtColor(cv2.cvtColor(imagem, cv2.COLOR_BGR2HSV), cv2.COLOR_HSV2BGR)
    elif indice_filtro == 8:
        sepia_filter = np.array([[0.272, 0.534, 0.131],
                                 [0.349, 0.686, 0.168],
                                 [0.393, 0.769, 0.189]])
        imagem_vintage = cv2.transform(imagem, sepia_filter)
        return np.clip(imagem_vintage, 0, 255).astype(np.uint8)
    elif indice_filtro == 9:
        return cv2.add(imagem, np.full_like(imagem, 30))
    elif indice_filtro == 10:
        return cv2.bilateralFilter(imagem, 15, 80, 80)
    elif indice_filtro == 11:
        pb_filter = cv2.cvtColor(imagem, cv2.COLOR_BGR2GRAY)
        return cv2.merge([pb_filter, pb_filter, pb_filter])
    elif indice_filtro == 12:
        lookup_table = np.array([min(i + 20, 255) for i in range(256)]).astype("uint8")
        return cv2.LUT(imagem, lookup_table)
    return imagem

# Função para desenhar o menu e o nome do filtro
def desenhar_menu_e_filtro(imagem, nome_filtro):
    instrucoes = [
        "Teclas de Atalho:",
        "'F' - Aplicar filtro",
        "'C' - Alterar adesivo (scroll do mouse)",
        "Clique esquerdo - Adicionar adesivo",
        "'S' - Salvar imagem",
        "Ctrl + Z - Desfazer",
        "ESC - Sair"
    ]

    altura_linha = 20
    margem = 10
    altura_menu = len(instrucoes) * altura_linha + margem * 2

    altura, largura, _ = imagem.shape
    sobreposicao = imagem.copy()
    cv2.rectangle(sobreposicao, (0, altura - altura_menu), (largura, altura), (0, 0, 0), -1)
    alpha = 0.6
    imagem = cv2.addWeighted(sobreposicao, alpha, imagem, 1 - alpha, 0)

    posicao_y = altura - altura_menu + margem
    for linha in instrucoes:
        cv2.putText(imagem, linha, (10, posicao_y), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1, cv2.LINE_AA)
        posicao_y += altura_linha

    cv2.putText(imagem, f"Filtro: {nome_filtro}", (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2, cv2.LINE_AA)

    return imagem

# Callback para eventos do mouse
def callback_mouse(evento, x, y, flags, parametros):
    global imagem_com_efeitos, indice_adesivo_atual, historico_acao
    if evento == cv2.EVENT_LBUTTONDOWN:
        x_original = int(x / escala_visualizacao)
        y_original = int(y / escala_visualizacao)
        historico_acao.append(imagem_com_efeitos.copy())
        adesivo = list(adesivos.values())[indice_adesivo_atual]
        imagem_com_efeitos = aplicar_adesivo(imagem_com_efeitos, adesivo, x_original, y_original)
        imagem_para_visualizacao = redimensionar_para_visualizacao(imagem_com_efeitos)
        imagem_com_menu = desenhar_menu_e_filtro(imagem_para_visualizacao.copy(), nomes_filtros[indice_filtro_atual])
        cv2.imshow("Editor", imagem_com_menu)
    elif evento == cv2.EVENT_MOUSEWHEEL:
        indice_adesivo_atual = (indice_adesivo_atual + (1 if flags > 0 else -1)) % len(adesivos)
        print(f"Adesivo atual: {list(adesivos.keys())[indice_adesivo_atual]}")

# Função principal do programa
def main():
    global imagem_com_efeitos, imagem_original, imagem_para_visualizacao, indice_filtro_atual, historico_acao

    caminho_imagem = selecionar_imagem()
    imagem_original = cv2.imread(caminho_imagem)
    if imagem_original is None:
        print("Erro ao carregar a imagem selecionada.")
        exit(1)

    imagem_para_visualizacao = redimensionar_para_visualizacao(imagem_original)
    imagem_com_efeitos = imagem_original.copy()
    historico_acao.append(imagem_com_efeitos.copy())

    imagem_com_menu = desenhar_menu_e_filtro(imagem_para_visualizacao.copy(), nomes_filtros[indice_filtro_atual])
    cv2.imshow("Editor", imagem_com_menu)
    cv2.setMouseCallback("Editor", callback_mouse)

    while True:
        tecla = cv2.waitKey(1) & 0xFF
        if tecla == 27:
            break
        elif tecla == ord('s'):
            Tk().withdraw()
            caminho_salvar = filedialog.asksaveasfilename(
                title="Salvar imagem como",
                defaultextension=".png",
                filetypes=[("PNG files", "*.png"), ("JPEG files", "*.jpg"), ("All files", "*.*")]
            )
            if caminho_salvar:
                cv2.imwrite(caminho_salvar, imagem_com_efeitos)
                print(f"Imagem salva em {caminho_salvar}")
        elif tecla == ord('f'):
            indice_filtro_atual = (indice_filtro_atual + 1) % len(nomes_filtros)
            imagem_com_efeitos = aplicar_filtro(imagem_original, indice_filtro_atual)
            imagem_para_visualizacao = redimensionar_para_visualizacao(imagem_com_efeitos)
            imagem_com_menu = desenhar_menu_e_filtro(imagem_para_visualizacao.copy(), nomes_filtros[indice_filtro_atual])
            cv2.imshow("Editor", imagem_com_menu)
        elif tecla == 26:
            if len(historico_acao) > 1:
                historico_acao.pop()
                imagem_com_efeitos = historico_acao[-1].copy()
                imagem_para_visualizacao = redimensionar_para_visualizacao(imagem_com_efeitos)
                imagem_com_menu = desenhar_menu_e_filtro(imagem_para_visualizacao.copy(), nomes_filtros[indice_filtro_atual])
                cv2.imshow("Editor", imagem_com_menu)

    cv2.destroyAllWindows()

if __name__ == "__main__":
    main()
