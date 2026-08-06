pipeline {
    agent any

    options {
        timestamps()
        disableConcurrentBuilds()
    }

    environment {
        PROJECT_DIR = 'D:/Test-Automation-Framework-main/Test-Automation-Framework-main'
        VENV_DIR = 'D:/Test-Automation-Framework-main/Test-Automation-Framework-main/.jenkins-venv'
        PYTHON_EXE = 'D:/Test-Automation-Framework-main/Test-Automation-Framework-main/.jenkins-venv/Scripts/python.exe'
        API_HOST = 'http://127.0.0.1:8787'
    }

    stages {
        stage('Prepare Python') {
            steps {
                dir("${env.PROJECT_DIR}") {
                    powershell '''
                        $ErrorActionPreference = 'Stop'
                        if (-not (Test-Path -LiteralPath $env:PYTHON_EXE)) {
                            & 'D:/python/python.exe' -m venv $env:VENV_DIR
                            if ($LASTEXITCODE -ne 0) {
                                throw "Creating the Jenkins virtual environment failed with exit code $LASTEXITCODE"
                            }
                        }
                        & $env:PYTHON_EXE -m pip install --disable-pip-version-check -e .
                        if ($LASTEXITCODE -ne 0) {
                            throw "Installing Python dependencies failed with exit code $LASTEXITCODE"
                        }
                    '''
                }
            }
        }

        stage('Start Test Environment') {
            steps {
                dir("${env.PROJECT_DIR}") {
                    powershell '''
                        & ./scripts/ci_start.ps1 -PythonExe $env:PYTHON_EXE
                    '''
                }
            }
        }

        stage('Run Pytest') {
            steps {
                dir("${env.PROJECT_DIR}") {
                    powershell '''
                        $ErrorActionPreference = 'Stop'
                        $resultRoot = Join-Path $env:WORKSPACE 'ci-results'
                        $allureResults = Join-Path $resultRoot 'allure-results'
                        $junitXml = Join-Path $resultRoot 'junit.xml'
                        New-Item -ItemType Directory -Force -Path $allureResults | Out-Null
                        & $env:PYTHON_EXE -m pytest -s -v ./testcase `
                            -m 'not integration or integration' `
                            --alluredir=$allureResults `
                            --clean-alluredir `
                            --junitxml=$junitXml
                        if ($LASTEXITCODE -ne 0) {
                            throw "Pytest failed with exit code $LASTEXITCODE"
                        }
                    '''
                }
            }
        }
    }

    post {
        always {
            powershell '''
                & "$env:PROJECT_DIR/scripts/ci_stop.ps1"
            '''
            junit allowEmptyResults: true, testResults: 'ci-results/junit.xml'
            allure includeProperties: false,
                   jdk: 'JDK21',
                   results: [[path: 'ci-results/allure-results']]
            archiveArtifacts allowEmptyArchive: true,
                             artifacts: 'ci-results/**/*'
        }
    }
}
