import time
from fastapi import FastAPI

app = FastAPI()


@app.get("/")
def healthcheck():
    return {"status": "ok"}


@app.get("/work")
def work():
    start = time.perf_counter()
    result = sum(range(10**6))
    duration_ms = (time.perf_counter() - start) * 1000
    return {"result": result, "duration_ms": round(duration_ms, 2)}
