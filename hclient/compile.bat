@echo off

REM Get the script path using %~dp0 (where the script is located)
set "scriptPath=%~dp0"

REM Build full paths to the include and lib directories
set "includePath=%scriptPath%include"
set "libPath=%scriptPath%lib"

REM Compile the program
cl /Fe:httptest.exe /I"%includePath%" /std:c++17 /EHsc user32.lib gdi32.lib httptest.cpp screencapture.cpp fileutils.cpp /link /LIBPATH:"%libPath%" libcurl.lib zlib.lib user32.lib gdi32.lib Ws2_32.lib Crypt32.lib Advapi32.lib

REM Check the compilation success
IF %ERRORLEVEL% NEQ 0 (
    echo Compilation error.
) ELSE (
    echo Compilation successful.
)

REM Pause to see the results
pause
