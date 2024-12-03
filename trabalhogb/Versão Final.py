import cv2
import numpy as np
from tkinter import Tk, filedialog, Button, Label

# ---------------------------------------
# Configurações iniciais e variáveis globais
# ---------------------------------------

# Carregar adesivos com transparência, cada adesivo é lido com canal alfa (IMREAD_UNCHANGED).
adesivos = {
    'oculos': cv2.imread('eyeglasses.png', cv2.IMREAD_UNCHANGED),
    'chapeu': cv2.imread('hat.png', cv2.IMREAD_UNCHANGED),
    'estrela': cv2.imread('star.png', cv2.IMREAD_UNCHANGED),
    'arvore': cv2.imread('arvore.png', cv2.IMREAD_UNCHANGED),
    'alce': cv2.imread('alce.png', cv2.IMREAD_UNCHANGED),
    'nascimento': cv2.imread('nascimento.png', cv2.IMREAD_UNCHANGED),
}

# Verifica se os adesivos foram carregados corretamente.
for nome, adesivo in adesivos.items():
    if adesivo is None:  # Se algum adesivo não foi carregado.
        print(f"Erro ao carregar o adesivo: {nome}")  # Imprime mensagem de erro.
        exit(1)  # Encerra o programa.

# Declaração de variáveis globais utilizadas em todo o programa.
indice_adesivo_atual = 0  # Indica qual adesivo está selecionado no momento.
indice_filtro_atual = 0   # Indica qual filtro está selecionado no momento.
historico_acao = []       # Lista para armazenar o histórico de ações (para desfazer alterações).
imagem_original = None    # Armazena a imagem original carregada pelo usuário.
imagem_com_efeitos = None # Armazena a imagem com filtros ou adesivos aplicados.
escala_visualizacao = None  # Armazena a escala da imagem para exibição na interface.
miniaturas = []           # Lista de miniaturas de filtros, para exibição na interface.
usando_webcam = False     # Indica se o programa está no modo de uso de webcam.
video_writer = None       # Objeto para gravar vídeos com frames processados.
video_filename = None     # Nome do arquivo de vídeo que será salvo.
gravando_video = False    # Indica se o programa está gravando um vídeo no momento.

# Definição de dimensões para a janela e elementos visuais.
LARGURA_JANELA = 1366
ALTURA_JANELA = 768
LARGURA_FRAME = 768
ALTURA_FRAME = 432
ALTURA_ADESIVOS = 100
ALTURA_BARRA = 100
ALTURA_BOTOES = 50

# Lista com os nomes dos filtros disponíveis.
nomes_filtros = [
    "Original",             # Filtro 0: Sem alterações na imagem.
    "Escala de Cinza",      # Filtro 1: Converte a imagem para preto e branco.
    "Inversão",             # Filtro 2: Inverte as cores da imagem.
    "Desfoque",             # Filtro 3: Aplica um desfoque na imagem.
    "Efeito Tumblr",        # Filtro 4: Aplica um efeito de tonalidade rosa.
    "Efeito Prism",         # Filtro 5: Aplica um efeito de arco-íris.
    "Vintage",              # Filtro 6: Aplica uma tonalidade sépia para um estilo retrô.
    "Silly Face",           # Filtro 7: Aumenta o brilho da imagem.
    "Kyle+Kendall Slim",    # Filtro 8: Aplica suavização à imagem.
    "Filtro Kodak",         # Filtro 9: Simula cores mais quentes, estilo filme Kodak.
    "Negativo da Foto"      # Filtro 10: Converte para negativo.
]

# ---------------------------------------
# Funções auxiliares
# ---------------------------------------

def redimensionar_para_visualizacao(imagem):
    """
    Redimensiona a imagem para caber no quadro de edição, mantendo a proporção.
    """
    global escala_visualizacao
    if imagem is None:  # Caso a imagem seja None, retorna None.
        return None
    altura, largura = imagem.shape[:2]  # Obtém as dimensões da imagem (altura, largura).
    # Calcula a escala máxima para que a imagem caiba dentro das dimensões do frame.
    escala_visualizacao = min(LARGURA_FRAME / largura, ALTURA_FRAME / altura)
    nova_largura = int(largura * escala_visualizacao)  # Calcula a nova largura.
    nova_altura = int(altura * escala_visualizacao)    # Calcula a nova altura.
    # Redimensiona a imagem para as novas dimensões.
    return cv2.resize(imagem, (nova_largura, nova_altura))

