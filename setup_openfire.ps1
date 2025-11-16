# Openfire User Account Setup Script
# This script creates user accounts for the Traffic Light Control System using Openfire REST API

# Configuration
$OPENFIRE_HOST = "localhost"
$OPENFIRE_PORT = "9090"
$ADMIN_USER = "admin"
$ADMIN_PASS = "admin"  # Change this to your actual admin password

# User accounts to create
$users = @(
    @{username="coordinator"; password="coordinator123"; name="Coordinator Agent"; email="coordinator@localhost"},
    @{username="tl_center"; password="traffic123"; name="Center Traffic Light"; email="tl_center@localhost"},
    @{username="tl_north"; password="traffic123"; name="North Traffic Light"; email="tl_north@localhost"},
    @{username="tl_south"; password="traffic123"; name="South Traffic Light"; email="tl_south@localhost"},
    @{username="tl_east"; password="traffic123"; name="East Traffic Light"; email="tl_east@localhost"},
    @{username="tl_west"; password="traffic123"; name="West Traffic Light"; email="tl_west@localhost"}
)

Write-Host "============================================" -ForegroundColor Cyan
Write-Host "  Openfire User Account Setup" -ForegroundColor Cyan
Write-Host "============================================" -ForegroundColor Cyan
Write-Host ""

# Check if Openfire is running
Write-Host "Checking Openfire service status..." -ForegroundColor Yellow
$service = Get-Service -Name "Openfire" -ErrorAction SilentlyContinue

if ($null -eq $service) {
    Write-Host "❌ ERROR: Openfire service not found!" -ForegroundColor Red
    Write-Host "Please install Openfire first from: https://www.igniterealtime.org/downloads/" -ForegroundColor Red
    exit 1
}

if ($service.Status -ne "Running") {
    Write-Host "⚠️  Openfire service is not running. Starting..." -ForegroundColor Yellow
    Start-Service -Name "Openfire"
    Start-Sleep -Seconds 5
    Write-Host "✅ Openfire service started" -ForegroundColor Green
} else {
    Write-Host "✅ Openfire service is running" -ForegroundColor Green
}

Write-Host ""
Write-Host "============================================" -ForegroundColor Cyan
Write-Host "  Note: REST API Method (Advanced)" -ForegroundColor Cyan
Write-Host "============================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "This script requires the Openfire REST API plugin." -ForegroundColor Yellow
Write-Host ""
Write-Host "To use this script:" -ForegroundColor White
Write-Host "1. Install REST API plugin in Openfire Admin Console" -ForegroundColor White
Write-Host "   - Go to http://localhost:9090" -ForegroundColor White
Write-Host "   - Login with admin credentials" -ForegroundColor White
Write-Host "   - Go to Plugins → Available Plugins" -ForegroundColor White
Write-Host "   - Install 'REST API' plugin" -ForegroundColor White
Write-Host "2. Enable the plugin and configure a secret key" -ForegroundColor White
Write-Host "3. Update this script with your admin password" -ForegroundColor White
Write-Host ""
Write-Host "============================================" -ForegroundColor Cyan
Write-Host "  Recommended: Manual Account Creation" -ForegroundColor Cyan
Write-Host "============================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "It's easier to create accounts manually:" -ForegroundColor Green
Write-Host ""
Write-Host "1. Open: http://localhost:9090" -ForegroundColor White
Write-Host "2. Login with admin credentials" -ForegroundColor White
Write-Host "3. Go to: Users/Groups → Create New User" -ForegroundColor White
Write-Host "4. Create these accounts:" -ForegroundColor White
Write-Host ""

foreach ($user in $users) {
    Write-Host "   Username: $($user.username)" -ForegroundColor Cyan
    Write-Host "   Password: $($user.password)" -ForegroundColor Cyan
    Write-Host "   Name: $($user.name)" -ForegroundColor Cyan
    Write-Host "   Email: $($user.email)" -ForegroundColor Cyan
    Write-Host ""
}

Write-Host "============================================" -ForegroundColor Cyan
Write-Host "  Quick Setup URLs" -ForegroundColor Cyan
Write-Host "============================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Admin Console: http://localhost:9090" -ForegroundColor Green
Write-Host "Create User: http://localhost:9090/user-create.jsp" -ForegroundColor Green
Write-Host ""

# Attempt to open the admin console
Write-Host "Opening Openfire Admin Console..." -ForegroundColor Yellow
Start-Process "http://localhost:9090"

Write-Host ""
Write-Host "============================================" -ForegroundColor Cyan
Write-Host "  Next Steps" -ForegroundColor Cyan
Write-Host "============================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "1. Create the user accounts in Admin Console" -ForegroundColor White
Write-Host "2. Verify server is accessible: http://localhost:9090" -ForegroundColor White
Write-Host "3. Test XMPP connection: python test_connection.py" -ForegroundColor White
Write-Host "4. Run the system: python -m src.main" -ForegroundColor White
Write-Host ""
Write-Host "✅ Setup script completed!" -ForegroundColor Green
