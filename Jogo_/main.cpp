#include <iostream>
#include <string>
#include <vector>
#include <cstdlib>
#include <ctime>

// GLAD
#include <glad/glad.h>

// GLFW
#include <GLFW/glfw3.h>

// GLM
#include <glm/glm.hpp>
#include <glm/gtc/matrix_transform.hpp>
#include <glm/gtc/type_ptr.hpp>

// STB_IMAGE
#include <stb_image.h>

using namespace glm;
using namespace std;

// Estrutura para representar os sprites
struct Sprite
{
    GLuint VAO, VBO;
    GLuint texID;
    vec3 position;
    vec3 dimensions;
    float angle;
    vec2 direction;
    bool isShooting;
    bool isAlive;

    void setupSprite(int texID, vec3 position, vec3 dimensions);
    void initializeVAO(); // Função para inicializar o VAO e VBO
};

// Variáveis globais
const GLuint WIDTH = 800, HEIGHT = 600;
const float BOUNDARY_LIMIT = 0.85f; // Definir o limite da janela para os tanques não sumirem

Sprite tankA, tankB; // Tanques
vector<Sprite> bulletsA, bulletsB; // Munição dos tanques
float tankSpeed = 50.0f;  // Diminuir ainda mais a velocidade dos tanques
float bulletSpeed = 100.0f;  // Diminuir a velocidade da munição
float tankWidth = 0.2f, tankHeight = 0.2f;
bool explosion = false; // Controle de explosão

// Código fonte do Vertex Shader (em GLSL): hardcoded
const GLchar *vertexShaderSource = "#version 400\n"
                                   "layout (location = 0) in vec3 position;\n"
                                   "layout (location = 1) in vec2 texc;\n"
                                   "uniform mat4 projection;\n"
                                   "uniform mat4 model;\n"
                                   "out vec2 texCoord;\n"
                                   "void main()\n"
                                   "{\n"
                                   "gl_Position = projection * model * vec4(position.x, position.y, position.z, 1.0);\n"
                                   "texCoord = vec2(texc.s, 1.0 - texc.t);\n"
                                   "}\0";

// Código fonte do Fragment Shader (em GLSL): hardcoded
const GLchar *fragmentShaderSource = "#version 400\n"
                                     "in vec2 texCoord;\n"
                                     "uniform sampler2D texBuffer;\n"
                                     "uniform vec2 offsetTex;\n"
                                     "out vec4 color;\n"
                                     "void main()\n"
                                     "{\n"
                                     "color = texture(texBuffer, texCoord + offsetTex);\n"
                                     "}\n\0";

// Protótipos das funções
void key_callback(GLFWwindow *window, int key, int scancode, int action, int mode);
int setupShader();
int loadTexture(string filePath, int &imgWidth, int &imgHeight);
void drawSprite(Sprite spr, GLuint shaderID);
void updateTank(Sprite &tank, GLFWwindow *window, float deltaTime, bool isPlayer);
void shootBullet(Sprite &tank, vector<Sprite> &bullets);
void updateBullets(vector<Sprite> &bullets, float deltaTime);
bool checkCollision(Sprite &tank, Sprite &bullet);
void triggerExplosion(Sprite &tank);

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

void Sprite::initializeVAO()
{
    float vertices[] = {
        // Posições         // Coordenadas de textura
        0.5f,  0.5f, 0.0f,  1.0f, 1.0f,
        0.5f, -0.5f, 0.0f,  1.0f, 0.0f,
       -0.5f, -0.5f, 0.0f,  0.0f, 0.0f,

        0.5f,  0.5f, 0.0f,  1.0f, 1.0f,
       -0.5f, -0.5f, 0.0f,  0.0f, 0.0f,
       -0.5f,  0.5f, 0.0f,  0.0f, 1.0f
    };

    glGenVertexArrays(1, &VAO);
    glGenBuffers(1, &VBO);

    glBindVertexArray(VAO);
    glBindBuffer(GL_ARRAY_BUFFER, VBO);
    glBufferData(GL_ARRAY_BUFFER, sizeof(vertices), vertices, GL_STATIC_DRAW);

    glVertexAttribPointer(0, 3, GL_FLOAT, GL_FALSE, 5 * sizeof(float), (void*)0);
    glEnableVertexAttribArray(0);

    glVertexAttribPointer(1, 2, GL_FLOAT, GL_FALSE, 5 * sizeof(float), (void*)(3 * sizeof(float)));
    glEnableVertexAttribArray(1);

    glBindBuffer(GL_ARRAY_BUFFER, 0);
    glBindVertexArray(0);
}

