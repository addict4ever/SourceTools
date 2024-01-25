#include "FileUtils.h"
#include <iostream>
#include <chrono>
#include <ctime>
#include <sstream>
#include <Windows.h>
#include <tchar.h>

std::string getHostName() {
    std::string hostname;
    char computerName[MAX_COMPUTERNAME_LENGTH + 1];
    DWORD size = sizeof(computerName) / sizeof(computerName[0]);
    if (GetComputerName(computerName, &size)) {
        hostname = computerName;
    } else {
        std::cerr << "Erreur lors de l'obtention du nom d'hôte." << std::endl;
    }
    return hostname;
}

std::string generateTimestamp() {
    auto now = std::chrono::system_clock::to_time_t(std::chrono::system_clock::now());
    std::tm localTime;
    if (localtime_s(&localTime, &now) != 0) {
        std::cerr << "Erreur lors de la récupération de l'heure locale." << std::endl;
    }

    std::stringstream timestamp;
    char buffer[20]; // Au format "%Y%m%d_%H%M%S"
    if (strftime(buffer, sizeof(buffer), "%Y%m%d_%H%M%S", &localTime) == 0) {
        std::cerr << "Erreur lors du formatage du timestamp." << std::endl;
    }
    timestamp << buffer;

    return timestamp.str();
}

void deleteFiles(const char* filesToDeletePattern) {
    try {
        for (const auto& entry : std::filesystem::directory_iterator(filesToDeletePattern)) {
            std::filesystem::remove(entry.path());
            std::cout << "Fichier supprimé : " << entry.path() << std::endl;
        }
    } catch (const std::filesystem::filesystem_error& e) {
        std::cerr << "Erreur lors de la suppression des fichiers : " << e.what() << std::endl;
    }
}
