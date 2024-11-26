'''
This script tests the xrd experiment class
'''

from AISHExperiment import AISHExperiment
from concurrent.futures import ThreadPoolExecutor
import logging
import time


# Set up logging
logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s.%(msecs)03d %(levelname)-8s: %(message)s",
    datefmt='%y-%m-%d %H:%M:%S'
)

experiment_thread = ThreadPoolExecutor(max_workers=1)

exp = AISHExperiment('test', 0, 180, 0.01, [300, 400, 500, 600])

def run_exp():
    exp.test_run_sequence()

experiment_thread.submit(run_exp)

for i in range(30):
    logging.info(f"{i} : {exp.get_progress()}")
    time.sleep(1)

    if i == 7:
        logging.info("Abort command sent")
        exp.abort()