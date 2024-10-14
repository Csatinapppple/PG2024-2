
/* Jogo de Tanques 2D utilizando OpenGL e GLSL
 * Adaptado por Rossana Baptista Queiroz
 * para a disciplina de Processamento Gráfico - Unisinos
 */

#include <iostream>
#include <string>
#include <vector>
#include <cstdlib>
#include <ctime>
// GLAD
#include "../include/glad.h"

// GLFW
#include <GLFW/glfw3.h>

#include "../include/tools.hpp"
// GLM
#include <glm/glm.hpp>
#include <glm/gtc/matrix_transform.hpp>
#include <glm/gtc/type_ptr.hpp>

// STB_IMAGE
#define STB_IMAGE_IMPLEMENTATION
#include "../include/stb_image.h"

using namespace glm;
using namespace std;

// Estrutura para representar os sprites
struct Sprite
{
    GLuint VAO;
    GLuint texID;
    vec3 position;
    vec3 dimensions;
    float angle;
    vec2 direction;
    bool isShooting;
    bool isAlive;

    void setupSprite(int texID, vec3 position, vec3 dimensions);
};

// Variáveis globais para controle
const GLuint WIDTH = 800, HEIGHT = 600;
Sprite tankA, tankB; // Tanques
vector<Sprite> bulletsA, bulletsB; // Munição de ambos os tanques
float tankSpeed = 300.0f;
float bulletSpeed = 500.0f;
float tankWidth = 0.2f, tankHeight = 0.2f;

// Código fonte do Vertex Shader (em GLSL): ainda hardcoded
std::string vertShaderSource = getFileContent("./src/shaders/vertexShader.glsl");
const GLchar* vertexShaderSource = vertShaderSource.c_str();
// Código fonte do Fragment Shader (em GLSL): ainda hardcoded
std::string fragShaderSource = getFileContent("./src/shaders/fragmentShader.glsl");
const GLchar* fragmentShaderSource = fragShaderSource.c_str();

// Protótipo da função de callback de teclado
void key_callback(GLFWwindow *window, int key, int scancode, int action, int mode);

// Protótipos das funções
int setupShader();
int loadTexture(string filePath, int &imgWidth, int &imgHeight);
void drawSprite(Sprite spr, GLuint shaderID);
void updateTank(Sprite &tank, GLFWwindow *window, float deltaTime);
void shootBullet(Sprite &tank, vector<Sprite> &bullets);
void updateBullets(vector<Sprite> &bullets, float deltaTime);
bool checkCollision(Sprite &tank, Sprite &bullet);
void key_callback(GLFWwindow* window, int key, int scancode, int action, int mods);

// Inicializa o tanque
void Sprite::setupSprite(int texID, vec3 pos, vec3 dim) {
    this->texID = texID;
    this->position = pos;
    this->dimensions = dim;
    this->angle = 0.0f;
    this->isShooting = false;
    this->isAlive = true;
    this->direction = vec2(1.0f, 0.0f); // Inicializa a direção padrão
}

