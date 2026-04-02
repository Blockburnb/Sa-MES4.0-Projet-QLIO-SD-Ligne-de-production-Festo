$ErrorActionPreference = "Stop"

$rootDir = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $rootDir

$repoUrl = "https://github.com/Blockburnb/Sa-MES4.0-Projet-QLIO-SD-Ligne-de-production-Festo.git"
$repoBranch = "main"
$projectDir = $rootDir

$venvDir = ""
$appFile = ""
$composeFile = ""
$sqlDumpFile = ""

function Update-ProjectPaths {
    $script:venvDir = Join-Path $script:projectDir ".venv"
    $script:appFile = Join-Path $script:projectDir "dashboard/dashboard_final.py"
    $script:composeFile = Join-Path $script:projectDir "TELEFAN/docker-compose.yml"
    $script:sqlDumpFile = Join-Path $script:projectDir "TELEFAN/FestoMES-2025-03-27.sql"
}

Update-ProjectPaths

$dbHostDefault = "localhost"
$dbPortDefault = "3306"
$dbUserDefault = "example_user"
$dbPasswordDefault = "example_password"
$dbNameDefault = "MES4"
$dbRootPassword = "example_root_password"
$dbNameRuntime = $dbNameDefault

$dashboardPort = 8501
$phpmyadminPort = 8080
$mariadbPort = 3306

function Log-Info([string]$msg) {
    Write-Host "[INFO] $msg"
}

function Log-Warn([string]$msg) {
    Write-Host "[WARN] $msg"
}

function Fail([string]$msg) {
    Write-Host "[ERROR] $msg"
    exit 1
}

function Ensure-GitSync {
    $git = Get-Command git -ErrorAction SilentlyContinue
    if (-not $git) {
        Log-Warn "Git introuvable. La synchronisation automatique est desactivee."
        return
    }

    $bootstrapDir = Join-Path $rootDir "project_main"

    if (-not (Test-Path (Join-Path $projectDir ".git"))) {
        if (Test-Path (Join-Path $bootstrapDir ".git")) {
            $script:projectDir = $bootstrapDir
            Update-ProjectPaths
        } else {
            if ((Test-Path $bootstrapDir) -and ((Get-ChildItem -Force $bootstrapDir | Measure-Object).Count -gt 0)) {
                Log-Warn "Le dossier de bootstrap Git existe deja et n'est pas vide: $bootstrapDir. Synchronisation ignoree."
                return
            }

            Log-Info "Depot Git non detecte. Clonage de la branche $repoBranch..."
            git clone --branch $repoBranch --single-branch $repoUrl $bootstrapDir *> $null
            if ($LASTEXITCODE -ne 0) {
                Log-Warn "Echec du clone Git depuis $repoUrl. Le dashboard continuera avec les fichiers locaux."
                return
            }

            $script:projectDir = $bootstrapDir
            Update-ProjectPaths
        }
    }

    Set-Location $projectDir

    git rev-parse --is-inside-work-tree *> $null
    if ($LASTEXITCODE -ne 0) {
        Log-Warn "Le dossier projet n'est pas un depot Git valide: $projectDir. Synchronisation ignoree."
        return
    }

    git diff --quiet 2>$null
    $dirtyWorktree = $LASTEXITCODE -ne 0
    git diff --cached --quiet 2>$null
    $dirtyIndex = $LASTEXITCODE -ne 0
    if ($dirtyWorktree -or $dirtyIndex) {
        Log-Warn "Modifications locales detectees dans $projectDir. Synchronisation Git ignoree."
        return
    }

    Log-Info "Synchronisation Git de la branche $repoBranch..."
    git fetch origin $repoBranch *> $null
    if ($LASTEXITCODE -ne 0) {
        Log-Warn "Echec de git fetch origin $repoBranch. Verifie reseau/acces GitHub. Le dashboard continuera avec la version locale."
        return
    }

    $currentBranch = (git rev-parse --abbrev-ref HEAD).Trim()
    if ($currentBranch -ne $repoBranch) {
        git checkout $repoBranch *> $null
        if ($LASTEXITCODE -ne 0) {
            Log-Warn "Impossible de basculer sur la branche $repoBranch. Le dashboard continuera sur la branche courante."
            return
        }
    }

    git pull --ff-only origin $repoBranch *> $null
    if ($LASTEXITCODE -ne 0) {
        Log-Warn "Echec du git pull --ff-only sur $repoBranch. Le dashboard continuera avec la version locale."
    }
}

function Test-PortInUse([int]$port) {
    try {
        $conn = Get-NetTCPConnection -State Listen -ErrorAction Stop | Where-Object { $_.LocalPort -eq $port }
        return $null -ne $conn
    } catch {
        return $false
    }
}

