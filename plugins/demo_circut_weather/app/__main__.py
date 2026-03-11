import logging
import os
import click
import sys
from typing import Optional

from starlette.applications import Starlette
from starlette.requests import Request
from starlette.routing import Mount, Route
from starlette.responses import JSONResponse, PlainTextResponse
#from weather import get_alerts, get_forecast

import uvicorn
from fastmcp import FastMCP, Context
from oauth2_middleware import OAuth2Middleware
from fastmcp_instantiator import mcp_application
from properties import CIRCUIT_LLM_API_APP_KEY, CIRCUIT_LLM_API_CLIENT_ID, CIRCUIT_LLM_API_ENDPOINT, CIRCUIT_LLM_API_MODEL_NAME, CIRCUIT_LLM_API_VERSION, JWKS_URI, AUDIENCE, ISSUER, CIRCUIT_CLIENT_ID, CIRCUIT_LLM_API_CLIENT_SECRET

os.environ["CIRCUIT_LLM_API_APP_KEY"] = CIRCUIT_LLM_API_APP_KEY
os.environ["CIRCUIT_LLM_API_CLIENT_ID"] = CIRCUIT_LLM_API_CLIENT_ID
os.environ["CIRCUIT_LLM_API_CLIENT_SECRET"] = CIRCUIT_LLM_API_CLIENT_SECRET
os.environ["CIRCUIT_LLM_API_ENDPOINT"] = CIRCUIT_LLM_API_ENDPOINT
os.environ["CIRCUIT_LLM_API_MODEL_NAME"] = CIRCUIT_LLM_API_MODEL_NAME
os.environ["CIRCUIT_LLM_API_VERSION"] = CIRCUIT_LLM_API_VERSION
os.environ["JWKS_URI"] = JWKS_URI
os.environ["AUDIENCE"] = AUDIENCE
os.environ["ISSUER"] = ISSUER
os.environ["CIRCUIT_CLIENT_ID"] = CIRCUIT_CLIENT_ID

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class MissingAPPKeyError(Exception):
    """Exception for missing APP key."""


class MissingCredentialsError(Exception):
    """Exception for missing Credentials key."""

class MissingAPIEndpoint(Exception):
    """Exception for missing API Endpoint key."""


def build_mcp_app(host: Optional[str] = None, port: Optional[int] = None):
    """Build and return the A2A Starlette application."""
    if os.getenv('CIRCUIT_LLM_API_APP_KEY') is None:
        raise MissingAPPKeyError('CIRCUIT_LLM_API_APP_KEY environment variable not set.')
    if os.getenv('CIRCUIT_LLM_API_CLIENT_ID') is None or os.getenv('CIRCUIT_LLM_API_CLIENT_SECRET') is None:
        raise MissingCredentialsError('CIRCUIT_LLM_API_CLIENT_ID or CIRCUIT_LLM_API_CLIENT_SECRET environment variables not set.')
    if os.getenv('CIRCUIT_LLM_API_ENDPOINT') is None:
        raise MissingCredentialsError('CIRCUIT_LLM_API_ENDPOINT environment variables not set.')

    # Derive a public URL for the agent card if host/port provided, else use env or fallback
    public_host = host or os.getenv('PUBLIC_HOST') or 'localhost'
    public_port = port or int(os.getenv('PUBLIC_PORT', '8006'))
    public_scheme = os.getenv('PUBLIC_SCHEME', 'http')
    mcp_base_url = f'{public_scheme}://{public_host}:{public_port}/'

    app = mcp_application.streamable_http_app()

    app.add_middleware(
        OAuth2Middleware
    )

    async def _ok(_request):
        return PlainTextResponse('ok')
    app.add_route('/healthz', _ok, methods=['GET'])
    app.add_route('/readyz', _ok, methods=['GET'])

    return app

# Expose module-level ASGI app for Gunicorn (UvicornWorker)
app = build_mcp_app()

@click.command()
@click.option('--host', 'host', default='0.0.0.0')
@click.option('--port', 'port', default=8006)
def main(host, port):
    """Local runner for the A2A server."""
    try:
        local_app = build_mcp_app(host=host, port=port)
        uvicorn.run(local_app, host=host, port=port)
    except MissingAPPKeyError as e:
        logger.error(f'Error: {e}')
        sys.exit(1)
    except MissingCredentialsError as e:
        logger.error(f'Error: {e}')
        sys.exit(1)
    except Exception as e:
        logger.error(f'An error occurred during server startup: {e}')
        sys.exit(1)

if __name__ == '__main__':
    main()