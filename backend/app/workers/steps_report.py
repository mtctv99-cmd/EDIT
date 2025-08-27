import logging

logger = logging.getLogger(__name__)


def run(job, db):
    logger.info("Generating report for job %s", job.id)
    # TODO: produce JSON report and store artifact
