import tensorflow as tf
from create import setup


def config():
    """This method creates a configuration specific to GPU part of the program.

       Keyword arguments:
        None
    """
    setup.directoriesConfig()
    setup.loggerConfig()
    tf.get_logger().setLevel('ERROR')




