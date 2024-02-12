#include "reconwin.h"

using namespace std;
namespace fs = filesystem;

bool isDomainJoined() {
    DWORD flags = DS_DIRECTORY_SERVICE_REQUIRED | DS_RETURN_DNS_NAME;
    PDOMAIN_CONTROLLER_INFO pdcInfo = nullptr;
    DWORD result = DsGetDcName(nullptr, nullptr, nullptr, nullptr, flags, &pdcInfo);
    if (result == ERROR_SUCCESS) {
        NetApiBufferFree(pdcInfo);
        return true;
    } else {
        return false;
    }
}

bool isAdmin() {
    BOOL isAdmin = FALSE;
    SID_IDENTIFIER_AUTHORITY NtAuthority = SECURITY_NT_AUTHORITY;
    PSID AdminGroup;
    if (AllocateAndInitializeSid(&NtAuthority, 2, SECURITY_BUILTIN_DOMAIN_RID, DOMAIN_ALIAS_RID_ADMINS, 0, 0, 0, 0, 0, 0, &AdminGroup)) {
        CheckTokenMembership(NULL, AdminGroup, &isAdmin);
        FreeSid(AdminGroup);
    }
    return isAdmin != 0;
}

std::vector<std::string> searchFilesByExtension(const std::string& directory, const std::string& extension) {
    std::vector<std::string> found_files;
    fs::path dir_path(directory);
    if (fs::exists(dir_path) && fs::is_directory(dir_path)) {
        for (const auto& entry : fs::recursive_directory_iterator(dir_path)) {
            if (entry.is_regular_file() && entry.path().extension() == extension) {
                found_files.push_back(entry.path().string());
            }
        }
    }
    return found_files;
}

void executePowerShellCommand(const std::string& command, std::unordered_map<std::string, std::string>& output_map, const std::string& key) {
    std::string powershell_command = "powershell -command \"" + command + "\"";
    std::string output;
    FILE* pipe = _popen(powershell_command.c_str(), "r");
    if (!pipe) {
        std::cout << "Error executing PowerShell command." << std::endl;
        return;
    }
    char buffer[128];
    while (!feof(pipe)) {
        if (fgets(buffer, 128, pipe) != NULL)
            output += buffer;
    }
    _pclose(pipe);
    output_map[key] = output;
}

void executeCommand(const char* command, string& output) {
    char buffer[128];
    output = "";
    FILE* pipe = _popen(command, "r");
    if (!pipe) {
        cout << "Error executing command." << endl;
        return;
    }
    while (!feof(pipe)) {
        if (fgets(buffer, 128, pipe) != NULL)
            output += buffer;
    }
    _pclose(pipe);
}

void writeHeader(ofstream& html_file) {
    if (html_file.is_open()) {
        html_file << "<html>\n<head>\n<title>Windows Recoon and System Information</title>\n<style>body { background-color: #f2f2f2; }</style>\n</head>\n<body>\n";
    } else {
        cout << "Error: Unable to write to HTML file." << endl;
    }
}

// Function to write HTML footer into a file
void writeFooter(ofstream& html_file) {
    if (html_file.is_open()) {
        html_file << "</body>\n</html>\n";
    } else {
        cout << "Error: Unable to write to HTML file." << endl;
    }
}

// Function to write a section with title and content into an HTML file
void writeSection(ofstream& html_file, const string& section_id, const string& title, const string& content) {
    if (html_file.is_open()) {
        html_file << "<h2 id=\"" << section_id << "\">" << title << "</h2>\n";
        html_file << "<pre>\n" << content << "</pre>\n";
    } else {
        cout << "Error: Unable to write to HTML file." << endl;
    }
}

// Function to write a link to a section into an HTML file
void writeSectionLink(ofstream& html_file, const string& section_id, const string& link_text) {
    if (html_file.is_open()) {
        html_file << "<a href=\"#" << section_id << "\">" << link_text << "</a><br>\n";
    } else {
        cout << "Error: Unable to write to HTML file." << endl;
    }
}

// Function to write a table from the output of a command into an HTML file
void writeTableFromCommandOutput(ofstream& html_file, const string& section_id, const string& title, const string& command_output) {
    if (html_file.is_open()) {
        html_file << "<h2 id=\"" << section_id << "\">" << title << "</h2>\n";
        html_file << "<table border=\"1\">\n";

        // Write table rows based on lines of command output
        istringstream iss(command_output);
        string line;
        bool isHeader = true;
        while (getline(iss, line)) {
            html_file << "<tr>\n";
            istringstream iss_line(line);
            string cell;
            while (getline(iss_line, cell, '\t')) {
                if (isHeader) {
                    html_file << "<th>" << cell << "</th>\n";
                } else {
                    html_file << "<td>" << cell << "</td>\n";
                }
            }
            html_file << "</tr>\n";
            isHeader = false;
        }
        html_file << "</table>\n";
    } else {
        cout << "Error: Unable to write to HTML file." << endl;
    }
}



