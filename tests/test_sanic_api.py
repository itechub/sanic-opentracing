import mock
import pytest
import unittest

import opentracing
from sanic import Sanic
from sanic_opentracing import SanicTracing


class TestValues(unittest.TestCase):
    def test_tracer(self):
        tracer = opentracing.Tracer()
        tracing = SanicTracing(tracer=tracer)
        assert tracing.tracer is tracer
        assert tracing.tracer is tracing._tracer
        assert tracing._trace_all_requests is False

    def test_global_tracer(self):
        tracing = SanicTracing()
        with mock.patch("opentracing.tracer"):
            assert tracing.tracer is opentracing.tracer
            opentracing.tracer = object()
            assert tracing.tracer is opentracing.tracer

    def test_trace_all_requests(self):
        app = Sanic("test_app")
        tracing = SanicTracing(
            tracer=opentracing.tracer, app=app, trace_all_requests=True
        )
        assert tracing._trace_all_requests is True

        tracing = SanicTracing(app=app, trace_all_requests=False)
        assert tracing._trace_all_requests is False

    def test_trace_all_requests_no_app(self):
        # when trace_all_requests is True, an app object is *required*
        with pytest.raises(ValueError):
            SanicTracing(trace_all_requests=True)

    def test_start_span_invalid(self):
        # start_span_cb need to be callable
        with pytest.raises(ValueError):
            SanicTracing(start_span_cb=0)
