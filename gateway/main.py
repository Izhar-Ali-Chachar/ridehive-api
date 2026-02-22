from fastapi import FastAPI

from contextlib import asynccontextmanager

from database.session import create_tables

@asynccontextmanager
async def spand_handler(app: FastAPI):
    await create_tables()
    yield

app = FastAPI(lifespan=spand_handler)

@app.get("/")
def health_check():
    return {"status": "ok"}