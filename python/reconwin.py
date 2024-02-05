from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
import textwrap

import os
import subprocess
import ctypes
import sys
username = os.getenv("USERNAME")
recon_data = None

def is_admin():

    try:

        return ctypes.windll.shell32.IsUserAnAdmin()

    except:

        return False


#if not is_admin():

   # ctypes.windll.shell32.ShellExecuteW(None, "runas", sys.executable, " ".join(sys.argv), None, 1)

   # sys.exit()
   
def insert_data(category, information, info_type):
    global recon_data
    if recon_data is None:
        recon_data = []
    recon_data.append([category, information, info_type])

def print_heading_and_insert(category, heading, info_type):
    insert_data(category, heading, info_type)


def execute_command(command):
    try:
        result = subprocess.run(command, shell=True, capture_output=True, text=True, encoding='utf-8', errors='replace')
        return result.stdout, result.stderr
    except Exception as e:
        return None, str(e)

def check_files_with_pattern(directory, file_pattern):
    dir_command = f'cd {directory} 2>nul && dir /s/b {file_pattern} 2>nul'
    result, error = execute_command(dir_command)
    
    if error:
        print(f"Error while checking files in {directory}: {error}")
    elif result:
        print_heading_and_insert("Files with pattern: {} in {}".format(file_pattern, directory), result[0], "FilesWithPattern_{}_{}_Setting".format(file_pattern, directory.replace('%', '').replace('\\', '_').replace('\\', '_')))

    else:
        print(f"No files found with pattern: {file_pattern} in {directory}")

def execute_command_powershell(command, output_list):
    result = subprocess.run(['powershell', command], capture_output=True, text=True)
    output_list.append(result.stdout)
    output_list.append(result.stderr)
                
def check_directory_permissions(directory_path):
    permissions_info, _ = execute_command(f'icacls "{directory_path}" 2>nul')
    if "(F) (M) (W) :\\ everyone authenticated users todos" in permissions_info:
        print(f"Directory: {directory_path}\nPermissions: {permissions_info}\n")
          
def list_files(user_directory, extensions, excluded_directories):
    try:
        for root, dirs, files in os.walk(user_directory):
            # Exclude specified directories
            dirs[:] = [d for d in dirs if d.lower() not in excluded_directories]
            
            for file in files:
                file_path = os.path.join(root, file)
                if any(file.lower().endswith(ext) for ext in extensions):
                    print_heading_and_insert("FILES", f"Found file: {file_path}", "Read/Write")
    except PermissionError as e:
        print(f"PermissionError: {e} - Skipped directory: {user_directory}")

def generate_pdf(file_path, recon_data):
    try:
        pdf_canvas = canvas.Canvas(file_path, pagesize=letter)
        pdf_canvas.setFont("Helvetica", 12)

        # Set starting y-coordinate for the page
        y_position = pdf_canvas._pagesize[1] - 80

        for category, information, info_type in recon_data:
            # Split information into lines for better formatting
            info_lines = information.split('\n')

            # Draw the category heading
            pdf_canvas.drawString(100, y_position, f"{category} Information")
            y_position -= 15

            # Draw the information lines
            for line in info_lines:
                # Wrap the line to fit within the page width
                wrapped_lines = textwrap.wrap(line, width=70)

                for wrapped_line in wrapped_lines:
                    y_position -= 15
                    pdf_canvas.drawString(100, y_position, wrapped_line)

                    # Check if there is enough space for the next line
                    if y_position <= 100:
                        pdf_canvas.showPage()  # Move to the next page
                        y_position = pdf_canvas._pagesize[1] - 80  # Reset y-coordinate

            # Add separation line at the end of the section
            y_position -= 30
            pdf_canvas.drawString(100, y_position, "-" * 50)  # Separation line
            y_position -= 15  # Additional space between sections

            # Check if there is enough space for the next section
            if y_position <= 100:
                pdf_canvas.showPage()  # Move to the next page
                y_position = pdf_canvas._pagesize[1] - 80  # Reset y-coordinate

        pdf_canvas.save()
        print("PDF created successfully.")
    except Exception as e:
        print(f"Error creating PDF: {e}")
        
def check_process_info():

    process_info_command = 'wmic process list full ^| find /i "executablepath" ^| find /i /v "system32" ^| find ":"'
    process_info_output, _ = execute_command(process_info_command)

    if process_info_output:
        running_processes_status = "Running Processes Found"
    else:
        running_processes_status = "No Running Processes"

    print_heading_and_insert("Running Processes", f"Checking for Running Processes: {running_processes_status}\n{process_info_output}", "RunningProcessesSetting")

    # Checking file permissions of running processes
    print_heading_and_insert("Checking file permissions of running processes", "[i] Checking file permissions of running processes (File backdooring - maybe the same files start automatically when Administrator logs in)", "FilePermissionsSetting")
    for line in process_info_output.split('\n'):
        if "=" in line:
            executable_path = line.split('=')[1].strip(' "')
            permissions_info, _ = execute_command(f'icacls "{executable_path}" 2>nul')
            if "(F) (M) (W) :\\ everyone authenticated users todos" in permissions_info:
                print(f"File: {executable_path}\nPermissions: {permissions_info}\n")

    # Checking directory permissions of running processes (DLL injection)
    print_heading_and_insert("Checking directory permissions of running processes", "[i] Checking directory permissions of running processes (DLL injection)", "DirectoryPermissionsSetting")
    for line in process_info_output.split('\n'):
        if "=" in line:
            executable_path = line.split('=')[1].strip(' "')
            directory_path = os.path.dirname(executable_path)
            permissions_info, _ = execute_command(f'icacls "{directory_path}" 2>nul')
            if "(F) (M) (W) :\\ everyone authenticated users todos" in permissions_info:
                print(f"Directory: {directory_path}\nPermissions: {permissions_info}\n")

    return process_info_output

