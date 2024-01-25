#include "FileUtils.h"
#include <iostream>

int main() {
    std::string hostname = getHostName();
    std::string timestamp = generateTimestamp();

    std::string outputArchiveName = hostname + "_" + timestamp + ".tar.gz";
    std::cout << "Archive créée : " << outputArchiveName << std::endl;

    const char* outputArchiveNamePatternBMP = "*.bmp";
    deleteFiles(outputArchiveNamePatternBMP);

    return 0;
}
