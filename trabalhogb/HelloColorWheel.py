import numpy as np
import matplotlib.pyplot as plt
import colorsys

# Configurações
resolution = 400  # Tamanho da imagem
num_rings = 100   # Número de anéis para suavizar a transição de V
num_segments = 360  # Número de segmentos para suavizar a transição de H

# Criar uma imagem RGB inicial
rgb_image = np.zeros((resolution, resolution, 3))

# Centro e raio do círculo
center = resolution // 2
radius = resolution // 2

# Preencher a imagem com base em H, S e V
for i in range(resolution):
    for j in range(resolution):
        # Calcular a distância e ângulo em relação ao centro
        dx = j - center
        dy = i - center
        distance = np.sqrt(dx**2 + dy**2)
        
        # Verificar se o ponto está dentro do círculo
        if distance <= radius:
            # Calcular H, S e V com base na posição
            h = (np.arctan2(dy, dx) + np.pi) / (2 * np.pi)  # Ângulo convertido para [0, 1]
            s = distance / radius  # Saturação de 0 (centro) a 1 (borda)
            v = 1.0  # Brilho máximo para visualizar a roda completa
            
            # Converter HSV para RGB
            r, g, b = colorsys.hsv_to_rgb(h, s, v)
            rgb_image[i, j] = [r, g, b]

# Exibir a roda de cores
plt.imshow(rgb_image)
plt.axis('off')  # Ocultar eixos
plt.title("Roda de Cores HSV")
plt.show()

plt.close(rgb_image)  # Fechar a figura adequadamente
