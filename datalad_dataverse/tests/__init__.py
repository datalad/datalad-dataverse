import os
import requests

# Retrieve user API tokens from env vars TESTS_TOKEN_*, where * is the user name
# (uppercase);
# This is how the CI setup is currently passing them into the test environment.
API_TOKENS = {k.split('_')[-1].lower(): v
              for k, v in os.environ.items() if k.startswith("TESTS_TOKEN")}

DATAVERSE_URL = os.environ.get("TESTS_DATAVERSE_BASEURL")
