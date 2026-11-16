from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routes import fixtures, predictions, value_bets, backtest, sportybet
from app.database import engine, Base

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Initialize SQLite database tables safely at startup
    Base.metadata.create_all(bind=engine)
    yield

app = FastAPI(
    title="Football Prediction & Value Betting Platform API",
    version="1.0.0",
    description="Statistical football prediction engine powered by the Dixon-Coles Bivariate Poisson Model",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(fixtures.router)
app.include_router(predictions.router)
app.include_router(value_bets.router)
app.include_router(backtest.router)
app.include_router(sportybet.router)

@app.get("/")
def root():
    return {
        "status": "online",
        "service": "Football Prediction Engine",
        "version": "1.0.0",
        "endpoints": [
            "/api/leagues",
            "/api/fixtures",
            "/api/predictions",
            "/api/value-bets",
            "/api/backtest",
            "/api/sportybet/fixtures",
            "/api/sportybet/value-bets",
            "/api/sportybet/action-sheet"
        ]
    }
