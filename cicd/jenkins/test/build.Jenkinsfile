pipeline {
    agent {
        label 'docker-builder'
    }
    parameters {
        string(name: 'GIT_BRANCH', defaultValue: 'main', description: 'Git Repo Branch to use')
    }
    options {
        disableConcurrentBuilds()
        buildDiscarder(logRotator(numToKeepStr: '15'))
        timestamps()
        timeout(time: 2, unit: 'HOURS')
    }
    environment {
        DOCKER_REGISTRY_URL = 'docker-test.int.esrlabs.com'
        SERVICE_NAME = 'issue-sync'
        DOCKER_IMAGE = "${DOCKER_REGISTRY_URL}/${SERVICE_NAME}"
        DOCKER_TEST_IMAGE = '${DOCKER_IMAGE}-test'
        DOCKER_STABLE_TAG = "${DOCKER_IMAGE}:stable"
    }
    stages {
        stage('GitCheckOut') {
            steps {
                cleanWs()
                withCredentials([usernamePassword(credentialsId: 'github-issue-sync-credentials', passwordVariable: 'GIT_PASSWORD', usernameVariable: 'GIT_USERNAME')]) {
                git url: 'https://github.com/esrlabs/issue-sync.git', branch: "${params.GIT_BRANCH}", credentialsId: 'github-issue-sync-credentials'
                }
            }
        }

        stage('Build Image') {
            steps {
                script {
                    def git_branch = sh(script: 'git rev-parse --abbrev-ref HEAD', returnStdout: true).replace('\n', '')
                    def date = sh(script: 'date +%Y-%m-%d-%Z-%H.%M', returnStdout: true).replace('\n', '')
                    def git_commit = sh(script: 'git rev-parse --short HEAD', returnStdout: true).trim()

                    echo "Will build Docker image based on GIT BRANCH ${git_branch} and GIT COMMIT ${git_commit}"

                    DOCKER_BUILD_TAG = "${DOCKER_IMAGE}:${git_branch}-${date}-${git_commit}"

                    DOCKER_ARTIFACTORY_TAG = "${DOCKER_IMAGE}:${git_branch}-latest"

                    sh "docker build -t ${DOCKER_BUILD_TAG} -f Dockerfile --no-cache ."
                    sh "docker tag ${DOCKER_BUILD_TAG} ${DOCKER_ARTIFACTORY_TAG}"

                    if ( params.GIT_BRANCH == 'main' && git_branch == 'main'){ 
                        sh "docker tag ${DOCKER_BUILD_TAG} ${DOCKER_STABLE_TAG}"
                    }

                }
            }
        }

        stage('Push to Artifactory') {
            steps {
                rtDockerPush(
                    serverId: 'esr-artifactory',
                    image: "${DOCKER_BUILD_TAG}",
                    targetRepo: 'esr-docker-test-local'
                )
                rtDockerPush(
                    serverId: 'esr-artifactory',
                    image: "${DOCKER_ARTIFACTORY_TAG}",
                    targetRepo: 'esr-docker-test-local'
                )
                rtPublishBuildInfo(
                    serverId: 'esr-artifactory'
                )
                rtAddInteractivePromotion(
                    serverId: 'esr-artifactory',
                    targetRepo: 'esr-docker-local',
                    comment: "Push ${DOCKER_ARTIFACTORY_TAG} image to artifactory",
                    status: 'Released',
                    sourceRepo: 'esr-docker-test-local',
                )
            }
        }

        stage('Promote to stable if main') {
            when {
                expression {
                    return params.GIT_BRANCH == 'main'
                }
            }
            steps {
                rtDockerPush(
                    serverId: 'esr-artifactory',
                    image: "${DOCKER_STABLE_TAG}",
                    targetRepo: 'esr-docker-test-local'
                )
                rtPublishBuildInfo(
                    serverId: 'esr-artifactory'
                )
                rtAddInteractivePromotion(
                    serverId: 'esr-artifactory',
                    targetRepo: 'esr-docker-local',
                    comment: "Push ${DOCKER_STABLE_TAG} image to artifactory",
                    status: 'Released',
                    sourceRepo: 'esr-docker-test-local',
                )
            }
        }

        stage('Echo docker run command') {
            steps {
                script {
                    echo "!!! ATTENTION !!! The service is set up to PRODUCTION mode and will connect to PROD KPM and PROD JIRA. Use with caution!"

                    echo "1. Make sure you have a valid token from https://vault.int.esrlabs.com and run "
                    echo "export VAULT_TOKEN=<insert_here_your_token>"

                    echo "2. If a issue-sync docker container is already running, stop and remove it with: "
                    echo "docker stop issue-sync && docker rm issue-sync"

                    echo "3. Run this command to start the container (it will pull the image automatically if connected to ESR VPN and you have access to the artifactory/registry): "
                    echo "##########################################################################################################################################################################################################"
                    echo 'docker run --detach --name "issue-sync" --label "issue-sync" -e VAULT_TOKEN=$VAULT_TOKEN --restart on-failure:5 --log-opt max-size=500m --log-opt max-file=5 docker-test.int.esrlabs.com/issue-sync:stable'
                    echo "##########################################################################################################################################################################################################"

                    echo "4. Please make sure the container is running with: "
                    echo "docker ps -a | grep issue-sync"

                    echo "5. Check the logs with: "
                    echo "docker logs --since 1h --follow issue-sync"
                    echo "or"
                    echo "docker logs --tail=150 --follow issue-sync"
                    echo "or"
                    echo "docker logs --since 2023-10-05 --follow issue-sync"

                    echo "6. If you want to restart the container, run: "
                    echo "docker restart issue-sync"

                    echo "7. Please make sure you clean the server VM from time to time from old docker images. You can do this with: "
                    echo "docker rmi -f \$(docker images -q docker-test.int.esrlabs.com/issue-sync)"

                    echo "8. For more commands check the make file inside the repo."
                }
            }
        }

    }
}