// Função principal
int main()
{
    srand(time(0)); // Semente para a geração aleatória de números
    // Inicialização do GLFW e criação da janela
    glfwInit();
    GLFWwindow *window = glfwCreateWindow(WIDTH, HEIGHT, "Jogo de Tanques", NULL, NULL);
    glfwMakeContextCurrent(window);
    glfwSetKeyCallback(window, key_callback);
    gladLoadGLLoader((GLADloadproc)glfwGetProcAddress);

    // Configuração inicial dos tanques
	tankA.setupSprite(0, vec3(-0.5f, -0.9f, 0.0f), vec3(tankWidth, tankHeight, 1.0f));
	tankB.setupSprite(1, vec3(0.5f, 0.9f, 0.0f), vec3(tankWidth, tankHeight, 1.0f));

	// Carregamento das texturas dos tanqu
	int imgWidth, imgHeight;
	tankA.texID = loadTexture("../Texturas/tank/PNG/Hulls_Color_A/Hulls_Color_A.png", imgWidth, imgHeight);
	tankB.texID = loadTexture("../Texturas/tank/PNG/Hulls_Color_B/Hulls_Color_B.png", imgWidth, imgHeight);


    // Carregamento dos shaders
    GLuint shaderProgram = setupShader();

    float lastTime = glfwGetTime();
    while (!glfwWindowShouldClose(window))
    {
        float currentTime = glfwGetTime();
        float deltaTime = currentTime - lastTime;
        lastTime = currentTime;

        glClear(GL_COLOR_BUFFER_BIT);

		glClearColor(0.2f, 0.3f, 0.3f, 1.0f); // Definir cor de fundo
		glClear(GL_COLOR_BUFFER_BIT);          // Limpar a tela com a cor definida

        // Atualiza os tanques
        updateTank(tankA, window, deltaTime);
        updateTank(tankB, window, deltaTime);

        // Atualiza as balas
        updateBullets(bulletsA, deltaTime);
        updateBullets(bulletsB, deltaTime);

        // Verifica colisões
        for (auto &bullet : bulletsA) {
            if (checkCollision(tankB, bullet)) {
                tankB.isAlive = false;
            }
        }
        for (auto &bullet : bulletsB) {
            if (checkCollision(tankA, bullet)) {
                tankA.isAlive = false;
            }
        }

        // Renderização dos sprites
        drawSprite(tankA, shaderProgram);
        drawSprite(tankB, shaderProgram);

        glfwSwapBuffers(window);
        glfwPollEvents();
    }

    glfwTerminate();
    return 0;
}

// Função de callback de teclado
void key_callback(GLFWwindow* window, int key, int scancode, int action, int mods)
{
    if (action == GLFW_PRESS || action == GLFW_REPEAT)
    {
        if (key == GLFW_KEY_ESCAPE) // Fecha a janela se a tecla ESC for pressionada
            glfwSetWindowShouldClose(window, true);
    }
}

int loadTexture(string filePath, int &imgWidth, int &imgHeight)
{
    GLuint textureID;
    glGenTextures(1, &textureID);
    glBindTexture(GL_TEXTURE_2D, textureID);

    // Configurar parâmetros de textura
    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_S, GL_REPEAT);
    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_T, GL_REPEAT);
    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_LINEAR);
    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_LINEAR);

    // Carregar a imagem usando stb_image
    int channels;
    unsigned char *data = stbi_load(filePath.c_str(), &imgWidth, &imgHeight, &channels, 0);
    if (data)
    {
        GLenum format = (channels == 4) ? GL_RGBA : GL_RGB; // Determinar o formato da imagem
        glTexImage2D(GL_TEXTURE_2D, 0, format, imgWidth, imgHeight, 0, format, GL_UNSIGNED_BYTE, data);
        glGenerateMipmap(GL_TEXTURE_2D);
    }
    else
    {
        cout << "Erro ao carregar a textura: " << filePath << endl;
        return -1; // Retornar erro se a textura não for carregada
    }

    stbi_image_free(data);
    return textureID; // Retornar o ID da textura carregada
}


// Lógica para movimentação do tanque
void updateTank(Sprite &tank, GLFWwindow *window, float deltaTime)
{
    if (tank.isAlive)
    {
        // Controles do tanque do jogador
        if (tank.texID == 0) { // Tanque A (jogador)
            if (glfwGetKey(window, GLFW_KEY_A) == GLFW_PRESS)
                tank.position.x -= tankSpeed * deltaTime;
            if (glfwGetKey(window, GLFW_KEY_D) == GLFW_PRESS)
                tank.position.x += tankSpeed * deltaTime;
            if (glfwGetKey(window, GLFW_KEY_W) == GLFW_PRESS)
                tank.position.y += tankSpeed * deltaTime;
            if (glfwGetKey(window, GLFW_KEY_S) == GLFW_PRESS)
                tank.position.y -= tankSpeed * deltaTime;
            if (glfwGetKey(window, GLFW_KEY_SPACE) == GLFW_PRESS)
                shootBullet(tank, bulletsA);
        } 
        else { // Tanque B (máquina)
            // Movimento automático
            tank.position.x += tankSpeed * deltaTime * ((rand() % 2 == 0) ? -1 : 1);
            shootBullet(tank, bulletsB);
        }
    }
}

