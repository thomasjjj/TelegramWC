# core.py
import datetime
import json
import logging
import os
import platform
import re
from pathlib import Path
from typing import Callable, Dict, Iterable, List, Optional, Set, Union

import pandas as pd
from wordcloud import WordCloud

PACKAGE_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = PACKAGE_DIR.parent.parent
LOG_FILE = PROJECT_ROOT / "telegramwordcloud.log"
ENV_FILE = PROJECT_ROOT / ".env"
ENV_KEYS = ("TELEGRAM_API_ID", "TELEGRAM_API_HASH", "TELEGRAM_PHONE")
TELEGRAM_SESSION_NAME = "telegramwordcloud_session"
FONT_FAMILY = "arial.ttf"  # keep current default  :contentReference[oaicite:9]{index=9}
TELETHON_CLIENT_KWARGS = {
    "device_model": "TelegramWordCloud",
    "system_version": "Android 13",
    "app_version": "1.2.0",
    "lang_code": "en",
    "system_lang_code": "en",
}

logger = logging.getLogger("telegramwordcloud")
if not logger.handlers:
    formatter = logging.Formatter("%(asctime)s [%(levelname)s] %(message)s")
    try:
        file_handler = logging.FileHandler(LOG_FILE)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
    except OSError:
        pass
    stream_handler = logging.StreamHandler()
    stream_handler.setFormatter(formatter)
    logger.addHandler(stream_handler)
logger.setLevel(logging.INFO)
logger.propagate = False

# Optional Telethon import (unchanged behavior)  :contentReference[oaicite:10]{index=10}
try:
    from telethon.sync import TelegramClient  # type: ignore
    from telethon.errors import (  # type: ignore
        ChannelPrivateError,
        FloodWaitError,
        PhoneCodeInvalidError,
        PhoneNumberInvalidError,
        SessionPasswordNeededError,
        UpdateAppToLoginError,
        UsernameInvalidError,
        UsernameNotOccupiedError,
    )
    TELETHON_AVAILABLE = True
except ImportError:
    TELETHON_AVAILABLE = False
    TelegramClient = None  # type: ignore
    ChannelPrivateError = FloodWaitError = PhoneCodeInvalidError = PhoneNumberInvalidError = SessionPasswordNeededError = UsernameInvalidError = UsernameNotOccupiedError = Exception  # type: ignore

try:
    import nltk
    from nltk.corpus import stopwords as nltk_stopwords

    nltk_available = True
except ImportError:
    nltk = None
    nltk_stopwords = None
    nltk_available = False


