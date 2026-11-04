Set-Location -Path $PSScriptRoot
$parts = Get-ChildItem -Filter 'blackcard-final.mp4.part-*' | Sort-Object Name
$out = [System.IO.File]::Create((Join-Path $PSScriptRoot 'blackcard-final.mp4'))
foreach ($p in $parts) { $b=[System.IO.File]::ReadAllBytes($p.FullName); $out.Write($b,0,$b.Length) }
$out.Close()
Write-Host ('DONE ' + (Get-Item 'blackcard-final.mp4').Length + ' bytes (expected 465439006)')
