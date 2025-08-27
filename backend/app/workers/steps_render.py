import logging

logger = logging.getLogger(__name__)


def run(job, db):
    logger.info("Rendering video for job %s", job.id)
    # TODO: implement ffmpeg render and subtitles burn-in
