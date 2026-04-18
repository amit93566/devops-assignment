pipeline {
    agent any

    environment {
        PATH = "/var/lib/jenkins/.local/bin:/opt/sonar-scanner/bin:${env.PATH}"
    }

    stages {

        stage('Checkout') {
            steps {
                git branch: 'main', url: 'https://github.com/amit93566/devops-assignment.git'
            }
        }

        stage('Install Dependencies') {
            steps {
                sh 'pip install -r requirements.txt --break-system-packages'
            }
        }

        stage('Run Tests') {
            steps {
                sh 'python3 -m pytest --tb=short'
            }
        }

        stage('SonarQube Analysis') {
            steps {
                sh '''
                    /opt/sonar-scanner/bin/sonar-scanner \
                    -Dsonar.projectKey=aceest-fitness \
                    -Dsonar.sources=. \
                    -Dsonar.host.url=http://localhost:9000 \
                    -Dsonar.token=$(cat /var/lib/jenkins/sonar-token.txt)
                '''
            }
        }

        stage('Build Docker Image') {
            steps {
                sh 'docker build -t aceest-fitness:latest .'
            }
        }

    }
}