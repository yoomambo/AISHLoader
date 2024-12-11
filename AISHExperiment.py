"""
AISHExperiment.py
This defines the AISHExperiment class, which is used to control the XRD machine. This stores the information 
"""

import numpy as np
import random
import time
import os
import logging
from datetime import datetime

# Set up logging
logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s.%(msecs)03d %(levelname)-8s: %(message)s",
    datefmt='%y-%m-%d %H:%M:%S'
)

RESULTS_FILE = r'C:\Users\9KKFWL2\Documents\Interfacing_Tests\Results\XRD.ascii'

# Diffractometer class from Nathan's code: https://github.com/njszym/AdaptiveXRD
# Copied only the relevant part to control the XRD, since the full code imports many machine learning libraries
# and is not needed for this project
class Diffractometer:
    """
    Main class used to interface with different
    types of diffractometers.
    """

    def __init__(self, instrument_name, results_dir=r'C:\Users\9KKFWL2\Documents\Interfacing_Tests\Results'):
        self.instrument_name = instrument_name
        self.results_dir = results_dir

        # Clear the results file, if it exists
        if os.path.exists(RESULTS_FILE):
            os.remove(RESULTS_FILE)

        # You may add your own instrument here
        known_instruments = ['Bruker', 'Aeris', 'Post Hoc']
        assert self.instrument_name in known_instruments, 'Instrument is not known'

    def execute_scan(self, min_angle, max_angle, prec, temp, spec_fname, init_step=0.02, init_time=0.1, final_step=0.01, final_time=0.2):

        # High precision = slow scan
        # Low precision = fast scan
        assert prec in ['Low', 'High'], 'Precision must be High or Low, not %s' % prec

        # To avoid tolerance issues
        min_angle -= 0.1
        max_angle += 0.1

        """
        Each diffractometer requires unique interfacing scripts.

        Our current workflow is compatible with two diffractometers:
        - Bruker D8 Advance
        - Panalytical Aeris     (not implemented here, deleted for brevity [bxl 241126])

        We also have a "Post Hoc" setting where measurements were
        performed beforehand and the adaptive algorithm learns
        to interpolate between high- and low-precision data.

        For use with a different instrument, add code here.
        """

        if self.instrument_name == 'Bruker':

            # Use these to set desired resolution
            if prec == 'High':
                step_size = final_step # deg
                time_per_step = final_time # sec
            if prec == 'Low':
                step_size = init_step # deg
                time_per_step = init_time # sec

            # Expected measurement time
            expec_time = time_per_step*(max_angle - min_angle)/step_size

            # Allow some tolerance before calling timeout
            # e.g., it may take some time reach the measurement temperature
            tolerance = 10000                                           #MODIFIED TO 10000 SECONDS to allow cooling down

            # Write to params file; will be read by LabLims job file
            with open(r"C:\Users\9KKFWL2\Documents\Interfacing_Tests\ScanParams.txt", 'w+') as f:
                f.write('start_angle;end_angle;step_size;time_per_step;\n')
                f.write('%s;%s;%s;%s;' % (min_angle, max_angle, step_size, time_per_step))

            # Scan script and exp jobfile must be written beforehand!
            jobname = 'C:/ProgramData/Bruker AXS/LabLims/Job.xml'
            with open(jobname, 'w+') as f:
                f.write('<?xml version="1.0"?>\n')
                f.write('<MeasurementJob>\n')
                f.write('  <SamplePosition>1A01</SamplePosition>\n')
                f.write('  <Priority>50</Priority>\n')
                f.write('  <Permanent>false</Permanent>\n')
                f.write('  <ExperimentFileOrID>%sC.bsml</ExperimentFileOrID>\n' % temp)
                f.write('  <ScriptFile>FullScanScript.cs</ScriptFile>\n')
                f.write('</MeasurementJob>\n')

            # Wait until results file is detected
            done, failed = False, False
            start_time = time.time()
            timeout = expec_time + tolerance
            while not done:
                time.sleep(5) # Check folder once every 5 seconds
                result_files = os.listdir(self.results_dir)
                if len(result_files) > 0:
                    assert len(result_files) == 1, 'Too many result files'
                    fname = result_files[0]
                    done = True
                elapsed_time = time.time() - start_time
                if elapsed_time > timeout:
                    done, failed = True, True

            # If measurement failed, abort scan
            if failed:
                print('Measurement failed. No results file detected.')
                return [None], [None]

            # If scan was successful: load xy values
            x, y = [], []
            with open(RESULTS_FILE) as f:
                for line in f.readlines()[3:]:
                    x.append(float(line.split(';')[2]))
                    y.append(float(line.split(';')[-1]))
            x = np.array(x)
            y = np.array(y)

            # Clean up results folder
            os.remove(RESULTS_FILE)

            return x, y

