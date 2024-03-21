from os import environ

from sqlalchemy import Column, ForeignKey, Integer, String
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship

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


async def add_torrent(torrent: Torrent) -> None:
    async with AsyncSession(engine, autoflush=True) as session:
        session.add(
            Torrent(
                info_hash=torrent.info_hash,
                name=torrent.name,
                size=torrent.size,
                age=torrent.age,
                files=[
                    TorrentFile(name=file.name, size=file.size, info_hash=torrent.info_hash)
                    for file in torrent.files
                ],
            )
        )
        await session.commit()


async def get_torrent(info_hash: str) -> Torrent | None:
    async with AsyncSession(engine, autoflush=True) as session:
        return await session.get(Torrent, info_hash)


async def init() -> None:
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all, checkfirst=True)
