#!/bin/bash
set -e -u
# This is setting up and launching a docker container with everything needed for
# our tests to run against this instance.
# Most importantly with respect to the CI builds, it deposits the API tokens
# for the users `testadmin` and `user1` in environment variables
# DATAVERSE_TEST_APITOKEN_TESTADMIN and DATAVERSE_TEST_APITOKEN_USER1
# respectively for use from within unit tests. Therefore this script is supposed
# to be sourced.

# For administrative tasks at the beginning, we need to execute request from
# within the container, since the respective API endpoints are only accessible
# from 'localhost' (from the POV of the dataverse server). Hence, finding the
# container ID and running via `docker exec` is required.

# Note, that there are a couple more setup scripts already available in the
# container in /opt/payara/dvinstall besides the currently used `setup-users.sh`.
# We may want to use more of them.
# Consider especially init-setup.sh, setup-dvs.sh

# log into Dockerhub to pull more images if the required variables are passed
if [[ ! -z "$1" ]] && [[ ! -z "$2" ]]; then
  DOCKERHUB_TOKEN="$1"
  DOCKERHUB_USERNAME="$2"
  docker login --password ${DOCKERHUB_TOKEN} --username ${DOCKERHUB_USERNAME}
fi

### Initial container setup
git clone https://github.com/IQSS/dataverse-docker
docker network create traefik
cp dataverse-docker/.env_sample dataverse-docker/.env
docker-compose --file dataverse-docker/docker-compose.yml --env-file dataverse-docker/.env up -d
# Wait for the API to become responsive. Note, that on AppVeyor it has been seen
# to take more than 4 minutes. However, time out after 10 min.
counter=0
set +e
# Note: `tee >(cat 1>&2)` does copy stdout to stderr in order see what was the
# actual output of curl in the CI log despite it being piped into `jq`.
# curl's `--silent --show-error`, disables displaying metrics for every single
# trial, polluting the log with useless information, while actual error
# messages still show up.
until [ "$(curl --silent --show-error "http://localhost:8080/api/search?q=whatever" | tee >(cat 1>&2) | jq .status)" == "\"OK\"" ]
do
  if [ $counter -gt 60 ]; then
    echo "Dataverse API unresponsive after 10 minutes. Giving up."
    exit 1
  fi
  sleep 10
  ((counter++))
done
set -e

# Dataverse is running, export base URL for test environment
export DATAVERSE_TEST_BASEURL="http://localhost:8080"

### Now, get users and there tokens for use with the tests
docker_id="$(docker ps -qf name="^dataverse$")"
echo "Dataverse container id: ${docker_id}"

# Put our data definitions in the container, so the setup API requests
# executed from within can access them:
docker cp tools/ci/dladmin.json "${docker_id}:/opt/payara/dvinstall/data/dladmin.json"
docker cp tools/ci/user1.json "${docker_id}:/opt/payara/dvinstall/data/user1.json"
docker cp tools/ci/root-dv.json "${docker_id}:/opt/payara/dvinstall/data/root-dv.json"
docker cp tools/ci/init_dataverse.sh "${docker_id}:/opt/payara/dvinstall/init_dataverse.sh"


# setup-users.sh comes with installation. Its output is some text, some JSON and
# finally two lines giving the tokens for users 'testadmin' and 'user1'
initresponse=$(docker exec "${docker_id}" /opt/payara/dvinstall/init_dataverse.sh)
tokens=$(echo "$initresponse" | grep "Token for" | awk '{print $4}')

token_admin=$(echo "${tokens}" | awk 'NR==1')
token_userone=$(echo "${tokens}" | awk 'NR==2')

# Check validity of received token for 'testadmin'
if [ -n "${token_admin}" ] && [ "${token_userone}" != "null" ]; then
  echo "Token for 'testadmin' received: ${token_admin}"
  adminResp=$(curl -H "X-Dataverse-key:${token_admin}" "http://localhost:8080/api/users/:me")
  if [ $(echo "${adminResp}" | jq .status) == "\"OK\"" ] && [ $(echo "${adminResp}" | jq .data.firstName) == "\"Datalad\"" ]; then
    echo "Token confirmed."
    export DATAVERSE_TEST_APITOKEN_TESTADMIN=${token_admin}
  else
    echo "Failed to use token. User query response: ${adminResp}"
    exit 1
  fi
else
  echo "Failed to receive token for 'testadmin'. Got: ${token_admin}"
  exit 1
fi
# Check validity of received token for 'uma'
if [ -n "${token_userone}" ] && [ "${token_userone}" != "null" ]; then
  echo "Token for 'user1' received: ${token_userone}"
  useroneResp=$(curl -H "X-Dataverse-key:${token_userone}" "http://localhost:8080/api/users/:me")
  if [ $(echo "${useroneResp}" | jq .status) == "\"OK\"" ] && [ $(echo "${useroneResp}" | jq .data.firstName) == "\"Regular\"" ]; then
    echo "Token confirmed."
    export DATAVERSE_TEST_APITOKEN_USER1=${token_userone}
  else
    echo "Failed to use token. User query response: ${useroneResp}"
    exit 1
  fi
else
  echo "Failed to receive token for 'user1'. Got: ${token_userone}"
  exit 1
fi
