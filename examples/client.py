import requests
import time
from jaeger_tracer import jaeger_tracer

WEBSERVER_HOST = "localhost"
WEBSERVER_PORT = 8000

url = f"http://{WEBSERVER_HOST}:{WEBSERVER_PORT}/log".format(WEBSERVER_HOST)
requests.get(url)

url = f'http://{WEBSERVER_HOST}:{WEBSERVER_PORT}/example1'
requests.get(url)

url = f'http://{WEBSERVER_HOST}:{WEBSERVER_PORT}/example2'
requests.get(url)

# allow tracer to flush the spans - https://github.com/jaegertracing/jaeger-client-python/issues/50
time.sleep(2)
jaeger_tracer.close()
