from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .db import Base, engine
from .routers import auth, catalog, orders, pharmacist, prescriptions

@asynccontextmanager
async def lifespan(_):
    Base.metadata.create_all(engine)
    yield


app = FastAPI(title="Pharmacy Reorder API", lifespan=lifespan)
app.add_middleware(CORSMiddleware, allow_origins=["http://localhost:5173"],
                   allow_methods=["*"], allow_headers=["*"])
app.include_router(auth.router)
app.include_router(catalog.router)
app.include_router(prescriptions.router)
app.include_router(orders.router)
app.include_router(pharmacist.router)


@app.get("/health")
def health():
    return {"ok": True}
