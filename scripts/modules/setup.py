import logging
import os
import warnings

from modules import constants

logging.basicConfig(filename='errors.log',
                    filemode='a',
                    format='%(asctime)s.%(msecs)03d %(levelname)s %(module)s - %(funcName)s: %(message)s',
                    datefmt='%Y-%m-%d %H:%M:%S',
                    level=logging.INFO)

# I am using beautiful soup for getting rid of HTML characters in caption and dates, in few cases it contains
# a name of a file, which triggers BS4 warning
warnings.filterwarnings("ignore", category=UserWarning, module='bs4')
# tf.get_logger().setLevel('ERROR')

if not os.path.exists(constants.IMAGES_DIRECTORY):
    os.makedirs(constants.IMAGES_DIRECTORY)
