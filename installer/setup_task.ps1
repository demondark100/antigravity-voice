param (
    [string]$InstallDir = "$env:LOCALAPPDATA\AntigravityVoice"
)

$TaskName = "AntigravityVoiceService"
$ExePath = Join-Path $InstallDir "bin\AntigravityVoiceService.exe"

if (-not (Test-Path $ExePath)) {
    $Pythonw = (Get-Command pythonw.exe -ErrorAction SilentlyContinue).Source
    if (-not $Pythonw) {
        $Pythonw = "$env:LOCALAPPDATA\Programs\Python\Python312\pythonw.exe"
    }
    $Action = New-ScheduledTaskAction -Execute $Pythonw -Argument "voice_reader.py" -WorkingDirectory $InstallDir
} else {
    $Action = New-ScheduledTaskAction -Execute $ExePath -WorkingDirectory $InstallDir
}

$Trigger = New-ScheduledTaskTrigger -AtLogOn -User $env:USERNAME
$Settings = New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries -ExecutionTimeLimit (New-TimeSpan -Days 365) -RestartCount 3 -RestartInterval (New-TimeSpan -Minutes 1)

try {
    Unregister-ScheduledTask -TaskName $TaskName -Confirm:$false -ErrorAction SilentlyContinue
    Register-ScheduledTask -TaskName $TaskName -Action $Action -Trigger $Trigger -Settings $Settings -Description "Antigravity Voice Assistant & Plan Narrator Background Daemon" | Out-Null
    Start-ScheduledTask -TaskName $TaskName -ErrorAction SilentlyContinue
    Write-Host "[+] Tarea programada '$TaskName' registrada e iniciada correctamente." -ForegroundColor Green
} catch {
    Write-Warning "[-] Error registrando la tarea programada: $_"
}
