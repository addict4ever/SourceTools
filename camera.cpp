#include <opencv2/opencv.hpp>
#include <iostream>
#include <chrono>
#include <thread>
#include <ctime>

int main()
{
    // Open the default camera
    cv::VideoCapture cap(0);

    if (!cap.isOpened())
    {
        std::cout << "Failed to open camera" << std::endl;
        return 1;
    }

    // Set the resolution of the capture
    cap.set(cv::CAP_PROP_FRAME_WIDTH, 640);
    cap.set(cv::CAP_PROP_FRAME_HEIGHT, 480);

    // Wait for 2 seconds
    std::this_thread::sleep_for(std::chrono::seconds(2));

    // Get the current time
    std::time_t now = std::time(nullptr);
    std::tm tm = *std::localtime(&now);

    // Format the time as a string
    char filename[256];
    std::strftime(filename, sizeof(filename), "%Y-%m-%d_%H-%M-%S.jpg", &tm);

    // Capture a single frame
    cv::Mat frame;
    cap >> frame;

    // Save the frame to a JPEG file with maximum quality
    std::vector<int> compression_params;
    compression_params.push_back(cv::IMWRITE_JPEG_QUALITY);
    compression_params.push_back(100);
    cv::imwrite(filename, frame, compression_params);

    // Cleanup
    cap.release();

    return 0;
}
