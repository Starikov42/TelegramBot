#!/bin/bash

APP_NAME="nginx_balancer"

PATH_IN_CONRAINER="/static/images/"
PATH_ON_HOST="/var/www/static/images/"

docker build -t $APP_NAME .
docker rm -f $(docker ps -aq --filter name=$APP_NAME)
docker run -d \
    --network=host \
    -p 80:80 \
    -p 443:443 \
    --name $APP_NAME \
    -v $PATH_ON_HOST:$PATH_IN_CONRAINER \
    $APP_NAME
