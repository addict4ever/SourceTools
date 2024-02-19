#include <windows.h>
#include <iostream>

void encode(LPCSTR inFilename, LPCSTR outFilename, const char* key)
{
    char buf[4096];
    HANDLE inFile = CreateFile(inFilename, GENERIC_READ, 0, NULL, OPEN_EXISTING, FILE_ATTRIBUTE_NORMAL, NULL);
    if (inFile == INVALID_HANDLE_VALUE) {
        std::cerr << "Error opening the input file." << std::endl;
        return;
    }

    int size = GetFileSize(inFile, NULL);
    if (size == INVALID_FILE_SIZE) {
        std::cerr << "Error getting file size." << std::endl;
        CloseHandle(inFile);
        return;
    }

    DWORD bytesRead = 0;
    if (!ReadFile(inFile, buf, size, &bytesRead, NULL)) {
        std::cerr << "Error reading the input file." << std::endl;
        CloseHandle(inFile);
        return;
    }

    CloseHandle(inFile);

    for (int i = 0; i < size; i++) {
        buf[i] ^= key[i % strlen(key)];
    }

    HANDLE outFile = CreateFile(outFilename, GENERIC_WRITE, 0, NULL, CREATE_ALWAYS, 0, NULL);
    if (outFile == INVALID_HANDLE_VALUE) {
        std::cerr << "Error creating the output file." << std::endl;
        return;
    }

    DWORD bytesWrite = 0;
    if (!WriteFile(outFile, buf, size, &bytesWrite, NULL)) {
        std::cerr << "Error writing to the output file." << std::endl;
        CloseHandle(outFile);
        return;
    }

    CloseHandle(outFile);
}

int main(int argc, char** argv) {
    if (argc != 4) {
        std::cout << "Usage: " << argv[0] << " <input_file> <output_file> <key>" << std::endl;
        return 1;
    }

    encode(argv[1], argv[2], argv[3]);

    return 0;
}