def aplicar_adesivo(imagem_fundo, adesivo, x, y):
    """
    Aplica um adesivo na posição especificada (x, y) da imagem.
    Suporta adesivos com canal alfa para transparência.
    """
    altura_adesivo, largura_adesivo = adesivo.shape[:2]  # Obtém as dimensões do adesivo.

    if adesivo.shape[2] == 4:  # Verifica se o adesivo possui canal alfa.
        azul, verde, vermelho, alfa = cv2.split(adesivo)  # Separa os canais RGBA.
        adesivo_rgb = cv2.merge((azul, verde, vermelho))  # Junta os canais RGB.
        mascara = alfa  # Define a máscara como o canal alfa.
    else:  # Caso o adesivo não tenha canal alfa.
        adesivo_rgb = adesivo  # Usa o adesivo sem alterações.
        # Cria uma máscara branca do tamanho do adesivo.
        mascara = np.ones((altura_adesivo, largura_adesivo), dtype=np.uint8) * 255

    # Verifica se o adesivo está dentro dos limites da imagem.
    if y + altura_adesivo > imagem_fundo.shape[0] or x + largura_adesivo > imagem_fundo.shape[1]:
        return  # Não aplica o adesivo se estiver fora dos limites.

    # Seleciona a região na imagem onde o adesivo será aplicado.
    roi = imagem_fundo[y:y + altura_adesivo, x:x + largura_adesivo]
    # Remove a área onde o adesivo será aplicado usando a máscara invertida.
    fundo = cv2.bitwise_and(roi, roi, mask=cv2.bitwise_not(mascara))
    # Combina a área limpa com o adesivo usando a máscara.
    sobreposicao = cv2.add(fundo, adesivo_rgb)
    # Insere o adesivo na imagem.
    imagem_fundo[y:y + altura_adesivo, x:x + largura_adesivo] = sobreposicao

def aplicar_adesivo_webcam(imagem_fundo, adesivo, x, y):
    """
    Aplica um adesivo na imagem de fundo usada na webcam e mantém os adesivos persistentes.
    """
    global imagem_com_adesivos
    altura_adesivo, largura_adesivo = adesivo.shape[:2]  # Obtém as dimensões do adesivo.

    if adesivo.shape[2] == 4:  # Verifica se o adesivo possui canal alfa.
        azul, verde, vermelho, alfa = cv2.split(adesivo)  # Separa os canais RGBA.
        adesivo_rgb = cv2.merge((azul, verde, vermelho))  # Junta os canais RGB.
        mascara = alfa  # Define a máscara como o canal alfa.
    else:  # Caso o adesivo não tenha canal alfa.
        adesivo_rgb = adesivo  # Usa o adesivo sem alterações.
        # Cria uma máscara branca do tamanho do adesivo.
        mascara = np.ones((altura_adesivo, largura_adesivo), dtype=np.uint8) * 255

    # Verifica se o adesivo está dentro dos limites da imagem.
    if y + altura_adesivo > imagem_fundo.shape[0] or x + largura_adesivo > imagem_fundo.shape[1]:
        return  # Não aplica o adesivo se estiver fora dos limites.

    # Seleciona a região na camada de adesivos onde o adesivo será aplicado.
    roi = imagem_com_adesivos[y:y + altura_adesivo, x:x + largura_adesivo]
    # Remove a área onde o adesivo será aplicado usando a máscara invertida.
    fundo = cv2.bitwise_and(roi, roi, mask=cv2.bitwise_not(mascara))
    # Combina a área limpa (fundo sem adesivo) com o adesivo usando a máscara.
    # A função cv2.add realiza a soma pixel a pixel do fundo e do adesivo RGB.
    sobreposicao = cv2.add(fundo, adesivo_rgb)

    # Atualiza a camada de adesivos, substituindo a área correspondente pelo adesivo já combinado.
    # Isso garante que o adesivo permaneça fixo na imagem, mesmo que o frame mude.
    imagem_com_adesivos[y:y + altura_adesivo, x:x + largura_adesivo] = sobreposicao

