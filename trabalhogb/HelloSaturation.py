import cv2 as cv
import numpy as np

# Carregar a imagem
img = cv.imread('baboon.png')
img_hsv = cv.cvtColor(img, cv.COLOR_BGR2HSV)

# Função callback para o trackbar
def update_saturation(scale):
    # Converte a escala do trackbar (0-200) para um fator de saturação (0.0 - 2.0)
    saturation_scale = scale / 100.0
    
    # Copiar a imagem HSV original para manter o valor original do canal de saturação
    img_hsv_adjusted = img_hsv.copy()
    H, S, V = cv.split(img_hsv_adjusted)
    
    # Ajustar saturação
    S = np.clip(S * saturation_scale, 0, 255).astype(np.uint8)
    img_hsv_adjusted = cv.merge([H, S, V])
    
    # Converter de volta para BGR e exibir
    img_adjusted = cv.cvtColor(img_hsv_adjusted, cv.COLOR_HSV2BGR)
    cv.imshow('Ajuste de Saturação', img_adjusted)

# Criar uma janela e o trackbar para ajustar a saturação
cv.namedWindow('Ajuste de Saturação')
cv.createTrackbar('Saturação', 'Ajuste de Saturação', 100, 200, update_saturation)

# Inicializar a visualização com saturação padrão (100%)
update_saturation(100)

# Manter a janela aberta até o usuário pressionar a tecla ESC
while True:
    if cv.waitKey(1) & 0xFF == 27:  # ESC key to exit
        break

cv.destroyAllWindows()
