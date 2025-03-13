#!/bin/bash
set -e
#echo "Cloning repos..."
#if [ ! -d "geo_ai_backend" ]; then
#    git clone git@gitlab.compvisionsys.com:geo_ai/geo_ai_backend.git
#fi
#
#if [ ! -d "geo_ai_frontend" ]; then
#    git clone git@gitlab.compvisionsys.com:geo_ai/geo_ai_frontend.git
#fi
#
#echo "Switching to specified branch configuration"
#pushd geo_ai_backend
#git checkout develop
#popd
#pushd geo_ai_frontend
#git checkout main
#popd

echo "copying docker file"
cp ./.deploy/Dockerfile_backend ./geo_ai_backend/Dockerfile
cp ./.deploy/Dockerfile_frontend ./geo_ai_frontend/Dockerfile

echo "copying files .env"
cp ./env/.env_backend ./geo_ai_backend/.env
cp ./env/.env_frontend ./geo_ai_frontend/.env

echo "starting nextcloud"
cd nextcloud
docker compose up db -d
sleep 40
docker compose up nextcloud -d
sleep 40

echo "start cron"

# docker exec -it nextcloud-nextcloud-1 /bin/bash service cron start
docker exec -it nextcloud-nextcloud-1 bash service cron start

cd ..

echo "starting webserver"
docker compose up -d