def check_system_info():

    # Path to the RDCMan.settings file
    rdcman_settings_path = os.path.join(os.environ['LOCALAPPDATA'], 'Local', 'Microsoft', 'Remote Desktop Connection Manager', 'RDCMan.settings')
    if os.path.exists(rdcman_settings_path):
        rdcman_status = f"Found: RDCMan.settings in {rdcman_settings_path}, check for credentials in .rdg files"
        with open(rdcman_settings_path, 'r', encoding='utf-8', errors='ignore') as file:
            rdcman_content = file.read()

        print_heading_and_insert("Remote Desktop Credentials Manager", f"{rdcman_status}\n{rdcman_content}", "RemoteDesktopCredentialsManagerSetting")
    else:
        rdcman_status = "RDCMan.settings not found"
        print_heading_and_insert("Remote Desktop Credentials Manager", f"{rdcman_status}", "RemoteDesktopCredentialsManagerSetting")

    # Windows equivalent command for checking Mounted Disks
    mounted_disks_info, _ = execute_command('wmic logicaldisk get caption 2>nul | more || fsutil fsinfo drives 2>nul')
    if mounted_disks_info:
        mounted_disks_status = "Mounted Disks Found"
    else:
        mounted_disks_status = "No Mounted Disks"
    print_heading_and_insert("Mounted Disks", f"Checking for Mounted Disks: {mounted_disks_status}\n{mounted_disks_info}", "MountedDisksSetting")

    # Windows equivalent commands
    system_info, _ = execute_command("systeminfo")
    print_heading_and_insert("SYSTEM", f"System Information:\n{system_info}", "SystemInfo")

    # Hostname
    hostname, _ = execute_command("hostname")
    print_heading_and_insert("SYSTEM", f"Hostname:\n{hostname}", "Hostname")

    # Windows version
    os_version, _ = execute_command("ver")
    print_heading_and_insert("SYSTEM", f"OS Version:\n{os_version}", "OSVersion")

    # CPU information
    cpu_info, _ = execute_command("wmic cpu get caption, deviceid, maxclockspeed, name, numberofcores, numberoflogicalprocessors /format:list")
    print_heading_and_insert("SYSTEM", f"CPU Information:\n{cpu_info}", "CPUInfo")

    # Memory information
    memory_info, _ = execute_command("wmic memorychip get capacity, caption, devicelocator, speed /format:list")
    print_heading_and_insert("SYSTEM", f"Memory Information:\n{memory_info}", "MemoryInfo")

    # Disk information
    disk_info, _ = execute_command("wmic diskdrive get caption, mediatype, model, size /format:list")
    print_heading_and_insert("SYSTEM", f"Disk Information:\n{disk_info}", "DiskInfo")

    # Installed software
    installed_software, _ = execute_command("wmic product get name, version /format:list")
    print_heading_and_insert("SYSTEM", f"Installed Software:\n{installed_software}", "InstalledSoftware")

    # Running processes
    processes_info, _ = execute_command("tasklist")
    print_heading_and_insert("SYSTEM", f"Running Processes:\n{processes_info}", "RunningProcesses")

    # Environment variables
    env_variables, _ = execute_command("set")
    print_heading_and_insert("SYSTEM", f"Environment Variables:\n{env_variables}", "EnvironmentVariables")

    # Network configuration
    network_config, _ = execute_command("ipconfig /all")
    print_heading_and_insert("NETWORK", f"Network Configuration:\n{network_config}", "NetworkConfig")

    # Firewall status
    firewall_status, _ = execute_command("netsh advfirewall show allprofiles")
    print_heading_and_insert("SECURITY", f"Firewall Status:\n{firewall_status}", "FirewallStatus")

    # List of installed Windows updates
    windows_updates, _ = execute_command("wmic qfe get hotfixid,installedon /format:list")
    print_heading_and_insert("SYSTEM", f"Installed Windows Updates:\n{windows_updates}", "InstalledWindowsUpdates")

    # List of Services
    hklm_command = 'wmic path Win32_SystemDriver get DisplayName, StartMode, State'
    hklm_result, _ = execute_command(hklm_command)
    print_heading_and_insert("Drivers", f"HKLM DriversCheck \n{hklm_result}", "DriversInfo")

    # Netstat
    netstat_command = 'netstat -ano'
    netstat_result, _ = execute_command(netstat_command)
    print_heading_and_insert("NETWORK", f"Network Information:\n{netstat_result}", "NetworkInfo")

    # Get the list of current network shares
    net_share_info, _ = execute_command('net share')
    print_heading_and_insert("Network Shares", f"Current Network Shares:\n{net_share_info}", "NetworkSharesSetting")
    
    # Get printer info
    printers_info, _ = execute_command('wmic printer get name, drivername, portname, horizontalresolution, verticalresolution, driverversion')
    print_heading_and_insert("Installed Printers", f"List of installed printers:\n{printers_info}", "PrintersListSetting")
    
    # Firewall Information
    firewall_state_info, _ = execute_command('netsh firewall show state')
    firewall_config_info, _ = execute_command('netsh firewall show config')
    print_heading_and_insert("Firewall State", f"Firewall State:\n{firewall_state_info}\nFirewall Configuration:\n{firewall_config_info}", "FirewallSetting")

    # ARP Information
    arp_info, _ = execute_command('arp -A')
    print_heading_and_insert("ARP", f"ARP Table:\n{arp_info}", "ARPSetting")

    # Network Routes Information
    routes_info, _ = execute_command('route print')
    print_heading_and_insert("Network Routes", f"Network Routes:\n{routes_info}", "NetworkRoutesSetting")

    # WDigest Info
    wdigest_info, _ = execute_command('wmic registry query "HKEY_LOCAL_MACHINE\\SYSTEM\\CurrentControlSet\\Control\\SecurityProviders\\WDigest" /v UseLogonCredential')
    if '1' in wdigest_info:
        wdigest_status = "Enabled"
    else:
        wdigest_status = "Disabled"
    print_heading_and_insert("WDigest Setting", f"WDigest is {wdigest_status}", "WDigestSetting")

    cached_creds_info, _ = execute_command('reg query "HKEY_LOCAL_MACHINE\\SOFTWARE\\Microsoft\\Windows NT\\CurrentVersion\\Winlogon" /v CACHEDLOGONSCOUNT')

    # CACHEDLOGONSCOUNT
    if 'CACHEDLOGONSCOUNT' in cached_creds_info and '1' in cached_creds_info:
        cached_creds_status = "Enabled"
    else:
        cached_creds_status = "Disabled"
    print_heading_and_insert("Cached Credentials", f"Cached Credentials are {cached_creds_status}", "CachedCredentialsSetting")

    # Check if the output contains information about antivirus products
    av_info, _ = execute_command('WMIC /Node:localhost /Namespace:\\\\root\\SecurityCenter2 Path AntiVirusProduct Get displayName /Format:List')

    if av_info:
        av_status = "Registered"
    else:
        av_status = "Not Registered"

    # Display the status of antivirus products
    print_heading_and_insert("Anti-Virus Settings", f"Registered Anti-Virus: {av_status}\n{av_info}", "AntiVirusSetting")

    # Check whitelisted paths for Windows Defender
    defender_paths_info, _ = execute_command('reg query "HKLM\\SOFTWARE\\Microsoft\\Windows Defender\\Exclusions\\Paths" 2>nul')

    # Check if the output contains information about whitelisted paths for Windows Defender
    if 'HKEY_LOCAL_MACHINE\\SOFTWARE\\Microsoft\\Windows Defender\\Exclusions\\Paths' in defender_paths_info:
        defender_paths_status = "Whitelisted Paths Exist"
    else:
        defender_paths_status = "No Whitelisted Paths"

    # Display the status of whitelisted paths for Windows Defender
    print_heading_and_insert("Windows Defender Whitelisted Paths", f"Checking for defender whitelisted PATHS: {defender_paths_status}", "DefenderPathsSetting")

    # DNS Cache Information
    dns_cache_info, _ = execute_command('ipconfig /displaydns | findstr "Record" | findstr "Name Host"')
    print_heading_and_insert("DNS Cache", f"DNS Cache:\n{dns_cache_info}", "DNSCacheSetting")

    # Information about registered WiFi networks
    wifi_profiles_info, _ = execute_command('netsh wlan show profiles | find "Profile "')
    for profile_name in wifi_profiles_info.splitlines():
        profile_details, _ = execute_command(f'netsh wlan show profiles name={profile_name.split(":")[1].strip()} key=clear | findstr "SSID Cipher Content" | find /v "Number"')
        print_heading_and_insert(f"WiFi Profile: {profile_name.strip()}", f"WiFi Profile Details:\n{profile_details}", f"WifiCredsSetting_{profile_name.strip()}")


