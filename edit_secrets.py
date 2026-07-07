import base64
import json
import subprocess
import tempfile
from pathlib import Path

SECRETS_PATH = Path("lists/secrets.json")


def main():
    secrets = json.loads(SECRETS_PATH.read_text())

    for key, value in secrets.items():
        decoded = base64.b32decode(value).decode("utf-8")

        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".txt", prefix=f"{key}_", delete=False
        ) as f:
            f.write(decoded)
            tmp_path = Path(f.name)

        subprocess.run(["code", "--wait", str(tmp_path)], check=True)

        edited = tmp_path.read_text()
        secrets[key] = base64.b32encode(edited.encode("utf-8")).decode("ascii")
        tmp_path.unlink()

        SECRETS_PATH.write_text(json.dumps(secrets, indent=4))


if __name__ == "__main__":
    main()
