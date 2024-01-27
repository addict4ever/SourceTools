// ScreenCapture.cpp

#include "ScreenCapture.h"
#include <iomanip> // Assurez-vous que cette ligne est présente

ScreenCapture::ScreenCapture() : captureCount(1) {}

BOOL CALLBACK ScreenCapture::MonitorEnumProc(HMONITOR hMonitor, HDC hdcMonitor, LPRECT lprcMonitor, LPARAM dwData) {
    ScreenCapture* capture = reinterpret_cast<ScreenCapture*>(dwData);

    // Capture the specific monitor
    capture->CaptureScreen(hMonitor);

    return TRUE; // Continue enumeration
}

void ScreenCapture::CaptureScreensAndSave() {
    EnumDisplayMonitors(NULL, NULL, MonitorEnumProc, reinterpret_cast<LPARAM>(this));

    std::cout << "Screen capture completed successfully." << std::endl;
}

void ScreenCapture::CaptureScreen(HMONITOR hMonitor) {
    MONITORINFOEX mi;
    mi.cbSize = sizeof(MONITORINFOEX);
    if (GetMonitorInfo(hMonitor, &mi)) {
        int width = mi.rcMonitor.right - mi.rcMonitor.left;
        int height = mi.rcMonitor.bottom - mi.rcMonitor.top;

        HDC hdcScreen = CreateDC(mi.szDevice, NULL, NULL, NULL);
        if (hdcScreen != NULL) {
            HDC hdcMem = CreateCompatibleDC(hdcScreen);
            HBITMAP hBitmap = CreateCompatibleBitmap(hdcScreen, width, height);
            HGDIOBJ oldBitmap = SelectObject(hdcMem, hBitmap);
            BitBlt(hdcMem, 0, 0, width, height, hdcScreen, 0, 0, SRCCOPY);
            SYSTEMTIME st;
            GetLocalTime(&st);
            char computerName[MAX_COMPUTERNAME_LENGTH + 1];
            DWORD size = sizeof(computerName);
            GetComputerName(computerName, &size);

            std::stringstream fileNameStream;
            fileNameStream << "monitor_capture_" << computerName << "_"
                           << st.wYear << std::setw(2) << std::setfill('0') << st.wMonth << std::setw(2) << st.wDay << "_"
                           << st.wHour << std::setw(2) << st.wMinute << std::setw(2) << st.wSecond
                           << "_screen" << captureCount << ".bmp";
            std::string fileName = fileNameStream.str();

            SaveCaptureToFile(hdcMem, hBitmap, width, height, fileName);
            SelectObject(hdcMem, oldBitmap);
            DeleteObject(hBitmap);
            DeleteDC(hdcMem);
            DeleteDC(hdcScreen);

            captureCount++;
        }
    }
}

void ScreenCapture::SaveCaptureToFile(HDC hdcMem, HBITMAP hBitmap, int width, int height, const std::string& fileName) {
    BITMAPINFOHEADER bi{};
    bi.biSize = sizeof(BITMAPINFOHEADER);
    bi.biWidth = width;
    bi.biHeight = -height; // Negative height to ensure correct orientation
    bi.biPlanes = 1;
    bi.biBitCount = 24;
    bi.biCompression = BI_RGB;

    BITMAPFILEHEADER bmfh{};
    bmfh.bfType = static_cast<WORD>('B' + ('M' << 8));
    bmfh.bfOffBits = sizeof(BITMAPFILEHEADER) + sizeof(BITMAPINFOHEADER);
    bmfh.bfSize = bmfh.bfOffBits + bi.biSizeImage;
    bmfh.bfReserved1 = 0;
    bmfh.bfReserved2 = 0;

    std::ofstream file(fileName, std::ios::binary);
    if (file.is_open()) {
        file.write(reinterpret_cast<const char*>(&bmfh), sizeof(BITMAPFILEHEADER));
        file.write(reinterpret_cast<const char*>(&bi), sizeof(BITMAPINFOHEADER));
        std::vector<BYTE> bits(width * height * 3);
        GetDIBits(hdcMem, hBitmap, 0, height, bits.data(), reinterpret_cast<BITMAPINFO*>(&bi), DIB_RGB_COLORS);
        file.write(reinterpret_cast<const char*>(bits.data()), bits.size());
        file.close();       
    } else {
        std::cerr << "Error: Unable to open the output file." << std::endl;
    }
}
