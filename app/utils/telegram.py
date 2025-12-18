import hmac
import hashlib
import json
import base64
from app import config

def decode_telegram_payload(tg_auth_result: str) -> dict:
    decoded = base64.b64decode(tg_auth_result).decode()
    return json.loads(decoded)

def verify_telegram_auth(data: dict) -> bool:
    bot_token = config.TELEGRAM_BOT_TOKEN.encode()
    secret_key = hashlib.sha256(bot_token).digest()

    received_hash = data.pop("hash", None)
    if not received_hash:
        return False

    data_check_string = "\n".join(
        f"{k}={v}" for k, v in sorted(data.items())
    )

    calculated_hash = hmac.new(
        secret_key,
        data_check_string.encode(),
        hashlib.sha256
    ).hexdigest()

    return calculated_hash == received_hash
