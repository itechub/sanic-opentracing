# Sanic OpenTracing

This package enables distributed tracing in Sanic applications via [The OpenTracing Project][opentracing]. Once a production system contends with real concurrency or splits into many services, crucial (and formerly easy) tasks become difficult:

* user-facing latency optimization
* root-cause analysis of backend errors 
* communication about distinct pieces of a now-distributed system

Distributed tracing follows a request on its journey from inception to completion from mobile/browser all the way to the microservices. 

As core services and libraries adopt OpenTracing, the application builder is no longer burdened with the task of adding basic tracing instrumentation to their own code. In this way, developers can build their applications with the tools they prefer and benefit from built-in tracing instrumentation. OpenTracing implementations exist for major distributed tracing systems and can be bound or swapped with a one-line configuration change.

If you want to learn more about the underlying python API, visit the python [source code][opentracing-python].


[openTracing]: http://opentracing.io/
[opentracing-python]: https://github.com/opentracing/opentracing-python

## Installation

Run the following command:

```
 $ pip install sanic_opentracing
```    

## Usage

This Sanic extension allows for tracing of Sanic apps using the OpenTracing API. All
that it requires is for a `SanicTracing` tracer to be initialized using an
instance of an OpenTracing tracer. You can either trace all requests to your site, or use function decorators to trace certain individual requests.

**Note:** `optional_args` in both cases are any number of attributes (as strings) of `sanic.Request` that you wish to set as tags on the created span

### Initialize

`SanicTracing` wraps the tracer instance that's supported by opentracing. To create a `SanicTracing` object, you can either pass in a tracer object directly or a callable that returns the tracer object. For example:

```
from sanic_opentracing import SanicTracing

opentracing_tracer = ## some OpenTracing tracer implementation
tracing = SanicTracing(tracer=opentracing_tracer, ...)
```
or

```
from sanic_opentracing import SanicTracing

def initialize_tracer():
    ...
    return opentracing_tracer
tracing = SanicTracing(tracer=opentracing_tracer, ...)
```

### Trace All Requests
Setting `trace_all_requests` to `Ture` when making the initialization. Normally, you maybe want to it to be configurable by environment variable.

```
from sanic_opentracing import SanicTracing

app = Sanic(__name__)
opentracing_tracer = ## some OpenTracing tracer implementation
tracing = SanicTracing(tracer=jaeger_tracer, trace_all_requests=True, app=app, [optional_args])
```

### Trace Individual Requests
Use the `@tracing.trace()` decorate to specify trace routes.

```
from sanic_opentracing import SanicTracing

app = Sanic(__name__)

opentracing_tracer = ## some OpenTracing tracer implementation  
tracing = SanicTracing(opentracing_tracer)

@app.route('/some_url')
@tracing.trace(optional_args)
def some_view_func():
	...     
	return some_view 
```

### Accessing Spans Manually

In order to access the span for a request, we've provided a method `SanicTracing.get_span(request)` that returns the span for the request, if it is exists and is not finished. This can be used to log important events to the span, set tags, or create child spans to trace non-RPC events. If no request is passed in, the current request will be used.

### Tracing an RPC

If you want to make an RPC and continue an existing trace, you can inject the current span into the RPC. For example, if making an http request, the following code will continue your trace across the wire:

```
@tracing.trace()
def some_view_func(request):
    new_request = some_http_request
    current_span = tracing.get_span(request)
    text_carrier = {}
    opentracing_tracer.inject(span, opentracing.Format.TEXT_MAP, text_carrier)
    for k, v in text_carrier.iteritems():
        new_request.add_header(k,v)
    ... # make request
```

## Examples

See [Examples](examples/) to view and run an example of Sanic applications with integrated OpenTracing tracers.

## Development Workflow

## References
- [Flask Opentracing](https://github.com/opentracing-contrib/python-flask)
- [Sanic Framework](https://github.com/huge-success/sanic)

