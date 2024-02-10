#include <iostream>
#include <fstream>
#include <unordered_map>
#include <vector>
#include "reconwin.h" 

int main() {
    std::unordered_map<std::string, std::string> system_outputs;
    bool onDomain = isDomainJoined();
    if (onDomain) {
        executeCommand("net user /domain", system_outputs["net_user_DOMAIN"]);
        executeCommand("net group", system_outputs["net_group_DOMAIN"]);
        executeCommand("net view", system_outputs["net_view_DOMAIN"]);
        executeCommand("gpresult /Scope Computer /v /R", system_outputs["gpresult_SCOPE"]);
    }
    if (isAdmin()) {
        executeCommand("netstat /anob", system_outputs["netstat_ADMIN"]);
        executeCommand("tasklist /V", system_outputs["tasklist_ADMIN"]);
        executeCommand("manage-bde -status", system_outputs["manage-bde"]);
        executeCommand("net session", system_outputs["net_session"]);
        executePowerShellCommand("auditpol /get /category:*", system_outputs, "security_event_audit_policy");
        executePowerShellCommand("Get-BitLockerVolume | Select-Object -Property VolumeStatus", system_outputs, "bitlocker_STATUS");
    }
    executePowerShellCommand("Get-Process | Select-Object -ExpandProperty ProcessName", system_outputs, "test_STATUS");
    classifyProcesses(system_outputs);
    executePowerShellCommand("Get-Process | Select-Object ProcessName, SessionId, MainWindowTitle", system_outputs, "Get_session");
    executePowerShellCommand("Get-WmiObject Win32_LogonSession | Select-Object -Property StartTime, LogonType, AuthenticationPackage, @{Name='User';Expression={$_.GetRelated('Win32_LoggedOnUser').User.Name}}", system_outputs, "logged_on_users");

    executePowerShellCommand("Get-WmiObject Win32_Battery", system_outputs, "battery_REPORT");
    executePowerShellCommand("Get-ChildItem Env:", system_outputs, "system_VARIABLES");
    executePowerShellCommand("Get-WinEvent -ListLog * | ForEach-Object { Get-WinEvent -LogName $_.LogName -FilterXPath \"*[System[(Level=1 or Level=2)]]\" -ErrorAction SilentlyContinue } | Format-Table -Property TimeCreated, Id, Message -Wrap -AutoSize", system_outputs, "event_error_critical_LOG");


    executePowerShellCommand("Get-CimInstance Win32_StartupCommand | Select-Object Caption, Command, Location, User", system_outputs, "startup_programs");
    executePowerShellCommand("(Get-ItemProperty -Path \"HKLM:\\Software\\Microsoft\\Windows\\CurrentVersion\\Policies\\System\").EnableLUA", system_outputs, "uac_STATUS");
    executePowerShellCommand("Get-ExecutionPolicy", system_outputs, "execution_policy");
    executePowerShellCommand("Get-MpComputerStatus", system_outputs, "defender_status");
    executePowerShellCommand("Get-MpPreference | Select-Object -Property *Protection", system_outputs, "malware_protection");
    
    executeCommand("netsh advfirewall show all", system_outputs["firewall_STATUS"]);
    executePowerShellCommand("Get-NetFirewallProfile | Select-Object -Property *", system_outputs, "firewall_PROFILS");
    executePowerShellCommand("Get-NetFirewallRule | Select-Object DisplayName, Action, Direction, Enabled", system_outputs, "firewall_RULES");

    executeCommand("sc query termservice", system_outputs["query_RDP"]);
    executeCommand("whoami /all", system_outputs["whoami_ALL"]);
    
    executeCommand("wmic bios get Manufacturer, SMBIOSBIOSVersion, ReleaseDate", system_outputs["bios_info"]);
    executeCommand("wmic path win32_videocontroller get caption, name, videoarchitecture, AdapterRAM", system_outputs["graphics_card_info"]);
    executeCommand("wmic diskdrive get DeviceID, Model, InterfaceType, MediaType, Size", system_outputs["disk_info"]);
    executeCommand("wmic cpu get Name, MaxClockSpeed, NumberOfCores, NumberOfLogicalProcessors", system_outputs["cpu_info"]);
    executePowerShellCommand("Get-WmiObject -Class SoftwareLicensingService", system_outputs, "windows_serials");
    executePowerShellCommand("Get-NetTCPConnection | Select-Object LocalAddress, LocalPort, RemoteAddress, RemotePort, State | Format-Table", system_outputs, "active_network_TCP");
    executePowerShellCommand("Get-NetUDPEndpoint | Select-Object LocalAddress, LocalPort, RemoteAddress, RemotePort, State | Format-Table", system_outputs, "active_network_UDP");

    executeCommand("wmic logicaldisk get caption, description, freespace, size, volumename", system_outputs["wmic_LOGICALDISK"]);
    executeCommand("arp -a", system_outputs["arp"]);
    executeCommand("net start", system_outputs["net_START"]);
    executeCommand("net user", system_outputs["net_USER"]);
    executeCommand("net localgroup", system_outputs["net_LOCALGROUP"]);
    executeCommand("net share", system_outputs["net_SHARE"]);   
    executeCommand("ipconfig /all", system_outputs["ipconfig_ALL"]);
    executePowerShellCommand("Get-NetAdapter | Select-Object Name, InterfaceDescription, Status, MacAddress, LinkSpeed, MediaType, DriverVersion, DriverDate, PhysicalMediaType, Virtual | Format-Table", system_outputs, "network_adapter_INFORMATION");
    executeCommand("route print", system_outputs["route_ROUTE-PRINT"]);
    executePowerShellCommand("Get-NetRoute", system_outputs, "route_GET-NETROUTE"); 
    executeCommand("schtasks /query", system_outputs["schtasks"]);
    executeCommand("tasklist /v /fo TABLE", system_outputs["tasklist"]);
    executeCommand("driverquery", system_outputs["driversquery"]);
    executeCommand("driverquery /v /fo table | findstr /i \"Running\"", system_outputs["driversquery_RUNNING"]);
    executeCommand("wmic printer list full", system_outputs["wmic_list_PRINTER"]);
    executeCommand("wmic qfe list full /format:table", system_outputs["Installed_HOTFIX"]);
    executeCommand("wmic product get name, version", system_outputs["Installed_SOFTWARE"]);
    executePowerShellCommand("Get-Service | Where-Object {$_.StartType -eq 'Automatic' -and $_.Status -ne 'Running'} | Select-Object -Property Name, DisplayName", system_outputs, "list_service_auto_NOT_RUNNING");
    executePowerShellCommand("Get-ItemProperty HKLM:\\Software\\Wow6432Node\\Microsoft\\Windows\\CurrentVersion\\Uninstall\\* | Select-Object DisplayName, DisplayVersion, Publisher, InstallDate", system_outputs, "installed_software_POWERSHELL");
    executePowerShellCommand("netsh wlan show profiles | Select-String \":(.+)$\" | %{$name=$_.Matches.Groups[1].Value.Trim(); $_} | %{(netsh wlan show profile name=\"$name\" key=clear)}  | Select-String \"Key Content\\W+\\:(.+)$\" | %{$pass=$_.Matches.Groups[1].Value.Trim(); $_} | %{[PSCustomObject]@{ PROFILE_NAME=$name;PASSWORD=$pass }} | Format-Table -AutoSize", system_outputs, "WIFI_PASS");
    executePowerShellCommand("Test-NetConnection -ComputerName www.google.ca -Port 443", system_outputs, "test_network_connection_DNS");
    executePowerShellCommand("Test-NetConnection -ComputerName 8.8.8.8 -Port 443", system_outputs, "test_network_connection_IP");


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
            const std::string& content = system_outputs[section_id];
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
        
        executeCommand("netstat -ano", system_outputs["netstat"]);
        writeTableFromCommandOutput(html_file, "netstat_table", "Results of the command netstat -ano", system_outputs["netstat"]);
        writeFooter(html_file);
                
        html_file.close();
        std::cout << "The file system_info.html has been successfully created." << std::endl;
    } else {
        std::cout << "Error opening HTML file." << std::endl;
    }

    return 0;
}
