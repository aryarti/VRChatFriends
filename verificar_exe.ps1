# Verifica o executável v1.1: metadados, janelas e consumo medido.
# build de clone limpo (regra do projeto), nunca da pasta de trabalho
$exe = 'C:\build\VRChatFriends\dist\VRChat Friends\VRChat Friends.exe'
$pasta = 'C:\build\VRChatFriends\dist\VRChat Friends'

$f = Get-Item $exe
Write-Output ("exe: {0} MB" -f [math]::Round($f.Length / 1MB, 1))
$tam = (Get-ChildItem $pasta -Recurse -File | Measure-Object -Property Length -Sum).Sum
Write-Output ("pasta inteira: {0} MB" -f [math]::Round($tam / 1MB, 1))
Write-Output ("versao: " + $f.VersionInfo.FileVersion + " | produto: " + $f.VersionInfo.ProductName + " | desc: " + $f.VersionInfo.FileDescription)
Write-Output ("icone embutido: " + [bool]($f.VersionInfo.OriginalFilename))

$ps = Get-Process -Name 'VRChat Friends' -ErrorAction SilentlyContinue
if (-not $ps) { Write-Output 'app: NAO ESTA RODANDO'; exit }

foreach ($p in $ps) {
    $t0 = $p.TotalProcessorTime.TotalSeconds
    Start-Sleep -Seconds 5
    $p.Refresh()
    $t1 = $p.TotalProcessorTime.TotalSeconds
    $cpu = [math]::Round(($t1 - $t0) / 5 / [Environment]::ProcessorCount * 100, 2)
    Write-Output ("pid {0}: RAM {1} MB | threads {2} | CPU {3}% (5s) | titulo '{4}'" -f `
        $p.Id, [math]::Round($p.WorkingSet64 / 1MB, 1), $p.Threads.Count, $cpu, $p.MainWindowTitle)
}
