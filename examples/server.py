from sanic import Sanic
from sanic import response
from sanic_opentracing import SanicTracing
from jaeger_tracer import jaeger_tracer

app = Sanic(__name__)
_tracing = SanicTracing(tracer=jaeger_tracer, trace_all_requests=True, app=app)


@app.route("/example1")
async def example1(request):
    return response.json("example1")


@app.route("/example2")
async def example2(request):
    return response.json("example2")


@app.route("/log")
@_tracing.trace()
def log(request):
    # Extract the span information for request object.
    with jaeger_tracer.start_active_span(
        "python webserver internal span of log method"
    ) as scope:
        a = 1
        b = 2
        c = a + b
        scope.span.log_kv({"event": "my computer knows math!", "result": c})
        return response.json("log")


if __name__ == "__main__":
    app.run(port=8000, host="0.0.0.0", debug=True)
