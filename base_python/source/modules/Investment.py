import logging
from scipy.interpolate import interp2d

from base_python.source.modules.GenericUnit import GenericUnit


class Investment(GenericUnit):

    def __init__(self, new_investment=True, economical_parameters=None):
        super().__init__(new_investment=new_investment, economical_parameters=economical_parameters)

    def run(self):
        logging.critical('Component of type Investment has no run function')
