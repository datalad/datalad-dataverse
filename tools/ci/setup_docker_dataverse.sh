#!/bin/bash
# This is setting up the (already running!) server with everything needed for
# our tests to run against this instance.
# Most importantly with respect to the CI builds, it deposits the API tokens
# for the users `pete` and `uma` in environment variabes TEST_TOKEN_PETE and
# TEST_TOKEN_UMA respectively for use from within unit tests. Therefore this
# script is supposed to be sourced.

# For administrative tasks at the beginning, we need to execute request from
# within the container, since the respective API endpoints are only accessible
# from 'localhost' (from the POV of the dataverse server). Hence, finding the
# container ID and running via `docker exec` is required.

# Note, that there are a couple more setup scripts already available in the
# container in /opt/payara/dvinstall besides the currently used `setup-users.sh`.
# We may want to use more of them.
# Consider especially init-setup.sh, setup-dvs.sh

### Initial container setup
git clone https://github.com/IQSS/dataverse-docker
docker network create traefik
cp dataverse-docker/.env_sample dataverse-docker/.env
docker-compose --file dataverse-docker/docker-compose.yml --env-file dataverse-docker/.env up -d
# On AppVeyor the server takes a while to become responsive.
# Note: We probably want to integrate the containers' `init-setup.sh`, which
# implements a way to keep probing the server until it's up rather than
# waiting a fix amount of time.
sleep 300


### Now, get users and there tokens for use with the tests
docker_id="$(docker ps -qf name="^dataverse$")"
echo "Dataverse container id: ${docker_id}"

# setup-users.sh comes with installation. Its output is some text, some JSON and
# finally two lines giving the tokens for users 'pete' and 'uma'
tokens=$(docker exec "${docker_id}" /opt/payara/dvinstall/setup-users.sh | grep "result" | awk '{print $5}')
token_pete=$(echo "${tokens}" | awk 'NR==1')
token_uma=$(echo "${tokens}" | awk 'NR==2')

# Check validity of received token for 'pete'
if [ -n "${token_pete}" ] && [ "${token_pete}" != "null" ]; then
  echo "Token for 'pete' received: ${token_pete}"
  peteResp=$(curl -H "X-Dataverse-key:${token_pete}" "http://localhost:8080/api/users/:me")
  if [ $(echo "${peteResp}" | jq .status) == "\"OK\"" ] && [ $(echo "${peteResp}" | jq .data.firstName) == "\"Pete\"" ]; then
    echo "Token confirmed."
    export TESTS_TOKEN_PETE=${token_pete}
  else
    echo "Failed to use token. User query response: ${peteResp}"
    exit 1
  fi
else
  echo "Failed to receive token for 'pete'. Got: ${token_pete}"
  exit 1
fi
# Check validity of received token for 'uma'
if [ -n "${token_uma}" ] && [ "${token_uma}" != "null" ]; then
  echo "Token for 'uma' received: ${token_uma}"
  umaResp=$(curl -H "X-Dataverse-key:${token_uma}" "http://localhost:8080/api/users/:me")
  if [ $(echo "${umaResp}" | jq .status) == "\"OK\"" ] && [ $(echo "${umaResp}" | jq .data.firstName) == "\"Uma\"" ]; then
    echo "Token confirmed."
    export TESTS_TOKEN_UMA=${token_uma}
  else
    echo "Failed to use token. User query response: ${umaResp}"
    exit 1
  fi
else
  echo "Failed to receive token for 'uma'. Got: ${token_uma}"
  exit 1
fi
