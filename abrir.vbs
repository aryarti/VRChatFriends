Dim sh, fso, base, py, scr
Set sh = CreateObject("WScript.Shell")
Set fso = CreateObject("Scripting.FileSystemObject")
base = fso.GetParentFolderName(WScript.ScriptFullName)
py = base & "\.venv\Scripts\pythonw.exe"
scr = base & "\ui_qml\main.py"
sh.CurrentDirectory = base
sh.Run """" & py & """ """ & scr & """", 0, False
