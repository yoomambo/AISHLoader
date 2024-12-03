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

exp = AISHExperiment('test2', 40, 44, 'Low', [30])

def run_exp():
    exp.run_sequence()

future = experiment_thread.submit(run_exp)

# Block the main thread until the task is finished
future.result()  # This will block until run_exp() finishes

# Once the thread is done, exit the program or perform any final actions
logging.info("Experiment is complete. Exiting program.")
experiment_thread.shutdown() 