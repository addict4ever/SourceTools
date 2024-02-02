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

Description :

The script leverages DirectShow, a multimedia framework on Windows, to identify connected cameras, presenting a list of their names. It subsequently records video from a selected camera, saving the file with the hostname and timestamp. Users can input their preferred recording duration.


cl /Fe:camera.exe /std:c++17 /EHsc user32.lib gdi32.lib camera.cpp main.cpp  /link user32.lib gdi32.lib Ws2_32.lib Crypt32.lib Advapi32.lib ole32.lib strmiids.lib oleaut32.lib
