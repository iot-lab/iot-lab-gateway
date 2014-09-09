#include <unistd.h>
#include <string.h>
#include <stdio.h>


int main()
{
	char hostname[256];

	gethostname(hostname, 256);
	printf("Hostname: %s\n", hostname);
	unsigned node_num;
	unsigned node_type = 0;

	char *pch;
	pch = strtok(hostname, "-");
	if (0 == strcmp("m3", pch))
		node_type = 3;
	if (0 == strcmp("a8", pch))
		node_type = 8;

	pch = strtok(NULL, "-");
	node_num = atoi(pch);

	printf("node_type: '%u', node_num '%u'\n", node_type, node_num);
	printf("node_id: %04x\n", node_type << 12 | node_num);

	node_type = 3;
	node_num = 312;
	printf("node_type: '%u', node_num '%u'\n", node_type, node_num);
	printf("node_id: %04x\n", node_type << 12 | node_num);
}
