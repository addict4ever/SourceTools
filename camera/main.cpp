#include "camera.h"
#include <iostream>
#include <chrono>

int main() {
    detectCameras();

    std::cout << "Choose the camera number you want to record: ";
    int cameraIndex;
    std::cin >> cameraIndex;

    std::cout << "Enter the recording duration in seconds: ";
    int recordingDuration;
    std::cin >> recordingDuration;

    recordVideo(cameraIndex, std::chrono::seconds(recordingDuration));

    return 0;
}
