import logging

logger = logging.getLogger(__name__)


def run(job, db):
    logger.info("Running ASR for job %s", job.id)
    # TODO: integrate FunASR
