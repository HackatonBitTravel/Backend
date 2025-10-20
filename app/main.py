
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.core.database import engine, Base
from app.routes import agencies, routes, schedules, reservations, search, tickets, auth, payments, lightning 

Base.metadata.create_all(bind=engine)

app = FastAPI(
    title=settings.APP_NAME,
    version=settings.API_VERSION,
    debug=settings.DEBUG
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(agencies.router)
app.include_router(routes.router)
app.include_router(schedules.router)
app.include_router(reservations.router)
app.include_router(search.router)
app.include_router(tickets.router)
app.include_router(payments.router)
app.include_router(lightning.router)

@app.get("/")
def root():
    return {
        "message": "Bienvenue sur BitTravel API",
        "version": settings.API_VERSION
    }
