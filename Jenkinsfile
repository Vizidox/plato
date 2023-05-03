project_version=''
local_api_image_name = 'plato-api'

sonar_project_key = 'plato'
sonar_url = 'https://sonar.morphotech.co.uk'
sonar_analyzed_dir = 'plato'

pipeline {
    agent {
        label env.agent_label
    }

    stages {
        stage('Build Project') {
            steps {
                script {
                    sh('docker-compose build plato-api')
                }
            }
        }
        stage('Run Tests') {
            steps{
                script{
                    if(!params.get('skipTests', false)) {
                        sh 'docker-compose -f tests/docker/docker-compose.build.test.yml up -d database'
                        sh 'docker-compose -f tests/docker/docker-compose.build.test.yml run --rm test-plato pytest --junitxml=/app/coverage/pytest-report.xml --cov-report=xml:/app/coverage/coverage.xml --cov=${sonar_analyzed_dir}'
                    }
                }
            }
        }
        stage('Get project version') {
            steps {
                script {
                    project_version = sh(script: 'docker-compose run --rm plato-api poetry version', returnStdout: true).trim().split(' ')[-1]
                }
                sh "echo 'current project version: ${project_version}'"
            }
        }
        stage('Push to Docker Hub and GitHub') {
            steps {
                sh "docker tag ${local_api_image_name} vizidox/plato:${project_version}"
                sh "docker push vizidox/plato:${project_version}"
                sh "docker tag vizidox/plato:${project_version} ghcr.io/vizidox/plato:${project_version}"
                sh "docker push ghcr.io/vizidox/plato:${project_version}"
                sh "docker tag ghcr.io/vizidox/plato:${project_version} ${local_api_image_name}" // tag the image with the original name for later docker-compose cleanup
            }
        }
        stage('Sonarqube code inspection') {
            steps {
                sh "docker run --rm -e SONAR_HOST_URL=\"${sonar_url}\" -v \"${WORKSPACE}:/usr/src\"  sonarsource/sonar-scanner-cli:${env.sonarqube_version} -X \
                -Dsonar.projectKey=${sonar_project_key}\
                -Dsonar.login=${env.sonar_account}\
                -Dsonar.password=${env.sonar_password}\
                -Dsonar.python.coverage.reportPaths=coverage/coverage.xml\
                -Dsonar.python.xunit.reportPath=coverage/pytest-report.xml\
                -Dsonar.projectBaseDir=${sonar_analyzed_dir}\
                -Dsonar.exclusions=\"/static/**/*, /templates/**/*\""
            }
        }
    }
    post {
        cleanup{
            sh 'docker-compose -f tests/docker/docker-compose.build.test.yml down -v --rmi all'
        }
    }
}
