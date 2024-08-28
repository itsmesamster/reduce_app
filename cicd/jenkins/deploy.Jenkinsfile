pipeline {
  agent {
    label 'docker-deploy'
  }
  options {
    disableConcurrentBuilds()
    buildDiscarder(logRotator(numToKeepStr: '15'))
  }
  environment {
    DOCKER_HOSTNAME = 'devops-tooling01.int.esrlabs.com'
    DOCKER_HOST = "ssh://docker_deploy@${DOCKER_HOSTNAME}"
  }
  stages {
    stage('Deploy') {
      steps {
            sshagent(['vault-docker-deploy-privatekey']) {
                sh("""
                if [ \$(grep -c ${DOCKER_HOSTNAME} ~/.ssh/known_hosts) -eq 0 ]; then
                    ssh-keyscan ${DOCKER_HOSTNAME} >> ~/.ssh/known_hosts
                fi
                docker run --detach --name "issue-sync" --label "issue-sync" -e VAULT_TOKEN=$VAULT_TOKEN --restart on-failure:5 --log-opt max-size=500m --log-opt max-file=5 docker-test.int.esrlabs.com/issue-sync:stable
                """)
            }
        }
    }
  }
}