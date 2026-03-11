import time
import requests
from langchain_openai import AzureChatOpenAI
import logging as log
from typing import Optional
import os

# Support running either with `python -m client.client` (preferred) or
# `python client/client.py` (script path) by attempting the import and
# falling back to dynamically adding the project root to sys.path.
try:  # First try normal absolute package import
    from app.properties import (
        CIRCUIT_LLM_API_APP_KEY,
        CIRCUIT_LLM_API_CLIENT_ID,
        CIRCUIT_LLM_API_CLIENT_SECRET,
        CIRCUIT_LLM_API_ENDPOINT,
        CIRCUIT_LLM_API_MODEL_NAME,
        CIRCUIT_LLM_API_VERSION,
        OAUTH_ENDPOINT,
    )
except ModuleNotFoundError:  # Fallback: adjust sys.path then retry
    import sys, pathlib
    project_root = pathlib.Path(__file__).resolve().parents[1]
    if str(project_root) not in sys.path:
        sys.path.insert(0, str(project_root))
    from app.properties import (
        CIRCUIT_LLM_API_APP_KEY,
        CIRCUIT_LLM_API_CLIENT_ID,
        CIRCUIT_LLM_API_CLIENT_SECRET,
        CIRCUIT_LLM_API_ENDPOINT,
        CIRCUIT_LLM_API_MODEL_NAME,
        CIRCUIT_LLM_API_VERSION,
        OAUTH_ENDPOINT,
    )

access_token: Optional[str] = None
last_generated = 0.0

def generate_bearer_token(client_id: str, client_secret: str) -> str | None:
    """
    Generates a bearer token by making a POST request to the specified token URL with the provided client ID and secret.
    :param token_url: The URL to which the POST request is made to obtain the bearer token.
    :param client_id: The client ID used for authentication in the request.
    :param client_secret: The client secret used for authentication in the request.
    :return:
    """
    global access_token, last_generated
    url = OAUTH_ENDPOINT
    headers = {'Content-Type': 'application/x-www-form-urlencoded'}
    auth_info = {'client_id': f'{client_id}',
                 'client_secret': f'{client_secret}',
                 'grant_type': "client_credentials"}
    response = requests.request("POST", url, data=auth_info, headers=headers)
    #log.warning(f"generate_bearer_token response_status_code: {response.status_code}")
    if response.status_code != 200:
        #log.warning(f"generate_bearer_token: {response.status_code}, {response.text}")
        return None
    json_response = response.json()
    access = json_response.get('access_token')
    if access:
        access_token = access  # type: ignore[assignment]
        last_generated = time.time()
    return access_token


def get_llm():
    # Refresh token if missing or older than ~3500 seconds (slightly before common 3600s expiry)
    if access_token is None or int(time.time()) > (last_generated + 3500):
        generate_bearer_token(CIRCUIT_LLM_API_CLIENT_ID, CIRCUIT_LLM_API_CLIENT_SECRET)

    # Depending on langchain_openai version, accepted params may be: azure_endpoint, api_key, api_version, model (or azure_deployment)
    if not access_token:
        raise RuntimeError("Failed to obtain access token for LLM usage.")

    return AzureChatOpenAI(
        azure_endpoint=CIRCUIT_LLM_API_ENDPOINT,
        api_key=access_token,  # type: ignore[arg-type]
        api_version=CIRCUIT_LLM_API_VERSION,
        model=CIRCUIT_LLM_API_MODEL_NAME,
        default_headers={'client-id': CIRCUIT_LLM_API_CLIENT_ID},
        model_kwargs={'user': f'{{"appkey": "{CIRCUIT_LLM_API_APP_KEY}"}}'},
        temperature=0,
        streaming=True
    )