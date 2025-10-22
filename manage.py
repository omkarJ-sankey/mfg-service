#!/usr/bin/env python
"""Django's command-line utility for administrative tasks."""
import os
import sys
from decouple import config

from opentelemetry.instrumentation.django import DjangoInstrumentor
from opentelemetry.instrumentation.requests import RequestsInstrumentor

try:
    from django.core.management import execute_from_command_line
except ImportError as exc:
    raise ImportError(
        """Couldn't import Django. Are you sure it's installed and
        available on your PYTHONPATH environment variable?
        Did youforget to activate a virtual environment?"""
    ) from exc


def main():
    """Run administrative tasks."""
    if config("DJANGO_APP_TYPE_BACKEND") == "true":
        os.environ.setdefault(
            "DJANGO_SETTINGS_MODULE", "backendServices.settings"
        )

    if config("DJANGO_APP_TYPE_ADMIN") == "true":
        os.environ.setdefault(
            "DJANGO_SETTINGS_MODULE", "adminServices.settings"
        )
    
    DjangoInstrumentor().instrument()
    RequestsInstrumentor().instrument()
    execute_from_command_line(sys.argv)


if __name__ == "__main__":
    main()
