
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


// Variáveis globais para controle
const GLuint WIDTH = 800, HEIGHT = 600;
Sprite tankA, tankB, weaponA, weaponB; // Tanques e armas
vector<Sprite> bulletsA, bulletsB; // Munição de ambos os tanques
float tankSpeed = 300.0f;
float bulletSpeed = 500.0f;
float tankWidth = 0.2f, tankHeight = 0.2f;
bool explosion = false; // Controle de explosão

// Código fonte do Vertex Shader (em GLSL): ainda hardcoded
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

// Código fonte do Fragment Shader (em GLSL): ainda hardcoded
const GLchar *fragmentShaderSource = "#version 400\n"
                                     "in vec2 texCoord;\n"
                                     "uniform sampler2D texBuffer;\n"
                                     "uniform vec2 offsetTex;\n"
                                     "out vec4 color;\n"
                                     "void main()\n"
                                     "{\n"
                                     "color = texture(texBuffer, texCoord + offsetTex);\n"
                                     "}\n\0";

// Protótipo da função de callback de teclado
void key_callback(GLFWwindow *window, int key, int scancode, int action, int mode);

// Protótipos das funções
int setupShader();
int loadTexture(string filePath, int &imgWidth, int &imgHeight);
void drawSprite(Sprite spr, GLuint shaderID);
void updateTank(Sprite &tank, Sprite &weapon, GLFWwindow *window, float deltaTime, bool isPlayer);
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

    // Atributos de posição
    glVertexAttribPointer(0, 3, GL_FLOAT, GL_FALSE, 5 * sizeof(float), (void*)0);
    glEnableVertexAttribArray(0);

    // Atributos de coordenadas de textura
    glVertexAttribPointer(1, 2, GL_FLOAT, GL_FALSE, 5 * sizeof(float), (void*)(3 * sizeof(float)));
    glEnableVertexAttribArray(1);

    glBindBuffer(GL_ARRAY_BUFFER, 0);
    glBindVertexArray(0);
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

    // Configuração inicial dos tanques e armas
    tankA.setupSprite(0, vec3(-0.5f, -0.9f, 0.0f), vec3(tankWidth, tankHeight, 1.0f));
    tankA.initializeVAO(); // Inicializar o VAO do tanque A

    tankB.setupSprite(1, vec3(0.5f, 0.9f, 0.0f), vec3(tankWidth, tankHeight, 1.0f));
    tankB.initializeVAO(); // Inicializar o VAO do tanque B

    weaponA.setupSprite(2, vec3(-0.5f, -0.75f, 0.0f), vec3(tankWidth / 2.0f, tankHeight / 2.0f, 1.0f));
    weaponA.initializeVAO(); // Inicializar o VAO da arma A

    weaponB.setupSprite(3, vec3(0.5f, 0.75f, 0.0f), vec3(tankWidth / 2.0f, tankHeight / 2.0f, 1.0f));
    weaponB.initializeVAO(); // Inicializar o VAO da arma B

    // Carregar texturas dos tanques e armas
    int imgWidth, imgHeight;
    tankA.texID = loadTexture("../Texturas/battle-tank-game-assets/PNG/Hulls_Color_A/Hulls_Color_A.png", imgWidth, imgHeight);
    tankB.texID = loadTexture("../Texturas/battle-tank-game-assets/PNG/Hulls_Color_B/Hulls_Color_B.png", imgWidth, imgHeight);
    weaponA.texID = loadTexture("../Texturas/battle-tank-game-assets/PNG/Weapon_Color_A/Weapon_Color_A.png", imgWidth, imgHeight);
    weaponB.texID = loadTexture("../Texturas/battle-tank-game-assets/PNG/Weapon_Color_B/Weapon_Color_B.png", imgWidth, imgHeight);


    // Carregamento dos shaders
    GLuint shaderProgram = setupShader();

    float lastTime = glfwGetTime();
    while (!glfwWindowShouldClose(window))
    {
        float currentTime = glfwGetTime();
        float deltaTime = currentTime - lastTime;
        lastTime = currentTime;

        glClearColor(0.2f, 0.3f, 0.3f, 1.0f); // Definir cor de fundo para teste
        glClear(GL_COLOR_BUFFER_BIT);

        glClear(GL_COLOR_BUFFER_BIT);

        // Atualiza os tanques e armas
        updateTank(tankA, weaponA, window, deltaTime, true);   // Tanque controlado pelo jogador
        updateTank(tankB, weaponB, window, deltaTime, false);  // Tanque controlado pela máquina

        // Atualiza as balas
        updateBullets(bulletsA, deltaTime);
        updateBullets(bulletsB, deltaTime);

        // Verifica colisões e aplica explosão
        for (auto &bullet : bulletsA) {
            if (checkCollision(tankB, bullet)) {
                tankB.isAlive = false;
                triggerExplosion(tankB); // Ativar explosão
            }
        }
        for (auto &bullet : bulletsB) {
            if (checkCollision(tankA, bullet)) {
                tankA.isAlive = false;
                triggerExplosion(tankA); // Ativar explosão
            }
        }

        // Renderização dos sprites
        drawSprite(tankA, shaderProgram);
        drawSprite(weaponA, shaderProgram);
        drawSprite(tankB, shaderProgram);
        drawSprite(weaponB, shaderProgram);

        glfwSwapBuffers(window);
        glfwPollEvents();
    }

    glfwTerminate();
    return 0;
}

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
        GLenum format = (channels == 4) ? GL_RGBA : GL_RGB;
        glTexImage2D(GL_TEXTURE_2D, 0, format, imgWidth, imgHeight, 0, format, GL_UNSIGNED_BYTE, data);
        glGenerateMipmap(GL_TEXTURE_2D);
    }
    else
    {
        cout << "Erro ao carregar a textura: " << filePath << endl;
        return -1;
    }
    stbi_image_free(data);
    return textureID;
}

// Lógica para movimentação do tanque
void updateTank(Sprite &tank, Sprite &weapon, GLFWwindow *window, float deltaTime, bool isPlayer)
{
    if (tank.isAlive)
    {
        // Controles do tanque do jogador
        if (isPlayer) {
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
        else { // Tanque controlado pela IA
            tank.position.x += tankSpeed * deltaTime * ((rand() % 2 == 0) ? -1 : 1);
            shootBullet(tank, bulletsB);
        }
        
        // Atualizar a posição da arma com o tanque
        weapon.position = tank.position;
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

// Função para acionar a explosão ao colidir
void triggerExplosion(Sprite &tank)
{
    // Aqui será carregada a textura de explosão para o tanque atingido
    int imgWidth, imgHeight;
    tank.texID = loadTexture("../Texturas/battle-tank-game-assets/PNG/Effects/Explosion.png", imgWidth, imgHeight);
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