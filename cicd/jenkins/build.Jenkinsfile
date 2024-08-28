pipeline {
    agent {
        label 'docker-deploy'
    }
    parameters {
        string(name: 'BRANCH', defaultValue: 'main', description: 'Git Repo Branch to use')
        booleanParam(name: 'DEPLOY', defaultValue: false, description: 'Deploy application. \n Deployment to prod is only possible when BRANCH is "main".')
    }
    options {
        disableConcurrentBuilds()
        buildDiscarder(logRotator(numToKeepStr: '10'))
        timestamps()
        timeout(time: 2, unit: 'HOURS')
    }
    environment {
        MAIN_BRANCH = 'main'
        DOCKER_TEST_REGISTRY_URL = 'docker-test.int.esrlabs.com'
        DOCKER_PORD_REGISTRY_URL = 'docker.int.esrlabs.com'
        SERVICE_NAME = 'issue-sync'
        DOCKER_TEST_IMAGE = "${DOCKER_TEST_REGISTRY_URL}/${SERVICE_NAME}"
        DOCKER_PROD_IMAGE = "${DOCKER_PORD_REGISTRY_URL}/${SERVICE_NAME}"
        DOCKER_LATEST_TAG = "${DOCKER_TEST_IMAGE}:latest"
        DOCKER_STABLE_TAG = "${DOCKER_PROD_IMAGE}:stable"
        VAULT_TOKEN = credentials('issue-sync-github-vault-token')
        DOCKER_HOSTNAME = 'devops-tooling01.int.esrlabs.com'
    }
    stages {
        stage('Pre-build') {
            steps {
                cleanWs()
                git url: 'https://github.com/esrlabs/issue-sync.git',
                    branch: "${params.BRANCH}",
                    credentialsId: 'github-issue-sync-credentials'
                script {
                    GIT_COMMIT_HASH_SHORT = sh(script: 'git rev-parse --short HEAD', returnStdout: true).trim()
                    DOCKER_GIT_TAG = "${env.DOCKER_TEST_IMAGE}:${GIT_COMMIT_HASH_SHORT}"
                    currentBuild.displayName = params.DEPLOY == true  ? "${BRANCH}-build-deploy" : "${BRANCH}-build"
                    currentBuild.description = "GIT_SHA: ${GIT_COMMIT_HASH_SHORT}"
                }
            }
        }
        stage('Docker Build') {
            steps {
                script {
                    sh script: "docker build -t ${DOCKER_GIT_TAG} --no-cache -f docker/Dockerfile .", label: "Build Docker Image"
                }
            }
            post {
                success {
                    script {
                        if (params.BRANCH == env.MAIN_BRANCH) {
                            sh script:"docker tag ${DOCKER_GIT_TAG} ${DOCKER_STABLE_TAG}", label: "main branch: Docker stable tagging"
                        }
                        sh script:"docker tag ${DOCKER_GIT_TAG} ${DOCKER_LATEST_TAG}", label: "non-main branch: Docker latest tagging"
                    }
                }
            }
        }
        stage('Docker Image latest tag push') {
            steps {
                rtDockerPush(
                    serverId: 'esr-artifactory',
                    image: "${DOCKER_GIT_TAG}",
                    targetRepo: 'esr-docker-test-local'
                )
                 rtDockerPush(
                    serverId: 'esr-artifactory',
                    image: "${DOCKER_LATEST_TAG}",
                    targetRepo: 'esr-docker-test-local'
                )
                rtPublishBuildInfo(
                    serverId: 'esr-artifactory'
                )
            }
        }
        stage('Docker Image stable tag push') {
            when {
                expression {
                    return (params.BRANCH == env.MAIN_BRANCH && params.DEPLOY == true);
                }
            }
            steps {
                rtDockerPush(
                    serverId: 'esr-artifactory',
                    image: "${DOCKER_STABLE_TAG}",
                    targetRepo: 'esr-docker-local'
                )
                rtPublishBuildInfo(
                    serverId: 'esr-artifactory'
                )
            }
        }
        stage('Deploy Non-Prod') {
            when {
                expression {
                    return (params.BRANCH != env.MAIN_BRANCH && params.DEPLOY == true);
                }
            }
            environment{
                DOCKER_HOST = "ssh://docker_deploy@${DOCKER_HOSTNAME}"
                DEPLOY_ENV = "dev"
                PROJECT = "${env.SERVICE_NAME}-${DEPLOY_ENV}"
                DOCKER_IMAGE_DEPLOY_TAG = "${DOCKER_LATEST_TAG}"
            }
            steps {
                dir('docker') {
                    sshagent(['vault-docker-deploy-privatekey']) {
                        sh script: ("""
                            if [ \$(grep -c ${DOCKER_HOSTNAME} ~/.ssh/known_hosts) -eq 0 ]; then
                                ssh-keyscan ${DOCKER_HOSTNAME} >> ~/.ssh/known_hosts
                            fi
                                docker-compose -p ${PROJECT} stop
                                docker-compose -p ${PROJECT} down -v
                                docker pull ${DOCKER_IMAGE_DEPLOY_TAG}
                                docker-compose -p ${PROJECT} up -d
                            """), label: "deploy service"
                    }
                }
            }
        }
        stage('Deploy Prod') {
            when {
                expression {
                    return (params.BRANCH == env.MAIN_BRANCH && params.DEPLOY == true);
                }
            }
            environment{
                DOCKER_HOST = "ssh://docker_deploy@${DOCKER_HOSTNAME}"
                DEPLOY_ENV = "prod"
                PROJECT = "${env.SERVICE_NAME}-${DEPLOY_ENV}"
                DOCKER_IMAGE_DEPLOY_TAG = "${DOCKER_STABLE_TAG}"
            }
            steps {
                dir('docker') {
                    sshagent(['vault-docker-deploy-privatekey']) {
                        sh script: ("""
                            if [ \$(grep -c ${DOCKER_HOSTNAME} ~/.ssh/known_hosts) -eq 0 ]; then
                                ssh-keyscan ${DOCKER_HOSTNAME} >> ~/.ssh/known_hosts
                            fi
                                docker pull ${DOCKER_IMAGE_DEPLOY_TAG}
                                docker-compose -p ${PROJECT} up -d

                            """), label: "deploy service"
                    }
                }
            }
        }
    }
    post {
        always {
            cleanWs()
        }
    }
}