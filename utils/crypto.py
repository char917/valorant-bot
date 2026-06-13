import os

from cryptography.fernet import Fernet, InvalidToken

_KEY = os.getenv("ENCRYPTION_KEY")
if not _KEY:
    raise RuntimeError("缺少 ENCRYPTION_KEY，請在 .env 填入（用 scripts/gen_key.py 產生）。")

_fernet = Fernet(_KEY.encode())

def encrypt(text: str) -> str:
    return _fernet.encrypt(text.encode()).decode()

def decrypt(token: str) -> str | None:
    try:
        return _fernet.decrypt(token.encode()).decode()
    except InvalidToken:
        return None