def aplicar_filtro_generico(imagem_base, indice_filtro):
    """
    Aplica um dos filtros predefinidos na imagem base fornecida.
    """
    # Verifica se a imagem base é válida (não é None). Se não for, retorna None.
    if imagem_base is None:
        return None

    # Aplica o filtro correspondente ao índice especificado.
    if indice_filtro == 0:  # Filtro Original: Retorna a imagem sem alterações.
        return imagem_base.copy()

    elif indice_filtro == 1:  # Escala de Cinza: Converte a imagem para tons de cinza.
        # Primeiro, converte para escala de cinza.
        filtro = cv2.cvtColor(imagem_base, cv2.COLOR_BGR2GRAY)
        # Em seguida, converte de volta para RGB para compatibilidade com as outras funções.
        return cv2.cvtColor(filtro, cv2.COLOR_GRAY2BGR)

    elif indice_filtro == 2:  # Inversão: Inverte as cores da imagem.
        return cv2.bitwise_not(imagem_base)

    elif indice_filtro == 3:  # Desfoque: Aplica um desfoque Gaussian Blur.
        # Usa um kernel 15x15 e sigma padrão para suavizar a imagem.
        return cv2.GaussianBlur(imagem_base, (15, 15), 0)

    elif indice_filtro == 4:  # Efeito Tumblr: Aplica um mapa de cores rosa (COLORMAP_PINK).
        return cv2.applyColorMap(imagem_base, cv2.COLORMAP_PINK)

    elif indice_filtro == 5:  # Efeito Prism: Aplica um mapa de cores em arco-íris.
        return cv2.applyColorMap(imagem_base, cv2.COLORMAP_RAINBOW)

    elif indice_filtro == 6:  # Vintage: Aplica um efeito sépia para estilo retrô.
        # Define a matriz de transformação de cores para o efeito sépia.
        sepia_filter = np.array([[0.272, 0.534, 0.131],
                                 [0.349, 0.686, 0.168],
                                 [0.393, 0.769, 0.189]])
        # Aplica a transformação de cores usando a matriz definida.
        imagem_vintage = cv2.transform(imagem_base, sepia_filter)
        # Clipa os valores para que permaneçam no intervalo de 0 a 255 (valores válidos para pixels).
        return np.clip(imagem_vintage, 0, 255).astype(np.uint8)

    elif indice_filtro == 7:  # Silly Face: Aumenta o brilho da imagem.
        # Soma uma constante de 30 a todos os pixels da imagem, aumentando o brilho.
        return cv2.add(imagem_base, np.full_like(imagem_base, 30))

    elif indice_filtro == 8:  # Kyle+Kendall Slim: Aplica um filtro bilateral para suavização.
        # Usa filtro bilateral com raio 15 e valores para sigmaColor e sigmaSpace iguais a 80.
        return cv2.bilateralFilter(imagem_base, 15, 80, 80)

    elif indice_filtro == 9:  # Filtro Kodak: Simula um efeito de cor quente.
        # Cria uma tabela de look-up para aumentar os valores de intensidade.
        lookup_table = np.array([min(i + 20, 255) for i in range(256)]).astype("uint8")
        # Aplica a tabela de look-up à imagem, ajustando os valores.
        return cv2.LUT(imagem_base, lookup_table)

    elif indice_filtro == 10:  # Negativo da Foto: Inverte as cores da imagem.
        # Usa a mesma técnica de inversão do filtro 2.
        return cv2.bitwise_not(imagem_base)

    # Caso o índice não corresponda a nenhum filtro, retorna a imagem original.
    return imagem_base

def salvar_imagem(imagem):
    """
    Salva a imagem atual na pasta que o usuário desejar.
    """
    # Cria uma janela de diálogo para o usuário selecionar onde salvar a imagem.
    Tk().withdraw()  # Oculta a janela principal do Tkinter.
    caminho_salvar = filedialog.asksaveasfilename(
        title="Salvar imagem como",  # Define o título da janela.
        defaultextension=".png",     # Extensão padrão do arquivo salvo.
        filetypes=[("PNG files", "*.png"), ("JPEG files", "*.jpg"), ("All files", "*.*")]  # Tipos de arquivos permitidos.
    )
    # Se o usuário escolheu um local para salvar:
    if caminho_salvar:
        # Salva a imagem no caminho especificado.
        cv2.imwrite(caminho_salvar, imagem)
        # Exibe uma mensagem confirmando o local onde a imagem foi salva.
        print(f"Imagem salva em {caminho_salvar}")

