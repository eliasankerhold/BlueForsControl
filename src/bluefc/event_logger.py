from logging import Formatter, StreamHandler, INFO, getLogger, DEBUG
from logging.handlers import RotatingFileHandler
import sys
import os

log_file = os.path.join('..', '..', 'logs', 'blue_fors_control.log')

if not os.path.isdir(os.path.dirname(log_file)):
    os.makedirs(os.path.dirname(log_file))

simple_formatter = Formatter("%(levelname)s: %(message)s")
detailed_formatter = Formatter('[%(asctime)s] %(levelname)s - %(message)s')

file_handler = RotatingFileHandler(filename=log_file, maxBytes=100000000, backupCount=99)
stdout_handler = StreamHandler(stream=sys.stdout)
file_handler.setLevel(INFO)
stdout_handler.setLevel(DEBUG)
file_handler.setFormatter(detailed_formatter)
stdout_handler.setFormatter(simple_formatter)

bfc_logger = getLogger(name='BlueFClient Logger')
bfc_logger.addHandler(file_handler)
bfc_logger.addHandler(stdout_handler)
bfc_logger.setLevel(DEBUG)
