# Module name: SetupCPU
# Purpose: This module contains function to set up the environment specific to CPU part of the program.

import warnings

from create.setup import directoriesConfig, loggerConfig


def config():
    """This method creates a configuration specific to CPU part of the program.

       Keyword arguments:
        None
    """

    directoriesConfig()
    loggerConfig()

    # I am using beautiful soup for getting rid of HTML characters in caption and dates, in few cases it contains
    # a name of a file, which triggers BS4 warning
    warnings.filterwarnings("ignore", category=UserWarning, module='bs4')