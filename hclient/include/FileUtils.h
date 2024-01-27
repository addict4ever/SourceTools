#pragma once
// fileutils.h
#ifndef FILEUTILS_H
#define FILEUTILS_H

// Function declarations

#endif // FILEUTILS_H
#define _SILENCE_EXPERIMENTAL_FILESYSTEM_DEPRECATION_WARNING
#include <filesystem>
#include <string>

namespace fs = std::filesystem;

std::string getHostName();
std::string generateTimestamp();
void deleteFiles(const char* filesToDeletePattern);
std::string compressFilesInCurrentDirectory(const char* outputArchiveNamePattern);