// Função para disparar uma bala
void shootBullet(Sprite &tank, vector<Sprite> &bullets)
{
    if (!tank.isShooting)
    {
        Sprite bullet;
        bullet.setupSprite(2, tank.position, vec3(0.05f, 0.05f, 1.0f));
        bullets.push_back(bullet);
        tank.isShooting = true;
    }
}

// Atualiza as balas
void updateBullets(vector<Sprite> &bullets, float deltaTime)
{
    for (auto &bullet : bullets)
    {
        bullet.position.y += bulletSpeed * deltaTime;
    }
}

// Verifica se houve colisão entre o tanque e uma bala
bool checkCollision(Sprite &tank, Sprite &bullet)
{
    return (tank.position.x < bullet.position.x + bullet.dimensions.x &&
            tank.position.x + tank.dimensions.x > bullet.position.x &&
            tank.position.y < bullet.position.y + bullet.dimensions.y &&
            tank.position.y + tank.dimensions.y > bullet.position.y);
}

// Configuração dos shaders
int setupShader()
{
    // Compilação do Vertex Shader
    GLuint vertexShader = glCreateShader(GL_VERTEX_SHADER);
    glShaderSource(vertexShader, 1, &vertexShaderSource, NULL);
    glCompileShader(vertexShader);
    
    // Verificar erros de compilação
    int success;
    glGetShaderiv(vertexShader, GL_COMPILE_STATUS, &success);
    if (!success)
    {
        char infoLog[512];
        glGetShaderInfoLog(vertexShader, 512, NULL, infoLog);
        cout << "Erro na compilação do Vertex Shader: " << infoLog << endl;
    }

    // Compilação do Fragment Shader
    GLuint fragmentShader = glCreateShader(GL_FRAGMENT_SHADER);
    glShaderSource(fragmentShader, 1, &fragmentShaderSource, NULL);
    glCompileShader(fragmentShader);
    
    // Verificar erros de compilação
    glGetShaderiv(fragmentShader, GL_COMPILE_STATUS, &success);
    if (!success)
    {
        char infoLog[512];
        glGetShaderInfoLog(fragmentShader, 512, NULL, infoLog);
        cout << "Erro na compilação do Fragment Shader: " << infoLog << endl;
    }

    // Linkar os shaders
    GLuint shaderProgram = glCreateProgram();
    glAttachShader(shaderProgram, vertexShader);
    glAttachShader(shaderProgram, fragmentShader);
    glLinkProgram(shaderProgram);

    // Verificar erros de linkagem
    glGetProgramiv(shaderProgram, GL_LINK_STATUS, &success);
    if (!success)
    {
        char infoLog[512];
        glGetProgramInfoLog(shaderProgram, 512, NULL, infoLog);
        cout << "Erro na linkagem dos shaders: " << infoLog << endl;
    }

    // Deletar shaders (eles já estão linkados no programa)
    glDeleteShader(vertexShader);
    glDeleteShader(fragmentShader);

    return shaderProgram;
}

// Função para desenhar um sprite
void drawSprite(Sprite spr, GLuint shaderID)
{
	glUseProgram(shaderID);

	// Definir a matriz de projeção ortográfica no início do programa
	mat4 projection = ortho(-1.0f, 1.0f, -1.0f, 1.0f, -1.0f, 1.0f);
	GLuint projectionLoc = glGetUniformLocation(shaderID, "projection");
	glUniformMatrix4fv(projectionLoc, 1, GL_FALSE, value_ptr(projection));

    mat4 model = mat4(1.0f);
    model = translate(model, spr.position);
    model = rotate(model, radians(spr.angle), vec3(0.0f, 0.0f, 1.0f));
    model = scale(model, spr.dimensions);
    
    GLuint modelLoc = glGetUniformLocation(shaderID, "model");
    glUniformMatrix4fv(modelLoc, 1, GL_FALSE, value_ptr(model));

    glBindTexture(GL_TEXTURE_2D, spr.texID); // Vincular a textura do sprite
    glBindVertexArray(spr.VAO);
    glDrawArrays(GL_TRIANGLES, 0, 6); // Renderizar o sprite
    glBindVertexArray(0);
}
