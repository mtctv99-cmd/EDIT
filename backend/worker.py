import os
from rq import Worker

from app.queue import redis_conn

if __name__ == "__main__":
    worker = Worker(["edit"], connection=redis_conn)
    worker.work()
