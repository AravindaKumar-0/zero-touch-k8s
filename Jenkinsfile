pipeline {
    agent any

    environment {
        DOCKERHUB_CREDENTIALS = credentials('dockerhub-creds')
        DOCKERHUB_USER = 'imaravinda'

        FRONTEND_IMAGE = 'imaravinda/zero-touch-frontend'
        BACKEND_IMAGE = 'imaravinda/zero-touch-backend'

        KUBECONFIG_CRED = 'kubeconfig-cred'

        HELM_RELEASE = 'zero-touch'
        HELM_CHART_PATH = './helm/zero-touch-k8s'

        IMAGE_TAG = "jenkins-${BUILD_NUMBER}"

        BACKEND_SERVICE = 'zero-touch-zero-touch-k8s-backend'
        BACKEND_API_PATH = '/api'
    }

    stages {

        stage('Checkout') {
            steps {
                checkout scm

                sh '''
                    set -e
                    pwd
                    ls -la
                    git rev-parse --short HEAD
                '''
            }
        }

        stage('Build Docker Images') {
            steps {
                sh '''
                    set -e

                    docker build \
                        -t "${FRONTEND_IMAGE}:${IMAGE_TAG}" \
                        ./frontend

                    docker build \
                        -t "${BACKEND_IMAGE}:${IMAGE_TAG}" \
                        ./backend

                    docker images | grep zero-touch || true
                '''
            }
        }

        stage('Push Images to Docker Hub') {
            steps {
                sh '''
                    set -e

                    echo "${DOCKERHUB_CREDENTIALS_PSW}" | \
                    docker login \
                        -u "${DOCKERHUB_CREDENTIALS_USR}" \
                        --password-stdin

                    docker push "${FRONTEND_IMAGE}:${IMAGE_TAG}"
                    docker push "${BACKEND_IMAGE}:${IMAGE_TAG}"

                    docker logout
                '''
            }
        }

        stage('Kubernetes Context Check') {
            steps {
                withCredentials([
                    file(
                        credentialsId: "${KUBECONFIG_CRED}",
                        variable: 'KUBECONFIG'
                    )
                ]) {
                    sh '''
                        set -e

                        kubectl config current-context
                        kubectl get nodes
                        kubectl get pods
                    '''
                }
            }
        }

        stage('Deploy via Helm') {
            steps {
                withCredentials([
                    file(
                        credentialsId: "${KUBECONFIG_CRED}",
                        variable: 'KUBECONFIG'
                    )
                ]) {
                    sh '''
                        set -e

                        helm upgrade --install \
                            "${HELM_RELEASE}" \
                            "${HELM_CHART_PATH}" \
                            --set frontend.image.repository="${FRONTEND_IMAGE}" \
                            --set frontend.image.tag="${IMAGE_TAG}" \
                            --set backend.image.repository="${BACKEND_IMAGE}" \
                            --set backend.image.tag="${IMAGE_TAG}"

                        helm status "${HELM_RELEASE}"
                    '''
                }
            }
        }

        stage('Verify Pods') {
            steps {
                withCredentials([
                    file(
                        credentialsId: "${KUBECONFIG_CRED}",
                        variable: 'KUBECONFIG'
                    )
                ]) {
                    sh '''
                        set -e

                        kubectl get pods -o wide

                        if kubectl get pods | grep -E \
                            'CrashLoopBackOff|ImagePullBackOff|ErrImagePull|Error'; then
                            exit 1
                        fi
                    '''
                }
            }
        }

        stage('Verify Services') {
            steps {
                withCredentials([
                    file(
                        credentialsId: "${KUBECONFIG_CRED}",
                        variable: 'KUBECONFIG'
                    )
                ]) {
                    sh '''
                        set -e

                        kubectl get svc
                        kubectl get svc "${BACKEND_SERVICE}"
                        kubectl get endpoints
                        kubectl get ingress
                    '''
                }
            }
        }

        stage('Verify Rollout') {
            steps {
                withCredentials([
                    file(
                        credentialsId: "${KUBECONFIG_CRED}",
                        variable: 'KUBECONFIG'
                    )
                ]) {
                    script {
                        try {
                            sh '''
                                set -e
                                kubectl rollout status deployment/zero-touch-zero-touch-k8s-backend --timeout=5m
                                kubectl rollout status deployment/zero-touch-zero-touch-k8s-frontend --timeout=5m
                            '''
                        } catch (err) {
                            echo "Rollout failed — rolling back to previous release"
                            sh '''
                                kubectl rollout undo deployment/zero-touch-zero-touch-k8s-backend
                                kubectl rollout undo deployment/zero-touch-zero-touch-k8s-frontend
                            '''
                            error("Deployment failed and was rolled back to the last known-good release")
                        }
                    }
                }
            }
        }

        stage('Backend Health Check') {
            steps {
                withCredentials([
                    file(
                        credentialsId: "${KUBECONFIG_CRED}",
                        variable: 'KUBECONFIG'
                    )
                ]) {
                    sh '''
                        set -e

                        kubectl run zero-touch-healthcheck \
                            --image=curlimages/curl:8.10.1 \
                            --restart=Never \
                            --rm \
                            -i \
                            --attach \
                            -- \
                            curl -fsS \
                            "http://${BACKEND_SERVICE}:80${BACKEND_API_PATH}"
                    '''
                }
            }
        }

        stage('Final Verification') {
            steps {
                withCredentials([
                    file(
                        credentialsId: "${KUBECONFIG_CRED}",
                        variable: 'KUBECONFIG'
                    )
                ]) {
                    sh '''
                        set -e

                        kubectl get pods -o wide
                        kubectl get svc
                        kubectl get endpoints
                        kubectl get ingress
                        helm status "${HELM_RELEASE}"

                        echo "Build: ${BUILD_NUMBER}"
                        echo "Image: ${IMAGE_TAG}"
                    '''
                }
            }
        }
    }

    post {
        success {
            echo "Build #${BUILD_NUMBER} deployed successfully."
        }

        failure {
            echo "Build #${BUILD_NUMBER} failed."
        }

        always {
            echo "Pipeline execution finished."
        }
    }
}
