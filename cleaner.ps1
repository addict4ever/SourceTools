# Liste des navigateurs à traiter
$browserNames = @("Chrome", "Firefox", "Edge", "Opera", "Brave", "Safari")

# Liste des fichiers à supprimer pour tous les navigateurs basés sur Chromium
$filesToDelete = @(
    "Top Sites",
    "Top Sites-journal",
    "Shortcuts",
    "Shortcuts-journal",
    "Visited Links",
    "History",
    "History-journal",
    "Web Data",
    "Web Data-journal",
    "Preferences",
    "Login Data",
    "Login Data-journal",
    "WebStorage",
    "Favicons",
    "IndexedDB",
    "Cache",
    "GPUCache",
    "Code Cache",
    "Local Storage",
    "Service Worker"
)

# Fonction pour supprimer les éléments si le chemin existe et gérer les erreurs
function Remove-PathIfExist {
    param ($path)
    if (Test-Path $path) {
        try {
            Remove-Item -Path $path -Recurse -Force -ErrorAction Stop
            Write-Host "Deleted: $path" -ForegroundColor Green
        }
        catch {
            Write-Host "Failed to delete: $path" -ForegroundColor Red
            Write-Host "Error details: $_" -ForegroundColor Red
        }
    } else {
        Write-Host "Path not found: $path" -ForegroundColor Yellow
    }
}

# Fonction pour obtenir les profils d'un navigateur donné
function Get-BrowserProfiles {
    param (
        [string]$browserDataPath
    )
    if (Test-Path $browserDataPath) {
        return Get-ChildItem -Path $browserDataPath -Directory | Where-Object { $_.Name -match '^Profile' -or $_.Name -eq 'Default' }
    }
    return @()
}

# Fonction pour supprimer les fichiers de données d'un navigateur
function Remove-BrowserData {
    param (
        [string]$browserPath,
        [array]$files
    )
    foreach ($file in $files) {
        $filePath = Join-Path $browserPath $file
        Remove-PathIfExist $filePath
    }
}

# Fonction pour détecter et nettoyer les navigateurs Chromium
function Clean-ChromiumBrowser {
    param (
        [string]$browserName,
        [string]$userDataPath
    )
    
    Write-Host "Cleaning $browserName user data..." -ForegroundColor Cyan

    if (Test-Path $userDataPath) {
        # Recherche de tous les profils (Default, Profile1, Profile2, etc.)
        $profiles = Get-BrowserProfiles -browserDataPath $userDataPath
        if ($profiles.Count -eq 0) {
            Write-Host "No profiles found for $browserName." -ForegroundColor Yellow
        }
        
        # Suppression des fichiers de données pour chaque profil
        foreach ($profile in $profiles) {
            Write-Host "Cleaning data for profile: $($profile.Name) in $browserName" -ForegroundColor Cyan
            Remove-BrowserData -browserPath $profile.FullName -files $filesToDelete
        }
    } else {
        Write-Host "Path not found: $userDataPath" -ForegroundColor Yellow
    }
}

# Fonction pour nettoyer Firefox et Safari (pas basés sur Chromium)
function Clean-OtherBrowsers {
    param (
        [string]$browserName,
        [string]$cachePath,
        [string]$cookiePath,
        [string]$historyPath
    )

    Write-Host "Cleaning $browserName user data..." -ForegroundColor Cyan

    # Suppression du cache, cookies et historique pour Firefox et Safari
    Remove-PathIfExist $cachePath
    Remove-PathIfExist $cookiePath
    Remove-PathIfExist $historyPath
}

