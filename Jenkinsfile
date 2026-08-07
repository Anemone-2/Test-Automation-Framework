pipeline {
    agent any

    options {
        timestamps()
        disableConcurrentBuilds()
        timeout(time: 30, unit: 'MINUTES')
        buildDiscarder(logRotator(numToKeepStr: '20'))
    }

    parameters {
        string(
            name: 'SNIPEIT_ENV_CREDENTIAL_ID',
            defaultValue: 'snipeit-env-file',
            description: 'Jenkins Secret file credential containing the Snipe-IT .env file'
        )
        string(
            name: 'PYTHON_BOOTSTRAP',
            defaultValue: 'D:/python/python.exe',
            description: 'Python executable used to create the Jenkins virtual environment'
        )
        choice(
            name: 'TEST_SCOPE',
            choices: ['all', 'smoke', 'api', 'web'],
            description: 'Snipe-IT test set to execute'
        )
        choice(
            name: 'BROWSER',
            choices: ['edge', 'chrome'],
            description: 'Browser used by Selenium Web tests'
        )
        booleanParam(
            name: 'HEADLESS',
            defaultValue: true,
            description: 'Run Selenium without displaying the browser window'
        )
    }

    environment {
        PROJECT_DIR = "${WORKSPACE}"
        VENV_DIR = "${WORKSPACE}/.jenkins-venv"
        PYTHON_EXE = "${WORKSPACE}/.jenkins-venv/Scripts/python.exe"
        RESULT_ROOT = "${WORKSPACE}/ci-results"
        ALLURE_RESULTS = "${WORKSPACE}/ci-results/allure-results"
        JUNIT_XML = "${WORKSPACE}/ci-results/junit.xml"
    }

    stages {
        stage('Prepare Python') {
            steps {
                dir("${env.PROJECT_DIR}") {
                    powershell '''
                        $ErrorActionPreference = 'Stop'
                        $bootstrap = Get-Command $env:PYTHON_BOOTSTRAP -ErrorAction Stop
                        if (-not (Test-Path -LiteralPath $env:PYTHON_EXE)) {
                            & $bootstrap.Source -m venv $env:VENV_DIR
                            if ($LASTEXITCODE -ne 0) {
                                throw "Creating the Jenkins virtual environment failed: $LASTEXITCODE"
                            }
                        }
                        & $env:PYTHON_EXE -m pip install --disable-pip-version-check -e .
                        if ($LASTEXITCODE -ne 0) {
                            throw "Installing Python dependencies failed: $LASTEXITCODE"
                        }
                    '''
                }
            }
        }

        stage('Start Snipe-IT') {
            steps {
                dir("${env.PROJECT_DIR}") {
                    withCredentials([
                        file(
                            credentialsId: "${params.SNIPEIT_ENV_CREDENTIAL_ID}",
                            variable: 'SNIPEIT_ENV_FILE'
                        )
                    ]) {
                        powershell '''
                            $ErrorActionPreference = 'Stop'
                            & powershell.exe -NoProfile -ExecutionPolicy Bypass `
                                -File ./scripts/snipeit_ci_start.ps1 `
                                -EnvFile $env:SNIPEIT_ENV_FILE
                            if ($LASTEXITCODE -ne 0) {
                                throw "Starting the Snipe-IT CI environment failed: $LASTEXITCODE"
                            }
                        '''
                    }
                }
            }
        }

        stage('Run Snipe-IT Tests') {
            steps {
                dir("${env.PROJECT_DIR}") {
                    withCredentials([
                        file(
                            credentialsId: "${params.SNIPEIT_ENV_CREDENTIAL_ID}",
                            variable: 'SNIPEIT_ENV_FILE'
                        )
                    ]) {
                        powershell '''
                            $ErrorActionPreference = 'Stop'
                            $env:SNIPEIT_BROWSER = $env:BROWSER
                            $env:SNIPEIT_HEADLESS = $env:HEADLESS.ToLowerInvariant()

                            $markerExpression = switch ($env:TEST_SCOPE) {
                                'smoke' { 'snipeit and smoke' }
                                'api' { 'snipeit and api' }
                                'web' { 'snipeit and web' }
                                default { 'snipeit' }
                            }

                            New-Item -ItemType Directory -Force -Path $env:ALLURE_RESULTS | Out-Null
                            $pytestArguments = @(
                                '-m', 'pytest',
                                '-q', './testcase/snipeit',
                                '-m', $markerExpression,
                                "--alluredir=$env:ALLURE_RESULTS",
                                '--clean-alluredir',
                                "--junitxml=$env:JUNIT_XML"
                            )
                            & $env:PYTHON_EXE @pytestArguments
                            if ($LASTEXITCODE -ne 0) {
                                throw "Snipe-IT tests failed: $LASTEXITCODE"
                            }
                        '''
                    }
                }
            }
        }
    }

    post {
        always {
            script {
                catchError(buildResult: 'UNSTABLE', stageResult: 'FAILURE') {
                    dir("${env.PROJECT_DIR}") {
                        withCredentials([
                            file(
                                credentialsId: "${params.SNIPEIT_ENV_CREDENTIAL_ID}",
                                variable: 'SNIPEIT_ENV_FILE'
                            )
                        ]) {
                            powershell '''
                                & powershell.exe -NoProfile -ExecutionPolicy Bypass `
                                    -File ./scripts/snipeit_ci_stop.ps1 `
                                    -EnvFile $env:SNIPEIT_ENV_FILE
                                if ($LASTEXITCODE -ne 0) {
                                    throw "Stopping the Snipe-IT CI environment failed: $LASTEXITCODE"
                                }
                            '''
                        }
                    }
                }
            }
            junit allowEmptyResults: true,
                  testResults: 'ci-results/junit.xml'
            allure includeProperties: false,
                   jdk: 'JDK21',
                   results: [[path: 'ci-results/allure-results']]
            archiveArtifacts allowEmptyArchive: true,
                             artifacts: 'ci-results/**/*'
        }
    }
}
