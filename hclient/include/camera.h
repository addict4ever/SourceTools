#pragma once

#include <Windows.h>
#include <dshow.h>
#include <string>
#include <chrono>

std::wstring GetHostName();
void detectCameras();
void recordVideo(int cameraIndex, std::chrono::seconds recordDuration);
