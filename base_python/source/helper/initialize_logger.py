# imports
import logging
import os
import datetime
from enum import Enum


class LoggingLevels(Enum):
    CRITICAL = logging.CRITICAL
    WARNING = logging.WARNING
    DEBUG = logging.DEBUG
    NONE = 1


def initialize_logger(level: LoggingLevels, log_file_dir: str = None):
    """
    This method is used to initialize a logger with a specific level and the preferred format.

    Args:
        level (LoggingLevels): Level of the outputs which should be printed in console
        log_file_dir (str):   Directory where the logfile of the run should be saved
    """

    from imp import reload  # python 2.x don't need to import reload, use it directly
    reload(logging)

    if level.name is not LoggingLevels.NONE:
        level = level.value
        # TODO: Logger so initialisieren, dass gar keine Meldungen ausgegeben werden.
    formatter = '%(levelname)s: %(message)s'
    if log_file_dir is not None:
        log_file_name = log_file_dir + '/run.log'

        if os.path.exists(log_file_name):
            os.remove(log_file_name)
        if level != LoggingLevels.NONE:
            logging.basicConfig(
                level=level,
                format=formatter,
                filename=log_file_name,
                force=True
            )
    if level != LoggingLevels.NONE:
        logging.basicConfig(
            level=level,
            format=formatter,
            force=True
        )

    # global logger
    logger = logging.getLogger(__name__).parent

    logger.handlers[0].level = logging.INFO
    # logger.handlers[0].mode = 'w'

    logging.info('LOG started at {}'.format(datetime.datetime.now().strftime("%c")))