def iniciar_video_writer(frame):
    """
    Inicializa o gravador de vídeo após o usuário escolher o local de salvamento.
    """
    global video_writer, video_filename, gravando_video

    # Exibe uma janela para o usuário escolher onde salvar o vídeo.
    Tk().withdraw()  # Oculta a janela principal do Tkinter.
    video_filename = filedialog.asksaveasfilename(
        title="Salvar vídeo como",  # Define o título da janela.
        defaultextension=".mp4",    # Extensão padrão do vídeo salvo.
        filetypes=[("Vídeo MP4", "*.mp4"), ("Todos os arquivos", "*.*")]  # Tipos de arquivos permitidos.
    )

    # Se o usuário não escolheu um local para salvar, cancela a gravação.
    if not video_filename:
        print("Gravação de vídeo cancelada.")  # Exibe uma mensagem de cancelamento.
        return

    # Define o codec de compressão de vídeo (MP4).
    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    # Inicializa o objeto VideoWriter com o codec, FPS, e dimensões do frame.
    video_writer = cv2.VideoWriter(video_filename, fourcc, 30, (frame.shape[1], frame.shape[0]))
    gravando_video = True  # Define que a gravação está ativa.
    print(f"Gravação de vídeo iniciada: {video_filename}")  # Mensagem de confirmação.

def salvar_frame_webcam(frame):
    """
    Salva o frame atual no gravador de vídeo, se a gravação estiver ativa.
    """
    global video_writer, gravando_video

    # Verifica se a gravação está ativa e o objeto VideoWriter está inicializado.
    if gravando_video and video_writer is not None:
        # Adiciona o frame atual ao vídeo.
        video_writer.write(frame)

def finalizar_video_writer():
    """
    Finaliza o gravador de vídeo e salva o arquivo.
    """
    global video_writer, gravando_video, video_filename

    # Verifica se a gravação está ativa e o objeto VideoWriter está inicializado.
    if gravando_video and video_writer is not None:
        # Libera o recurso do VideoWriter, finalizando o vídeo.
        video_writer.release()
        video_writer = None  # Reseta o objeto para None.
        gravando_video = False  # Define que a gravação não está mais ativa.
        # Mensagem confirmando o local onde o vídeo foi salvo.
        print(f"Vídeo salvo em: {video_filename}")

def desfazer_acao():
    """
    Desfaz a última ação do usuário, caso possível.
    """
    global imagem_com_efeitos, historico_acao  # Referencia as variáveis globais necessárias.

    # Verifica se há pelo menos uma ação no histórico além do estado inicial.
    if len(historico_acao) > 1:
        # Remove a última ação realizada do histórico.
        historico_acao.pop()
        # Define a imagem com efeitos como o estado anterior no histórico.
        imagem_com_efeitos = historico_acao[-1].copy()
        # Atualiza a interface para refletir as mudanças após desfazer a ação.
        atualizar_janela()

def gerar_miniaturas(imagem):
    """
    Gera miniaturas dos filtros disponíveis para exibição na barra de filtros.
    """
    global miniaturas  # Declara a variável global que armazena as miniaturas dos filtros.

    # Inicializa a lista de miniaturas como vazia.
    miniaturas = []

    # Itera sobre o número total de filtros disponíveis.
    for i in range(len(nomes_filtros)):
        # Aplica o filtro correspondente ao índice atual na imagem base.
        filtro_aplicado = aplicar_filtro_generico(imagem, i)
        # Define a largura de cada miniatura com base na largura da janela e no número de filtros.
        largura_miniatura = LARGURA_JANELA // len(nomes_filtros)
        # Redimensiona a imagem filtrada para criar uma miniatura de altura fixa (80 pixels).
        miniatura = cv2.resize(filtro_aplicado, (largura_miniatura, 80))
        # Adiciona a miniatura gerada à lista global de miniaturas.
        miniaturas.append(miniatura)

