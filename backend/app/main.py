from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.api.news import router as news_router
from app.config import get_settings
from app.db import init_db, make_engine, make_session_factory


@asynccontextmanager
async def lifespan(app: FastAPI):
    settings = get_settings()
    engine = make_engine(settings.database_url)
    init_db(engine)
    app.state.session_factory = make_session_factory(engine)
    yield
    engine.dispose()


app = FastAPI(lifespan=lifespan)
app.include_router(news_router)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}
