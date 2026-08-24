pipeline {
    agent any

    environment {
        DOCKERHUB_CREDENTIALS = credentials('dockerhub-creds')      
        KUBECONFIG_CRED       = credentials('kubeconfig-cred')      
        DOCKERHUB_USER        = '<your-dockerhub-username>'
        FRONTEND_IMAGE        = "${DOCKERHUB_USER}/frontend"
        BACKEND_IMAGE         = "${DOCKERHUB_USER}/backend"
        HELM_RELEASE          = 'app-release'
        HELM_CHART_PATH       = './helm/app-chart'
        BACKEND_HEALTH_URL    = 'http://<backend-service-or-ingress>/health'
    }

    stages {

        stage('Checkout') {
            steps {
                checkout scm
            }
        }

        stage('Build Docker Images') {
            steps {
                script {
                    sh "docker build -t ${FRONTEND_IMAGE}:${BUILD_NUMBER} ./frontend"
                    sh "docker build -t ${BACKEND_IMAGE}:${BUILD_NUMBER} ./backend"
                }
            }
        }

        stage('Push to Docker Hub') {
            steps {
                script {
                    sh "echo ${DOCKERHUB_CREDENTIALS_PSW} | docker login -u ${DOCKERHUB_CREDENTIALS_USR} --password-stdin"
                    sh "docker push ${FRONTEND_IMAGE}:${BUILD_NUMBER}"
                    sh "docker push ${BACKEND_IMAGE}:${BUILD_NUMBER}"
                }
            }
        }

        stage('Deploy via Helm') {
            steps {
                withCredentials([file(credentialsId: 'kubeconfig-cred', variable: 'KUBECONFIG')]) {
                    sh """
                        helm upgrade --install ${HELM_RELEASE} ${HELM_CHART_PATH} \
                          --set frontend.image.repository=${FRONTEND_IMAGE} \
                          --set frontend.image.tag=${BUILD_NUMBER} \
                          --set backend.image.repository=${BACKEND_IMAGE} \
                          --set backend.image.tag=${BUILD_NUMBER}
                    """
                }
            }
        }

        stage('Verify Rollout') {
            steps {
                withCredentials([file(credentialsId: 'kubeconfig-cred', variable: 'KUBECONFIG')]) {
                    script {
                        try {
                            sh "kubectl rollout status deployment/backend --timeout=60s"
                            sh "kubectl rollout status deployment/frontend --timeout=60s"
                        } catch (err) {
                            echo "Rollout failed — rolling back to previous release"
                            sh "kubectl rollout undo deployment/backend"
                            sh "kubectl rollout undo deployment/frontend"
                            error("Deployment failed and was rolled back to the last known-good release")
                        }
                    }
                }
            }
        }

        stage('Post-deploy Health Check') {
            steps {
                script {
                    def response = sh(
                        script: "curl -s -o /dev/null -w '%{http_code}' ${BACKEND_HEALTH_URL}",
                        returnStdout: true
                    ).trim()
                    if (response != '200') {
                        error("Health check failed with status ${response}")
                    } else {
                        echo "Health check passed (200 OK)"
                    }
                }
            }
        }
    }

    post {
        success {
            echo "Pipeline completed successfully — build #${BUILD_NUMBER} deployed and healthy."
        }
        failure {
            echo "Pipeline failed — check rollout/health check logs above."
        }
    }
}
