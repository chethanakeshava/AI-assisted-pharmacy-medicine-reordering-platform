from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .config import assert_safe_config, settings
from .db import Base, engine
from .routers import auth, catalog, dashboard, orders, pharmacist, prescriptions, refills, stock, store

@asynccontextmanager
async def lifespan(_):
    assert_safe_config()
    Base.metadata.create_all(engine)
    yield


app = FastAPI(title="Pharmacy Reorder API", lifespan=lifespan)
app.add_middleware(CORSMiddleware, allow_origins=[o.strip() for o in settings.cors_origins.split(",") if o.strip()],
                   allow_methods=["*"], allow_headers=["*"])


@app.middleware("http")
async def security_headers(request, call_next):
    resp = await call_next(request)
    resp.headers["X-Content-Type-Options"] = "nosniff"
    resp.headers["X-Frame-Options"] = "DENY"
    resp.headers["Referrer-Policy"] = "no-referrer"
    resp.headers.setdefault("Cache-Control", "no-store")   # health data: never cache API responses
    return resp
app.include_router(auth.router)
app.include_router(catalog.router)
app.include_router(prescriptions.router)
app.include_router(orders.router)
app.include_router(pharmacist.router)
app.include_router(store.router)
app.include_router(refills.router)
app.include_router(stock.router)
app.include_router(dashboard.router)


@app.get("/health")
def health():
    return {"ok": True}