def atualizar_janela():
    """
    Atualiza a janela principal do editor, incluindo o frame atual e os elementos visuais.
    """
    global imagem_com_efeitos, usando_webcam  # Referencia as variáveis globais necessárias.

    # Verifica se há uma imagem com efeitos carregada. Caso contrário, não faz nada.
    if imagem_com_efeitos is None:
        return

    # Se estiver usando a webcam e a gravação de vídeo estiver ativa:
    if usando_webcam and video_writer is not None:
        # Salva o frame atual no arquivo de vídeo.
        salvar_frame_webcam(imagem_com_efeitos)

    # Redimensiona a imagem para caber no quadro de edição, mantendo as proporções.
    visualizacao = redimensionar_para_visualizacao(imagem_com_efeitos)
    # Define a largura total da janela.
    largura_total = LARGURA_JANELA
    # Define a altura total da janela.
    altura_total = ALTURA_JANELA

    # Cria uma janela em branco (preta) com as dimensões da área de edição.
    janela = np.zeros((altura_total, largura_total, 3), dtype=np.uint8)

    # Calcula o deslocamento horizontal necessário para centralizar o quadro na janela.
    x_offset_frame = (largura_total - visualizacao.shape[1]) // 2
    # Define o deslocamento vertical do quadro, abaixo da área reservada aos adesivos.
    y_offset_frame = ALTURA_ADESIVOS

    # Preenche a parte superior da janela com as miniaturas dos adesivos.
    janela[:ALTURA_ADESIVOS] = desenhar_area_adesivos(largura_total)
    # Insere o frame redimensionado na área central da janela, abaixo dos adesivos.
    janela[y_offset_frame:y_offset_frame + visualizacao.shape[0], x_offset_frame:x_offset_frame + visualizacao.shape[1]] = visualizacao
    # Preenche a área abaixo do frame com as miniaturas dos filtros.
    janela[y_offset_frame + visualizacao.shape[0]:y_offset_frame + visualizacao.shape[0] + ALTURA_BARRA] = desenhar_barra_de_filtros(largura_total)
    # Desenha os botões "Salvar" e "Desfazer" na parte inferior da janela.
    desenhar_botoes(janela, largura_total, y_offset_frame + visualizacao.shape[0] + ALTURA_BARRA)

    # Exibe a janela do editor atualizada com os elementos visuais montados.
    cv2.imshow("Editor", janela)

def desenhar_area_adesivos(largura):
    """
    Cria a área horizontal com as miniaturas dos adesivos disponíveis.
    """
    # Cria uma área preta (vazia) com altura fixa para exibir os adesivos.
    area = np.zeros((ALTURA_ADESIVOS, largura, 3), dtype=np.uint8)
    # Define o deslocamento horizontal inicial para posicionar os adesivos.
    x_offset = 10

    # Itera sobre os adesivos carregados, junto com seus índices e nomes.
    for i, (nome, adesivo) in enumerate(adesivos.items()):
        # Redimensiona o adesivo para um tamanho fixo de 80x80 pixels.
        adesivo_redimensionado = cv2.resize(adesivo[:, :, :3], (80, 80))
        # Insere o adesivo redimensionado na área horizontal, com deslocamento calculado.
        area[10:90, x_offset:x_offset + 80] = adesivo_redimensionado
        # Desenha um contorno verde ao redor do adesivo selecionado atualmente.
        if i == indice_adesivo_atual:
            cv2.rectangle(area, (x_offset, 10), (x_offset + 80, 90), (0, 255, 0), 2)
        # Incrementa o deslocamento horizontal para posicionar o próximo adesivo.
        x_offset += 90

    # Retorna a área preenchida com os adesivos e seus contornos.
    return area

def desenhar_barra_de_filtros(largura):
    """
    Cria a barra horizontal com as miniaturas dos filtros disponíveis.
    """
    global miniaturas  # Referencia a lista global de miniaturas.

    # Cria uma área preta (vazia) com altura fixa para exibir as miniaturas dos filtros.
    barra = np.zeros((ALTURA_BARRA, largura, 3), dtype=np.uint8)
    # Define a largura de cada miniatura com base na largura total da janela e no número de filtros.
    largura_miniatura = largura // len(nomes_filtros)
    # Define o deslocamento horizontal inicial para posicionar as miniaturas dos filtros.
    x_offset = 0

    # Itera sobre as miniaturas disponíveis e seus índices.
    for i, miniatura in enumerate(miniaturas):
        # Verifica se a miniatura está disponível (não é None).
        if miniatura is not None:
            # Redimensiona a miniatura para a largura calculada, mantendo a altura fixa (80 pixels).
            miniatura_redimensionada = cv2.resize(miniatura, (largura_miniatura, 80))
            # Insere a miniatura redimensionada na barra, com deslocamento calculado.
            barra[10:90, x_offset:x_offset + largura_miniatura] = miniatura_redimensionada
        # Desenha um contorno verde ao redor da miniatura correspondente ao filtro selecionado atualmente.
        if i == indice_filtro_atual:
            cv2.rectangle(barra, (x_offset, 10), (x_offset + largura_miniatura, 90), (0, 255, 0), 2)
        # Incrementa o deslocamento horizontal para posicionar a próxima miniatura.
        x_offset += largura_miniatura

    return barra  # Retorna a barra preenchida com miniaturas e contornos.
