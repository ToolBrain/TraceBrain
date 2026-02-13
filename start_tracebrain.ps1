Write-Host "STARTING TRACEBRAIN API"
Start-Process powershell "-NoExit", 
  "cd src; python -m uvicorn tracebrain.main:app --reload --port 8000"

Write-Host "STARTING WEB FRONTEND"
Start-Process powershell "-NoExit", 
  "cd web; npm run dev"

Start-Sleep -Seconds 3

Write-Host "OPENING IN CHROME"
Start-Process "chrome.exe" "http://localhost:5173/"