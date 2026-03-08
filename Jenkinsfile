pipeline {
    agent any

    stages {
        stage('Checkout') {
            steps {
                checkout scm
            }
        }
        stage('Build & Test') {
            steps {
                sh 'docker build -t aceest-fitness:latest .'
                sh 'docker run --rm aceest-fitness:latest pytest tests/ -v'
            }
        }
    }
    post {
        always {
            cleanWs()
        }
    }
}