def desenhar_botoes(janela, largura, y_offset):
    """
    Desenha os botões "Salvar" e "Desfazer" na interface, abaixo da barra de filtros.
    """
    # Define a largura e altura dos botões, além do espaçamento horizontal entre eles.
    botao_largura = 200
    botao_altura = ALTURA_BOTOES
    espaco = 20

    # Calcula a posição horizontal do botão "Salvar", centralizando-o com margem à esquerda.
    x_salvar = (largura // 2) - botao_largura - espaco
    # Calcula a posição horizontal do botão "Desfazer", centralizando-o com margem à direita.
    x_desfazer = (largura // 2) + espaco

    # Desenha o botão "Salvar" como um retângulo preenchido na janela, usando uma cor cinza claro.
    cv2.rectangle(janela, (x_salvar, y_offset), (x_salvar + botao_largura, y_offset + botao_altura), (200, 200, 200), -1)
    # Adiciona o texto "Salvar" no centro do botão, com uma fonte simples e cor preta.
    cv2.putText(janela, "Salvar", (x_salvar + 50, y_offset + 35), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 0, 0), 2)

    # Desenha o botão "Desfazer" como um retângulo preenchido na janela, também em cinza claro.
    cv2.rectangle(janela, (x_desfazer, y_offset), (x_desfazer + botao_largura, y_offset + botao_altura), (200, 200, 200), -1)
    # Adiciona o texto "Desfazer" no centro do botão, com uma fonte simples e cor preta.
    cv2.putText(janela, "Desfazer", (x_desfazer + 35, y_offset + 35), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 0, 0), 2)
