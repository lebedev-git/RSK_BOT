# Активируем виртуальное окружение
.\venv\Scripts\Activate.ps1

# Проверяем активацию
Write-Host "Виртуальное окружение активировано"
Write-Host "Python path: $(Get-Command python).Source" 