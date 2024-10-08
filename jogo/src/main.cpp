// GLAD
#include "../include/glad.h"

// GLFW
#include <GLFW/glfw3.h>

#include "../include/shader.hpp"
#include "../include/tools.hpp"

GLfloat vertices[] = {
	-0.5, 0.5, 0,
	0.5, -0.5, 0,
	0.5, 0.5, 0
};

GLFWwindow* window;
GLuint vertexShader,fragmentShader;
std::string vertexShaderSrc=getFileContent("./src/shaders/vertexShader.glsl"),
						fragmentShaderSrc=getFileContent("./src/shaders/fragmentShader.glsl");


int main() {

	

	return 0;
}
