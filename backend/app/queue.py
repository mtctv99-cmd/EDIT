from rq import Queue
from redis import Redis

from .config import settings

redis_conn = Redis.from_url(settings.redis_url)
queue = Queue("edit", connection=redis_conn)
