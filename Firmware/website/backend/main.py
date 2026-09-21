from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from routers import device, web, ai

app = FastAPI(title="GrowHub core api")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # change to web url in prod
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(device.router, prefix="/api/device", tags=["Hardware"])
app.include_router(web.router, prefix="/api/web", tags=["Frontend"])
app.include_router(ai.router, prefix="/api/ai", tags=["Intelligence"])

@app.get("/")
def health_check():
    return {"status": "GrowHub server is live"}