def user_info():
    # Current user/group info
    current_user_info, _ = execute_command("whoami /all")
    print_heading_and_insert("USER/GROUP", f"Current user/group info:\n{current_user_info}", "UserGroupInfo")

    # Users that have previously logged onto the system
    logged_users, _ = execute_command("net user")
    print_heading_and_insert("USER/GROUP", f"Users that have previously logged onto the system:\n{logged_users}", "LoggedUsers")

    # Who else is logged on
    logged_in_users, _ = execute_command("query user")
    print_heading_and_insert("USER/GROUP", f"Who else is logged on:\n{logged_in_users}", "LoggedInUsers")

    # Group memberships
    group_memberships, _ = execute_command("whoami /groups")
    print_heading_and_insert("USER/GROUP", f"Group memberships:\n{group_memberships}", "GroupMemberships")

    # Superuser account(s)
    super_users, _ = execute_command("net user /domain")
    print_heading_and_insert("USER/GROUP", f"Superuser account(s):\n{super_users}", "SuperUsers")

    # Local administrator accounts
    local_admins, _ = execute_command("net localgroup administrators")
    print_heading_and_insert("USER/GROUP", f"Local Administrator Accounts:\n{local_admins}", "LocalAdmins")

    # Locked-out user accounts
    locked_accounts, _ = execute_command("net accounts")
    print_heading_and_insert("USER/GROUP", f"Locked-out User Accounts:\n{locked_accounts}", "LockedAccounts")

    # Security policies
    security_policies, _ = execute_command("secedit /export /cfg -")
    print_heading_and_insert("USER/GROUP", f"Security Policies:\n{security_policies}", "SecurityPolicies")

    # Scheduled Tasks
    scheduled_task, _ = execute_command('schtasks /query /fo TABLE /nh | findstr /v /i "disable deshab informa"')
    print_heading_and_insert("USER/GROUP", f"Scheduled Task:\n{scheduled_task}", "ScheduledTask")

    # Check if you can modify any service registry
    registry_modification_info, _ = execute_command('for /f %a in (\'reg query hklm\system\currentcontrolset\services\') do del %temp%\\reg.hiv >nul 2>&1 & reg save %a %temp%\\reg.hiv >nul 2>&1 && reg restore %a %temp%\\reg.hiv >nul 2>&1 && echo.You can modify %a')
    print_heading_and_insert("Check If You Can Modify Any Service Registry", registry_modification_info, "CheckRegistryModificationAbilitiesSetting")

    # Unquoted Service Paths
    unquoted_service_paths_info, _ = execute_command('for /f "tokens=2" %n in (\'sc query state^= all^| findstr SERVICE_NAME\') do (for /f "delims=: tokens=1*" %r in (\'sc qc "%~n" ^| findstr BINARY_PATH_NAME ^| findstr /i /v /l /c:"c:\\windows\\system32" ^| findstr /v /c:""""\') do (echo.%~s ^| findstr /r /c:"[a-Z][ ][a-Z]" >nul 2>&1 && (echo.%n && echo.%~s && icacls %~s | findstr /i "(F) (M) (W) :\\" | findstr /i ":\\ everyone authenticated users todos %username%") && echo.))')
    print_heading_and_insert("Unquoted Service Paths", unquoted_service_paths_info, "UnquotedServicePathsSetting")



