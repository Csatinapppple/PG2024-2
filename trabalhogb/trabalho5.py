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
indice_adesivo_atual = 0  # Índice do adesivo atual
indice_filtro_atual = 0  # Índice do filtro atual
historico_acao = []  # Histórico de estados para desfazer ações
imagem_original = None  # Imagem original carregada
imagem_com_efeitos = None  # Imagem com efeitos aplicados

# Dimensões mínimas da janela
LARGURA_MINIMA = 800
ALTURA_MINIMA = 600

# Lista de nomes dos filtros
nomes_filtros = ["Original", "Escala de Cinza", "Inversão", "Desfoque"]

# Função para selecionar imagem
def selecionar_imagem():
    """Abre uma janela para o usuário selecionar uma imagem do computador."""
    Tk().withdraw()  # Oculta a janela principal do Tkinter
    caminho_arquivo = filedialog.askopenfilename(
        title="Selecione uma imagem",
        filetypes=[("Imagens", "*.png *.jpg *.jpeg *.bmp *.tiff *.gif")]
    )
    if not caminho_arquivo:
        print("Nenhuma imagem selecionada. O programa será encerrado.")
        exit(1)
    return caminho_arquivo

# Função para centralizar a imagem
def centralizar_imagem(imagem, largura_minima, altura_minima):
    """Centraliza a imagem em um fundo preto com dimensões mínimas de largura e altura."""
    altura, largura, canais = imagem.shape
    nova_altura = max(altura, altura_minima)
    nova_largura = max(largura, largura_minima)

    # Cria um fundo preto com as dimensões mínimas
    quadro_centralizado = np.zeros((nova_altura, nova_largura, canais), dtype=np.uint8)

    # Calcula as posições para centralizar a imagem
    deslocamento_y = (nova_altura - altura) // 2
    deslocamento_x = (nova_largura - largura) // 2

    # Coloca a imagem centralizada no fundo
    quadro_centralizado[deslocamento_y:deslocamento_y + altura, deslocamento_x:deslocamento_x + largura] = imagem
    return quadro_centralizado

# Função para aplicar adesivos
def aplicar_adesivo(imagem_fundo, adesivo, posicao_x, posicao_y):
    """Aplica um adesivo na imagem em uma posição específica (posicao_x, posicao_y)."""
    altura_adesivo, largura_adesivo = adesivo.shape[:2]
    altura_fundo, largura_fundo = imagem_fundo.shape[:2]

    # Ajusta a posição caso o adesivo ultrapasse os limites da imagem
    if posicao_x + largura_adesivo > largura_fundo or posicao_y + altura_adesivo > altura_fundo:
        largura_adesivo = min(largura_adesivo, largura_fundo - posicao_x)
        altura_adesivo = min(altura_adesivo, altura_fundo - posicao_y)
        adesivo = adesivo[:altura_adesivo, :largura_adesivo]

    # Verifica se o adesivo possui transparência
    if adesivo.shape[2] == 4:
        azul, verde, vermelho, alfa = cv2.split(adesivo)
        mascara = alfa.astype(np.uint8)
        adesivo = cv2.merge((azul, verde, vermelho))
    else:
        mascara = np.ones(adesivo.shape[:2], dtype=np.uint8) * 255

    # Combina o adesivo com a região de interesse na imagem de fundo
    area_interesse = imagem_fundo[posicao_y:posicao_y + altura_adesivo, posicao_x:posicao_x + largura_adesivo]
    fundo_mascarado = cv2.bitwise_and(area_interesse, area_interesse, mask=cv2.bitwise_not(mascara))
    adesivo_mascarado = cv2.bitwise_and(adesivo, adesivo, mask=mascara)
    imagem_fundo[posicao_y:posicao_y + altura_adesivo, posicao_x:posicao_x + largura_adesivo] = cv2.add(fundo_mascarado, adesivo_mascarado)
    return imagem_fundo

