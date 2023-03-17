#include <Windows.h>
#include <stdio.h>

int main()
{
    DWORD dwSize, dwIndex;
    TCHAR szName[MAX_PATH];
    HKEY hKey;

    RegOpenKeyEx(HKEY_LOCAL_MACHINE, TEXT("SYSTEM\\CurrentControlSet\\Services"), 0, KEY_READ, &hKey);

    for (dwIndex = 0; ; ++dwIndex)
    {
        dwSize = MAX_PATH;
        if (RegEnumKeyEx(hKey, dwIndex, szName, &dwSize, NULL, NULL, NULL, NULL) == ERROR_SUCCESS)
        {
            HKEY hSubKey;
            TCHAR szSubKey[MAX_PATH];
            snprintf(szSubKey, MAX_PATH, TEXT("SYSTEM\\CurrentControlSet\\Services\\%s"), szName);

            if (RegOpenKeyEx(HKEY_LOCAL_MACHINE, szSubKey, 0, KEY_READ, &hSubKey) == ERROR_SUCCESS)
            {
                TCHAR szDescription[MAX_PATH];
                TCHAR szObjectName[MAX_PATH];
                DWORD dwStart, dwType, dwSize;

                dwSize = sizeof(szDescription);
                if (RegQueryValueEx(hSubKey, TEXT("Description"), NULL, &dwType, (LPBYTE)szDescription, &dwSize) != ERROR_SUCCESS)
                {
                    szDescription[0] = '\0';
                }

                dwSize = sizeof(szObjectName);
                if (RegQueryValueEx(hSubKey, TEXT("ObjectName"), NULL, &dwType, (LPBYTE)szObjectName, &dwSize) != ERROR_SUCCESS)
                {
                    szObjectName[0] = '\0';
                }

                dwSize = sizeof(dwStart);
                if (RegQueryValueEx(hSubKey, TEXT("Start"), NULL, &dwType, (LPBYTE)&dwStart, &dwSize) == ERROR_SUCCESS && dwType == REG_DWORD)
                {
                    const char* pszStatus = (dwStart == 0x4) ? "\033[37mDisabled\033[0m" : "\033[31mActive\033[0m";
                    const char* pszStartType = "\033[32mUnknown\033[0m";
                    switch (dwStart)
                    {
                        case 0x0: pszStartType = "\033[32mBoot\033[0m"; break;
                        case 0x1: pszStartType = "\033[32mSystem\033[0m"; break;
                        case 0x2: pszStartType = "\033[32mAutomatic\033[0m"; break;
                        case 0x3: pszStartType = "\033[32mManual\033[0m"; break;
                    }

                    printf("\033[33m%s\033[0m \033[35m%s\033[0m \033[31m%s\033[0m \033[37m%s\033[0m \033[32m%s\033[0m\n", szName, szDescription, pszStatus, szObjectName, pszStartType);
                }
                else
                {
                    printf("\033[33m%s\033[0m \033[35m%s\033[0m \033[31mUnknown\033[0m\n", szName, szDescription);
                }

                RegCloseKey(hSubKey);
            }
        }
        else
       

        {
            break;
        }
    }

    RegCloseKey(hKey);

    return 0;
}
