from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from routers import device, web, ai, auth
from routers.auth import WEB_ORIGIN_REGEX
import accounts
import history

history.init_db()
accounts.init_db()
device.load_hubs()

app = FastAPI(title="GrowHub core api")

app.add_middleware(
    CORSMiddleware,
    allow_origin_regex=WEB_ORIGIN_REGEX,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(device.router, prefix="/api/device", tags=["Hardware"])
app.include_router(web.router, prefix="/api/web", tags=["Frontend"])
app.include_router(ai.router, prefix="/api/ai", tags=["Intelligence"])
app.include_router(auth.router, prefix="/api/auth", tags=["Accounts"])

@app.get("/")
def health_check():
    return {"status": "GrowHub server is live"}
