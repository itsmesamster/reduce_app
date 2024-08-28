# 3rd party
from fastapi import FastAPI
from prometheus_client import make_asgi_app
from prometheus_client.exposition import basic_auth_handler  #  noqa: F401


# project


# Create app
monitor_api = FastAPI(debug=False)


# Add prometheus asgi middleware to route /metrics requests
metrics_app = make_asgi_app()
monitor_api.mount("/metrics", metrics_app)
