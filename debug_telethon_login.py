import argparse
import os
import sys
from getpass import getpass

PROJECT_ROOT = os.path.dirname(__file__)
SRC_PATH = os.path.join(PROJECT_ROOT, "src")
if SRC_PATH not in sys.path:
    sys.path.insert(0, SRC_PATH)

from telegramwordcloud.core import (
    TELEGRAM_SESSION_NAME,
    TELETHON_CLIENT_KWARGS,
    TGWCCore,
    TelegramClient,
    logger,
)


def load_credentials(core: TGWCCore):
    creds = core.read_env_credentials()
    if not creds:
        raise SystemExit("No credentials found. Fill TELEGRAM_API_ID/TELEGRAM_API_HASH/TELEGRAM_PHONE in .env.")
    missing = [key for key in ("TELEGRAM_API_ID", "TELEGRAM_API_HASH", "TELEGRAM_PHONE") if not creds.get(key)]
    if missing:
        raise SystemExit(f"Missing keys in .env: {', '.join(missing)}")
    return creds


def prompt_code(two_factor: bool = False) -> str:
    if two_factor:
        return getpass("Enter Telegram 2FA password: ").strip()
    return input("Enter the Telegram login code you just received (SMS/app): ").strip()


def main():
    parser = argparse.ArgumentParser(description="Manual Telethon login/debug helper.")
    parser.add_argument("--channel", default="bbcrussian", help="Channel username or invite link to fetch after login.")
    parser.add_argument("--session-suffix", default="debug", help="Suffix for the session file to avoid clobbering GUI sessions.")
    args = parser.parse_args()

    core = TGWCCore()
    creds = load_credentials(core)
    api_id = int(creds["TELEGRAM_API_ID"])
    api_hash = creds["TELEGRAM_API_HASH"]
    phone = creds["TELEGRAM_PHONE"]

    session_name = f"{TELEGRAM_SESSION_NAME}_{args.session_suffix}"
    logger.info("Using session %s", session_name)

    client = TelegramClient(session_name, api_id, api_hash, **TELETHON_CLIENT_KWARGS)
    client.connect()
    try:
        if not client.is_user_authorized():
            logger.info("Requesting login code for %s", phone)

            def provider(two_factor=False):
                return prompt_code(two_factor=two_factor)

            core._login(client, phone, provider)
            logger.info("Authentication successful.")
        else:
            logger.info("Existing session is already authenticated.")

        logger.info("Fetching latest message from %s ...", args.channel)
        message = next(client.iter_messages(args.channel, limit=1))
        snippet = str(message.message or "")[:200]
        try:
            print(f"Latest message snippet: {snippet}")
        except UnicodeEncodeError:
            print("Latest message snippet:", snippet.encode("utf-8", errors="ignore").decode("utf-8"))
        logger.info("Success. You can now use the GUI with the same session.")
    finally:
        client.disconnect()


if __name__ == "__main__":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass
    os.chdir(os.path.dirname(__file__))
    sys.exit(main())
