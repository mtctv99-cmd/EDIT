import logging

logger = logging.getLogger(__name__)


def run(job, db):
    logger.info("Downloading %s", job.source_url)
    # TODO: implement yt-dlp or ffmpeg download
