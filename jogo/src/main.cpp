// GLAD
#include "../include/glad.h"

// GLFW
#include <GLFW/glfw3.h>

GLfloat vertices[] = {
	-0.5, 0.5, 0,
	0.5, -0.5, 0,
	0.5, 0.5, 0
}

GLuint vertexShader;
const GLchar *vertexShaderSource = readFile("./shaders/vertexShader.cpp");

int main() {
	GLuint VBO;
	glGenBuffers(1, &VBO);

	glBindBuffer(GL_ARRAY_BUFFER, VBO);

	glBufferData(GL_ARRAY_BUFFER, sizeof(vertices), vertices, GL_STATIC_DRAW);


}
