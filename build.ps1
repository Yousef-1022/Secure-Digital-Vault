# Run venv
./run_venv.ps1
Set-Location Secure-Digital-Vault

# Build qrc file (Its using an older PyQt version)
pyrcc5 vault.qrc -o images_qrc.py
../qrc_fixer.ps1

# Move qrc file
Remove-Item "utils\images_qrc.py"
Move-Item "images_qrc.py" "utils\"

# Build
pyinstaller --onefile --noconsole --icon assets/logo.png --name Vault main.py

# Cleanup
Remove-Item "Vault.spec"
Remove-Item -Path "build" -Recurse -Force
Copy-Item "dist\Vault.exe" .
Remove-Item -Path "dist" -Recurse -Force
Set-Location ..
deactivate