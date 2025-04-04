import logging


def setup_logger():
    logging.basicConfig(
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        level=logging.INFO,
        filename="data/logs/bot.log"
    )
    return logging.getLogger(__name__)


logger = setup_logger()