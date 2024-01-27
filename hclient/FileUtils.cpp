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
        std::string pattern(filesToDeletePattern);
        for (const auto& entry : std::filesystem::directory_iterator(std::filesystem::current_path())) {

            if (entry.path().extension() == ".bmp" && std::filesystem::is_regular_file(entry)) {
                std::filesystem::remove(entry.path());
                std::cout << "Fichier supprimé : " << entry.path() << std::endl;
            }
        }
    } catch (const std::filesystem::filesystem_error& e) {
        std::cerr << "Erreur lors de la suppression des fichiers : " << e.what() << std::endl;
    }
}

std::string compressFilesInCurrentDirectory(const char* outputArchiveNamePattern) {
    try {
        std::string hostname = getHostName();
        std::string timestamp = generateTimestamp();
        std::string outputArchiveName = hostname + "_" + timestamp + ".tar.gz";

        std::filesystem::path currentDirectory = std::filesystem::current_path();
        std::filesystem::path outputArchivePath = currentDirectory / outputArchiveName;

        std::filesystem::create_directories(outputArchivePath.parent_path());

        std::string command = "tar czvf \"" + outputArchivePath.string() + "\" " + outputArchiveNamePattern;

        if (std::system(command.c_str()) != 0) {
            std::cerr << "Erreur lors de la compression des fichiers." << std::endl;
            return ""; // Ou une indication d'erreur si nécessaire
        }

        std::cout << "Compression réussie. Archive créée : " << outputArchivePath << std::endl;

        return outputArchivePath.string(); // Retourne le chemin complet du fichier d'archive

    } catch (const std::filesystem::filesystem_error& e) {
        std::cerr << "Erreur lors de la compression des fichiers : " << e.what() << std::endl;
        return ""; // Ou une indication d'erreur si nécessaire
    }
}
