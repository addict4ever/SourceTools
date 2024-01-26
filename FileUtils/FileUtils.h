#pragma once
#include <string>
#include <filesystem>

std::string getHostName();
std::string generateTimestamp();
void deleteFiles(const char* filesToDeletePattern);
void compressFilesInCurrentDirectory(const char* outputArchiveNamePattern);
