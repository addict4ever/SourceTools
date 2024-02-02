#include <Windows.h>
#include <dshow.h>
#include <iostream>
#include <chrono>
#include <thread>
#include <iomanip>

std::wstring GetHostName() {
    wchar_t buffer[MAX_COMPUTERNAME_LENGTH + 1];
    DWORD size = sizeof(buffer) / sizeof(buffer[0]);
    if (GetComputerNameW(buffer, &size)) {
        return buffer;
    }
    return L"UnknownHostName";
}

void detectCameras() {
    HRESULT hr = CoInitialize(NULL);
    if (FAILED(hr)) {
        std::cerr << "Error initializing COM." << std::endl;
        return;
    }

    ICreateDevEnum* deviceEnumerator = NULL;
    hr = CoCreateInstance(CLSID_SystemDeviceEnum, NULL, CLSCTX_INPROC_SERVER, IID_PPV_ARGS(&deviceEnumerator));
    if (FAILED(hr)) {
        std::cerr << "Error creating device enumerator instance." << std::endl;
        CoUninitialize();
        return;
    }

    IEnumMoniker* enumMoniker = NULL;
    hr = deviceEnumerator->CreateClassEnumerator(CLSID_VideoInputDeviceCategory, &enumMoniker, 0);
    if (hr != S_OK) {
        std::cerr << "No cameras found." << std::endl;
        deviceEnumerator->Release();
        CoUninitialize();
        return;
    }

    int index = 0;
    while (true) {
        IMoniker* moniker = NULL;
        if (enumMoniker->Next(1, &moniker, NULL) == S_OK) {
            IPropertyBag* propertyBag = NULL;
            hr = moniker->BindToStorage(0, 0, IID_PPV_ARGS(&propertyBag));
            if (SUCCEEDED(hr)) {
                VARIANT var;
                VariantInit(&var);

                hr = propertyBag->Read(L"FriendlyName", &var, 0);
                if (SUCCEEDED(hr)) {
                    wprintf(L"%d. Detected Camera: %s\n", index + 1, var.bstrVal);
                    ++index;
                    VariantClear(&var);
                } else {
                    std::cerr << "Error reading device name." << std::endl;
                }
                propertyBag->Release();
            } else {
                std::cerr << "Error binding to moniker storage." << std::endl;
            }
            moniker->Release();
        } else {
            break;
        }
    }

    enumMoniker->Release();
    deviceEnumerator->Release();
    CoUninitialize();
}

void recordVideo(int cameraIndex) {
    CoInitialize(NULL);

    ICreateDevEnum* deviceEnumerator = NULL;
    HRESULT hr = CoCreateInstance(CLSID_SystemDeviceEnum, NULL, CLSCTX_INPROC_SERVER, IID_PPV_ARGS(&deviceEnumerator));
    if (FAILED(hr)) {
        std::cerr << "Error creating device enumerator instance." << std::endl;
        return;
    }

    IEnumMoniker* enumMoniker = NULL;
    hr = deviceEnumerator->CreateClassEnumerator(CLSID_VideoInputDeviceCategory, &enumMoniker, 0);
    if (hr == S_OK) {
        int index = 0;

        while (true) {
            IMoniker* moniker = NULL;
            if (enumMoniker->Next(1, &moniker, NULL) == S_OK) {
                if (index == cameraIndex - 1) {
                    IGraphBuilder* graphBuilder = NULL;
                    hr = CoCreateInstance(CLSID_FilterGraph, NULL, CLSCTX_INPROC_SERVER, IID_IGraphBuilder, (void**)&graphBuilder);
                    if (SUCCEEDED(hr)) {
                        IBaseFilter* captureFilter = NULL;
                        hr = moniker->BindToObject(0, 0, IID_IBaseFilter, (void**)&captureFilter);
                        if (SUCCEEDED(hr)) {
                            hr = graphBuilder->AddFilter(captureFilter, L"Capture Filter");
                            if (SUCCEEDED(hr)) {
                                ICaptureGraphBuilder2* captureGraphBuilder = NULL;
                                hr = CoCreateInstance(CLSID_CaptureGraphBuilder2, NULL, CLSCTX_INPROC_SERVER, IID_ICaptureGraphBuilder2, (void**)&captureGraphBuilder);
                                if (SUCCEEDED(hr)) {
                                    hr = captureGraphBuilder->SetFiltergraph(graphBuilder);
                                    if (SUCCEEDED(hr)) {
                                        IBaseFilter* aviMuxFilter = NULL;
                                        hr = CoCreateInstance(CLSID_AviDest, NULL, CLSCTX_INPROC_SERVER, IID_IBaseFilter, (void**)&aviMuxFilter);
                                        if (SUCCEEDED(hr)) {
                                            hr = graphBuilder->AddFilter(aviMuxFilter, L"AVI Mux Filter");
                                            if (SUCCEEDED(hr)) {
                                                auto now = std::chrono::system_clock::now();
                                                auto in_time_t = std::chrono::system_clock::to_time_t(now);
                                                std::tm timeinfo;
                                                localtime_s(&timeinfo, &in_time_t);
                                                char buffer[80];
                                                strftime(buffer, sizeof(buffer), "%Y%m%d_%H%M%S", &timeinfo);
                                                std::wstring filename = GetHostName() + L"_" + std::wstring(buffer, buffer + strlen(buffer));

                                                std::wstring fullFilePath = L".\\" + filename + L".avi";

                                                hr = captureGraphBuilder->SetOutputFileName(&MEDIASUBTYPE_Avi, fullFilePath.c_str(), &aviMuxFilter, NULL);
                                                if (SUCCEEDED(hr)) {
                                                    hr = captureGraphBuilder->RenderStream(NULL, NULL, captureFilter, NULL, aviMuxFilter);
                                                    if (SUCCEEDED(hr)) {
                                                        IMediaControl* mediaControl = NULL;
                                                        hr = graphBuilder->QueryInterface(IID_IMediaControl, (void**)&mediaControl);
                                                        if (SUCCEEDED(hr)) {
                                                            hr = mediaControl->Run();
                                                            if (SUCCEEDED(hr)) {
                                                                std::this_thread::sleep_for(std::chrono::seconds(5));
                                                            }
                                                            mediaControl->Release();
                                                        }
                                                    }
                                                }
                                            }
                                            aviMuxFilter->Release();
                                        }
                                    }
                                    captureGraphBuilder->Release();
                                }
                            }
                            captureFilter->Release();
                        }
                    }
                    graphBuilder->Release();
                }
                moniker->Release();
                ++index;
            } else {
                break;
            }
        }

        enumMoniker->Release();
    }

    deviceEnumerator->Release();
    CoUninitialize();
}

int main() {
    detectCameras();

    std::cout << "Choose the camera number you want to record: ";
    int cameraIndex;
    std::cin >> cameraIndex;

    recordVideo(cameraIndex);

    return 0;
}