def interesting_files():

    # Database configuration files - Paths might differ on Windows
    db_configs = [
        'C:\\ProgramData\\MySQL\\MySQL Server 8.0\\my.ini',  # MySQL configuration file
        'C:\\Program Files (x86)\\MySQL\\MySQL Server 8.0\\my.ini',  # MySQL (x86) configuration file
        'C:\\Program Files\\MariaDB\\*\\data\\my.ini',  # MariaDB configuration file
        'C:\\Program Files (x86)\\MariaDB\\*\\data\\my.ini',  # MariaDB (x86) configuration file
        'C:\\Program Files\\PostgreSQL\\*\\data\\pg_hba.conf',  # PostgreSQL pg_hba.conf file
        'C:\\Program Files (x86)\\PostgreSQL\\*\\data\\pg_hba.conf',  # PostgreSQL (x86) pg_hba.conf file
        'C:\\Program Files\\Microsoft SQL Server\\MSSQL*\\MSSQL\\Binn\\sqlservr.exe',  # Microsoft SQL Server configuration
        'C:\\Program Files (x86)\\Microsoft SQL Server\\MSSQL*\\MSSQL\\Binn\\sqlservr.exe',  # Microsoft SQL Server (x86) configuration
        'C:\\Program Files\\MongoDB\\Server\\*\\bin\\mongod.cfg',  # MongoDB configuration file
        'C:\\Program Files\\MongoDB\\Server\\*\\bin\\mongos.cfg',  # MongoDB sharding router configuration file
    ]
    for file_path in db_configs:
        if os.path.exists(file_path):
            with open(file_path, 'r') as file:
                content = file.read()
            print_heading_and_insert("FILES", f"Found database configuration file: {file_path}\n{content}\n", "DBConfig")

    # Web server configuration files - Paths might differ on Windows
    web_configs = [
        'C:\\Program Files\\Apache Group\\Apache2\\conf\\httpd.conf',  # Apache configuration file
        'C:\\nginx\\conf\\nginx.conf',  # Nginx configuration file
        'C:\\Windows\\System32\\inetsrv\\config\\applicationHost.config',  # IIS configuration file
        'C:\\wamp\\bin\\apache\\apache*\\conf\\httpd.conf',  # WampServer Apache configuration file
        'C:\\xampp\\apache\\conf\\httpd.conf',  # XAMPP Apache configuration file
        'C:\\lighttpd\\conf\\lighttpd.conf',  # Lighttpd configuration file
        'C:\\Program Files\\Cherokee\\conf\\cherokee.conf',  # Cherokee configuration file
    ]
    for file_path in web_configs:
        if os.path.exists(file_path):
            with open(file_path, 'r') as file:
                content = file.read()
            print_heading_and_insert("FILES", f"Found web server configuration file: {file_path}\n{content}\n", "WebConfig")

    # Firewall configuration files
    firewall_configs = [
        'HKEY_LOCAL_MACHINE\\SYSTEM\\CurrentControlSet\\Services\\SharedAccess\\Parameters\\FirewallPolicy\\DomainProfile',
        'HKEY_LOCAL_MACHINE\\SYSTEM\\CurrentControlSet\\Services\\SharedAccess\\Parameters\\FirewallPolicy\\PublicProfile',
        'HKEY_LOCAL_MACHINE\\SYSTEM\\CurrentControlSet\\Services\\SharedAccess\\Parameters\\FirewallPolicy\\StandardProfile',
        'HKEY_LOCAL_MACHINE\\SOFTWARE\\Policies\\Microsoft\\WindowsFirewall',
        'HKEY_LOCAL_MACHINE\\SOFTWARE\\Policies\\Microsoft\\WindowsFirewall\\DomainProfile',
        'HKEY_LOCAL_MACHINE\\SOFTWARE\\Policies\\Microsoft\\WindowsFirewall\\PublicProfile',
        'HKEY_LOCAL_MACHINE\\SOFTWARE\\Policies\\Microsoft\\WindowsFirewall\\StandardProfile',
    ]
    for registry_key in firewall_configs:
        firewall_status, _ = execute_command(f'reg query "{registry_key}"')
        print_heading_and_insert("Firewall Configuration", "Registry Key: {}\n{}".format(registry_key, firewall_status), "FirewallConfig_{}".format(registry_key.replace('\\', '_')))


    # Proxy server configuration file
    proxy_configs = [
        'C:\\Squid\\etc\\squid.conf',
        'C:\\Windows\\System32\\inetsrv\\config\\applicationHost.config',  # IIS configuration file
        'C:\\Program Files\\Microsoft ISA Server\\ISALogs\\isaproxy.ini',  # ISA Server configuration file
        'C:\\Program Files\\Microsoft Forefront Threat Management Gateway\\Logs\\WebProxy\\w3proxy.log',  # Forefront TMG configuration file
        'C:\\CCProxy\\CCProxy.ini',  # CCProxy configuration file
        'C:\\Program Files\\WinGate\\WinGate.ini',  # WinGate configuration file
        'C:\\3proxy\\3proxy.cfg',  # 3Proxy configuration file
        'C:\\Wingate\\WinGates.ini',  # Wingate configuration file
    ]
    for file_path in proxy_configs:
        if os.path.exists(file_path):
            with open(file_path, 'r') as file:
                content = file.read()
            print_heading_and_insert("FILES", f"Found proxy server configuration file: {file_path}\n{content}\n", "ProxyConfig")

    # Security configuration files
    #security_configs = [
    #    'C:\\Windows\\System32\\GroupPolicy\\Machine\\registry.pol',  # Group Policy settings
    #    'C:\\Windows\\System32\\GroupPolicyUsers\\registry.pol',  # Group Policy settings for users
    #    'C:\\Windows\\System32\\SecConfig.efi',  # Secure Boot configuration
    #    'C:\\Windows\\System32\\Security\\AccountPolicy\\GptTmpl.inf',  # Account policies
    #    'C:\\Windows\\System32\\security\\templates\\policies\\gpt0000.inf',  # Security template configurations
    #    'C:\\Windows\\Security\\Database\\edb.log',  # Security database logs
    #    'C:\\Windows\\Security\\Database\\secedit.sdb',  # Security database
    #]
    #for file_path in security_configs:
    #    if os.path.exists(file_path):
    #        with open(file_path, 'r', encoding='utf-8', errors='ignore') as file:
    #            content = file.read()
    #        print_heading_and_insert("FILES", f"Found security configuration file: {file_path}\n{content}\n", "SecurityConfig")

    # Other potentially interesting files
    other_files = [
        'C:\\Windows\\System32\\drivers\\etc\\hosts',
        'C:\\Windows\\System32\\drivers\\etc\\lmhosts.sam',
        'C:\\Windows\\System32\\drivers\\etc\\networks',
        'C:\\Windows\\System32\\drivers\\etc\\protocol',
        'C:\\Windows\\System32\\drivers\\etc\\services'
        # Add more files if needed
    ]
    for file_path in other_files:
        if os.path.exists(file_path):
            with open(file_path, 'r') as file:
                content = file.read()
            print_heading_and_insert("FILES", f"Found interesting file: {file_path}\n{content}\n", f"OtherFile_{os.path.basename(file_path)}")

    user_directory = os.path.expanduser("~")
    file_extensions = [
        '.txt', '.csv', '.zip', '.doc', '.docx', '.xls', '.xlsx', '.ppt', '.pptx',
        '.pdf', '.rtf', '.html', '.xml', '.msg', '.eml', '.odt',
        '.ods', '.odp', '.mdb', '.accdb', '.pub', '.vsd', '.vsdx', '.dwg', '.dxf',
        '.psd', '.ai', '.indd', '.cdr', '.jpeg', '.jpg', '.png', '.gif', '.bmp',
        '.tiff', '.tif', '.eps', '.svg', '.mp3', '.mp4', '.avi', '.mov', '.wmv',
        '.flv', '.wav', '.ogg', '.wma', '.exe', '.dll', '.bat', '.ps1', '.sh'
        # Add more extensions if necessary
    ]
    excluded_directories = ['appdata']  # Add more directories to exclude if needed

    list_files(user_directory, file_extensions, excluded_directories)


