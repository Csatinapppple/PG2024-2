#version 400
in vec2 texCoord;
uniform sampler2D texBuffer;
uniform vec2 offsetTex;
out vec4 color;
void main()
{
	color = texture(texBuffer, texCoord + offsetTex);
}
