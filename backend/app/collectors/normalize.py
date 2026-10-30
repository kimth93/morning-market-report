from __future__ import annotations

import html
import re
from datetime import date, datetime
from email.utils import parsedate_to_datetime
from urllib.parse import urlparse
from zoneinfo import ZoneInfo

from app.collectors.press_map import PRESS_BY_DOMAIN

KST = ZoneInfo("Asia/Seoul")
_TAG_PATTERN = re.compile(r"<[^>]+>")


def strip_markup(text: str) -> str:
    return html.unescape(_TAG_PATTERN.sub("", text))


def parse_pub_date(value: str) -> datetime:
    return parsedate_to_datetime(value)


def to_kst_date(value: datetime) -> date:
    return value.astimezone(KST).date()


def press_name(url: str) -> str:
    domain = urlparse(url).hostname or ""
    if domain.startswith("www."):
        domain = domain[len("www."):]
    return PRESS_BY_DOMAIN.get(domain, domain)
