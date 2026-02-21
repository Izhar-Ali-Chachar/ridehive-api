from fastapi import FastAPI

from app.routes.rides import router as ride_router

from contextlib import asynccontextmanager

from app.db.session import create_tables

@asynccontextmanager
async def spand_handler(app: FastAPI):
    await create_tables()
    yield

app = FastAPI(lifespan=spand_handler)

app.include_router(router = ride_router)

@app.get("/")
def health_check():
    return {"status": "ok"}