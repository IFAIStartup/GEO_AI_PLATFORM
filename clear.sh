#!/bin/bash

echo "Clear docker container"
docker stop $(docker ps -a -q)
echo "Clear docker iamges"
docker rm $(docker ps -a -q); docker rmi $(docker images -a -q);

echo "rm nextcloud"
cd nextcloud
rm -rf pgdata
rm -rf '2. Init Database'

echo "rm repo"
cd ..
rm -rf geo_ai_backend
rm -rf geo_ai_frontend
rm -rf pgdata
rm -rf pgadmin
rm -rf queries.yaml
rm -rf '2. Init Database'

