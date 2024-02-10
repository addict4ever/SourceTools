#pragma once

#include <iostream>
#include <fstream>
#include <cstdlib>
#include <cstdio>
#include <unordered_map>
#include <vector>
#include <string>
#include <sstream>
#include <filesystem>
#include <Windows.h>
#include <Dsgetdc.h> 
#include <lm.h>
#include <algorithm>
 

namespace fs = std::filesystem;

bool isDomainJoined();
bool isAdmin();
std::vector<std::string> searchFilesByExtension(const std::string& directory, const std::string& extension);
void executePowerShellCommand(const std::string& command, std::unordered_map<std::string, std::string>& output_map, const std::string& key);
void executeCommand(const char* command, std::string& output);
void writeHeader(std::ofstream& html_file);
void writeFooter(std::ofstream& html_file);
void writeSection(std::ofstream& html_file, const std::string& section_id, const std::string& title, const std::string& content);
void writeSectionLink(std::ofstream& html_file, const std::string& section_id, const std::string& link_text);
void writeTableFromCommandOutput(std::ofstream& html_file, const std::string& section_id, const std::string& title, const std::string& command_output);
void classifyProcesses(std::unordered_map<std::string, std::string>& system_outputs);

