import base64
import json


def parse_secrets(*secret_keys: str) -> str | list[str]:
    secrets = json.load(open("lists/secrets.json"))
    decoded = [base64.b64decode(secrets[key]).decode("utf-8") for key in secret_keys]
    return decoded[0] if len(secret_keys) == 1 else decoded
