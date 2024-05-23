$filePath = "images_qrc.py"

# QtCore must be import from PyQt6
$searchText = "from PyQt5"
$replaceText = "PyQt6"

$lines = Get-Content -Path $filePath
for ($i = 0; $i -lt $lines.Length; $i++) {
    if ($lines[$i] -match [regex]::Escape($searchText)) {
        $lines[$i] = $lines[$i] -replace "PyQt5", $replaceText
    }
}

$lines | Set-Content -Path $filePath