# Creates an object to control the XRD, each object represents an AISH experiment
class AISHExperiment:
    _SAVE_DIR = './AISH_results'
    _MAX_TEMP = 1100
    
    def __init__(self, name, sample_num, min_angle, max_angle, precision, temperatures):
        self.results_dir = f"{self._SAVE_DIR}/{name}"
        self.sample_num = sample_num
        
        self.min_angle = min_angle
        self.max_angle = max_angle
        self.precision = precision
        
        #Ensure no temperatures are above 1100C
        self.temperatures = [temp if temp <= self._MAX_TEMP else self._MAX_TEMP for temp in temperatures]
        self.temperatures.append(25) #Add room temperature to the end to cool down

        print(f"temperatures {self.temperatures}")

        self.progress = {'cur_step': 0, 'total_steps': len(temperatures), 'cur_temp': 25}

        self.ABORT = False


    def run_sequence(self):
        for idx, temp in enumerate(self.temperatures):
            if not self.ABORT:
                #Update the progress
                self.progress['cur_step'] = idx
                self.progress['cur_temp'] = temp
                logging.info(f"Executing scan at {temp}C, min 2theta: {self.min_angle}, max 2theta: {self.max_angle}")
                
                self._single_scan(temp)
            else:
                logging.error("Experiment aborted")
                self.progress['cur_temp'] = 25

                #Run the XRD scan, blocking call, run to 25C to cool down
                self._single_scan(25)
                
                logging.info("XRD experiment ABORT complete")
                return

            #We need to wait for the Bruker to move the Job.xml to finished, 
            #otherwise it will just move our new file and the new job will never be executed
            # Set the timeout in seconds
            timeout = 3600
            start_time = time.time()

            # Wait until the timeout is reached or 'Job.xml' is no longer in the directory
            while time.time() - start_time < timeout and 'Job.xml' in os.listdir('C:/ProgramData/Bruker AXS/LabLims/'):
                time.sleep(0.5)

            # If the timeout was reached without moving the file, throw an error
            if 'Job.xml' in os.listdir('C:/ProgramData/Bruker AXS/LabLims/'):
                logging.error("Timeout reached. Job.xml was not moved to finished in time.")
                raise TimeoutError("Timeout reached while waiting for Job.xml to be moved to finished.")

        logging.info("XRD experiment complete")

    def _single_scan(self, temp):
        existing_file = None
        precision = self.precision

        # Define diffractometer object
        diffrac = Diffractometer('Bruker')

        # Run initial scan
        min_angle = self.min_angle
        max_angle = self.max_angle
        x, y = diffrac.execute_scan(min_angle, max_angle, precision, temp, None)

        # Write data
        # Check if the Spectra directory exists, if not, create it
        if not os.path.exists(self.results_dir):
            os.makedirs(self.results_dir)

        spectrum_fname = f'{datetime.now().strftime("%y%m%d-%H%M%S")}_temp_{temp}.xy'
        with open(f'{self.results_dir}/{spectrum_fname}', 'w+') as f:
            for (xval, yval) in zip(x, y):
                f.write('%s %s\n' % (xval, yval))

        abs_saved_filepath = os.path.abspath(f'{self.results_dir}/{spectrum_fname}')
        logging.info(f"Saved data of scan for {temp}C to {abs_saved_filepath}")

    def get_progress(self):
        return {'progress': self.progress,
                'xrd_params': {'sample_num': self.sample_num,
                                'min_angle': self.min_angle, 
                               'max_angle': self.max_angle, 
                               'precision': self.precision, 
                               'temperatures': self.temperatures}
                }
    
    def abort(self):
        self.ABORT = True

