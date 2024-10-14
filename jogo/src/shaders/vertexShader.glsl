#version 400
layout (location = 0) in vec3 position;
layout (location = 1) in vec2 texc;
uniform mat4 projection;
uniform mat4 model;
out vec2 texCoord;
void main()
{
	gl_Position = projection * model * vec4(position.x, position.y, position.z, 1.0);
	texCoord = vec2(texc.s, 1.0 - texc.t);
}
