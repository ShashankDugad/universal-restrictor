"""
OpenTelemetry distributed tracing setup.
"""
import os
import logging

logger = logging.getLogger(__name__)

TRACING_ENABLED = False
tracer = None

def setup_tracing(service_name: str = "universal-restrictor"):
    """Initialize OpenTelemetry tracing."""
    global TRACING_ENABLED, tracer
    
    otlp_endpoint = os.getenv("OTLP_ENDPOINT")
    if not otlp_endpoint:
        logger.info("OTLP_ENDPOINT not set - tracing disabled")
        return
    
    try:
        from opentelemetry import trace
        from opentelemetry.sdk.trace import TracerProvider
        from opentelemetry.sdk.trace.export import BatchSpanProcessor
        from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
        from opentelemetry.sdk.resources import Resource
        
        resource = Resource.create({"service.name": service_name})
        provider = TracerProvider(resource=resource)
        
        exporter = OTLPSpanExporter(endpoint=otlp_endpoint)
        processor = BatchSpanProcessor(exporter)
        provider.add_span_processor(processor)
        
        trace.set_tracer_provider(provider)
        tracer = trace.get_tracer(__name__)
        
        TRACING_ENABLED = True
        logger.info(f"OpenTelemetry tracing enabled: {otlp_endpoint}")
        
    except ImportError:
        logger.warning("OpenTelemetry not installed - pip install opentelemetry-api opentelemetry-sdk opentelemetry-exporter-otlp")
    except Exception as e:
        logger.error(f"Failed to setup tracing: {e}")

def get_tracer():
    """Get the tracer instance."""
    return tracer

def trace_span(name: str):
    """Decorator to trace a function."""
    def decorator(func):
        if not TRACING_ENABLED or tracer is None:
            return func
        
        def wrapper(*args, **kwargs):
            with tracer.start_as_current_span(name):
                return func(*args, **kwargs)
        return wrapper
    return decorator
