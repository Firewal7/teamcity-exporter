import base64
import logging
import sys
import time
from urllib.request import Request, urlopen
from urllib.error import URLError
import json
import os
from prometheus_client import start_http_server
from prometheus_client.core import GaugeMetricFamily
from prometheus_client.core import REGISTRY

logger = logging.getLogger('teamcity-exporter')

# Карта метрик для каждой метрики, которую мы собираем с TeamCity
# Включает:
# имя метрики
# описание метрики
# URL API для сбора метрик
# ключ метрики, который определяет, какой ключ словаря использовать
metric_map = {
    "teamcity_build_queue_length": {
        "name": "teamcity_build_queue_length",
        "description": "TeamCity Build Queue Length",
        "api_url":"/app/rest/buildQueue",
        "metric_key": "count"
    },
    "teamcity_agents_count": {
        "name": "teamcity_agents_count",
        "description": "TeamCity Agents Count",
        "api_url":"/app/rest/agents",
        "metric_key": "count",
    },
    "teamcity_disabled_agents_count": {
        "name": "teamcity_disabled_agents_count",
        "description": "TeamCity Disabled Agents Count",
        "api_url":"/app/rest/agents?locator=enabled:false",
        "metric_key": "count",
    },
    "teamcity_unauthorized_agents_count": {
        "name": "teamcity_unauthorized_agents_count",
        "description": "TeamCity Unauthorized Agents Count",
        "api_url":"/app/rest/agents?locator=authorized:false",
        "metric_key": "count",
    },
    "teamcity_disconnected_agents_count": {
        "name": "teamcity_disconnected_agents_count",
        "description": "TeamCity Disconnected Agents Count",
        "api_url":"/app/rest/agents?locator=connected:false",
        "metric_key": "count",
    },
    "teamcity_investigations_count": {
        "name": "teamcity_investigations_count",
        "description": "TeamCity Investigations Count",
        "api_url":"/app/rest/investigations",
        "metric_key": "count",
    },
    "teamcity_running_builds": {
        "name": "teamcity_running_builds",
        "description": "TeamCity Running Builds",
        "api_url":"/app/rest/builds?locator=running:true",
        "metric_key": "count",
    },
    "teamcity_hanging_builds": {
        "name": "teamcity_hanging_builds",
        "description": "TeamCity Hanging Builds",
        "api_url":"/app/rest/builds?locator=state:running,hanging:true",
        "metric_key": "count",
    },
    "teamcity_build_configuration_count" : {
        "name": "teamcity_build_configuration_count",
        "description": "TeamCity Build Configuration Count",
        "api_url": "/app/rest/buildTypes",
        "metric_key": "count"
    }

} 

logger = logging.getLogger('teamcity-exporter')

# Параметры по умолчанию, которые можно изменить
TE_LISTEN_ADDRESS = os.getenv('TE_LISTEN_ADDRESS', "0.0.0.0")
TE_LISTEN_PORT = int(os.getenv('TE_LISTEN_PORT', 9191))
TE_LOG_LEVEL = os.getenv('TE_LOG_LEVEL', "ERROR")

def setup_logger():
    logger.setLevel(logging.INFO)
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    if TE_LOG_LEVEL == "DEBUG":
        logger.setLevel(logging.DEBUG)
        debug_logger = logging.StreamHandler(sys.stdout)
        debug_logger.setLevel(logging.DEBUG)
        debug_logger.setFormatter(formatter)
        logger.addHandler(debug_logger)
    error_logger = logging.StreamHandler(sys.stderr)
    error_logger.setLevel(logging.ERROR)
    error_logger.setFormatter(formatter)
    logger.addHandler(error_logger)
    info_logger = logging.StreamHandler(sys.stdout)
    info_logger.setLevel(logging.INFO)
    info_logger.setFormatter(formatter)
    logger.addHandler(info_logger)

class TeamcityCollector(object):
    def __init__(self, token, server, port=80):
        self.token = token
        self.server = server
        self.port = port

    def collect(self):
        headers = {"Authorization": f"Bearer {self.token}", "Accept": "application/json"}

        for metric, params in metric_map.items():
            request_url = f"{self.server}{params['api_url']}"
            request = Request(request_url, headers=headers)

            try:
                result = urlopen(request)
            except URLError as e:
                logger.error(f"Ошибка отправки запроса {request_url}: {e}")
                yield self.scrape_error(1)
                continue

            try:
                json_result = json.loads(result.read())
                logger.debug(f"Полный JSON-ответ для запроса {request_url}: {json_result}")
            except Exception as e:
                logger.error(f"Ошибка разбора JSON-ответа для запроса {request_url}: {e}")
                continue

            func = lambda sample: GaugeMetricFamily(params["name"], params["description"], value=sample)

            try:
                value = json_result.get(params["metric_key"], None)
                if value is not None or params["metric_key"] == "count":
                    yield func(value)
                else:
                    logger.warning(f"Ключ {params['metric_key']} не найден в ответе для метрики {params['name']}. Ответ: {json_result}")
            except Exception as e:
                logger.error(f"Ошибка обработки значения метрики {params['name']}: {e}")

        yield self.scrape_error(0)

    def scrape_error(self, sample):
        return GaugeMetricFamily("teamcity_scrape_error", "Если экспортер смог вызвать методы API", value=sample)

def main():
    setup_logger()

    TE_API_TOKEN = os.getenv('TE_API_TOKEN')

    if not TE_API_TOKEN:
        logger.error("TE_API_TOKEN env не определен")
        sys.exit(1)

    TE_API_URL = os.getenv('TE_API_URL').strip("/")

    REGISTRY.register(TeamcityCollector(TE_API_TOKEN, TE_API_URL))
    
    try:
        start_http_server(port=TE_LISTEN_PORT, addr=TE_LISTEN_ADDRESS)
    except Exception as e:
        logger.error(f"Не удалось запустить HTTP-сервер: {e}")
        sys.exit(1)

    logger.info(f"Начало прослушивания на {TE_LISTEN_ADDRESS}:{TE_LISTEN_PORT}")
    while True:
        try:
            time.sleep(1)
        except KeyboardInterrupt:
            logger.info("Остановка сервера...")
            sys.exit(0)

if __name__ == '__main__':
    main()
