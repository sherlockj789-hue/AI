# =========================================================================
# THE ULTIMATE CONTROL ASSISTANT WIDGET
# =========================================================================

function Show-AI-Menu {
    Clear-Host
    Write-Host "=========================================================" -ForegroundColor Cyan
    Write-Host " NOVA CORE INFINITE ENTERPRISE MATRIX CONTROLLER      " -ForegroundColor Green
    Write-Host "=========================================================" -ForegroundColor Cyan
    Write-Host " [1] Wake Up Background Engines and Run AI Factory"
    Write-Host " [2] Open Active Code Folder View"
    Write-Host " [3] View Self-Evolving Design Memories"
    Write-Host " [4] Kill All Active AI Loop Processes"
    Write-Host " [5] Exit Control Deck"
    Write-Host "=========================================================" -ForegroundColor Cyan
    
    $choice = Read-Host "Select an operational command option [1-5]"
    
    if ($choice -eq "1") {
        Write-Host "Booting background server models and starting loop..." -ForegroundColor Green
        Start-Process -FilePath "ollama" -ArgumentList "serve" -WindowStyle Hidden
        Start-Sleep -Seconds 5
        python smart_founder.py
        Pause
        Show-AI-Menu
    }
    elseif ($choice -eq "2") {
        Write-Host "Opening sandbox application directory..." -ForegroundColor Yellow
        if (Test-Path ".\autonomous_company_projects\Nova_Core_Platform") {
            explorer ".\autonomous_company_projects\Nova_Core_Platform"
        } else {
            Write-Host "Active folder footprint not found yet. Run option 1 first!" -ForegroundColor Red
            Start-Sleep -Seconds 3
        }
        Show-AI-Menu
    }
    elseif ($choice -eq "3") {
        Write-Host "Loading self-taught design rules..." -ForegroundColor Magenta
        if (Test-Path ".\agent_design_lessons") {
            Get-ChildItem ".\agent_design_lessons\*.txt" | ForEach-Object {
                Write-Host "--- Lesson: $_ ---" -ForegroundColor Cyan
                Get-Content $_.FullName
            }
        } else {
            Write-Host "Memory profiles are completely empty." -ForegroundColor Red
        }
        Pause
        Show-AI-Menu
    }
    elseif ($choice -eq "4") {
        Write-Host "Forcing emergency shutdown on loop processes..." -ForegroundColor Red
        Stop-Process -Name "python" -Force -ErrorAction SilentlyContinue
        Stop-Process -Name "ollama" -Force -ErrorAction SilentlyContinue
        Write-Host "Background engines stopped cleanly." -ForegroundColor Green
        Start-Sleep -Seconds 3
        Show-AI-Menu
    }
    elseif ($choice -eq "5") {
        Write-Host "Exiting controller window." -ForegroundColor Green
        Exit
    }
    else {
        Write-Host "Invalid selection made." -ForegroundColor Red
        Start-Sleep -Seconds 2
        Show-AI-Menu
    }
}

Show-AI-Menu
# =========================================================================
# THE ULTIMATE CONTROL ASSISTANT WIDGET
# =========================================================================

function Show-AI-Menu {
    Clear-Host
    Write-Host "=========================================================" -ForegroundColor Cyan
    Write-Host " NOVA CORE INFINITE ENTERPRISE MATRIX CONTROLLER      " -ForegroundColor Green
    Write-Host "=========================================================" -ForegroundColor Cyan
    Write-Host " [1] Wake Up Background Engines and Run AI Factory"
    Write-Host " [2] Open Active Code Folder View"
    Write-Host " [3] View Self-Evolving Design Memories"
    Write-Host " [4] Kill All Active AI Loop Processes"
    Write-Host " [5] Exit Control Deck"
    Write-Host "=========================================================" -ForegroundColor Cyan
    
    $choice = Read-Host "Select an operational command option [1-5]"
    
    if ($choice -eq "1") {
        Write-Host "Booting background server models and starting loop..." -ForegroundColor Green
        Start-Process -FilePath "ollama" -ArgumentList "serve" -WindowStyle Hidden
        Start-Sleep -Seconds 5
        python smart_founder.py
        Pause
        Show-AI-Menu
    }
    elseif ($choice -eq "2") {
        Write-Host "Opening sandbox application directory..." -ForegroundColor Yellow
        if (Test-Path ".\autonomous_company_projects\Nova_Core_Platform") {
            explorer ".\autonomous_company_projects\Nova_Core_Platform"
        } else {
            Write-Host "Active folder footprint not found yet. Run option 1 first!" -ForegroundColor Red
            Start-Sleep -Seconds 3
        }
        Show-AI-Menu
    }
    elseif ($choice -eq "3") {
        Write-Host "Loading self-taught design rules..." -ForegroundColor Magenta
        if (Test-Path ".\agent_design_lessons") {
            Get-ChildItem ".\agent_design_lessons\*.txt" | ForEach-Object {
                Write-Host "--- Lesson: $_ ---" -ForegroundColor Cyan
                Get-Content $_.FullName
            }
        } else {
            Write-Host "Memory profiles are completely empty." -ForegroundColor Red
        }
        Pause
        Show-AI-Menu
    }
    elseif ($choice -eq "4") {
        Write-Host "Forcing emergency shutdown on loop processes..." -ForegroundColor Red
        Stop-Process -Name "python" -Force -ErrorAction SilentlyContinue
        Stop-Process -Name "ollama" -Force -ErrorAction SilentlyContinue
        Write-Host "Background engines stopped cleanly." -ForegroundColor Green
        Start-Sleep -Seconds 3
        Show-AI-Menu
    }
    elseif ($choice -eq "5") {
        Write-Host "Exiting controller window." -ForegroundColor Green
        Exit
    }
    else {
        Write-Host "Invalid selection made." -ForegroundColor Red
        Start-Sleep -Seconds 2
        Show-AI-Menu
    }
}

Show-AI-Menu
