import cv2  # Biblioteca para manipulação de imagens e vídeos
import numpy as np  # Biblioteca para operações numéricas
from tkinter import Tk, filedialog  # Interface gráfica para seleção de arquivos

# Carregar adesivos (stickers) com transparência
# Cada adesivo é carregado como uma imagem com 4 canais (BGR + Alfa)
adesivos = {
    'oculos': cv2.imread('eyeglasses.png', cv2.IMREAD_UNCHANGED),
    'chapeu': cv2.imread('hat.png', cv2.IMREAD_UNCHANGED),
    'estrela': cv2.imread('star.png', cv2.IMREAD_UNCHANGED),
    'arvore': cv2.imread('arvore.png', cv2.IMREAD_UNCHANGED),
    'alce': cv2.imread('alce.png', cv2.IMREAD_UNCHANGED),
    'nascimento': cv2.imread('nascimento.png', cv2.IMREAD_UNCHANGED),
}

# Verifica se todos os adesivos foram carregados corretamente
# Caso algum adesivo não seja encontrado, o programa encerra com uma mensagem de erro.
for nome, adesivo in adesivos.items():
    if adesivo is None:
        print(f"Erro ao carregar o adesivo: {nome}")
        exit(1)

# Variáveis globais
indice_adesivo_atual = 0  # Índice do adesivo que está selecionado para ser aplicado
indice_filtro_atual = 0  # Índice do filtro atualmente aplicado à imagem
historico_acao = []  # Lista que armazena os estados da imagem para desfazer ações
imagem_original = None  # A imagem original carregada pelo usuário
imagem_com_efeitos = None  # A imagem atual com efeitos e adesivos aplicados

# Dimensões mínimas para a janela de visualização
LARGURA_MINIMA = 800
ALTURA_MINIMA = 600

# Lista de nomes dos filtros para exibição
nomes_filtros = [
    "Original", "Escala de Cinza", "Inversão", "Desfoque", "Clarendon",
    "Efeito Tumblr", "Efeito Prism", "Pretty Freckles", "Vintage",
    "Silly Face", "Kyle+Kendall Slim", "Filtro P&B", "Filtro Kodak"
]

# Função para selecionar uma imagem
def selecionar_imagem():
    """
    Exibe uma janela para o usuário selecionar uma imagem do computador.
    Retorna o caminho completo do arquivo selecionado.
    """
    Tk().withdraw()  # Oculta a janela principal do Tkinter
    caminho_arquivo = filedialog.askopenfilename(
        title="Selecione uma imagem",
        filetypes=[("Imagens", "*.png *.jpg *.jpeg *.bmp *.tiff *.gif")]
    )
    if not caminho_arquivo:
        print("Nenhuma imagem selecionada. O programa será encerrado.")
        exit(1)
    return caminho_arquivo

# Função para centralizar uma imagem em um fundo preto
def centralizar_imagem(imagem, largura_minima, altura_minima):
    """
    Centraliza uma imagem em um fundo preto com dimensões mínimas.
    Caso a imagem seja menor que as dimensões mínimas, ela será centralizada.
    """
    altura, largura, canais = imagem.shape
    nova_altura = max(altura, altura_minima)
    nova_largura = max(largura, largura_minima)

    # Cria um fundo preto com as dimensões mínimas
    quadro_centralizado = np.zeros((nova_altura, nova_largura, canais), dtype=np.uint8)

    # Calcula os deslocamentos para centralizar a imagem
    deslocamento_y = (nova_altura - altura) // 2
    deslocamento_x = (nova_largura - largura) // 2

    # Insere a imagem no centro do fundo preto
    quadro_centralizado[deslocamento_y:deslocamento_y + altura, deslocamento_x:deslocamento_x + largura] = imagem
    return quadro_centralizado

