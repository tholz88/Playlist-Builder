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
          sh(script: "docker build --target test -t ${env.IMAGE_NAME}:test .")
        }
      }
    }

    stage('Run tests') {
      steps {
        dir(env.BACKEND_DIR) {
          sh(script: "docker run --rm --env-file .env ${env.IMAGE_NAME}:test")
        }
      }
      post {
        always {
          // Falls du JUnit-Reports erzeugst, Pfad hier aktivieren:
          // junit allowEmptyResults: true, testResults: "${env.BACKEND_DIR}/reports/**/*.xml"
        }
      }
    }

    stage('Build prod image') {
      steps {
        dir(env.BACKEND_DIR) {
          sh(script: "docker build --target prod -t ${env.IMAGE_NAME}:latest .")
        }
      }
    }

    stage('Login & Push') {
      steps {
        withCredentials([usernamePassword(credentialsId: 'registry-creds', usernameVariable: 'REG_USER', passwordVariable: 'REG_PASS')]) {
          sh(script: """
            echo "\$REG_PASS" | docker login ${env.REGISTRY} -u "\$REG_USER" --password-stdin
            docker push ${env.IMAGE_NAME}:latest
          """.stripIndent())
        }
      }
    }

    stage('Deploy') {
      steps {
        sshagent(credentials: ['deploy-key']) {
          sh(script: """
            ssh -o StrictHostKeyChecking=no deploy@your-server.example '
              set -e
              cd /srv/playlist-backend
              docker compose pull || true
              docker compose up -d
              docker compose ps
            '
          """.stripIndent())
        }
      }
    }
  }

  post {
    always {
      sh(script: 'docker image prune -f || true')
    }
    failure {
      echo "Build or deployment failed. Check above logs."
    }
  }
}