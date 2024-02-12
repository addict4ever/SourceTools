#include <iostream>
#include <fstream>
#include <unordered_map>
#include <vector>
#include "reconwin.h" 

int main() {
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
