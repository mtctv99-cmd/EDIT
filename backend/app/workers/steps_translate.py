import logging

logger = logging.getLogger(__name__)


def run(job, db):
    logger.info("Translating subtitles for job %s", job.id)
    # TODO: integrate Gemini translate
