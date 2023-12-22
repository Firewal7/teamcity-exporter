## Teamcity Prometheus Exporter

Все значения в docker.env меняем на свои.

#### Собираем образ:
```
docker build -t project/teamcity-exporter:latest .
```
#### Запускаем контейнер:
```
docker run -it -p 9191:9191 --env-file docker.env project/teamcity-exporter:latest

http://192.168.0.6:9191 
```
```
#### Default envs
* TE_LISTEN_ADDRESS=0.0.0.0
* TE_LISTEN_PORT=9191
* TE_LOG_LEVEL=INFO

#### Exposed metrics
* teamcity_build_queue_length
* teamcity_agents_count
* teamcity_disabled_agents_count
* teamcity_unauthorized_agents_count
* teamcity_disconnected_agents_count
* teamcity_investigations_count
* teamcity_running_builds
```