def startup_info():

    registry_startup_keys = [
        r'HKEY_LOCAL_MACHINE\SOFTWARE\Microsoft\Windows\CurrentVersion\Run',
        r'HKEY_LOCAL_MACHINE\SOFTWARE\Microsoft\Windows\CurrentVersion\RunOnce',
        r'HKEY_CURRENT_USER\SOFTWARE\Microsoft\Windows\CurrentVersion\Run',
        r'HKEY_CURRENT_USER\SOFTWARE\Microsoft\Windows\CurrentVersion\RunOnce'
    ]

    registry_startup_info = ""
    for key in registry_startup_keys:
        registry_info, _ = execute_command(f'reg query {key} 2>nul')
        registry_startup_info += f"{registry_info}\n"

    # Vérifier si des informations sur le démarrage sont trouvées dans le registre
    if registry_startup_info:
        registry_startup_status = "Registry Startup Entries Found"
    else:
        registry_startup_status = "No Registry Startup Entries Found"

    # Afficher le statut des entrées de démarrage dans le registre
    print_heading_and_insert("Run At Startup (Registry)", f"Checking for Registry Startup Entries: {registry_startup_status}\n{registry_startup_info}", "RegistryRunAtStartupSetting")

    # Vérifier les permissions des répertoires de démarrage
    startup_directories = [
        "C:\\ProgramData\\Microsoft\\Windows\\Start Menu\\Programs\\Startup",
        f"C:\\Users\\{os.getlogin()}\\AppData\\Roaming\\Microsoft\\Windows\\Start Menu\\Programs\\Startup"
    ]

    for directory in startup_directories:
        check_directory_permissions(directory)


            
