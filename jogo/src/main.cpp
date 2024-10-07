// GLAD
#include "../include/glad.h"

// GLFW
#include <GLFW/glfw3.h>

#include "../include/file_tools.hpp"

GLfloat vertices[] = {
	-0.5, 0.5, 0,
	0.5, -0.5, 0,
	0.5, 0.5, 0
};

GLuint vertexShader;
std::string vertexShaderSource = readFile("./src/shaders/vertexShader.glsl");

int main() {

	GLuint VBO;
	glGenBuffers(1, &VBO);
	std::cout << vertexShaderSource;
	glBindBuffer(GL_ARRAY_BUFFER, VBO);

	glBufferData(GL_ARRAY_BUFFER, sizeof(vertices), vertices, GL_STATIC_DRAW);


}
