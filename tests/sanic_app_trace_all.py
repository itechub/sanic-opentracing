#! /usr/bin/env python
# -*- coding: utf-8 -*-
# vim:fenc=utf-8
from sanic import Sanic, request, response
import opentracing
from opentracing.ext import tags
from opentracing.mocktracer import MockTracer
from sanic_opentracing import SanicTracing
import aiohttp


app = Sanic(__name__)
test_app = app.test_client
tracing = SanicTracing(tracer=MockTracer(), app=app, trace_all_requests=True, exceptions=[RuntimeError,])

@app.listener('before_server_start')
async def init(app, loop):
    app.aiohttp_session = aiohttp.ClientSession(loop=loop)

@app.listener('after_server_stop')
def finish(app, loop):
    loop.run_until_complete(app.aiohttp_session.close())
    loop.close()

@app.route("/test")
def check_test_works(request):
    return response.text("Test")

@app.route("/decorated_test")
@tracing.trace()
def decorated_fn_simple(request):
    return response.text("Decorated Test")


@app.route("/error_test")
@tracing.trace()
def decorated_fn_with_error(request):
    raise RuntimeError("Should not happen")


@app.route("/decorated_child_span_test")
@tracing.trace()
def decorated_fn_with_child_span(request):
    with tracing.tracer.start_active_span("child"):
        return response.text("Success")


@app.route("/wire")
@tracing.trace()
async def send_request(request):
    span = tracing.get_span(request)
    headers = {}
    tracing.tracer.inject(span.context, opentracing.Format.TEXT_MAP, headers)
    res = await app.aiohttp_session.get(f"http://{request.host}/test") 
    return response.text("wire")
