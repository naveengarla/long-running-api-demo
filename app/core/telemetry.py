from opentelemetry import trace
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.instrumentation.sqlalchemy import SQLAlchemyInstrumentor
from opentelemetry.instrumentation.celery import CeleryInstrumentor
import os

def init_tracer(service_name: str):
    # check if OTEL_EXPORTER_OTLP_ENDPOINT is set
    if not os.getenv("OTEL_EXPORTER_OTLP_ENDPOINT"):
        print("OTEL_EXPORTER_OTLP_ENDPOINT not set, skipping telemetry.")
        return

    resource = Resource.create(attributes={"service.name": service_name})
    tracer_provider = TracerProvider(resource=resource)
    trace.set_tracer_provider(tracer_provider)
    
    # OTLP Exporter (defaults to localhost:4317 or uses env var)
    otlp_exporter = OTLPSpanExporter()
    
    span_processor = BatchSpanProcessor(otlp_exporter)
    tracer_provider.add_span_processor(span_processor)

def instrument_fastapi(app):
    if os.getenv("OTEL_EXPORTER_OTLP_ENDPOINT"):
        FastAPIInstrumentor.instrument_app(app)
        SQLAlchemyInstrumentor().instrument(enable_commenter=True, comment_check_query=True)

def instrument_celery(app):
     if os.getenv("OTEL_EXPORTER_OTLP_ENDPOINT"):
        CeleryInstrumentor().instrument()
        SQLAlchemyInstrumentor().instrument(enable_commenter=True, comment_check_query=True)
