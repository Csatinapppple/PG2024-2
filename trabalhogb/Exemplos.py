import numpy as np
import cv2 as cv

img = cv.imread('baboon.png') #original

kernel = np.ones((3, 3), np.float32) / 2
print(kernel)

correlated_image = cv.filter2D(img, -1, kernel)

sobel_horizontal = cv.Sobel(img, cv.CV_64F, 1, 0, ksize=3)
laplacian_image = cv.Laplacian(img, cv.CV_64F)

smoothed_image = cv.blur(img, (5, 5))
blurred_image = cv.GaussianBlur(img, (5, 5), 1.5)

laplacian_image = cv.Laplacian(img, cv.CV_64F)

kernel = np.array([[0, -1, 0],
                   [-1, 5, -1],
                   [0, -1, 0]])
sharpened_image = cv.filter2D(img, -1, kernel)

median_filtered_image = cv.medianBlur(img, 5)

# Carregar a imagem em escala de cinza
img = cv.imread('baboon.png', cv.IMREAD_GRAYSCALE)

# Definir o kernel (vizinhança)
kernel = np.ones((3, 3), np.uint8)

# Aplicar o filtro de Máximo (Dilatação)
filtro_maximo = cv.dilate(img, kernel)

# Aplicar o filtro de Mínimo (Erosão)
filtro_minimo = cv.erode(img, kernel)

print(kernel)

cv.imshow("Filtro correlação",correlated_image)
#cv.imshow("Filtro de Máximo", filtro_maximo)
#cv.imshow("Filtro de Mínimo", filtro_minimo)




k = cv.waitKey(0)