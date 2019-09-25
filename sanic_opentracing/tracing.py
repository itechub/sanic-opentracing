from functools import wraps
from inspect import isawaitable
from typing import List, AnyStr, Callable

from sanic import Sanic
from sanic.response import HTTPResponse
from sanic.request import Request
import opentracing
from opentracing.ext import tags


class SanicTracing(opentracing.Tracer):
    def __init__(
        self,
        tracer: opentracing.tracer = None,
        app: Sanic = None,
        traced_attributes: List[AnyStr] = None,
        start_span_cb: Callable = None,
        trace_all_requests: bool = False,
        *exceptions: List[Exception],
    ):
        if start_span_cb is not None and not callable(start_span_cb):
            raise ValueError("start_span_cb is not callable")

        if trace_all_requests and app is None:
            raise ValueError(
                f"trace_all_requests={trace_all_requests} requires a non None app"
            )

        if not callable(tracer):
            self._tracer = tracer
            self._tracer_getter = None
        else:
            self._tracer = None
            self._tracer_getter = tracer

        self._trace_all_requests = trace_all_requests
        self._start_span_cb = start_span_cb
        self._current_scopes = {}
        self._exceptions_to_trace = exceptions
        self._attributes = traced_attributes or []
        self._app = app

        if self._trace_all_requests and self._app:

            @app.middleware(middleware_or_request="request")
            def start_trace(request: Request):
                self._before_request_fn(request, self._attributes)

            @app.middleware(middleware_or_request="response")
            def end_trace(request: Request, response: HTTPResponse):
                self._after_request_fn(request, response)
                return response

            if self._exceptions_to_trace:

                @app.exception(*self._exceptions_to_trace)
                def end_trace_error(request: Request, exception: Exception):
                    if exception is not None:
                        self._after_request_fn(
                            request=request, response=None, error=exception
                        )

    @property
    def tracer(self):
        if not self._tracer:
            if self._tracer_getter is None:
                return opentracing.tracer
            self._tracer = self._tracer_getter()
        return self._tracer

    def trace(self, *attributes):
        def decorator(f):
            @wraps(f)
            async def decorated_function(request, *args, **kwargs):
                if self._trace_all_requests:
                    response = f(request, *args, **kwargs)
                    if isawaitable(response):
                        return await response
                    return response

                self._before_request_fn(request, list(attributes))
                try:
                    response = f(request, *args, **kwargs)
                    if isawaitable(response):
                        response = await response
                    self._after_request_fn(request, response, None)
                    return response
                except Exception as e:
                    if self._exceptions_to_trace and e in self._exceptions_to_trace:
                        self._after_request_fn(request, None, e)
                    raise
                self._after_request_fn()

            return decorated_function

        return decorator

    def get_span(self, request=None):
        """
        Returns the span tracing `request`, or the current request if
        `request==None`.
        If there is no such span, get_span returns None.
        @param request the request to get the span from
        """
        if request is None:
            return None
        scope = self._current_scopes.get(request, None)
        return None if scope is None else scope.span

    def _before_request_fn(self, request: Request, attributes: List[AnyStr] = None):
        operation_name = request.path
        headers = {}
        for k, v in request.headers.items():
            headers[k.lower()] = v
        try:
            span_ctx = self.tracer.extract(opentracing.Format.HTTP_HEADERS, headers)
            scope = self.tracer.start_active_span(operation_name, child_of=span_ctx)
        except (
            opentracing.InvalidCarrierException,
            opentracing.SpanContextCorruptedException,
        ):
            scope = self.tracer.start_active_span(operation_name)

        self._current_scopes[repr(request)] = scope

        span = scope.span
        span.set_tag(tags.COMPONENT, "Sanic")
        span.set_tag(tags.HTTP_METHOD, request.method)
        span.set_tag(tags.HTTP_URL, request.url)
        span.set_tag(tags.SPAN_KIND, tags.SPAN_KIND_RPC_SERVER)

        for attr in attributes:
            if hasattr(request, attr):
                payload = str(getattr(request, attr))
                if payload:
                    span.set_tag(attr, payload)

        self._call_start_span_cb(span, request)

    def _after_request_fn(
        self, request: Request, response: HTTPResponse, error: Exception = None
    ):
        scope = self._current_scopes.pop(repr(request), None)
        if scope is None:
            return
        if response is not None:
            scope.span.set_tag(tags.HTTP_STATUS_CODE, response.status)

        if error is not None:
            scope.span.set_tag(tags.ERROR, True)
            scope.span.log_kv({"event": tags.ERROR, "error.object": error})
        scope.close()

    def _call_start_span_cb(self, span, request):
        if self._start_span_cb is None:
            return

        try:
            self._start_span_cb(span, request)
        except Exception:
            pass