class TGWCCore:
    """Logic service: environment, IO, Telethon, processing, saving."""

    def __init__(self):
        self.project_root = PROJECT_ROOT

    # ------- ENV -------
    def read_env_credentials(self) -> Dict[str, str]:
        if not ENV_FILE.exists():
            return {}
        credentials: Dict[str, str] = {}
        try:
            with ENV_FILE.open("r", encoding="utf-8") as f:
                for raw in f:
                    line = raw.strip()
                    if not line or line.startswith("#") or "=" not in line:
                        continue
                    k, v = line.split("=", 1)
                    credentials[k.strip()] = v.strip()
        except OSError as exc:
            logger.warning("Unable to read %s: %s", ENV_FILE, exc)
        return credentials

    def write_env_credentials(self, creds: Dict[str, str]) -> None:
        lines = [f"{k}={creds.get(k, '')}" for k in ENV_KEYS]
        try:
            with ENV_FILE.open("w", encoding="utf-8") as f:
                f.write("\n".join(lines) + "\n")
        except OSError as exc:
            raise OSError(f"Unable to write to {ENV_FILE}: {exc}") from exc

    # ------- IO -------
    def ensure_dir(self, path: str) -> str:
        sanitized = self._sanitize_path(path)
        if not sanitized:
            raise ValueError("Please provide an output directory.")
        os.makedirs(sanitized, exist_ok=True)
        return sanitized

    def build_export_dir(self, base_dir: str, channel_label: str) -> Path:
        base = Path(self.ensure_dir(base_dir))
        sanitized = self.sanitize_channel_label(channel_label)
        timestamp = datetime.datetime.now().strftime("%Y%m%d%H%M%S")
        export_dir = base / "exports" / sanitized / timestamp
        export_dir.mkdir(parents=True, exist_ok=True)
        return export_dir

    def load_csv(self, csv_path: str) -> pd.DataFrame:
        path = self._sanitize_path(csv_path)
        if not path:
            raise ValueError("Please select a Telegram export CSV file.")
        if not os.path.exists(path):
            raise FileNotFoundError(f"{path} does not exist.")
        df = pd.read_csv(path, low_memory=False, encoding="utf-8")
        return df.replace(["NaN", "nan"], float("nan"))

    def load_json_export(self, json_path: str) -> pd.DataFrame:
        path = self._sanitize_path(json_path)
        if not path:
            raise ValueError("Please select a Telegram export JSON file.")
        if not os.path.exists(path):
            raise FileNotFoundError(f"{path} does not exist.")

        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)

        messages = self._extract_messages_from_dump(data)
        rows: List[Dict[str, Union[str, int]]] = []
        for msg in messages:
            text_content = self._stringify_telegram_text(msg.get("text", ""))
            rows.append(
                {
                    "id": msg.get("id"),
                    "date": msg.get("date"),
                    "from": msg.get("from") or msg.get("actor"),
                    "type": msg.get("type"),
                    "text": text_content,
                }
            )

        if not rows:
            raise ValueError("No messages were found inside the JSON export.")
        return pd.DataFrame(rows)

    def save_messages_csv(self, df: pd.DataFrame, output_dir: str, channel_label: str, filename: Optional[str] = None) -> str:
        directory = Path(self.ensure_dir(output_dir))
        sanitized = self.sanitize_channel_label(channel_label)
        if not filename:
            filename = f'telegram_messages_{sanitized}_{datetime.datetime.now().strftime("%Y%m%d%H%M%S")}.csv'
        path = directory / filename
        df.to_csv(path, index=False, encoding="utf-8")
        logger.info("Channel messages saved to %s", path)
        return str(path)

    def save_wordcloud_image(self, wc: WordCloud, output_dir: str, filename: Optional[str] = None) -> str:
        directory = Path(self.ensure_dir(output_dir))
        if not filename:
            filename = f'wordcloud_{datetime.datetime.now().strftime("%Y%m%d%H%M%S")}.jpg'
        path = directory / filename
        wc.to_file(path)
        logger.info("Word cloud saved to %s", path)
        return str(path)

    # ------- Text / stopwords -------
    def flatten_text_columns(self, df: pd.DataFrame) -> List[str]:
        text_cols = [c for c in df.columns if c.lower().startswith("text")]
        if not text_cols:
            text_cols = df.select_dtypes(include=["object"]).columns.tolist()
        out: List[str] = []
        for col in text_cols:
            for val in df[col].dropna().astype(str):
                s = self._clean_value(val)
                if s:
                    out.append(s)
        return out

    def _clean_value(self, v: str) -> str:
        x = v.strip()
        if not x:
            return ""
        if x.lower() in {"nan", "none", "null", "nat"}:
            return ""
        return x

    def _stringify_telegram_text(self, value: Union[str, List, Dict]) -> str:
        if isinstance(value, str):
            return value
        if isinstance(value, dict):
            return value.get("text") or value.get("href") or ""
        if isinstance(value, list):
            parts = [self._stringify_telegram_text(item) for item in value]
            return "".join(parts)
        return ""

    def load_stopwords(self, path: str) -> Set[str]:
        stoplist: Set[str] = set()
        if os.path.exists(path):
            with open(path, "r", encoding="utf-8") as f:
                words = [w.strip() for w in f.readlines()]
            stoplist.update({w for w in words if w})
        if nltk_available and nltk_stopwords is not None:
            try:
                nltk.data.find("corpora/stopwords")
            except LookupError:
                nltk.download("stopwords", quiet=True)
            for lang in ("english", "russian"):
                try:
                    stoplist.update(nltk_stopwords.words(lang))
                except LookupError:
                    continue
        return stoplist

    def build_wordcloud(self, tokens: Iterable[str], stopwords: Set[str]) -> WordCloud:
        corpus = " ".join(tokens)
        if not corpus.strip():
            raise ValueError("Not enough text to build a word cloud.")
        font_path = FONT_FAMILY
        if font_path and not Path(font_path).exists():
            logger.warning("Font %s not found; falling back to default font.", font_path)
            font_path = None
        return WordCloud(font_path=font_path, width=1000, height=700, stopwords=stopwords).generate(corpus)

    # ------- Telethon -------
    def download_channel(
        self,
        api_id: int,
        api_hash: str,
        phone: str,
        channel: str,
        code_provider,
        *,
        progress_callback: Optional[Callable[[int, Optional[int]], None]] = None,
        date_from: Optional[datetime.datetime] = None,
        date_to: Optional[datetime.datetime] = None,
        last_n: Optional[int] = None,
    ) -> pd.DataFrame:
        if not TELETHON_AVAILABLE:
            raise ImportError("Telethon is required. Install it with 'pip install telethon'.")
        if not channel:
            raise ValueError("Enter the channel username or invite link to download.")

        client = TelegramClient(TELEGRAM_SESSION_NAME, api_id, api_hash, **TELETHON_CLIENT_KWARGS)
        messages = []
        estimated_total = None
        try:
            client.connect()
            if not client.is_user_authorized():
                self._login(client, phone, code_provider)
            limit = last_n if last_n and last_n > 0 else None
            if progress_callback and not last_n:
                try:
                    latest_msg = next(client.iter_messages(channel, limit=1))
                    estimated_total = getattr(latest_msg, "id", None)
                except StopIteration:
                    estimated_total = None
                except Exception:
                    estimated_total = None
                progress_callback(0, estimated_total)

            processed = 0
            for msg in client.iter_messages(
                channel,
                limit=limit,
                offset_date=date_to,
                reverse=False,
            ):
                msg_date = getattr(msg, "date", None)
                if date_from and msg_date and msg_date < date_from:
                    break
                text = getattr(msg, "message", None)
                if text:
                    messages.append(
                        {
                            "id": msg.id,
                            "date": msg.date.isoformat() if getattr(msg, "date", None) else "",
                            "sender_id": getattr(msg, "sender_id", None),
                            "text": text,
                        }
                    )
                processed += 1
                if progress_callback:
                    progress_callback(processed, estimated_total)
        except (UsernameInvalidError, UsernameNotOccupiedError, ChannelPrivateError) as exc:
            raise ValueError("Unable to access that channel. Check the username/link or join the channel first.") from exc
        finally:
            client.disconnect()

        if not messages:
            raise ValueError("The selected channel did not return any text messages.")
        return pd.DataFrame(messages)

    def _login(self, client, phone: str, code_provider):
        """
        Request a login code, prompt the user (via the supplied code_provider) for the OTP,
        retry on invalid codes, and fall back to the 2FA password prompt when required.
        """
        if not phone:
            raise ValueError("A phone number is needed the first time you sign in.")

        MAX_ATTEMPTS = 3
        try:
            sent = client.send_code_request(phone)
        except FloodWaitError as exc:
            raise ValueError(f"Telegram rate limited the login-code request. Wait {exc.seconds} seconds.") from exc
        except UpdateAppToLoginError as exc:
            raise ValueError(
                "Telegram rejected the login request (UpdateAppToLoginError). "
                "Visit my.telegram.org, create a new API ID/hash, and try again."
            ) from exc

        for attempt in range(1, MAX_ATTEMPTS + 1):
            code = code_provider()
            if not code:
                raise ValueError("Verification code was not provided.")

            try:
                client.sign_in(phone=phone, code=code, phone_code_hash=sent.phone_code_hash)
                return
            except PhoneCodeInvalidError:
                if attempt < MAX_ATTEMPTS:
                    logger.warning("Invalid login code (attempt %s/%s). Retrying...", attempt, MAX_ATTEMPTS)
                    continue
                raise ValueError(
                    "The verification code was invalid too many times. Please request a new code and try again."
                )
            except SessionPasswordNeededError:
                password = code_provider(two_factor=True)
                if not password:
                    raise ValueError("Two-factor password was not provided.")
                client.sign_in(password=password)
                return
            except PhoneNumberInvalidError as exc:
                raise ValueError(
                    "The phone number is invalid. Ensure it includes the country code (e.g. +15551234567)."
                ) from exc

    # ------- Utils -------
    def sanitize_channel_label(self, value: str) -> str:
        if not value:
            return "channel"
        cleaned = re.sub(r"https?://t\.me/", "", value, flags=re.IGNORECASE)
        cleaned = cleaned.replace("@", "")
        cleaned = re.sub(r"[^A-Za-z0-9_-]+", "_", cleaned).strip("_")
        return cleaned or "channel"

    def _sanitize_path(self, raw: str) -> str:
        if not raw:
            return ""
        trimmed = raw.strip().strip('"').strip("'")
        return os.path.abspath(trimmed) if trimmed else ""

    def _extract_messages_from_dump(self, data) -> List[Dict]:
        if isinstance(data, dict):
            if "messages" in data:
                return [msg for msg in data.get("messages", []) if isinstance(msg, dict)]
            chats = data.get("chats")
            if isinstance(chats, dict):
                collected: List[Dict] = []
                for chat in chats.get("list", []):
                    collected.extend(self._extract_messages_from_dump(chat))
                return collected
        if isinstance(data, list):
            collected = []
            for item in data:
                collected.extend(self._extract_messages_from_dump(item))
            return collected
        return []
