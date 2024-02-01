#pragma once

#include <iostream>
#include <chrono>
#include <thread>
#include <mutex>
#include <stdexcept>
#include <cstring>
#include <cstdlib>
#include <winsock2.h>  
#include <ws2tcpip.h>  

#pragma comment(lib, "ws2_32.lib") 

constexpr int BUFFER_SIZE = 20000;

class TunnelingClient {
public:
    TunnelingClient(const std::pair<std::string, int>& tunnelAddress, const std::pair<std::string, int>& forwardAddress);
    ~TunnelingClient();

    void startTunneling();

private:
    void establishConnection(std::pair<std::string, int>& address, SOCKET& clientSocket);
    void tunnel2forward();
    void forward2tunnel();
    void stopThreads();
    void closeConnections();

private:
    WSADATA wsaData; 
    std::pair<std::string, int> tunnelAddress;
    std::pair<std::string, int> forwardAddress;
    SOCKET tunnelSocket;
    SOCKET forwardSocket;
    std::mutex sendingSocketMutex;
    std::mutex receivingSocketMutex;
    std::chrono::steady_clock::time_point lastDataReceivedTime;
    std::thread tunnel2forwardThread;
    std::thread forward2tunnelThread;
};
