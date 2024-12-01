import numpy as np
import cv2 as cv

img = cv.imread('baboon.png') #original
print("Atributos da imagem",img.shape,"\n")

imgResult = img.copy()
imgColored = img.copy()
imgInverted = img.copy()

mColor = [255, 0, 255] #cor colorizadora

B, G, R = cv.split(img) #separando os canais usando o split

imgGray = cv.cvtColor(img, cv.COLOR_RGB2GRAY)
print("Atributos da imagem",imgGray.shape,"\n")

for i in range(img.shape[0]): #percorre linhas
	for j in range(img.shape[1]): #percorre colunas
		# Passando o valor do canal azul para os outros canais
		imgResult[i,j,0] = img[i,j,0] # canal B!!!!!!!!!!!!!!!!
		imgResult[i,j,1] = img[i,j,0] # canal G
		imgResult[i,j,2] = img[i,j,0] # canal R!!!!
		# Colorização
		imgColored[i,j,0] = img[i,j,0] | mColor[0] # canal B!!!!!!!!!!!!!!!!
		imgColored[i,j,1] = img[i,j,1] | mColor[1] # canal G
		imgColored[i,j,2] = img[i,j,2] | mColor[2] # canal R!!!!
		# Inversão
		imgInverted[i,j,0] = img[i,j,0] ^ 255 # canal B!!!!!!!!!!!!!!!!
		imgInverted[i,j,1] = img[i,j,1] ^ 255 # canal G
		imgInverted[i,j,2] = img[i,j,2] ^ 255 # canal R!!!!
		
cv.imshow("Imagem Original", img)
cv.imshow("Canal Azul (Splitted)",B)
cv.imshow("Canal Azul",imgResult)
cv.imshow("Colorizada",imgColored)
cv.imshow("Inversão",imgInverted)

k = cv.waitKey(0)