# Função para aplicar um adesivo na imagem
def aplicar_adesivo(imagem_fundo, adesivo, posicao_x, posicao_y):
    """
    Adiciona um adesivo em uma posição específica da imagem.
    Adesivos que ultrapassam os limites da imagem são ajustados.
    """
    altura_adesivo, largura_adesivo = adesivo.shape[:2]
    altura_fundo, largura_fundo = imagem_fundo.shape[:2]

    # Ajusta o tamanho do adesivo caso ultrapasse os limites da imagem
    if posicao_x + largura_adesivo > largura_fundo or posicao_y + altura_adesivo > altura_fundo:
        largura_adesivo = min(largura_adesivo, largura_fundo - posicao_x)
        altura_adesivo = min(altura_adesivo, altura_fundo - posicao_y)
        adesivo = adesivo[:altura_adesivo, :largura_adesivo]

    # Verifica se o adesivo possui transparência (canal alfa)
    if adesivo.shape[2] == 4:
        azul, verde, vermelho, alfa = cv2.split(adesivo)
        mascara = alfa.astype(np.uint8)  # Usa o canal alfa como máscara
        adesivo = cv2.merge((azul, verde, vermelho))
    else:
        mascara = np.ones(adesivo.shape[:2], dtype=np.uint8) * 255

    # Seleciona a região de interesse (ROI) no fundo onde o adesivo será aplicado
    area_interesse = imagem_fundo[posicao_y:posicao_y + altura_adesivo, posicao_x:posicao_x + largura_adesivo]
    fundo_mascarado = cv2.bitwise_and(area_interesse, area_interesse, mask=cv2.bitwise_not(mascara))
    adesivo_mascarado = cv2.bitwise_and(adesivo, adesivo, mask=mascara)
    imagem_fundo[posicao_y:posicao_y + altura_adesivo, posicao_x:posicao_x + largura_adesivo] = cv2.add(fundo_mascarado, adesivo_mascarado)
    return imagem_fundo

# Função para aplicar filtros predefinidos
def aplicar_filtro(imagem, indice_filtro):
    """
    Aplica um dos filtros predefinidos à imagem com base no índice selecionado.
    Filtros disponíveis incluem filtros originais e personalizados.
    """
    if indice_filtro == 0:  # Imagem original sem alterações
        return imagem.copy()
    elif indice_filtro == 1:  # Escala de Cinza
        filtro = cv2.cvtColor(imagem, cv2.COLOR_BGR2GRAY)
        return cv2.cvtColor(filtro, cv2.COLOR_GRAY2BGR)
    elif indice_filtro == 2:  # Inversão
        return cv2.bitwise_not(imagem)
    elif indice_filtro == 3:  # Desfoque
        return cv2.GaussianBlur(imagem, (15, 15), 0)
    elif indice_filtro == 4:  # Clarendon
        return cv2.addWeighted(imagem, 1.2, cv2.GaussianBlur(imagem, (15, 15), 0), -0.2, 0)
    elif indice_filtro == 5:  # Efeito Tumblr
        return cv2.applyColorMap(imagem, cv2.COLORMAP_PINK)
    elif indice_filtro == 6:  # Prism
        return cv2.applyColorMap(imagem, cv2.COLORMAP_RAINBOW)
    elif indice_filtro == 7:  # Pretty Freckles
        return cv2.cvtColor(cv2.cvtColor(imagem, cv2.COLOR_BGR2HSV), cv2.COLOR_HSV2BGR)
    elif indice_filtro == 8:  # Vintage
        sepia_filter = np.array([[0.272, 0.534, 0.131],
                                 [0.349, 0.686, 0.168],
                                 [0.393, 0.769, 0.189]])
        imagem_vintage = cv2.transform(imagem, sepia_filter)
        return np.clip(imagem_vintage, 0, 255).astype(np.uint8)  # Usando np.clip
    elif indice_filtro == 9:  # Silly Face
        return cv2.add(imagem, np.full_like(imagem, 30))
    elif indice_filtro == 10:  # Kyle+Kendall Slim
        return cv2.bilateralFilter(imagem, 15, 80, 80)
    elif indice_filtro == 11:  # Filtro P&B
        pb_filter = cv2.cvtColor(imagem, cv2.COLOR_BGR2GRAY)
        return cv2.merge([pb_filter, pb_filter, pb_filter])
    elif indice_filtro == 12:  # Filtro Kodak
        lookup_table = np.array([min(i + 20, 255) for i in range(256)]).astype("uint8")
        return cv2.LUT(imagem, lookup_table)
    return imagem  # Retorna a imagem sem alterações se nenhum filtro corresponder

