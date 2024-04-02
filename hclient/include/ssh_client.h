#ifndef SSH_CLIENT_H
#define SSH_CLIENT_H

#include <string>

std::string ssh_client(const char* server_address, int server_port, const char* username, const char* password);

#endif // SSH_CLIENT_H
