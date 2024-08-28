.DEFAULT_GOAL := build


REGISTRY_URL=docker-test.int.esrlabs.com
DEPLOY_HOSTNAME=docker01.int.esrlabs.com
REPO_NAME=issue-sync
GIT_BRANCH := $(shell git rev-parse --abbrev-ref HEAD)
GIT_COMMIT := $(shell git rev-parse --short HEAD)
DATE := $(shell date +%Y-%m-%d-%Z-%H.%M)
MAX_LOGS=--log-opt max-size=500m --log-opt max-file=5
IMAGE_TAG=${GIT_BRANCH}-${DATE}-${GIT_COMMIT}

git_clone_ssh:
	git clone git@github.com:esrlabs/${REPO_NAME}.git

run_echo:
	@echo " ------- Have you exported locally the VAULT_TOKEN env var based on the Dockerfile VAULT_URL ? ------- "

##################### KPM TO JIRA SERVICE #####################
K2J_IMAGE_NAME=${REPO_NAME}-kpm-to-jira

k2j_echoo:
	@echo "REGISTRY URL: ${K2J_IMAGE_NAME}"
	@echo "IMAGE_NAME:   ${K2J_IMAGE_NAME}"
	@echo "IMAGE_TAG:    ${IMAGE_TAG}"

# MAIN DOCKER COMMANDS / MAKE TARGETS
# run with e.g.: make k2j_build

# Build the service container
k2j_build: k2j_echoo k2j_clean
	docker build -t ${REGISTRY_URL}/${K2J_IMAGE_NAME}:${IMAGE_TAG} -f docker/Dockerfile.hcp5_kpm2jira .

# Run the container
k2j_run: k2j_build run_echo
	docker run --detach --name "${K2J_IMAGE_NAME}" --label "${K2J_IMAGE_NAME}" -e VAULT_TOKEN=$$ISSUE_SYNC_VAULT_TOKEN --restart on-failure:5 ${MAX_LOGS} ${REGISTRY_URL}/${K2J_IMAGE_NAME}:${IMAGE_TAG}
	make k2j_logs

k2j_logs:
	docker logs --tail=150 --follow $$(docker ps -a -q --filter=label=${K2J_IMAGE_NAME})

# Run service unit tests inside docker container
# optional: run --detach 
k2j_test:
	docker build -t ${K2J_IMAGE_NAME}-test:${IMAGE_TAG}-test -f docker/tests/Dockerfile.test_hcp5_kpm2jira .
	docker run --detach --label "${K2J_IMAGE_NAME}-test" --name "${K2J_IMAGE_NAME}-test" ${K2J_IMAGE_NAME}-test:${IMAGE_TAG}-test

k2j_clean_test:
	-docker stop $$(docker ps -a -q --filter=label=${K2J_IMAGE_NAME}-test)
	-docker rm -f $$(docker ps -a -q --filter=label=${K2J_IMAGE_NAME}-test)
	-docker rmi -f $$(docker images -q ${K2J_IMAGE_NAME}-test)

k2j_clean: k2j_clean_test
	-docker stop $$(docker ps -a -q --filter=label=${K2J_IMAGE_NAME})
	-docker rm -f $$(docker ps -a -q --filter=label=${K2J_IMAGE_NAME})
	-docker rmi -f $$(docker images -q ${REGISTRY_URL}/${K2J_IMAGE_NAME})
	-docker rmi -f $$(docker images -q ${K2J_IMAGE_NAME})

k2j_stop:
	-docker stop $$(docker ps -a -q --filter=label=${K2J_IMAGE_NAME})

k2j_restart:
	docker restart $$(docker ps -a -q --filter=label=${K2J_IMAGE_NAME})
	make k2j_logs

k2j_push:
	docker push ${REGISTRY_URL}/${K2J_IMAGE_NAME}:${IMAGE_TAG}

k2j_pull: k2j_clean
	docker pull ${REGISTRY_URL}/${K2J_IMAGE_NAME}:${IMAGE_TAG}


##################### JIRA TO JIRA SERVICE #####################
J2J_IMAGE_NAME=${REPO_NAME}-jira-to-jira

j2j_echoo:
	@echo "REGISTRY URL: ${J2J_IMAGE_NAME}"
	@echo "IMAGE_NAME:   ${J2J_IMAGE_NAME}"
	@echo "IMAGE_TAG:    ${IMAGE_TAG}"

# MAIN DOCKER COMMANDS / MAKE TARGETS
# run with e.g.: make j2j_build

# Build the service container
j2j_build: j2j_echoo j2j_clean
	docker build -t ${REGISTRY_URL}/${J2J_IMAGE_NAME}:${IMAGE_TAG} -f docker/Dockerfile.hcp5_jira2jira .

# Run the container
j2j_run: j2j_build run_echo
	docker run --detach --name "${J2J_IMAGE_NAME}" --label "${J2J_IMAGE_NAME}" -e VAULT_TOKEN=$$ISSUE_SYNC_VAULT_TOKEN --restart on-failure:5 ${MAX_LOGS} ${REGISTRY_URL}/${J2J_IMAGE_NAME}:${IMAGE_TAG}
	make j2j_logs

j2j_logs:
	docker logs --tail=150 --follow $$(docker ps -a -q --filter=label=${J2J_IMAGE_NAME})

# Run service unit tests inside docker container
# optional: run --detach 
j2j_test:
	docker build -t ${J2J_IMAGE_NAME}-test:${IMAGE_TAG}-test -f docker/tests/Dockerfile.test_hcp5_jira2jira .
	docker run --detach --label "${J2J_IMAGE_NAME}-test" --name "${J2J_IMAGE_NAME}-test" ${J2J_IMAGE_NAME}-test:${IMAGE_TAG}-test

j2j_clean_test:
	-docker stop $$(docker ps -a -q --filter=label=${J2J_IMAGE_NAME}-test)
	-docker rm -f $$(docker ps -a -q --filter=label=${J2J_IMAGE_NAME}-test)
	-docker rmi -f $$(docker images -q ${J2J_IMAGE_NAME}-test)

j2j_clean: j2j_clean_test
	-docker stop $$(docker ps -a -q --filter=label=${J2J_IMAGE_NAME})
	-docker rm -f $$(docker ps -a -q --filter=label=${J2J_IMAGE_NAME})
	-docker rmi -f $$(docker images -q ${REGISTRY_URL}/${J2J_IMAGE_NAME})
	-docker rmi -f $$(docker images -q ${J2J_IMAGE_NAME})

j2j_stop:
	-docker stop $$(docker ps -a -q --filter=label=${J2J_IMAGE_NAME})

j2j_restart:
	docker restart $$(docker ps -a -q --filter=label=${J2J_IMAGE_NAME})
	make j2j_logs

j2j_push:
	docker push ${REGISTRY_URL}/${J2J_IMAGE_NAME}:${IMAGE_TAG}

j2j_pull: j2j_clean
	docker pull ${REGISTRY_URL}/${J2J_IMAGE_NAME}:${IMAGE_TAG}