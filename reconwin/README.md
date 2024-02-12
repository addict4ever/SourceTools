/* Copyright (c) [2024] [F.B (Addict)]

Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated documentation files (the "Software"), to deal in the Software without restriction, including without limitation the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, and to permit persons to whom the Software is furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all copies or substantial portions of the Software. */

DESCRIPTION:

Detect Basic System Info With Inside Windows Command 

USAGE :



COMPILE : 

cl /Fe:reconwin.exe /I"C:\temp\hclient\include" /std:c++17 /EHsc user32.lib gdi32.lib reconwin.cpp main.cpp /link /LIBPATH:"C:\temp\hclient\lib" libcurl.lib zlib.lib user32.lib gdi32.lib Ws2_32.lib Advapi32.lib Netapi32.lib
