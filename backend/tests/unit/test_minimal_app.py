#!/usr/bin/env python3
"""
Minimal FastAPI app to test if the basic setup works.
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(title="Test App")

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/health")
async def health_check():
    return {"status": "healthy"}

@app.get("/")
async def root():
    return {"message": "Test app is working"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("test_minimal_app:app", host="0.0.0.0", port=8001, reload=True)