# Função para desenhar o menu e o nome do filtro
def desenhar_menu_e_filtro(imagem, nome_filtro):
    """
    Exibe o menu de comandos e o nome do filtro atualmente aplicado sobre a imagem.
    O menu é exibido em uma área semitransparente no rodapé da imagem.
    """
    instrucoes = [
        "Teclas de Atalho:",
        "'F' - Aplicar filtro",
        "'C' - Alterar adesivo (scroll do mouse)",
        "Clique esquerdo - Adicionar adesivo",
        "'S' - Salvar imagem",
        "Ctrl + Z - Desfazer",
        "ESC - Sair"
    ]

    # Adiciona o menu no rodapé da imagem
    altura, largura, _ = imagem.shape
    sobreposicao = imagem.copy()
    cv2.rectangle(sobreposicao, (0, altura - 100), (largura, altura), (0, 0, 0), -1)  # Fundo preto semitransparente
    alpha = 0.6
    imagem = cv2.addWeighted(sobreposicao, alpha, imagem, 1 - alpha, 0)

    # Desenha as instruções do menu
    posicao_y = altura - 80
    deslocamento_y = 20
    for linha in instrucoes:
        cv2.putText(imagem, linha, (10, posicao_y), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1, cv2.LINE_AA)
        posicao_y += deslocamento_y

    # Exibe o nome do filtro no topo da imagem
    cv2.putText(imagem, f"Filtro: {nome_filtro}", (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2, cv2.LINE_AA)

    return imagem

# Callback para eventos do mouse
def callback_mouse(evento, x, y, flags, parametros):
    """
    Callback para manipulação de eventos do mouse.
    Permite adicionar adesivos na imagem com cliques e alternar adesivos com o scroll.
    """
    global imagem_com_efeitos, indice_adesivo_atual, historico_acao
    if evento == cv2.EVENT_LBUTTONDOWN:  # Clique esquerdo adiciona adesivo
        historico_acao.append(imagem_com_efeitos.copy())
        adesivo = list(adesivos.values())[indice_adesivo_atual]
        imagem_com_efeitos = aplicar_adesivo(imagem_com_efeitos, adesivo, x, y)
        imagem_com_menu = desenhar_menu_e_filtro(imagem_com_efeitos.copy(), nomes_filtros[indice_filtro_atual])
        cv2.imshow("Editor", imagem_com_menu)
    elif evento == cv2.EVENT_MOUSEWHEEL:  # Scroll alterna o adesivo atual
        indice_adesivo_atual = (indice_adesivo_atual + (1 if flags > 0 else -1)) % len(adesivos)
        print(f"Adesivo atual: {list(adesivos.keys())[indice_adesivo_atual]}")

# Função principal do programa
def main():
    """
    Gerencia o fluxo principal do programa.
    Permite selecionar uma imagem, aplicar filtros, adicionar adesivos e salvar.
    """
    global imagem_com_efeitos, imagem_original, indice_filtro_atual, historico_acao

    # Seleciona a imagem para edição
    caminho_imagem = selecionar_imagem()
    imagem_original = cv2.imread(caminho_imagem)
    if imagem_original is None:
        print("Erro ao carregar a imagem selecionada.")
        exit(1)

    # Centraliza a imagem em um fundo preto se necessário
    imagem_original = centralizar_imagem(imagem_original, LARGURA_MINIMA, ALTURA_MINIMA)
    imagem_com_efeitos = imagem_original.copy()
    historico_acao.append(imagem_com_efeitos.copy())  # Salva o estado inicial

    # Exibe a interface inicial com o menu e a imagem
    imagem_com_menu = desenhar_menu_e_filtro(imagem_com_efeitos.copy(), nomes_filtros[indice_filtro_atual])
    cv2.imshow("Editor", imagem_com_menu)
    cv2.setMouseCallback("Editor", callback_mouse)

    # Loop principal de eventos
    while True:
        tecla = cv2.waitKey(1) & 0xFF
        if tecla == 27:  # ESC para sair
            break
        elif tecla == ord('s'):  # Salvar imagem
            Tk().withdraw()
            caminho_salvar = filedialog.asksaveasfilename(
                title="Salvar imagem como",
                defaultextension=".png",
                filetypes=[("PNG files", "*.png"), ("JPEG files", "*.jpg"), ("All files", "*.*")]
            )
            if caminho_salvar:  # Salva apenas se o usuário selecionar um caminho
                cv2.imwrite(caminho_salvar, imagem_com_efeitos)
                print(f"Imagem salva em {caminho_salvar}")
        elif tecla == ord('f'):  # Aplica o próximo filtro na lista
            indice_filtro_atual = (indice_filtro_atual + 1) % len(nomes_filtros)
            imagem_com_efeitos = aplicar_filtro(imagem_original, indice_filtro_atual)
            imagem_com_menu = desenhar_menu_e_filtro(imagem_com_efeitos.copy(), nomes_filtros[indice_filtro_atual])
            cv2.imshow("Editor", imagem_com_menu)
        elif tecla == 26:  # Ctrl + Z para desfazer
            if len(historico_acao) > 1:
                historico_acao.pop()
                imagem_com_efeitos = historico_acao[-1].copy()
                imagem_com_menu = desenhar_menu_e_filtro(imagem_com_efeitos.copy(), nomes_filtros[indice_filtro_atual])
                cv2.imshow("Editor", imagem_com_menu)

    cv2.destroyAllWindows()  # Fecha todas as janelas do OpenCV


if __name__ == "__main__":
    main()
