#!/bin/bash
set -e -u
# This script is meant to setup the inital users and data for datalad-dataverse's
# tests. It is supposed to be run from within the container (as root) and called
# accordingly by setup_docker_dataverse.sh

SERVER=http://localhost:8080/api
curl -X PUT -d burrito $SERVER/admin/settings/BuiltinUsers.KEY

# create our admin
admin=$(curl -s -H "Content-type:application/json" -X POST -d @data/dladmin.json "$SERVER/builtin-users?password=dladmin1&key=burrito")
adminToken=$(echo "$admin" | jq .data.apiToken | tr -d \")
printf "\n%b\n" "Token for testadmin: ${adminToken}"
# Actually make superuser:
# TODO: double check output and possibly swallow/analyze
curl -X POST "http://localhost:8080/api/admin/superuser/testadmin"

# a second user
userOne=$(curl -s -H "Content-type:application/json" -X POST -d @data/user1.json "$SERVER/builtin-users?password=password1&key=burrito")
userOneToken=$(echo "$userOne" | jq .data.apiToken | tr -d \")
printf "\n%b\n" "Token for user1: ${userOneToken}"

# a root dataverse:
# TODO: double check output and possibly swallow/analyze
curl -s -H "Content-type:application/json" -X POST -d @data/root-dv.json "$SERVER/dataverses/root?key=$adminToken"