def callback_mouse(evento, x, y, flags, parametros):
    """
    Lida com cliques do mouse na interface, permitindo interação com adesivos, filtros e botões.
    """
    global imagem_com_efeitos, imagem_original, imagem_com_adesivos, historico_acao
    global indice_adesivo_atual, indice_filtro_atual, gravando_video  # Declara as variáveis globais necessárias.

    # Detecta cliques do botão esquerdo do mouse.
    if evento == cv2.EVENT_LBUTTONDOWN:
        # Calcula a altura da área de visualização, baseada na imagem redimensionada.
        visualizacao_altura = redimensionar_para_visualizacao(imagem_com_efeitos).shape[0]
        # Calcula a posição horizontal inicial do quadro redimensionado.
        x_offset_frame = (LARGURA_JANELA - LARGURA_FRAME) // 2
        # Calcula a posição vertical inicial do quadro redimensionado.
        y_offset_frame = ALTURA_ADESIVOS

        # Se o clique ocorrer na área dos adesivos:
        if 0 <= y <= ALTURA_ADESIVOS:
            # Calcula o índice do adesivo clicado com base na posição horizontal.
            indice = x // 90
            # Verifica se o índice está dentro da faixa de adesivos disponíveis.
            if indice < len(adesivos):
                # Atualiza o índice do adesivo atual.
                indice_adesivo_atual = indice
                # Se estiver usando a webcam e o vídeo não estiver sendo gravado, inicia a gravação.
                if usando_webcam and not gravando_video:
                    iniciar_video_writer(imagem_com_efeitos)
                # Atualiza a interface para refletir a seleção do adesivo.
                atualizar_janela()

        # Se o clique ocorrer na área do quadro de edição:
        elif y_offset_frame <= y <= y_offset_frame + visualizacao_altura:
            # Calcula a posição horizontal correspondente na imagem original.
            x_original = int((x - x_offset_frame) / escala_visualizacao)
            # Calcula a posição vertical correspondente na imagem original.
            y_original = int((y - y_offset_frame) / escala_visualizacao)
            # Obtém o adesivo selecionado com base no índice atual.
            adesivo = list(adesivos.values())[indice_adesivo_atual]

            # Se estiver usando a webcam:
            if usando_webcam:
                # Aplica o adesivo à camada de adesivos da webcam.
                aplicar_adesivo_webcam(imagem_com_efeitos, adesivo, x_original, y_original)
                # Se o vídeo ainda não estiver sendo gravado, inicia a gravação.
                if not gravando_video:
                    iniciar_video_writer(imagem_com_efeitos)
            else:
                # Adiciona o estado atual da imagem ao histórico antes de aplicar o adesivo.
                historico_acao.append(imagem_com_efeitos.copy())
                # Aplica o adesivo diretamente na imagem atual.
                aplicar_adesivo(imagem_com_efeitos, adesivo, x_original, y_original)

            # Atualiza a interface para refletir a aplicação do adesivo.
            atualizar_janela()

        # Se o clique ocorrer na área da barra de filtros:
        elif y_offset_frame + visualizacao_altura < y <= y_offset_frame + visualizacao_altura + ALTURA_BARRA:
            # Calcula o índice do filtro clicado com base na posição horizontal.
            indice_filtro = x // (LARGURA_JANELA // len(nomes_filtros))
            # Verifica se o índice está dentro da faixa de filtros disponíveis.
            if indice_filtro < len(nomes_filtros):
                # Atualiza o índice do filtro atual.
                indice_filtro_atual = indice_filtro

                # Se estiver usando a webcam:
                if usando_webcam:
                    # Aplica o filtro à imagem atual.
                    imagem_com_efeitos = aplicar_filtro_generico(imagem_com_efeitos, indice_filtro_atual)
                    # Se o vídeo ainda não estiver sendo gravado, inicia a gravação.
                    if not gravando_video:
                        iniciar_video_writer(imagem_com_efeitos)
                else:
                    # Aplica o filtro à imagem original e armazena o estado no histórico.
                    imagem_com_efeitos = aplicar_filtro_generico(imagem_original, indice_filtro_atual)
                    historico_acao.append(imagem_com_efeitos.copy())

                # Atualiza a interface para refletir a aplicação do filtro.
                atualizar_janela()

        # Se o clique ocorrer na área dos botões:
        elif y_offset_frame + visualizacao_altura + ALTURA_BARRA <= y <= y_offset_frame + visualizacao_altura + ALTURA_BARRA + ALTURA_BOTOES:
            # Calcula as posições horizontais dos botões "Salvar" e "Desfazer".
            largura_botoes = 200
            espaco_botoes = 20
            x_salvar = (LARGURA_JANELA // 2) - largura_botoes - espaco_botoes
            x_desfazer = (LARGURA_JANELA // 2) + espaco_botoes

            # Se o clique ocorrer no botão "Salvar":
            if x_salvar <= x <= x_salvar + largura_botoes:
                # Se estiver usando a webcam e o vídeo estiver sendo gravado, finaliza a gravação.
                if usando_webcam and gravando_video:
                    finalizar_video_writer()
                else:
                    # Salva a imagem atual.
                    salvar_imagem(imagem_com_efeitos)
            # Se o clique ocorrer no botão "Desfazer":
            elif x_desfazer <= x <= x_desfazer + largura_botoes:
                # Desfaz a última ação realizada.
                desfazer_acao()  # Chama a função para desfazer a última ação realizada pelo usuário.

def carregar_imagem_e_iniciar():
    """
    Permite ao usuário carregar uma imagem do sistema de arquivos e inicializa o editor para manipulação da imagem.
    """
    global imagem_original, imagem_com_efeitos, miniaturas, historico_acao  # Declara as variáveis globais necessárias.

    # Esconde a janela principal do Tkinter para não interferir na seleção de arquivos.
    Tk().withdraw()
    # Abre um diálogo para o usuário selecionar uma imagem para carregar.
    caminho_imagem = filedialog.askopenfilename(
        title="Selecione uma imagem",  # Define o título da janela de diálogo.
        filetypes=[  # Define os tipos de arquivo que podem ser carregados.
            ("Imagens", "*.png *.jpg *.jpeg *.bmp *.tiff *.gif")
        ]
    )
    # Se o usuário cancelar a seleção ou não selecionar um arquivo, a função retorna sem fazer nada.
    if not caminho_imagem:
        return

    # Carrega a imagem selecionada usando a biblioteca OpenCV.
    imagem_original = cv2.imread(caminho_imagem)
    # Verifica se a imagem foi carregada com sucesso.
    if imagem_original is None:
        print("Erro ao carregar a imagem.")  # Exibe uma mensagem de erro no console.
        return  # Sai da função sem prosseguir.

    # Cria uma cópia da imagem original para ser usada nas manipulações.
    imagem_com_efeitos = imagem_original.copy()
    # Inicializa o histórico de ações com a imagem original.
    historico_acao = [imagem_com_efeitos.copy()]
    # Gera miniaturas dos filtros disponíveis para exibição na interface.
    gerar_miniaturas(imagem_original)

    # Cria uma janela OpenCV chamada "Editor" para exibir a interface do editor.
    cv2.namedWindow("Editor")
    # Associa a função de callback do mouse à janela do editor para capturar interações do usuário.
    cv2.setMouseCallback("Editor", callback_mouse)
    # Atualiza a interface para exibir a imagem carregada e os elementos iniciais.
    atualizar_janela()

    # Loop principal para manter a interface do editor aberta.
    while True:
        # Aguarda por eventos de teclado.
        if cv2.waitKey(1) & 0xFF == 27:  # Verifica se a tecla "ESC" foi pressionada.
            cv2.destroyAllWindows()  # Fecha todas as janelas abertas pelo OpenCV.
            exit(0)  # Finaliza completamente o programa.

def inicializar_webcam():
    """
    Inicializa a webcam para captura de vídeo em tempo real, permitindo a aplicação de filtros e adesivos.
    """
    global usando_webcam, imagem_com_efeitos, imagem_com_adesivos, miniaturas  # Declara as variáveis globais necessárias.

    usando_webcam = True  # Define que o programa está no modo de uso da webcam.
    # Tenta abrir a webcam para captura de vídeo.
    captura = cv2.VideoCapture(0)
    # Verifica se a webcam foi aberta com sucesso.
    if not captura.isOpened():
        print("Erro ao acessar a webcam.")  # Exibe uma mensagem de erro no console.
        return  # Sai da função sem prosseguir.

    # Captura um frame inicial da webcam para configurar a interface.
    ret, frame = captura.read()
    # Verifica se o frame inicial foi capturado com sucesso.
    if not ret:
        print("Erro ao capturar o frame inicial.")  # Exibe uma mensagem de erro no console.
        return  # Sai da função sem prosseguir.

    # Inicializa uma camada vazia para armazenar adesivos aplicados na webcam.
    imagem_com_adesivos = np.zeros_like(frame)
    # Gera miniaturas dos filtros disponíveis com base no frame inicial capturado.
    gerar_miniaturas(frame)

    # Cria uma janela OpenCV chamada "Editor" para exibir a interface do editor.
    cv2.namedWindow("Editor")
    # Associa a função de callback do mouse à janela do editor para capturar interações do usuário.
    cv2.setMouseCallback("Editor", callback_mouse)

    # Loop principal para processar frames da webcam em tempo real.
    while True:
        # Captura um novo frame da webcam.
        ret, frame = captura.read()
        # Se a captura falhar, sai do loop.
        if not ret:
            break

        # Aplica o filtro selecionado ao frame capturado.
        frame_com_filtro = aplicar_filtro_generico(frame, indice_filtro_atual)
        # Combina o frame com filtro com a camada de adesivos.
        imagem_com_efeitos = cv2.add(frame_com_filtro, imagem_com_adesivos)

        # Salva o frame processado no arquivo de vídeo, se a gravação estiver ativa.
        salvar_frame_webcam(imagem_com_efeitos)
        # Atualiza a interface para exibir o frame processado.
        atualizar_janela()

        # Verifica se a tecla "ESC" foi pressionada para sair.
        if cv2.waitKey(1) & 0xFF == 27:  # 27 é o código ASCII para "ESC".
            captura.release()  # Libera a webcam.
            finalizar_video_writer()  # Finaliza o arquivo de vídeo, se estiver sendo gravado.
            cv2.destroyAllWindows()  # Fecha todas as janelas abertas pelo OpenCV.
            exit(0)  # Finaliza completamente o programa.

def escolher_modo():
    """
    Exibe uma interface gráfica inicial para o usuário escolher entre carregar uma imagem ou usar a webcam.
    """
    # Cria uma janela do Tkinter para a seleção do modo.
    root = Tk()
    root.title("Escolha o Modo")  # Define o título da janela.
    root.geometry("300x150")  # Define as dimensões da janela.
    root.resizable(False, False)  # Impede que a janela seja redimensionada.

    # Adiciona uma mensagem de instrução na janela.
    Label(root, text="Escolha o modo de edição:", font=("Arial", 12)).pack(pady=10)

    # Adiciona um botão para carregar uma imagem, que destrói a janela e chama a função correspondente.
    Button(root, text="Carregar Imagem", command=lambda: [root.destroy(), carregar_imagem_e_iniciar()],
           width=20, height=2).pack(pady=5)

    # Adiciona um botão para usar a webcam, que destrói a janela e chama a função correspondente.
    Button(root, text="Usar Webcam", command=lambda: [root.destroy(), inicializar_webcam()],
           width=20, height=2).pack(pady=5)

    # Exibe a janela e aguarda interação do usuário.
    root.mainloop()

def main():
    """
    Ponto de entrada do programa principal.
    Essa função é responsável por iniciar o programa e exibir a interface inicial ao usuário.
    """
    escolher_modo()  # Invoca a função que exibe a interface para o usuário escolher entre carregar uma imagem ou usar a webcam.

if __name__ == "__main__":
    """
    Garante que o código seja executado apenas quando o arquivo é chamado diretamente,
    e não importado como um módulo em outro script.
    """
    main()  # Chama a função principal para iniciar o programa.
