#include <windows.h>
#include <stdio.h>
#include <tlhelp32.h>
#include <wincrypt.h>
#include <psapi.h>
#pragma comment(lib, "crypt32.lib")
#pragma comment(lib, "Advapi32.lib")

void CheckPrivileges() {
    HANDLE hToken;
    DWORD dwSize;
    PTOKEN_PRIVILEGES pPrivileges;
    BOOL bResult;

    // Open the access token of the current process
    if (!OpenProcessToken(GetCurrentProcess(), TOKEN_QUERY, &hToken)) {
        printf("Error opening current process token (%d)\n", GetLastError());
        return;
    }

    // Determine the required size for privileges information
    bResult = GetTokenInformation(hToken, TokenPrivileges, NULL, 0, &dwSize);
    if (!bResult && GetLastError() != ERROR_INSUFFICIENT_BUFFER) {
        printf("Error retrieving token size (%d)\n", GetLastError());
        CloseHandle(hToken);
        return;
    }

    // Allocate memory for privileges information
    pPrivileges = (PTOKEN_PRIVILEGES)malloc(dwSize);
    if (!pPrivileges) {
        printf("Memory allocation error\n");
        CloseHandle(hToken);
        return;
    }

    // Get privileges information
    bResult = GetTokenInformation(hToken, TokenPrivileges, pPrivileges, dwSize, &dwSize);
    if (!bResult) {
        printf("Error retrieving privileges information (%d)\n", GetLastError());
        free(pPrivileges);
        CloseHandle(hToken);
        return;
    }

    // Iterate through privileges and display them
    for (DWORD i = 0; i < pPrivileges->PrivilegeCount; ++i) {
        LUID_AND_ATTRIBUTES laa = pPrivileges->Privileges[i];
        DWORD dwNameSize = 0;
        wchar_t *szName;

        // Get the size of privilege name
        LookupPrivilegeNameW(NULL, &laa.Luid, NULL, &dwNameSize);

        // Allocate memory for privilege name
        szName = (wchar_t *)malloc(dwNameSize * sizeof(wchar_t));
        if (!szName) {
            printf("Memory allocation error\n");
            free(pPrivileges);
            CloseHandle(hToken);
            return;
        }

        // Get privilege name
        if (LookupPrivilegeNameW(NULL, &laa.Luid, szName, &dwNameSize)) {
            printf("Privilege: %ls\n", szName);
        }

        free(szName);
    }

    free(pPrivileges);
    CloseHandle(hToken);
}

int main() {
    CheckPrivileges();
    return 0;
}
