import warnings
from create import setup


def config():
    """This method creates a configuration specific to CPU part of the program.

       Keyword arguments:
        None
    """
    setup.directoriesConfig()
    setup.loggerConfig()

    # I am using beautiful soup for getting rid of HTML characters in caption and dates, in few cases it contains
    # a name of a file, which triggers BS4 warning
    warnings.filterwarnings("ignore", category=UserWarning, module='bs4')