function Check-RequiredPorts {
    if (Test-PortInUse $dashboardPort) {
        Fail "Le port $dashboardPort est deja utilise. Ferme le service occupe puis relance."
    }

    if (Test-PortInUse $phpmyadminPort) {
        Log-Warn "Le port $phpmyadminPort est deja utilise. phpMyAdmin peut ne pas demarrer correctement."
    }

    if (Test-PortInUse $mariadbPort) {
        Log-Warn "Le port $mariadbPort est deja utilise. MariaDB Docker peut ne pas demarrer correctement."
    }
}

function Find-Python {
    $py3 = Get-Command python3 -ErrorAction SilentlyContinue
    if ($py3) { return $py3.Source }

    $py = Get-Command python -ErrorAction SilentlyContinue
    if ($py) { return $py.Source }

    Fail "Python introuvable. Installe Python 3 puis relance."
}

function Get-ComposeCommand {
    $docker = Get-Command docker -ErrorAction SilentlyContinue
    if (-not $docker) {
        return $null
    }

    try {
        docker compose version *> $null
        if ($LASTEXITCODE -eq 0) {
            return @("docker", "compose")
        }
    } catch {}

    $dockerCompose = Get-Command docker-compose -ErrorAction SilentlyContinue
    if ($dockerCompose) {
        return @("docker-compose")
    }

    return $null
}

function Invoke-Compose([string[]]$composeCmd, [string[]]$args) {
    & $composeCmd[0] @($composeCmd[1..($composeCmd.Length-1)]) @args
    return $LASTEXITCODE
}

function Wait-ForMariaDb([string]$containerId) {
    for ($i = 1; $i -le 60; $i++) {
        docker exec $containerId mariadb-admin ping -h 127.0.0.1 -uroot "-p$dbRootPassword" --silent *> $null
        if ($LASTEXITCODE -eq 0) {
            Log-Info "MariaDB est disponible."
            return $true
        }
        Start-Sleep -Seconds 2
    }
    return $false
}

function Resolve-DbName([string]$containerId) {
    $query = "SELECT SCHEMA_NAME FROM information_schema.SCHEMATA WHERE SCHEMA_NAME IN ('MES4','mes4') ORDER BY (SCHEMA_NAME='MES4') DESC LIMIT 1;"
    $dbName = docker exec $containerId mariadb -uroot "-p$dbRootPassword" -Nse $query 2>$null
    if ($LASTEXITCODE -eq 0 -and -not [string]::IsNullOrWhiteSpace($dbName)) {
        return $dbName.Trim()
    }
    return $dbNameDefault
}

function Import-SqlIfNeeded([string]$containerId, [string]$targetDb) {
    $countQuery = "SELECT COUNT(*) FROM information_schema.tables WHERE table_schema='$targetDb';"
    $tableCount = docker exec $containerId mariadb -uroot "-p$dbRootPassword" -Nse $countQuery 2>$null
    if ($LASTEXITCODE -ne 0 -or [string]::IsNullOrWhiteSpace($tableCount)) {
        $tableCount = "0"
    }

    if ([int]$tableCount -gt 0) {
        Log-Info "Base $targetDb deja peuplee ($tableCount tables)."
        return
    }

    if (-not (Test-Path $sqlDumpFile)) {
        Log-Warn "Dump SQL introuvable: $sqlDumpFile. Le dashboard continuera, mais sans import automatique."
        return
    }

    Log-Info "Import du dump SQL initial dans $targetDb..."
    docker exec $containerId mariadb -uroot "-p$dbRootPassword" -e "CREATE DATABASE IF NOT EXISTS \`$targetDb\`;" *> $null

    $filtered = Join-Path $env:TEMP "festo_filtered.sql"
    Get-Content $sqlDumpFile | Where-Object {
        $_ -notmatch '^/\*!40000 DROP DATABASE IF EXISTS ' -and
        $_ -notmatch '^CREATE DATABASE ' -and
        $_ -notmatch '^USE `[^`]+`;' 
    } | Set-Content -NoNewline:$false $filtered

    Get-Content $filtered | docker exec -i $containerId mariadb -uroot "-p$dbRootPassword" $targetDb
    Remove-Item $filtered -Force -ErrorAction SilentlyContinue

    if ($LASTEXITCODE -ne 0) {
        Fail "Echec de l'import SQL dans $targetDb."
    }

    Log-Info "Import SQL termine."
}

