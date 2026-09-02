import os

# LLM Specific
# CIRCUIT_LLM_API_APP_KEY = os.environ.get('CIRCUIT_LLM_API_APP_KEY', "<your-llm-appkey-here>")
# CIRCUIT_LLM_API_CLIENT_ID = os.environ.get('CIRCUIT_LLM_API_CLIENT_ID', "<your-llm-clientid-here>")
# CIRCUIT_LLM_API_CLIENT_SECRET = os.environ.get('CIRCUIT_LLM_API_CLIENT_SECRET', "<your-llm-secret-here>")
# CIRCUIT_LLM_API_MODEL_NAME = os.environ.get('CIRCUIT_LLM_API_MODEL_NAME', "<your-llm-model-here>")
# CIRCUIT_LLM_API_ENDPOINT = os.environ.get('CIRCUIT_LLM_API_ENDPOINT', "<your-llm-endpoint-here>")
# CIRCUIT_LLM_API_VERSION = os.environ.get('CIRCUIT_LLM_API_VERSION', "<your-llm-version-here>")

CIRCUIT_LLM_API_APP_KEY = os.environ.get('CIRCUIT_LLM_API_APP_KEY', "egai-prd-cx-020057031-rag-1778098830283")
CIRCUIT_LLM_API_CLIENT_ID = os.environ.get('CIRCUIT_LLM_API_CLIENT_ID', "0oauhiuja2rNYjGj15d7")
# CIRCUIT_LLM_API_CLIENT_SECRET = os.environ.get('CIRCUIT_LLM_API_CLIENT_SECRET', "BnvR2MZW8OtIgiOCXVAIZ7QN4sGp3RifImVHASDMfFT8eDPy22X_oFTY8d12Me8g")
CIRCUIT_LLM_API_CLIENT_SECRET = os.environ.get('CIRCUIT_LLM_API_CLIENT_SECRET', "q6-01L9RblvyY9cIuF2GqtuXjOEuVYyLnz5yW39Yo6N8PEb1-RCnCCuwr37yDr-y")
# CIRCUIT_LLM_API_MODEL_NAME = os.environ.get('CIRCUIT_LLM_API_MODEL_NAME', "gpt-4o-mini")
CIRCUIT_LLM_API_MODEL_NAME = os.environ.get('CIRCUIT_LLM_API_MODEL_NAME', "gpt-5-nano")
CIRCUIT_LLM_API_ENDPOINT = "https://chat-ai.cisco.com"
CIRCUIT_LLM_API_VERSION = "2025-04-01-preview"


JWKS_URI = os.environ.get('JWKS_URI', "<your-jwks-value-here>")
AUDIENCE = os.environ.get('AUDIENCE', "<your-aud-here>")
ISSUER = os.environ.get('ISSUER', "<your-iss-here>")
CIRCUIT_CLIENT_ID = os.environ.get('CIRCUIT_CLIENT_ID', "<your-clientid-here>")

OAUTH_ENDPOINT = os.environ.get('OAUTH_ENDPOINT', "https://id.cisco.com/oauth2/default/v1/token")