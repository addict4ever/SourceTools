#include "ctun.h"

int main() {
    std::pair<std::string, int> tunnelAddress("16.16.16.114", 10000);
    std::pair<std::string, int> forwardAddress("127.0.0.1", 3389);

    try {
        TunnelingClient tunnelingClient(tunnelAddress, forwardAddress);
        tunnelingClient.startTunneling();
    } catch (const std::exception& e) {
        std::cerr << "An exception occurred" << std::endl;
        std::cerr << e.what() << std::endl;
    }

    return 0;
}