function Start-DockerStack {
    $composeCmd = Get-ComposeCommand
    if (-not $composeCmd) {
        Fail "Docker/Docker Compose introuvable. Installe Docker Desktop puis relance."
    }

    docker info *> $null
    if ($LASTEXITCODE -ne 0) {
        Fail "Docker est installe mais le daemon ne repond pas. Lance Docker Desktop puis relance."
    }

    if (-not (Test-Path $composeFile)) {
        Fail "Fichier Docker Compose introuvable: $composeFile"
    }

    Log-Info "Demarrage des containers Docker..."
    $upArgs = @("-f", $composeFile, "up", "-d")
    $null = Invoke-Compose $composeCmd $upArgs
    if ($LASTEXITCODE -ne 0) {
        Fail "Echec du demarrage Docker Compose. Verifie la configuration dans $composeFile."
    }

    $psArgs = @("-f", $composeFile, "ps", "-q", "mariadb")
    $dbContainerId = (& $composeCmd[0] @($composeCmd[1..($composeCmd.Length-1)]) @psArgs 2>$null).Trim()
    if ([string]::IsNullOrWhiteSpace($dbContainerId)) {
        Fail "Container mariadb non detecte apres demarrage. Verifie le service 'mariadb' puis lance les logs Docker."
    }

    Log-Info "Attente de disponibilite de MariaDB..."
    if (-not (Wait-ForMariaDb $dbContainerId)) {
        Fail "MariaDB n'a pas repondu a temps. Verifie les logs Docker du service mariadb."
    }

    $targetDb = Resolve-DbName $dbContainerId
    Import-SqlIfNeeded $dbContainerId $targetDb
    $script:dbNameRuntime = Resolve-DbName $dbContainerId
    Log-Info "Base active detectee: $script:dbNameRuntime"
}

function Setup-PythonEnv([string]$pythonCmd) {
    if (-not (Test-Path $venvDir)) {
        Log-Info "Creation de l'environnement virtuel..."
        & $pythonCmd -m venv $venvDir
        if ($LASTEXITCODE -ne 0) {
            Fail "Echec de creation du venv."
        }
    }

    $venvPython = Join-Path $venvDir "Scripts/python.exe"
    if (-not (Test-Path $venvPython)) {
        Fail "Python du venv introuvable: $venvPython"
    }

    Log-Info "Mise a jour de pip..."
    & $venvPython -m pip install --upgrade pip
    if ($LASTEXITCODE -ne 0) {
        Fail "Echec de mise a jour de pip."
    }

    Log-Info "Installation des dependances Python..."
    & $venvPython -m pip install streamlit pandas plotly mysql-connector-python
    if ($LASTEXITCODE -ne 0) {
        Fail "Echec d'installation des dependances Python."
    }
}

function Wait-ForHttp([string]$url, [int]$maxAttempts = 90) {
    for ($i = 1; $i -le $maxAttempts; $i++) {
        try {
            $resp = Invoke-WebRequest -Uri $url -UseBasicParsing -TimeoutSec 2
            if ($resp.StatusCode -ge 200 -and $resp.StatusCode -lt 500) {
                return $true
            }
        } catch {}
        Start-Sleep -Seconds 1
    }
    return $false
}

function Launch-Dashboard {
    if (-not (Test-Path $appFile)) {
        Fail "Fichier dashboard introuvable: $appFile"
    }

    $env:DB_HOST = if ($env:DB_HOST) { $env:DB_HOST } else { $dbHostDefault }
    $env:DB_PORT = if ($env:DB_PORT) { $env:DB_PORT } else { $dbPortDefault }
    $env:DB_USER = if ($env:DB_USER) { $env:DB_USER } else { $dbUserDefault }
    $env:DB_PASSWORD = if ($env:DB_PASSWORD) { $env:DB_PASSWORD } else { $dbPasswordDefault }
    $env:DB_NAME = if ($env:DB_NAME) { $env:DB_NAME } else { $script:dbNameRuntime }

    $dashboardUrl = "http://localhost:$dashboardPort"
    $healthUrl = "$dashboardUrl/_stcore/health"
    $venvPython = Join-Path $venvDir "Scripts/python.exe"

    Log-Info "Dashboard: $dashboardUrl"
    Log-Info "phpMyAdmin: http://localhost:$phpmyadminPort"
    Log-Info "Arret: CTRL+C"
    Write-Host ""

    $proc = Start-Process -FilePath $venvPython -ArgumentList @("-m", "streamlit", "run", $appFile) -PassThru

    if (Wait-ForHttp $healthUrl 90) {
        Log-Info "Streamlit est disponible ($healthUrl)."
        Start-Process $dashboardUrl | Out-Null
    } else {
        Log-Warn "Streamlit ne repond pas sur $healthUrl apres attente."
    }

    Wait-Process -Id $proc.Id
}

function Main {
    Ensure-GitSync

    $pythonCmd = Find-Python
    Log-Info "Python detecte: $pythonCmd"

    Check-RequiredPorts
    Setup-PythonEnv $pythonCmd
    Start-DockerStack
    Launch-Dashboard
}

Main
