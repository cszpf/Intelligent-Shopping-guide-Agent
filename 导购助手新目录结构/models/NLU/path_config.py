import os
import sys


class Config(object):
    """
    Config class: the absolute path of the SLU package
    """

    def __init__(self):
        self.SLU_path = os.path.dirname(__file__)  # fixme: please modify this path when in new environment
