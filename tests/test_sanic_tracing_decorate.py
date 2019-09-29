import unittest
from unittest import mock
from sanic.request import Request
from sanic.response import HTTPResponse
import opentracing
from opentracing.ext import tags
from opentracing.mocktracer import MockTracer
from sanic_opentracing import SanicTracing

from .sanic_app_trace_decorate import app, test_app, tracing


class TestTracing(unittest.TestCase):
    def setUp(self):
        tracing.tracer.reset()

    def test_route_without_tracing(self):
        request, response = test_app.get("/test")

    def test_decorated_route(self):
        request, response = test_app.get("/decorated_test")

    def test_span_tags(self):
        request, response = test_app.get("/decorated_test")
        spans = tracing.tracer.finished_spans()
        assert len(spans) == 1
        assert spans[0].tags == {
            tags.COMPONENT: "Sanic",
            tags.HTTP_METHOD: "GET",
            tags.HTTP_STATUS_CODE: response.status_code,
            tags.SPAN_KIND: tags.SPAN_KIND_RPC_SERVER,
            tags.HTTP_URL: request.url,
        }

    def test_attributes_tags(self):
        request, response = test_app.get("/attributes_test")
        spans = tracing.tracer.finished_spans()
        assert len(spans) == 1
        assert spans[0].tags == {
            tags.COMPONENT: "Sanic",
            tags.HTTP_METHOD: "GET",
            tags.HTTP_STATUS_CODE: response.status_code,
            tags.SPAN_KIND: tags.SPAN_KIND_RPC_SERVER,
            tags.HTTP_URL: request.url,
            "url": request.url,
            "method": "GET",
            "ip": "127.0.0.1"
        }

    def test_error(self):
        try:
            test_app.get("/error_test")
        except RuntimeError:
            pass

        assert len(tracing._current_scopes) == 0

        spans = tracing.tracer.finished_spans()
        assert len(spans) == 1
        self._verify_error(spans[0])

        # Decorator.
        spans = tracing.tracer.finished_spans()
        assert len(spans) == 1
        self._verify_error(spans[0])

    def _verify_error(self, span):
        assert span.tags.get(tags.ERROR) is True
        assert len(span.logs) == 1
        assert span.logs[0].key_values.get("event", None) is tags.ERROR
        assert isinstance(
            span.logs[0].key_values.get("error.object", None), RuntimeError
        )

    def test_over_wire(self):
        request, response = test_app.get("/wire")
        assert "OK" in str(response.status_code)

        spans = tracing.tracer.finished_spans()
        assert len(spans) == 2
        assert spans[0].context.trace_id == spans[1].context.trace_id
        assert spans[0].parent_id == spans[1].context.span_id

    def test_child_span(self):
        request, response = test_app.get("/decorated_child_span_test")
        assert "OK" in str(response.status_code)

        spans = tracing.tracer.finished_spans()
        assert len(spans) == 2
        assert spans[0].context.trace_id == spans[1].context.trace_id
        assert spans[0].parent_id == spans[1].context.span_id


class TestTracingStartSpanCallback(unittest.TestCase):
    def test_simple(self):
        def start_span_cb(span, request):
            span.set_tag("component", "not-sanic")
            span.set_tag("utag", "uvalue")

        tracing = SanicTracing(
            tracer=MockTracer(),
            app=app,
            trace_all_requests=True,
            start_span_cb=start_span_cb,
        )
        request, response = test_app.get("/test")
        assert "OK" in str(response.status_code)

        spans = tracing.tracer.finished_spans()
        assert len(spans) == 1
        assert spans[0].tags.get(tags.COMPONENT, None) == "not-sanic"
        assert spans[0].tags.get("utag", None) == "uvalue"

    def test_error(self):
        def start_span_cb(span, request):
            raise RuntimeError("Should not happen")

        tracing = SanicTracing(
            tracer=MockTracer(),
            app=app,
            trace_all_requests=True,
            start_span_cb=start_span_cb,
        )
        request, response = test_app.get("/test")
        assert "OK" in str(response.status_code)

        spans = tracing.tracer.finished_spans()
        assert len(spans) == 1
        assert spans[0].tags.get(tags.ERROR, None) is None
