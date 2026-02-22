from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlmodel import SQLModel
from .models import Riders, Rides, Payment, Drivers, Fares

from fastapi import Depends
from typing import Annotated

url = "sqlite+aiosqlite:///./ridehive.db"

engine = create_async_engine(
    url=url,
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
        yield session

sessionDep = Annotated[AsyncSession, Depends(get_session)]