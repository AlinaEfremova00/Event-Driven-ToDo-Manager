from fastapi import FastAPI, Depends, HTTPException, Request
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
from sqlalchemy.orm import Session
import requests
from database import SessionLocal, Task
from pydantic import BaseModel
from redis_client import redis_client, get_tasks_cache_key, get_task_cache_key, clear_tasks_cache
from slowapi import Limiter
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from slowapi.extension import _rate_limit_exceeded_handler
import json
import os
import time
from prometheus_client import Counter, Histogram, generate_latest
from fastapi.responses import Response



# Настройка rate limiter
REDIS_HOST = os.getenv("REDIS_HOST", "redis")
REDIS_PORT = os.getenv("REDIS_PORT", "6379")

storage_uri = f"redis://{REDIS_HOST}:{REDIS_PORT}/0"

limiter = Limiter(
   key_func=get_remote_address,
   storage_uri=storage_uri,
)

app = FastAPI()
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# Подключаем статические файлы (HTML, CSS, JS)
app.mount("/static", StaticFiles(directory="static"), name="static")


REQUEST_COUNT = Counter(
    "task_service_requests_total",
    "Total requests",
    ["method", "endpoint"]
)

REQUEST_LATENCY = Histogram(
    "task_service_latency_seconds",
    "Request latency"
)


@app.middleware("http")
async def metrics_middleware(request, call_next):
    start = time.time()
    response = await call_next(request)
    duration = time.time() - start

    REQUEST_COUNT.labels(request.method, request.url.path).inc()
    REQUEST_LATENCY.observe(duration)

    return response

@app.get("/")
async def serve_index():
    with open("static/index.html", "r", encoding="utf-8") as f:
        return HTMLResponse(content=f.read())


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


class TaskCreate(BaseModel):
    title: str


class TaskOut(BaseModel):
    id: str
    title: str
    status: str


@app.post("/tasks")
def create_task(request: Request, task: TaskCreate, db: Session = Depends(get_db)):
    db_task = Task(title=task.title, status="NEW")
    db.add(db_task)
    db.commit()
    db.refresh(db_task)

    clear_tasks_cache()

    try:
        requests.post(
             "http://event-service:8002/event",
            json={
                "type": "TASK_CREATED",
                "task": {"id": db_task.id, "title": db_task.title, "status": db_task.status}
            },
            timeout=2
        )
    except Exception as e:
        print(f"Failed to send event: {e}")

    return {
        "id": db_task.id,
        "title": db_task.title,
        "status": db_task.status
    }


@app.get("/tasks")
def get_tasks(request: Request, db: Session = Depends(get_db)):
    cache_key = get_tasks_cache_key()

    cached = redis_client.get(cache_key)
    if cached:
        print("Returning tasks from Redis cache")
        return json.loads(cached)

    print("Fetching tasks from PostgreSQL")
    tasks = db.query(Task).all()

    result = [
        {"id": t.id, "title": t.title, "status": t.status}
        for t in tasks
    ]

    redis_client.setex(cache_key, 30, json.dumps(result))

    return result


@app.get("/tasks/{task_id}")
#@limiter.limit("10/second")
def get_task(request: Request, task_id: str, db: Session = Depends(get_db)):
    cache_key = get_task_cache_key(task_id)

    cached = redis_client.get(cache_key)
    if cached:
        print(f"Returning task {task_id} from Redis cache")
        return json.loads(cached)

    task = db.query(Task).filter(Task.id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    task_dict = {"id": task.id, "title": task.title, "status": task.status}
    redis_client.setex(cache_key, 60, json.dumps(task_dict))

    return task_dict

@app.delete("/tasks/{task_id}")
#@limiter.limit("5/second")
def delete_task(request: Request, task_id: str, db: Session = Depends(get_db)):
    task = db.query(Task).filter(Task.id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    db.delete(task)
    db.commit()
    clear_tasks_cache()

    return {"status": "deleted"}

@app.get("/metrics")
def metrics():
    return Response(generate_latest(), media_type="text/plain")