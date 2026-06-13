"""
FastAPI application entry point.

Registers all routers for the Cart/Checkout infrastructure layer.
"""
from fastapi import FastAPI

from app.routers import cart, checkout, buy_again

app = FastAPI(title="Intent2Cart API", version="0.1.0")

# Register routers
app.include_router(cart.router)
app.include_router(checkout.router)
app.include_router(buy_again.router)


@app.get("/health")
async def health():
    return {"status": "ok"}
