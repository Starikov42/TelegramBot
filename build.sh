docker-compose rm -f
docker-compose pull
docker-compose --project-name tg_bot up --build -d
# docker-compose stop -t 1