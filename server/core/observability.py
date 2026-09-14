"""Prometheus 指标和 OpenTelemetry 链路追踪。"""
import logging
import time

from fastapi import FastAPI, Request
from prometheus_client import Counter, Histogram, make_asgi_app

from core.config import settings

logger = logging.getLogger(__name__)
REQUESTS = Counter("http_requests_total", "HTTP requests", ["method", "route", "status"])
LATENCY = Histogram("http_request_duration_seconds", "HTTP request latency", ["method", "route"])


def setup_observability(app: FastAPI, engine) -> None:
    @app.middleware("http")
    async def metrics_middleware(request: Request, call_next):
        started = time.perf_counter()
        response = await call_next(request)
        route = request.scope.get("route")
        route_path = getattr(route, "path", "unmatched")
        REQUESTS.labels(request.method, route_path, response.status_code).inc()
        LATENCY.labels(request.method, route_path).observe(time.perf_counter() - started)
        return response

    app.mount("/metrics", make_asgi_app())
    if not settings.otel_exporter_otlp_endpoint:
        return
    try:
        from opentelemetry import trace
        from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
        from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
        from opentelemetry.instrumentation.sqlalchemy import SQLAlchemyInstrumentor
        from opentelemetry.sdk.resources import Resource
        from opentelemetry.sdk.trace import TracerProvider
        from opentelemetry.sdk.trace.export import BatchSpanProcessor

        provider = TracerProvider(resource=Resource.create({"service.name": settings.otel_service_name}))
        provider.add_span_processor(BatchSpanProcessor(OTLPSpanExporter(endpoint=settings.otel_exporter_otlp_endpoint)))
        trace.set_tracer_provider(provider)
        FastAPIInstrumentor.instrument_app(app)
        SQLAlchemyInstrumentor().instrument(engine=engine)
    except Exception:
        logger.exception("OpenTelemetry initialization failed", extra={"event": "otel_init_failed"})
