from fastapi import FastAPI
from app.db import engine, Base
from app.routes import users, assets, portfolios

# создаём все таблицы (для dev)
Base.metadata.create_all(bind=engine)

app = FastAPI(title="Currency Rebalancer API")

# Подключаем роутеры
app.include_router(users.router)
app.include_router(assets.router)
app.include_router(portfolios.router)

@app.get("/")
def read_root():
    return {"message": "Welcome to Currency Rebalancer API"}

