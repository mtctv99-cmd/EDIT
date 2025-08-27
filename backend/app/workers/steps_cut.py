import logging

logger = logging.getLogger(__name__)


def run(job, db):
    logger.info("Cutting video for job %s", job.id)
    # TODO: implement silence-based split
