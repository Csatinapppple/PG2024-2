#ifndef TOOLS_HPP__
#define TOOLS_HPP__

#include <string>
#include <fstream>
#include <GLFW/glfw3.h>
#include "./glad.h"

std::string
getFileContent(const std::string& path)
{
  std::ifstream file(path);
  std::string content((std::istreambuf_iterator<char>(file)), std::istreambuf_iterator<char>());
	

  return content;
}


#endif
