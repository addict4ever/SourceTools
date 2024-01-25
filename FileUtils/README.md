/*

Copyright (c) [2024] [F.B (Addict)]



Permission is hereby granted, free of charge, to any person obtaining a copy

of this software and associated documentation files (the "Software"), to deal

in the Software without restriction, including without limitation the rights

to use, copy, modify, merge, publish, distribute, sublicense, and/or sell

copies of the Software, and to permit persons to whom the Software is

furnished to do so, subject to the following conditions:



The above copyright notice and this permission notice shall be included in all

copies or substantial portions of the Software.

*/ 

cl /Fe:testtar.exe /I"C:\temp\vcpkg\installed\x86-windows\include" /EHsc /std:c++17 /I"C:\temp\vcpkg\scripts\buildsystems" /DCMAKE_TOOLCHAIN_FILE="C:\temp\vcpkg\scripts\buildsystems\vcpkg.cmake" user32.lib gdi32.lib testtar.cpp /link /LIBPATH:"C:\temp\vcpkg\installed\x86-windows\lib"
