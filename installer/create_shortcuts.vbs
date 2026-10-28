' VBScript para crear accesos directos dinámicos en Windows
Option Explicit
Dim objShell, strDesktop, strPrograms, objShortcut, strInstallDir

Set objShell = CreateObject("WScript.Shell")
strDesktop = objShell.SpecialFolders("Desktop")
strPrograms = objShell.SpecialFolders("Programs") & "\Antigravity Voice"

Dim objFSO: Set objFSO = CreateObject("Scripting.FileSystemObject")
If Not objFSO.FolderExists(strPrograms) Then
    objFSO.CreateFolder(strPrograms)
End If

strInstallDir = objShell.ExpandEnvironmentStrings("%LOCALAPPDATA%\AntigravityVoice")
If Not objFSO.FolderExists(strInstallDir) Then
    strInstallDir = objFSO.GetParentFolderName(objFSO.GetParentFolderName(WScript.ScriptFullName))
End If

' 1. Acceso directo Widget Flotante en Escritorio
Set objShortcut = objShell.CreateShortcut(strDesktop & "\Antigravity Voice Widget.lnk")
If objFSO.FileExists(strInstallDir & "\bin\AntigravityVoiceWidget.exe") Then
    objShortcut.TargetPath = strInstallDir & "\bin\AntigravityVoiceWidget.exe"
    objShortcut.WorkingDirectory = strInstallDir
Else
    objShortcut.TargetPath = strInstallDir & "\iniciar_widget.bat"
    objShortcut.WorkingDirectory = strInstallDir
End If
objShortcut.Description = "Control flotante para Antigravity Voice Assistant"
objShortcut.WindowStyle = 1
objShortcut.Save

' 2. Acceso directo en Menú Inicio: Widget
Set objShortcut = objShell.CreateShortcut(strPrograms & "\Antigravity Voice Widget.lnk")
If objFSO.FileExists(strInstallDir & "\bin\AntigravityVoiceWidget.exe") Then
    objShortcut.TargetPath = strInstallDir & "\bin\AntigravityVoiceWidget.exe"
    objShortcut.WorkingDirectory = strInstallDir
Else
    objShortcut.TargetPath = strInstallDir & "\iniciar_widget.bat"
    objShortcut.WorkingDirectory = strInstallDir
End If
objShortcut.Description = "Control flotante para Antigravity Voice Assistant"
objShortcut.Save

' 3. Acceso directo en Menú Inicio: Servicio en Segundo Plano
Set objShortcut = objShell.CreateShortcut(strPrograms & "\Iniciar Servicio de Voz.lnk")
If objFSO.FileExists(strInstallDir & "\bin\AntigravityVoiceService.exe") Then
    objShortcut.TargetPath = strInstallDir & "\bin\AntigravityVoiceService.exe"
    objShortcut.WorkingDirectory = strInstallDir
Else
    objShortcut.TargetPath = strInstallDir & "\iniciar_segundo_plano.vbs"
    objShortcut.WorkingDirectory = strInstallDir
End If
objShortcut.Description = "Iniciar Asistente y Narrador de Planes en segundo plano"
objShortcut.Save

' 4. Acceso directo en Menú Inicio: Detener Voz
Set objShortcut = objShell.CreateShortcut(strPrograms & "\Detener Voz.lnk")
objShortcut.TargetPath = strInstallDir & "\detener_voz.bat"
objShortcut.WorkingDirectory = strInstallDir
objShortcut.Description = "Detener reproductor de voz"
objShortcut.Save
