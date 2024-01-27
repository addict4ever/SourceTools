// ScreenCapture.h

#ifndef SCREEN_CAPTURE_H
#define SCREEN_CAPTURE_H

#include <windows.h>
#include <iostream>
#include <fstream>
#include <vector>
#include <sstream>

class ScreenCapture {
public:
    ScreenCapture();

    void CaptureScreensAndSave();

private:
    int captureCount;

    static BOOL CALLBACK MonitorEnumProc(HMONITOR hMonitor, HDC hdcMonitor, LPRECT lprcMonitor, LPARAM dwData);

    void CaptureScreen(HMONITOR hMonitor);

    void SaveCaptureToFile(HDC hdcMem, HBITMAP hBitmap, int width, int height, const std::string& fileName);
};

#endif // SCREEN_CAPTURE_H
