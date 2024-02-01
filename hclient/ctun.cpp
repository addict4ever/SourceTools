#include "ctun.h"

TunnelingClient::TunnelingClient(const std::pair<std::string, int>& tunnelAddress, const std::pair<std::string, int>& forwardAddress)
    : tunnelAddress(tunnelAddress), forwardAddress(forwardAddress), tunnelSocket(INVALID_SOCKET), forwardSocket(INVALID_SOCKET) {
    
    if (WSAStartup(MAKEWORD(2, 2), &wsaData) != 0) {
        throw std::runtime_error("Failed to initialize Winsock");
    }
}

TunnelingClient::~TunnelingClient() {
    stopThreads();
    closeConnections();
    std::cout << "\nStopped correctly" << std::endl;
    WSACleanup();
}

void TunnelingClient::establishConnection(std::pair<std::string, int>& address, SOCKET& clientSocket) {
    clientSocket = socket(AF_INET, SOCK_STREAM, 0);

    while (true) {
        try {
            sockaddr_in serverAddr{};
            serverAddr.sin_family = AF_INET;
            serverAddr.sin_port = htons(address.second);
            inet_pton(AF_INET, address.first.c_str(), &serverAddr.sin_addr);

            if (connect(clientSocket, reinterpret_cast<struct sockaddr*>(&serverAddr), sizeof(serverAddr)) == 0) {
                break;
            }
        } catch (...) {
            std::this_thread::sleep_for(std::chrono::seconds(1));
        }
    }
}

void TunnelingClient::tunnel2forward() {
    while (true) {
        try {
            char data[BUFFER_SIZE];
            int bytesRead = recv(tunnelSocket, data, BUFFER_SIZE, 0);

            if (bytesRead <= 0) {
                throw std::runtime_error("Tunnel has dropped, this shouldn't happen, restart RPPF.");
            }

            lastDataReceivedTime = std::chrono::steady_clock::now();

            std::lock_guard<std::mutex> lock(sendingSocketMutex);
            send(forwardSocket, data, bytesRead, 0);

        } catch (const std::exception& e) {
            std::cerr << "Exception in tunnel2forward: " << e.what() << std::endl;

            std::exit(1);
        }
    }
}


void TunnelingClient::forward2tunnel() {
    while (true) {
        try {
            char data[BUFFER_SIZE];
            int bytesRead = recv(forwardSocket, data, BUFFER_SIZE, 0);

            if (bytesRead <= 0) {
                continue;
            }

            send(tunnelSocket, data, bytesRead, 0);

        } catch (const std::exception& e) {
            std::cerr << "Exception in forward2tunnel: " << e.what() << std::endl;
        }
    }
}

void TunnelingClient::stopThreads() {
    if (tunnel2forwardThread.joinable()) {
        tunnel2forwardThread.join();
    }

    if (forward2tunnelThread.joinable()) {
        forward2tunnelThread.join();
    }
}

void TunnelingClient::startTunneling() {
    try {
        std::cout << "Creating tunnel to " << tunnelAddress.first << std::endl;
        establishConnection(tunnelAddress, tunnelSocket);
        std::cout << "Tunnel created" << std::endl;

        std::cout << "Opening forward connection to " << forwardAddress.first << std::endl;
        establishConnection(forwardAddress, forwardSocket);
        std::cout << "Connection created" << std::endl;
        std::cout << "--------------------------------------------" << std::endl;
        std::cout << "Ready to transfer data" << std::endl;

        tunnel2forwardThread = std::thread(&TunnelingClient::tunnel2forward, this);
        forward2tunnelThread = std::thread(&TunnelingClient::forward2tunnel, this);

        tunnel2forwardThread.join();
        forward2tunnelThread.join();

    } catch (const std::exception& e) {
        std::cerr << "An exception occurred" << std::endl;
        std::cerr << e.what() << std::endl;
        std::cerr << "Trying to close sockets" << std::endl;
        stopThreads();
        closeConnections();
        std::cout << "\nStopped correctly" << std::endl;
        std::exit(0);
    }
}

void TunnelingClient::closeConnections() {
    if (tunnelSocket != INVALID_SOCKET) {
        shutdown(tunnelSocket, SD_BOTH);
        closesocket(tunnelSocket);
    }

    if (forwardSocket != INVALID_SOCKET) {
        shutdown(forwardSocket, SD_BOTH);
        closesocket(forwardSocket);
    }
}
