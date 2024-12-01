import numpy as np
import cv2 as cv
# Matpoltlib: se você nãi tiver: pip install matplotlib
import matplotlib.pyplot as plt


# Carregar a imagem
img = cv.imread('baboon.png')
imgResult = img.copy()
imgResult2 = img.copy()

# Exibir atributos da imagem
print("Atributos da imagem", img.shape, "\n")

for i in range(img.shape[0]): #percorre linhas
	for j in range(img.shape[1]): #percorre colunas
		media = (img.item(i,j,0) + img.item(i,j,1) + img.item(i,j,2))/3.0
		imgResult[i, j, 0] = media  # Canal B
		imgResult[i, j, 1] = media  # Canal G
		imgResult[i, j, 2] = media  # Canal R
		media = img.item(i,j,0) * 0.07 + img.item(i,j,1) * 0.71 + img.item(i,j,2) *0.21
		imgResult2[i, j, 0] = media  # Canal B
		imgResult2[i, j, 1] = media  # Canal G
		imgResult2[i, j, 2] = media  # Canal R

# Converter imagens para RGB para exibir corretamente com matplotlib
img_rgb = cv.cvtColor(img, cv.COLOR_BGR2RGB)
imgResult_rgb = cv.cvtColor(imgResult, cv.COLOR_BGR2RGB)
imgResult2_rgb = cv.cvtColor(imgResult2, cv.COLOR_BGR2RGB)

# Exibir as três imagens lado a lado com matplotlib
plt.figure(figsize=(15, 5))

plt.subplot(1, 3, 1)
plt.imshow(img_rgb)
plt.title("Imagem Original")
plt.axis("off")

plt.subplot(1, 3, 2)
plt.imshow(imgResult_rgb)
plt.title("Grayscale (Média)")
plt.axis("off")

plt.subplot(1, 3, 3)
plt.imshow(imgResult2_rgb)
plt.title("Grayscale (Ponderado)")
plt.axis("off")

plt.show()
plt.close(img_rgb)
plt.close(imgResult_rgb)
plt.close(imgResult2_rgb)