def check_other_info():
    # Group Policy Result
    gpresult_info, _ = execute_command("gpresult /r")
    print_heading_and_insert("Group Policy Result", f"Group Policy Result:\n{gpresult_info}", "GroupPolicyResult")

    # DPAPI MASTER KEYS
    dpapi_master_keys_info = []
    execute_command_powershell('Get-ChildItem %appdata%\\Microsoft\\Protect', dpapi_master_keys_info)
    dpapi_master_keys_info.append("Looking inside %localappdata%\\Microsoft\\Protect")
    execute_command_powershell('Get-ChildItem %localappdata%\\Microsoft\\Protect', dpapi_master_keys_info)
    print_heading_and_insert("DPAPI MASTER KEYS", "\n".join(dpapi_master_keys_info), "DPAPIMasterKeysSetting")

    # Check if .rdg files exist in Credentials folder
    credentials_dir_info = []
    credentials_dir_info.append("Looking inside %appdata%\\Microsoft\\Credentials\\")
    dir_command = 'dir /b/a %appdata%\\Microsoft\\Credentials\\ 2>nul'
    credentials_dir_result, _ = execute_command(dir_command)
    credentials_dir_info.append(credentials_dir_result)
    print_heading_and_insert("Credentials_Rdg_Files", "\n".join(credentials_dir_info), "Credentials_Rdg_Files_In_Docx_File")

    # Check for the existence of various unattended files
    unattended_files_info = []
    unattended_files_info.append("Checking for the existence of various unattended files")
    unattended_files_paths = [
        "%WINDIR%\\sysprep\\sysprep.xml",
        "%WINDIR%\\sysprep\\sysprep.inf",
        "%WINDIR%\\sysprep.inf",
        "%WINDIR%\\Panther\\Unattended.xml",
        "%WINDIR%\\Panther\\Unattend.xml",
        "%WINDIR%\\Panther\\Unattend\\Unattend.xml",
        "%WINDIR%\\Panther\\Unattend\\Unattended.xml",
        "%WINDIR%\\System32\\Sysprep\\unattend.xml",
        "%WINDIR%\\System32\\Sysprep\\unattended.xml",
        "%WINDIR%\\..\\unattend.txt",
        "%WINDIR%\\..\\unattend.inf"
    ]
    for path in unattended_files_paths:
        if subprocess.run(f'IF EXIST {path} ECHO.{path} exists.', shell=True).returncode == 0:
            unattended_files_info.append(path)
            file_content_command = f'type {path}'
            content, _ = execute_command(file_content_command)
            unattended_files_info.append(content)
    print_heading_and_insert("Unattended Files", "\n".join(unattended_files_info), "UnattendedFilesSetting")

    # MSINFO32 Command
    # MSINFO32 Command
    msinfo32_info, _ = execute_command("msinfo32 /report %TEMP%\\msinfo32_output.txt")

    # Utilisez l'encodage approprié (UTF-16 Little Endian) lors de la lecture du fichier
    with open(os.path.join(os.environ['TEMP'], 'msinfo32_output.txt'), 'r', encoding='utf-16-le') as msinfo_file:
        msinfo_content = msinfo_file.read()

    print_heading_and_insert("MSINFO32", f"MSINFO32 Output:\n{msinfo_content}", "Msinfo32Output")


