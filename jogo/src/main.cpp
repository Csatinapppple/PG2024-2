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

GLuint vertexShader;
std::string vertexShaderPath=getFileContent("./src/shaders/vertexShader.glsl");


int main() {
	using namespace std;

	cout << vertexShaderPath << endl;

	return 0;
}
