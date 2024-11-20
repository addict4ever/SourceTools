# Action de la tâche : exécuter PowerShell avec le script cleaner.ps1
$TaskAction = New-ScheduledTaskAction -Execute "powershell.exe" -Argument "-ExecutionPolicy Bypass -WindowStyle Hidden -File C:\Windows\System32\cleaner.ps1"

# Déclencheur de la tâche : tous les jours à 15h00
$TaskTriggerTime = New-ScheduledTaskTrigger -Daily -At "3:00PM"

# Déclencheur de la tâche : au démarrage de la session utilisateur
$TaskTriggerSessionStart = New-ScheduledTaskTrigger -AtStartup

# Paramètres de la tâche : la tâche s'exécutera pour tous les utilisateurs, avec des privilèges élevés
$TaskPrincipal = New-ScheduledTaskPrincipal -UserId "Everyone" -LogonType ServiceAccount

# Créer la tâche planifiée
Register-ScheduledTask -Action $TaskAction -Trigger $TaskTriggerTime -TaskName "CleanerScript" -Description "Exe" -RunLevel Highest
