import logging

logger = logging.getLogger(__name__)


def run(job, db):
    logger.info("Adjusting speed for job %s", job.id)
    # TODO: implement ffmpeg speed change
