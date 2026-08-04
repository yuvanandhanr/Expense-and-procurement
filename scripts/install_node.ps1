$nodeDir = "c:\Yuvan\Proj\Expense and Procurement\.node"
if (!(Test-Path $nodeDir)) { 
    New-Item -ItemType Directory -Path $nodeDir 
}
$zipPath = "$nodeDir\node.zip"
Write-Host "Downloading Node.js..."
Invoke-WebRequest -Uri "https://nodejs.org/dist/v20.11.0/node-v20.11.0-win-x64.zip" -OutFile $zipPath
Write-Host "Extracting Node.js..."
Expand-Archive -Path $zipPath -DestinationPath $nodeDir -Force
Remove-Item $zipPath
Write-Host "Node.js extracted successfully!"
