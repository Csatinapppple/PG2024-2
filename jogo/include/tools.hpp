#ifndef TOOLS_HPP__
#define TOOLS_HPP__

#include <string>
#include <fstream>
#include <GLFW/glfw3.h>
#include "./glad.h"
#define W 800
#define H 600

std::string
getFileContent(const std::string& path)
{
  std::ifstream file(path);
  std::string content((std::istreambuf_iterator<char>(file)), std::istreambuf_iterator<char>());

  return content;
}


int start_glfw(GLFWwindow** localWindow){
  using namespace std;
  if (!glfwInit()){
    cerr << "ERROR: Could not start glfw\n";
    return 1;
  }

  glfwWindowHint(GLFW_CONTEXT_VERSION_MAJOR, 3);
  glfwWindowHint(GLFW_CONTEXT_VERSION_MINOR, 3);
  glfwWindowHint(GLFW_OPENGL_FORWARD_COMPAT, GL_TRUE);
  glfwWindowHint(GLFW_OPENGL_PROFILE, GLFW_OPENGL_CORE_PROFILE);

  *localWindow = glfwCreateWindow(W,H, "game test", nullptr, nullptr);

  if (!*localWindow) {
    cerr << "ERROR: could not open window with GLFW3\n";
    return 1;
  }

  glfwMakeContextCurrent(*localWindow);



}

#endif