# Função para aplicar filtros
def aplicar_filtro(imagem, indice_filtro):
    """Aplica filtros predefinidos na imagem com base no índice do filtro."""
    if indice_filtro == 0:  # Retorna a imagem original
        return imagem.copy()
    elif indice_filtro == 1:  # Filtro em escala de cinza
        filtro = cv2.cvtColor(imagem, cv2.COLOR_BGR2GRAY)
        return cv2.cvtColor(filtro, cv2.COLOR_GRAY2BGR)  # Converte de volta para 3 canais
    elif indice_filtro == 2:  # Filtro de inversão
        return cv2.bitwise_not(imagem)
    elif indice_filtro == 3:  # Filtro de desfoque
        return cv2.GaussianBlur(imagem, (15, 15), 0)
    return imagem

# Função para desenhar o menu e nome do filtro
def desenhar_menu_e_filtro(imagem, nome_filtro):
    """Desenha o menu e o nome do filtro diretamente sobre a imagem."""
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

    # Adiciona o texto das instruções
    posicao_y = altura - 80
    deslocamento_y = 20
    for linha in instrucoes:
        cv2.putText(imagem, linha, (10, posicao_y), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1, cv2.LINE_AA)
        posicao_y += deslocamento_y

    # Adiciona o nome do filtro no topo
    cv2.putText(imagem, f"Filtro: {nome_filtro}", (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2, cv2.LINE_AA)

    return imagem

# Callback para eventos do mouse
def callback_mouse(evento, x, y, flags, parametros):
    """Callback para manipulação de eventos do mouse, como adicionar adesivos."""
    global imagem_com_efeitos, indice_adesivo_atual, historico_acao
    if evento == cv2.EVENT_LBUTTONDOWN:
        historico_acao.append(imagem_com_efeitos.copy())
        adesivo = list(adesivos.values())[indice_adesivo_atual]
        imagem_com_efeitos = aplicar_adesivo(imagem_com_efeitos, adesivo, x, y)
        imagem_com_menu = desenhar_menu_e_filtro(imagem_com_efeitos.copy(), nomes_filtros[indice_filtro_atual])
        cv2.imshow("Editor", imagem_com_menu)
    elif evento == cv2.EVENT_MOUSEWHEEL:  # Scroll do mouse para trocar adesivos
        indice_adesivo_atual = (indice_adesivo_atual + (1 if flags > 0 else -1)) % len(adesivos)
        print(f"Adesivo atual: {list(adesivos.keys())[indice_adesivo_atual]}")

# Função principal
def main():
    """Função principal que controla o fluxo do programa."""
    global imagem_com_efeitos, imagem_original, indice_filtro_atual, historico_acao

    # Seleciona a imagem
    caminho_imagem = selecionar_imagem()
    imagem_original = cv2.imread(caminho_imagem)
    if imagem_original is None:
        print("Erro ao carregar a imagem selecionada.")
        exit(1)

    # Centraliza a imagem se for menor que as dimensões mínimas
    imagem_original = centralizar_imagem(imagem_original, LARGURA_MINIMA, ALTURA_MINIMA)
    imagem_com_efeitos = imagem_original.copy()
    historico_acao.append(imagem_com_efeitos.copy())  # Salva o estado inicial

    # Adiciona o menu e exibe
    imagem_com_menu = desenhar_menu_e_filtro(imagem_com_efeitos.copy(), nomes_filtros[indice_filtro_atual])
    cv2.imshow("Editor", imagem_com_menu)
    cv2.setMouseCallback("Editor", callback_mouse)

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
        elif tecla == ord('f'):  # Aplicar filtro
            indice_filtro_atual = (indice_filtro_atual + 1) % len(nomes_filtros)
            imagem_com_efeitos = aplicar_filtro(imagem_original, indice_filtro_atual)
            imagem_com_menu = desenhar_menu_e_filtro(imagem_com_efeitos.copy(), nomes_filtros[indice_filtro_atual])
            cv2.imshow("Editor", imagem_com_menu)
        elif tecla == 26:  # Ctrl + Z (Desfazer)
            if len(historico_acao) > 1:
                historico_acao.pop()
                imagem_com_efeitos = historico_acao[-1].copy()
                imagem_com_menu = desenhar_menu_e_filtro(imagem_com_efeitos.copy(), nomes_filtros[indice_filtro_atual])
                cv2.imshow("Editor", imagem_com_menu)

    cv2.destroyAllWindows()  # Fecha todas as janelas ao sair


if __name__ == "__main__":
    main()
