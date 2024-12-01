import cv2
import numpy as np
import matplotlib.pyplot as plt

# Carregar uma imagem em escala de cinza
image = cv2.imread('baboon.png', cv2.IMREAD_GRAYSCALE)

# Kernel Sobel para bordas horizontais (não rotacionado)
sobel_horizontal = np.array([[1, 2, 1],
                             [0, 0, 0],
                             [-1, -2, -1]])

# Aplicar o filtro usando o kernel original
sobel_filtered = cv2.filter2D(image, -1, sobel_horizontal)

# Kernel Sobel rotacionado 180° para bordas horizontais
sobel_horizontal_rotated = np.array([[-1, -2, -1],
                                     [0, 0, 0],
                                     [1, 2, 1]])

# Aplicar o filtro usando o kernel rotacionado
sobel_filtered_rotated = cv2.filter2D(image, -1, sobel_horizontal_rotated)

# Exibir os resultados
plt.figure(figsize=(10, 5))

plt.subplot(1, 3, 1)
plt.title('Imagem Original')
plt.imshow(image, cmap='gray')

plt.subplot(1, 3, 2)
plt.title('Filtro Sobel Original')
plt.imshow(sobel_filtered, cmap='gray')

plt.subplot(1, 3, 3)
plt.title('Filtro Sobel Rotacionado')
plt.imshow(sobel_filtered_rotated, cmap='gray')

plt.show()
