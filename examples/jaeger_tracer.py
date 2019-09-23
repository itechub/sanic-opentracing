import os
from jaeger_client import Config
from sanic_opentracing import SanicTracing

JAEGER_HOST = os.environ.get("JAEGER_HOST ", "localhost")

config = Config(
    config={
        "sampler": {"type": "const", "param": 1},
        "logging": True,
        "local_agent": {"reporting_host": JAEGER_HOST},
    },
    service_name="Sanic-Opentracing-Example",
)
jaeger_tracer = config.initialize_tracer()