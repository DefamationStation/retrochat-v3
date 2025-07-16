# Build script for RetroChat v3
# Run this script to build both the executable and pip package locally

Write-Host "🚀 Building RetroChat v3..." -ForegroundColor Green

# Clean previous builds
Write-Host "🧹 Cleaning previous builds..." -ForegroundColor Yellow
if (Test-Path "dist") { Remove-Item -Recurse -Force "dist" }
if (Test-Path "build") { Remove-Item -Recurse -Force "build" }
if (Test-Path "*.egg-info") { Remove-Item -Recurse -Force "*.egg-info" }

# Install dependencies
Write-Host "📦 Installing build dependencies..." -ForegroundColor Yellow
pip install pyinstaller build wheel

# Build executable with PyInstaller
Write-Host "🔨 Creating executable..." -ForegroundColor Yellow
pyinstaller retrochat.spec --clean --noconfirm

if (Test-Path "dist\rchat.exe") {
    Write-Host "✅ Executable created successfully: dist\rchat.exe" -ForegroundColor Green
} else {
    Write-Host "❌ Failed to create executable" -ForegroundColor Red
    exit 1
}

# Test the executable
Write-Host "🧪 Testing executable..." -ForegroundColor Yellow
try {
    & ".\dist\rchat.exe" --help 2>&1 | Out-Null
    if ($LASTEXITCODE -eq 0) {
        Write-Host "✅ Executable test passed" -ForegroundColor Green
    } else {
        Write-Host "⚠️  Executable created but may have issues" -ForegroundColor Yellow
    }
} catch {
    Write-Host "⚠️  Could not test executable (this is normal)" -ForegroundColor Yellow
}

# Build Python package
Write-Host "📦 Creating Python package..." -ForegroundColor Yellow
$env:PACKAGE_VERSION = "3.0.0-dev"
python -m build

if (Test-Path "dist\*.whl") {
    Write-Host "✅ Python package created successfully" -ForegroundColor Green
} else {
    Write-Host "❌ Failed to create Python package" -ForegroundColor Red
    exit 1
}

# Summary
Write-Host ""
Write-Host "🎉 Build complete!" -ForegroundColor Green
Write-Host "📁 Built files:" -ForegroundColor Cyan
Get-ChildItem "dist" | ForEach-Object {
    Write-Host "   - $($_.Name)" -ForegroundColor White
}

Write-Host ""
Write-Host "🚀 Usage:" -ForegroundColor Cyan
Write-Host "   Executable: .\dist\rchat.exe" -ForegroundColor White
Write-Host "   Pip install: pip install .\dist\retrochat_cli-3.0.0.dev0-py3-none-any.whl" -ForegroundColor White
Write-Host "   Then run: rchat" -ForegroundColor White
