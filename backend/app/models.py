from __future__ import annotations

import datetime as dt
from typing import Optional

from sqlalchemy import ForeignKey, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.db import Base


class NewsItem(Base):
    __tablename__ = "news_items"

    id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str]
    source: Mapped[str]
    date: Mapped[dt.date]
    url: Mapped[str] = mapped_column(unique=True)
    description: Mapped[Optional[str]] = mapped_column(Text)
    collected_at: Mapped[dt.datetime]


class NewsSummary(Base):
    __tablename__ = "news_summaries"

    id: Mapped[int] = mapped_column(primary_key=True)
    news_id: Mapped[int] = mapped_column(ForeignKey("news_items.id"))
    summary_text: Mapped[str] = mapped_column(Text)
    hallucination_risk: Mapped[str]
    generated_at: Mapped[dt.datetime]


class EmailSubscriber(Base):
    __tablename__ = "email_subscribers"

    id: Mapped[int] = mapped_column(primary_key=True)
    email: Mapped[str]
    name: Mapped[str]
    subscribed_at: Mapped[dt.datetime]


class ApiUsage(Base):
    __tablename__ = "api_usage"

    id: Mapped[int] = mapped_column(primary_key=True)
    kind: Mapped[str]
    model: Mapped[str]
    input_tokens: Mapped[int]
    output_tokens: Mapped[int]
    created_at: Mapped[dt.datetime]
