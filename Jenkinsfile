pipeline {
  agent any
  environment {
    IMAGE_NAME = 'registry.example.com/playlist-backend'
    REGISTRY   = 'registry.example.com'
    DOCKER_BUILDKIT = '1'
    BACKEND_DIR = 'backend'
  }
  options {
    ansiColor('xterm')
    timestamps()
    disableConcurrentBuilds()
  }
  stages {
    stage('Checkout') {
      steps {
        checkout scm
      }
    }

    stage('Build test image') {
      steps {
        dir(env.BACKEND_DIR) {
          sh 'docker build --target test -t ${IMAGE_NAME}:test .'
        }
      }
    }

    stage('Run tests') {
      steps {
        dir(env.BACKEND_DIR) {
          sh 'docker run --rm --env-file .env ${IMAGE_NAME}:test'
        }
      }
      post {
        always {
          // junit allowEmptyResults: true, testResults: "${BACKEND_DIR}/reports/**/*.xml"
        }
      }
    }

    stage('Build prod image') {
      when { succeeded() }
      steps {
        dir(env.BACKEND_DIR) {
          sh 'docker build --target prod -t ${IMAGE_NAME}:latest .'
        }
      }
    }

    stage('Login & Push') {
      when { succeeded() }
      steps {
        withCredentials([usernamePassword(credentialsId: 'registry-creds', usernameVariable: 'REG_USER', passwordVariable: 'REG_PASS')]) {
          sh '''
            echo "$REG_PASS" | docker login ${REGISTRY} -u "$REG_USER" --password-stdin
            docker push ${IMAGE_NAME}:latest
          '''
        }
      }
    }

    stage('Deploy') {
      when { succeeded() }
      steps {
        sshagent(credentials: ['deploy-key']) {
          sh '''
            ssh -o StrictHostKeyChecking=no deploy@your-server.example '
              set -e
              cd /srv/playlist-backend
              docker compose pull || true
              docker compose up -d
              docker compose ps
            '
          '''
        }
      }
    }
  }
  post {
    always {
      sh 'docker image prune -f || true'
    }
    failure {
      echo "Build or deployment failed. Check above logs."
    }
  }
}