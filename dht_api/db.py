from datetime import datetime, timezone
from os import environ

import structlog
from sqlalchemy import Column, DateTime, ForeignKey, Integer, String
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.future import select
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

log = structlog.get_logger(__name__)
Base = declarative_base()

DB_FILE = environ.get("DB_FILE") or "torrents.db"
engine = create_async_engine(f"sqlite+aiosqlite:///{DB_FILE}", echo=True)


class TorrentFile(Base):
    __tablename__ = "torrent_files"
    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    size = Column(Integer, nullable=False)
    info_hash = Column(String, ForeignKey("torrents.info_hash"))


class Torrent(Base):
    __tablename__ = "torrents"
    info_hash = Column(String, primary_key=True)
    name = Column(String, nullable=False)
    size = Column(Integer, nullable=False)
    age = Column(String, nullable=False)
    files = relationship("TorrentFile", backref="torrent", lazy="joined")
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())


async def add_torrent(torrent: Torrent) -> None:
    async with AsyncSession(engine, autoflush=True) as session, session.begin():
        existing_result = await session.execute(
            select(Torrent).filter(Torrent.info_hash == torrent.info_hash)
        )
        if existing := existing_result.scalar():
            log.info("updating existing torrent", info_hash=torrent.info_hash)
            existing.age = torrent.age
            existing.updated_at = datetime.now(timezone.utc)  # type: ignore
            return

        log.info("adding new", info_hash=torrent.info_hash)
        session.add(torrent)


async def get_torrent(info_hash: str) -> Torrent | None:
    async with AsyncSession(engine, autoflush=True) as session:
        return await session.get(Torrent, info_hash)


async def init() -> None:
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all, checkfirst=True)
