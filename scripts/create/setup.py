# Module name: Setup
# Purpose: This module contains functions to set up the environment prior to downloading the dataset.

import logging
import os

from constants import IMAGES_DIRECTORY, DATA_DIRECTORY, DATASET_DIRECTORY, STATS_DIRECTORY, LOGS_DIRECTORY


def directoriesConfig():
    """This method creates all the directories needed for database creation.

       Keyword arguments:
        None
    """

    if not os.path.exists(IMAGES_DIRECTORY):
        os.makedirs(IMAGES_DIRECTORY)

    if not os.path.exists(DATA_DIRECTORY):
        os.makedirs(DATA_DIRECTORY)

    if not os.path.exists(DATASET_DIRECTORY):
        os.makedirs(DATASET_DIRECTORY)

    if not os.path.exists(STATS_DIRECTORY):
        os.makedirs(STATS_DIRECTORY)

    if not os.path.exists(LOGS_DIRECTORY):
        os.makedirs(LOGS_DIRECTORY)


def loggerConfig():
    """This method sets up the logger.

       Keyword arguments:
        None
    """

    logging.basicConfig(filename=f'{LOGS_DIRECTORY}/errors.log',
                        filemode='a',
                        format='%(asctime)s.%(msecs)03d %(levelname)s %(module)s - %(funcName)s: %(message)s',
                        datefmt='%Y-%m-%d %H:%M:%S',
                        level=logging.INFO)