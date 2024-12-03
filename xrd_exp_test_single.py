import os
import time
import numpy as np
from datetime import datetime
from AISHExperiment import Diffractometer
from AISHExperiment import AISHExperiment
from concurrent.futures import ThreadPoolExecutor



experiment_thread = ThreadPoolExecutor(max_workers=1)
def run_exp():
    print("STARTING RUN")

    # Define diffractometer object
    instrument = 'Bruker'
    diffrac = Diffractometer(instrument)

    # Run initial scan
    min_angle, max_angle = 20.0, 40.0
    temp = 30 # Temperature
    existing_file = None
    prec = 'Low'
    x, y = diffrac.execute_scan(min_angle, max_angle, prec, temp, existing_file)

    print("AFTER scan")
    AISHExperiment.save_data(x,y,temp)

experiment_thread.submit(run_exp)

for i in range(400):
    print(f"Step {i}")
    time.sleep(10)

# Write data
# spectrum_fname = f'{datetime.now().strftime("%y%m%d%M%S")}_ScanData.xy'
# if existing_file != None:
#     spectrum_fname = existing_file
# with open('Spectra/%s' % spectrum_fname, 'w+') as f:
#     for (xval, yval) in zip(x, y):
#         f.write('%s %s\n' % (xval, yval))

#     print("saved file")
