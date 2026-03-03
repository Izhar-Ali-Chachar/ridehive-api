from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlmodel import SQLModel
from database.models import Riders, Rides, Payment, Drivers, Fares
import os

from fastapi import Depends
from typing import Annotated

DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "sqlite+aiosqlite:///./ridehive.db"
)

if DATABASE_URL.startswith("sqlite:///"):
    DATABASE_URL = DATABASE_URL.replace(
        "sqlite:///",
        "sqlite+aiosqlite:///"
    )

engine = create_async_engine(
    url=DATABASE_URL,
    echo=True
)

async_session = async_sessionmaker(
    bind=engine,
    expire_on_commit=False
)

async def create_tables():
    async with engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.create_all)

async def get_session():
    async with async_session() as session:
        try:
            yield session
            await session.commit() 
        except Exception:
            await session.rollback()
            raise
sessionDep = Annotated[AsyncSession, Depends(get_session)]