# Fonction pour exécuter un script PowerShell avec -ExecutionPolicy Bypass
function Execute-PSWithBypass {
    param (
        [string]$scriptPath
    )
    Start-Process powershell.exe -ArgumentList "-ExecutionPolicy Bypass -File `"$scriptPath`"" -Wait
}

# Stop browser processes before deleting data
Write-Host "Stopping browser processes..." -ForegroundColor Cyan
Get-Process Chrome, msedge, firefox, opera, brave, safari -ErrorAction SilentlyContinue | Stop-Process -Force

# Suppression des traces de navigateurs
foreach ($browserName in $browserNames) {
    $userDataPath = ""
    $cachePath = ""
    $cookiePath = ""
    $historyPath = ""

    # Déterminer les chemins de cache, cookies, et historique en fonction du navigateur
    Switch ($browserName) {
        "Chrome" {
            $userDataPath = "$env:LOCALAPPDATA\Google\Chrome\User Data"
        }
        "Edge" {
            $userDataPath = "$env:LOCALAPPDATA\Microsoft\Edge\User Data"
        }
        "Brave" {
            $userDataPath = "$env:LOCALAPPDATA\BraveSoftware\Brave-Browser\User Data"
        }
        "Opera" {
            $userDataPath = "$env:APPDATA\Opera Software\Opera Stable"
        }
        "Firefox" {
            $cachePath = "$env:APPDATA\Mozilla\Firefox\Profiles\*.default\cache2\entries"
            $cookiePath = "$env:APPDATA\Mozilla\Firefox\Profiles\*.default\cookies.sqlite"
            $historyPath = "$env:APPDATA\Mozilla\Firefox\Profiles\*.default\places.sqlite"
        }
        "Safari" {
            $cachePath = "$env:LOCALAPPDATA\Apple Computer\Safari\Cache.db"
            $cookiePath = "$env:LOCALAPPDATA\Apple Computer\Safari\Cookies.db"
            $historyPath = "$env:LOCALAPPDATA\Apple Computer\Safari\History.db"
        }
    }

    # Si c'est un navigateur Chromium (Chrome, Edge, Brave, Opera), nettoyer les données utilisateur
    if ($browserName -in @("Chrome", "Edge", "Brave", "Opera")) {
        Clean-ChromiumBrowser -browserName $browserName -userDataPath $userDataPath
    } else {
        Clean-OtherBrowsers -browserName $browserName -cachePath $cachePath -cookiePath $cookiePath -historyPath $historyPath
    }
}

# Suppression des fichiers temporaires système et utilisateur
$TempPaths = @(
    "$env:Temp",              # Répertoire temporaire de l'utilisateur
    "$env:SystemRoot\Temp"     # Répertoire temporaire système
)

foreach ($TempPath in $TempPaths) {
    if (Test-Path $TempPath) {
        Write-Host "Cleaning temp folder: $TempPath" -ForegroundColor Cyan
        Get-ChildItem -Path $TempPath -Recurse -Force | ForEach-Object {
            try {
                Remove-Item $_.FullName -Force -Recurse -ErrorAction Stop
                Write-Host "Deleted: $($_.FullName)" -ForegroundColor Green
            }
            catch {
                Write-Host "Failed to delete: $($_.FullName)" -ForegroundColor Red
                Write-Host "Error details: $_" -ForegroundColor Red
            }
        }
    } else {
        Write-Host "Path not found: $TempPath" -ForegroundColor Yellow
    }
}

# Suppression des fichiers dans les dossiers Recent
$recentPaths = @(
    "$env:APPDATA\Microsoft\Windows\Recent\AutomaticDestinations\*",
    "$env:APPDATA\Microsoft\Windows\Recent\CustomDestinations\*",
    "$env:APPDATA\Microsoft\Windows\Recent\*"
)

foreach ($recentPath in $recentPaths) {
    Remove-PathIfExist $recentPath
}

# Suppression des fichiers spécifiques au système
$systemFilesToDelete = @(
    "$env:USERPROFILE\AppData\Local\Microsoft\Windows\Explorer\thumbcache_*.db",
    "$env:USERPROFILE\AppData\Local\Microsoft\Windows\Explorer\iconcache_*.db"
)

foreach ($filePath in $systemFilesToDelete) {
    Remove-PathIfExist $filePath
}

# Suppression des fichiers journaux et rapports d'erreur système
$logPaths = @(
    "C:\Windows\Logs",
    "C:\Windows\Memory.dmp",
    "C:\Windows\Minidump",
    "C:\ProgramData\Microsoft\Windows\WER\ReportArchive",
    "C:\ProgramData\Microsoft\Windows\WER\ReportQueue"
)

foreach ($logPath in $logPaths) {
    Remove-PathIfExist $logPath
}

# Suppression des fichiers Prefetch
Write-Host "Cleaning Prefetch files..." -ForegroundColor Cyan
Remove-PathIfExist "C:\Windows\Prefetch\*"

# Suppression des caches de polices
Write-Host "Cleaning FontCache files..." -ForegroundColor Cyan
Remove-PathIfExist "C:\Windows\ServiceProfiles\LocalService\AppData\Local\FontCache\*"

# Suppression des fichiers de sauvegarde des mises à jour Windows
Write-Host "Cleaning Windows Update files..." -ForegroundColor Cyan
dism /online /cleanup-image /startcomponentcleanup

# Suppression des points de restauration système (attention, cela supprime la possibilité de revenir en arrière)
Write-Host "Deleting system restore points..." -ForegroundColor Yellow
vssadmin delete shadows /for=C: /all /quiet

# Suppression des fichiers de crash d'applications
Write-Host "Cleaning crash dumps..." -ForegroundColor Cyan
Remove-PathIfExist "$env:USERPROFILE\AppData\Local\CrashDumps\"

# Suppression des historiques de Windows Defender
Write-Host "Cleaning Windows Defender history..." -ForegroundColor Cyan
Remove-Item "$env:ProgramData\Microsoft\Windows Defender\Scans\History" -Recurse -Force

# Redémarrer l'explorateur après suppression
Write-Host "Restarting explorer..." -ForegroundColor Cyan
Stop-Process -Name explorer -Force -ErrorAction SilentlyContinue
Start-Process explorer

Write-Host "Clean up completed!" -ForegroundColor Green
