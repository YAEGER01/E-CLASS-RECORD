# Email Configuration Setup Script
# Run this to set up your email credentials

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "E-Class Record - Email Setup" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

Write-Host "This script will help you configure email notifications for student registration approvals." -ForegroundColor Yellow
Write-Host ""

# Check if .env file exists
$envFile = ".env"
$envExists = Test-Path $envFile

if ($envExists) {
    Write-Host "Found existing .env file." -ForegroundColor Green
    $overwrite = Read-Host "Do you want to update email settings? (y/n)"
    if ($overwrite -ne 'y') {
        Write-Host "Setup cancelled." -ForegroundColor Yellow
        exit
    }
}

Write-Host ""
Write-Host "Email Configuration" -ForegroundColor Cyan
Write-Host "===================" -ForegroundColor Cyan
Write-Host ""

# Get SMTP configuration
Write-Host "Enter SMTP Server (default: smtp.gmail.com):" -ForegroundColor White
$smtpServer = Read-Host
if ([string]::IsNullOrWhiteSpace($smtpServer)) {
    $smtpServer = "smtp.gmail.com"
}

Write-Host "Enter SMTP Port (default: 587):" -ForegroundColor White
$smtpPort = Read-Host
if ([string]::IsNullOrWhiteSpace($smtpPort)) {
    $smtpPort = "587"
}

Write-Host "Enter Sender Email Address:" -ForegroundColor White
$senderEmail = Read-Host

Write-Host "Enter Sender Email Password (for Gmail, use App Password):" -ForegroundColor White
$senderPassword = Read-Host -AsSecureString
$senderPasswordPlain = [Runtime.InteropServices.Marshal]::PtrToStringAuto([Runtime.InteropServices.Marshal]::SecureStringToBSTR($senderPassword))

Write-Host "Enter Sender Name (default: E-Class Record System - ISU Cauayan):" -ForegroundColor White
$senderName = Read-Host
if ([string]::IsNullOrWhiteSpace($senderName)) {
    $senderName = "E-Class Record System - ISU Cauayan"
}

# Create or update .env file
Write-Host ""
Write-Host "Saving configuration..." -ForegroundColor Yellow

$envContent = @"
# Email SMTP Configuration
SMTP_SERVER=$smtpServer
SMTP_PORT=$smtpPort
SENDER_EMAIL=$senderEmail
SENDER_PASSWORD=$senderPasswordPlain
SENDER_NAME=$senderName
"@

# If .env exists, read it and update only email settings
if ($envExists) {
    $existingContent = Get-Content $envFile -Raw
    
    # Remove existing email configuration
    $existingContent = $existingContent -replace "(?m)^# Email SMTP Configuration.*?(?=\r?\n\r?\n|\r?\n#|\z)", ""
    $existingContent = $existingContent -replace "(?m)^SMTP_SERVER=.*\r?\n", ""
    $existingContent = $existingContent -replace "(?m)^SMTP_PORT=.*\r?\n", ""
    $existingContent = $existingContent -replace "(?m)^SENDER_EMAIL=.*\r?\n", ""
    $existingContent = $existingContent -replace "(?m)^SENDER_PASSWORD=.*\r?\n", ""
    $existingContent = $existingContent -replace "(?m)^SENDER_NAME=.*\r?\n", ""
    
    # Add new email configuration
    $envContent = $existingContent.Trim() + "`r`n`r`n" + $envContent
}

$envContent | Out-File -FilePath $envFile -Encoding UTF8

Write-Host ""
Write-Host "========================================" -ForegroundColor Green
Write-Host "Email configuration saved successfully!" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Green
Write-Host ""

Write-Host "Configuration saved to: $envFile" -ForegroundColor Cyan
Write-Host ""

Write-Host "Next Steps:" -ForegroundColor Yellow
Write-Host "1. If using Gmail, make sure you've generated an App Password" -ForegroundColor White
Write-Host "   - Go to: https://myaccount.google.com/apppasswords" -ForegroundColor Gray
Write-Host "2. Update your application to load .env variables" -ForegroundColor White
Write-Host "3. Test email by approving/rejecting a student registration" -ForegroundColor White
Write-Host ""

Write-Host "Gmail App Password Setup:" -ForegroundColor Cyan
Write-Host "1. Enable 2-Factor Authentication on your Google Account" -ForegroundColor White
Write-Host "2. Go to Security > App passwords" -ForegroundColor White
Write-Host "3. Select 'Mail' and 'Windows Computer'" -ForegroundColor White
Write-Host "4. Copy the 16-character password" -ForegroundColor White
Write-Host "5. Re-run this script and use that password" -ForegroundColor White
Write-Host ""

$testEmail = Read-Host "Would you like to test the email configuration? (y/n)"
if ($testEmail -eq 'y') {
    Write-Host ""
    Write-Host "Testing email configuration..." -ForegroundColor Yellow
    Write-Host "Make sure your Flask app is running and try approving a test registration." -ForegroundColor White
    Write-Host "Check the console logs for email status." -ForegroundColor White
}

Write-Host ""
Write-Host "Setup complete!" -ForegroundColor Green