def credential_other_info():
    # McAffee SiteList.xml
    site_list_paths = [
        "%ProgramFiles%\\**\\SiteList.xml",
        "%ProgramFiles(x86)%\\**\\SiteList.xml",
        "\"%windir%\\..\\Documents and Settings\"\\**\\SiteList.xml",
        "%windir%\\..\\Users\\**\\SiteList.xml"
    ]

    # Stoker les informations dans cette variable
    site_list_infos = []

    for path in site_list_paths:
        dir_command = f'cd {path} 2>nul && dir /s SiteList.xml 2>nul'
        site_list_info, _ = execute_command(dir_command)
        site_list_infos.append(site_list_info)

    # Afficher les informations en utilisant print_heading_and_insert
    print_heading_and_insert("McAffee SiteList.xml", "\n".join(site_list_infos), "McAffeeSiteListSetting")

    # Check for GPP Password files
    gpp_password_info = []
    gpp_password_paths = [
        "\"%SystemDrive%\\Microsoft\\Group Policy\\history\"\\**\\Groups.xml",
        "\"%SystemDrive%\\Microsoft\\Group Policy\\history\"\\**\\Services.xml",
        "\"%SystemDrive%\\Microsoft\\Group Policy\\history\"\\**\\Scheduledtasks.xml",
        "\"%SystemDrive%\\Microsoft\\Group Policy\\history\"\\**\\DataSources.xml",
        "\"%SystemDrive%\\Microsoft\\Group Policy\\history\"\\**\\Printers.xml",
        "\"%SystemDrive%\\Microsoft\\Group Policy\\history\"\\**\\Drives.xml",
        "\"%windir%\\..\\Documents and Settings\\All Users\\Application Data\\Microsoft\\Group Policy\\history\"\\**\\Groups.xml",
        "\"%windir%\\..\\Documents and Settings\\All Users\\Application Data\\Microsoft\\Group Policy\\history\"\\**\\Services.xml",
        "\"%windir%\\..\\Documents and Settings\\All Users\\Application Data\\Microsoft\\Group Policy\\history\"\\**\\Scheduledtasks.xml",
        "\"%windir%\\..\\Documents and Settings\\All Users\\Application Data\\Microsoft\\Group Policy\\history\"\\**\\DataSources.xml",
        "\"%windir%\\..\\Documents and Settings\\All Users\\Application Data\\Microsoft\\Group Policy\\history\"\\**\\Printers.xml",
        "\"%windir%\\..\\Documents and Settings\\All Users\\Application Data\\Microsoft\\Group Policy\\history\"\\**\\Drives.xml"
    ]

    for path in gpp_password_paths:
        dir_command = f'cd {path} 2>nul && dir /s/b Groups.xml == Services.xml == Scheduledtasks.xml == DataSources.xml == Printers.xml == Drives.xml 2>nul'
        gpp_password_info, _ = execute_command(dir_command)
        print_heading_and_insert("GPP Password", '\n'.join(gpp_password_info), "GPPPasswordSetting")




    # Check for cloud credentials files
    cloud_creds_paths = [
        "\"%SystemDrive%\\Users\"\\**\\.aws",
        "\"%SystemDrive%\\Users\"\\**\\credentials",
        "\"%SystemDrive%\\Users\"\\**\\gcloud",
        "\"%SystemDrive%\\Users\"\\**\\credentials.db",
        "\"%SystemDrive%\\Users\"\\**\\legacy_credentials",
        "\"%SystemDrive%\\Users\"\\**\\access_tokens.db",
        "\"%SystemDrive%\\Users\"\\**\\.azure",
        "\"%SystemDrive%\\Users\"\\**\\accessTokens.json",
        "\"%SystemDrive%\\Users\"\\**\\azureProfile.json",
        "\"%windir%\\..\\Documents and Settings\"\\**\\.aws",
        "\"%windir%\\..\\Documents and Settings\"\\**\\credentials",
        "\"%windir%\\..\\Documents and Settings\"\\**\\gcloud",
        "\"%windir%\\..\\Documents and Settings\"\\**\\credentials.db",
        "\"%windir%\\..\\Documents and Settings\"\\**\\legacy_credentials",
        "\"%windir%\\..\\Documents and Settings\"\\**\\access_tokens.db",
        "\"%windir%\\..\\Documents and Settings\"\\**\\.azure",
        "\"%windir%\\..\\Documents and Settings\"\\**\\accessTokens.json",
        "\"%windir%\\..\\Documents and Settings\"\\**\\azureProfile.json"
    ]

    for path in cloud_creds_paths:
        dir_command = f'cd {path} 2>nul && dir /s/b .aws == credentials == gcloud == credentials.db == legacy_credentials == access_tokens.db == .azure == accessTokens.json == azureProfile.json 2>nul'
        cloud_creds_info, _ = execute_command(dir_command)
        print_heading_and_insert("Cloud Credentials", '\n'.join(cloud_creds_info), "CloudCredsSetting")




    # Check for AppCmd.exe
    appcmd_path = "%systemroot%\\system32\\inetsrv\\appcmd.exe"
    appcmd_info, _ = execute_command(f'IF EXIST {appcmd_path} ECHO.{appcmd_path} exists.')
    print_heading_and_insert("AppCmd", appcmd_info, "AppCMDSetting")
    
    # RegFilesCredentials
    print_heading_and_insert("[+] Files in Registry that may contain credentials", "", "RegFilesCredentialsSetting")

    # Registry keys to check
     # Registry keys to check
    registry_keys = [
        "HKCU\\Software\\ORL\\WinVNC3\\Password",
        "HKEY_LOCAL_MACHINE\\SOFTWARE\\RealVNC\\WinVNC4\\password",
        "HKLM\\SOFTWARE\\Microsoft\\Windows NT\\Currentversion\\WinLogon",
        "HKLM\\SYSTEM\\CurrentControlSet\\Services\\SNMP",
        "HKCU\\Software\\TightVNC\\Server",
        "HKCU\\Software\\SimonTatham\\PuTTY\\Sessions",
        "HKCU\\Software\\OpenSSH\\Agent\\Keys"
    ]

    for key in registry_keys:
        print(f"Looking inside {key}")
        reg_query_info, reg_query_error = execute_command(f'reg query {key} 2>&1')  # Capture both standard output and errors
        if reg_query_error:
            print(f"Error while querying registry key {key}: {reg_query_error}")
        else:
            print_heading_and_insert(f"Registry Key: {key}", reg_query_info, f"RegistryKey_{key}_Setting")
    

    # Files to check in user profile and system directories
    user_profile_dir = "%USERPROFILE%"
    system_dir = "..\\..\\..\\..\\..\\..\\..\\..\\..\\..\\..\\"

    files_to_check = [
        "*password*",
        "*credential*",
        "RDCMan.settings",
        "*.rdg",
        "SCClient.exe",
        "*_history",
        ".sudo_as_admin_successful",
        ".profile",
        "*bashrc",
        "httpd.conf",
        "*.plan",
        ".htpasswd",
        ".git-credentials",
        "*.rhosts",
        "hosts.equiv",
        "Dockerfile",
        "docker-compose.yml",
        "appcmd.exe",
        "TypedURLs",
        "TypedURLsTime",
        "History",
        "Bookmarks",
        "Cookies",
        "Login Data",
        "places.sqlite",
        "key3.db",
        "key4.db",
        "credentials",
        "credentials.db",
        "access_tokens.db",
        "accessTokens.json",
        "legacy_credentials",
        "azureProfile.json",
        "unattend.txt",
        "access.log",
        "error.log",
        "*.gpg",
        "*.pgp",
        "*config*.php",
        "elasticsearch.y*ml",
        "kibana.y*ml",
        "*.p12",
        "*.der",
        "*.csr",
        "*.cer",
        "known_hosts",
        "id_rsa",
        "id_dsa",
        "*.ovpn",
        "anaconda-ks.cfg",
        "hostapd.conf",
        "rsyncd.conf",
        "cesi.conf",
        "supervisord.conf",
        "tomcat-users.xml",
        "*.kdbx",
        "KeePass.config",
        "Ntds.dit",
        "SAM",
        "SYSTEM",
        "FreeSSHDservice.ini",
        "sysprep.inf",
        "sysprep.xml",
        "unattend.xml",
        "unattended.xml",
        "*vnc*.ini",
        "*vnc*.c*nf*",
        "*vnc*.txt",
        "*vnc*.xml",
        "groups.xml",
        "services.xml",
        "scheduledtasks.xml",
        "printers.xml",
        "drives.xml",
        "datasources.xml",
        "php.ini",
        "https.conf",
        "https-xampp.conf",
        "httpd.conf",
        "my.ini",
        "my.cnf",
        "access.log",
        "error.log",
        "server.xml",
        "SiteList.xml",
        "ConsoleHost_history.txt",
        "setupinfo",
        "setupinfo.bak"
    ]

    for file_pattern in files_to_check:
        check_files_with_pattern(user_profile_dir, file_pattern)
        check_files_with_pattern(system_dir, file_pattern)

   
def rewin():
    credential_other_info()
    check_other_info()
    check_system_info()
    user_info()
    interesting_files()
    check_process_info()
    startup_info()
    return recon_data

if __name__ == "__main__":
    recon_data = rewin()
    print(recon_data)
    #generate_pdf("recon_data.pdf", recon_data)





