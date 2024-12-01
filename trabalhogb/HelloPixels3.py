import numpy as np
import cv2 as cv

img = cv.imread('baboon.png') #original
print("Atributos da imagem",img.shape,"\n")

imgGray = cv.cvtColor(img, cv.COLOR_RGB2GRAY)
imgResult = imgGray.copy()

k = 150

for i in range(imgGray.shape[0]): #percorre linhas
	for j in range(imgGray.shape[1]): #percorre colunas
		if imgGray[i,j] >= k:
			imgResult[i,j] = 255
		else:
			imgResult[i,j] = 0

cv.imshow("Imagem Original", img)
cv.imshow("Grayscale (cvtColor)",imgGray)
cv.imshow("Binarizada",imgResult)

k = cv.waitKey(0)