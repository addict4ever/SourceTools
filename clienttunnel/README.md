/* Copyright (c) [2024] [F.B (Addict)]

Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated documentation files (the "Software"), to deal in the Software without restriction, including without limitation the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, and to permit persons to whom the Software is furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all copies or substantial portions of the Software. */

cl /Fe:stun.exe /I"C:\temp\vcpkg\installed\x86-windows-static\include" /std:c++latest /EHsc user32.lib gdi32.lib libcurl.lib ctun.cpp main.cpp /link /LIBPATH:"C:\temp\vcpkg\installed\x86-windows-static\lib" ws2_32.lib
