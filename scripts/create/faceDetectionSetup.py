# Module name: faceDetectionSetup
# Purpose: This module contains function to set up the environment specific to the face detection part of the program.

import tensorflow as tf

from create.setup import directoriesConfig, loggerConfig


def config():
    """This method creates a configuration specific to the face detection part of the program.

       Keyword arguments:
        None
    """

    directoriesConfig()
    loggerConfig()
    tf.get_logger().setLevel('ERROR')