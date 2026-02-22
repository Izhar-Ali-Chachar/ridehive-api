from fastapi import FastAPI, HTTPException


app = FastAPI(root_path="rider")

@app.post("/register")
async def register_rider(rider: )
