"""Custom middleware for opentelemetry"""

# import logging
from opentelemetry import trace
from decouple import config
# logging.basicConfig(level=logging.INFO)

tracer = trace.get_tracer(__name__)

class OpenTelemetryMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Code to be executed for each request before   
        # the view (and later middleware) are called.
        with tracer.start_as_current_span(
            "Tracer",
            record_exception=True,
            set_status_on_exception=True
        ) as span:
            response = self.get_response(request)
            url = request.build_absolute_uri()
            status_code = response.status_code
            # Add URL and status code as span attributes
            span.set_attribute("http.url", url)
            span.set_attribute("http.status_code", status_code)
            # Code to be executed for each request/response
            # after the view is called.
            response["Access-Control-Allow-Origin"] = config('DJANGO_APP_CONTACTLESS_BACKEND_URL')
            response["Access-Control-Allow-Methods"] = "PUT, GET, HEAD, POST, DELETE, OPTIONS"
        return response