// Função principal
int main()
{
    srand(time(0)); // Semente para geração de números aleatórios

    glfwInit();
    GLFWwindow *window = glfwCreateWindow(WIDTH, HEIGHT, "Jogo de Tanques", NULL, NULL);
    glfwMakeContextCurrent(window);
    glfwSetKeyCallback(window, key_callback);
    gladLoadGLLoader((GLADloadproc)glfwGetProcAddress);

    // Ativar a transparência
    glEnable(GL_BLEND);
    glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA);

    // Configuração inicial dos tanques
    tankA.setupSprite(0, vec3(-0.5f, 0.9f, 0.0f), vec3(tankWidth, tankHeight, 1.0f));
    tankA.initializeVAO();

    tankB.setupSprite(1, vec3(0.5f, -0.9f, 0.0f), vec3(tankWidth, tankHeight, 1.0f));
    tankB.initializeVAO();

    // Carregamento das texturas dos tanques
    int imgWidth, imgHeight;
    tankA.texID = loadTexture("../Texturas/tank_simples/tank_a/tank_a.png", imgWidth, imgHeight);
    tankB.texID = loadTexture("../Texturas/tank_simples/tank_b/tank_b.png", imgWidth, imgHeight);

    // Carregar shaders
    GLuint shaderProgram = setupShader();

    float lastTime = glfwGetTime();
    while (!glfwWindowShouldClose(window))
    {
        float currentTime = glfwGetTime();
        float deltaTime = currentTime - lastTime;
        lastTime = currentTime;

        glClear(GL_COLOR_BUFFER_BIT);

        // Atualiza os tanques e munições
        updateTank(tankA, window, deltaTime, false);  // Tanque A controlado pela IA
        updateTank(tankB, window, deltaTime, true);   // Tanque B controlado pelo jogador

        updateBullets(bulletsA, deltaTime);
        updateBullets(bulletsB, deltaTime);

        // Verifica colisões
        for (auto &bullet : bulletsA) {
            if (checkCollision(tankB, bullet)) {
                tankB.isAlive = false;
                triggerExplosion(tankB);
            }
        }
        for (auto &bullet : bulletsB) {
            if (checkCollision(tankA, bullet)) {
                tankA.isAlive = false;
                triggerExplosion(tankA);
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

// Função para carregar texturas usando stb_image
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

// Função para configurar shaders
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

    // Certificar que o slot de textura correto está ativado
    glActiveTexture(GL_TEXTURE0);
    glBindTexture(GL_TEXTURE_2D, spr.texID); 

    // Matriz de projeção ortográfica
    mat4 projection = ortho(-1.0f, 1.0f, -1.0f, 1.0f, -1.0f, 1.0f);
    GLuint projectionLoc = glGetUniformLocation(shaderID, "projection");
    glUniformMatrix4fv(projectionLoc, 1, GL_FALSE, value_ptr(projection));

    // Matriz de transformação do modelo
    mat4 model = mat4(1.0f);
    model = translate(model, spr.position);
    model = rotate(model, radians(spr.angle), vec3(0.0f, 0.0f, 1.0f));
    model = scale(model, spr.dimensions);
    
    GLuint modelLoc = glGetUniformLocation(shaderID, "model");
    glUniformMatrix4fv(modelLoc, 1, GL_FALSE, value_ptr(model));

    glBindVertexArray(spr.VAO);
    glDrawArrays(GL_TRIANGLES, 0, 6); // Renderizar o sprite
    glBindVertexArray(0);
}

// Função para disparar uma bala
void shootBullet(Sprite &tank, vector<Sprite> &bullets)
{
    Sprite bullet;
    bullet.setupSprite(tank.texID, vec3(tank.position.x, tank.position.y, 0.0f), vec3(0.05f, 0.1f, 1.0f)); // Tamanho da bala
    bullets.push_back(bullet);
}

// Atualiza as balas
void updateBullets(vector<Sprite> &bullets, float deltaTime)
{
    for (auto &bullet : bullets)
    {
        bullet.position.y += bulletSpeed * deltaTime; // Movimentar as balas
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

// Função para acionar a explosão ao colidir
void triggerExplosion(Sprite &tank)
{
    // Aqui será carregada a textura de explosão para o tanque atingido
    int imgWidth, imgHeight;
    tank.texID = loadTexture("../Texturas/tank_simples/efeitos/Explosion.png", imgWidth, imgHeight);
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

// Lógica para movimentação do tanque
void updateTank(Sprite &tank, GLFWwindow *window, float deltaTime, bool isPlayer)
{
    if (tank.isAlive)
    {
        // Controles do tanque do jogador
        if (isPlayer) {
            if (glfwGetKey(window, GLFW_KEY_A) == GLFW_PRESS && tank.position.x > -BOUNDARY_LIMIT)
                tank.position.x -= tankSpeed * deltaTime;
            if (glfwGetKey(window, GLFW_KEY_D) == GLFW_PRESS && tank.position.x < BOUNDARY_LIMIT)
                tank.position.x += tankSpeed * deltaTime;
            if (glfwGetKey(window, GLFW_KEY_W) == GLFW_PRESS && tank.position.y < 0.7f) // Limite superior do movimento
                tank.position.y += tankSpeed * deltaTime;
            if (glfwGetKey(window, GLFW_KEY_S) == GLFW_PRESS && tank.position.y > -0.9f) // Limite inferior do movimento
                tank.position.y -= tankSpeed * deltaTime;
            if (glfwGetKey(window, GLFW_KEY_SPACE) == GLFW_PRESS)
                shootBullet(tank, bulletsB); // Atirar do tanque do jogador
        }
        else {
            // Movimento do tanque da IA
            tank.position.x += tankSpeed * deltaTime * ((rand() % 2 == 0) ? -1 : 1); // Movimento lateral aleatório

            if (tank.position.x > BOUNDARY_LIMIT) tank.position.x = BOUNDARY_LIMIT; // Limite direito
            if (tank.position.x < -BOUNDARY_LIMIT) tank.position.x = -BOUNDARY_LIMIT; // Limite esquerdo

            if (rand() % 100 < 5) { // Chance de disparar aleatoriamente
                shootBullet(tank, bulletsA); // Disparar a munição da IA
            }
        }
    }
}