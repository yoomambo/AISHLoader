import numpy as np
import random
import time
import os
import logging

# Set up logging
logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s.%(msecs)03d %(levelname)-8s: %(message)s",
    datefmt='%y-%m-%d %H:%M:%S'
)

# Diffractometer class from Nathan's code: https://github.com/njszym/AdaptiveXRD
# Copied only the relevant part to control the XRD, since the full code imports many machine learning libraries
# and is not needed for this project
class Diffractometer:
    """
    Main class used to interface with different
    types of diffractometers.
    """

    def __init__(self, instrument_name, results_dir='Results'):
        self.instrument_name = instrument_name
        self.results_dir = results_dir

        # You may add your own instrument here
        known_instruments = ['Bruker', 'Aeris', 'Post Hoc']
        assert self.instrument_name in known_instruments, 'Instrument is not known'

    def execute_scan(self, min_angle, max_angle, prec, temp, spec_fname, init_step, init_time, final_step, final_time):

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
            tolerance = 600 # by default, allow 10 minutes

            # Write to params file; will be read by LabLims job file
            with open('ScanParams.txt', 'w+') as f:
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
            with open('Results/XRD.ascii') as f:
                for line in f.readlines()[3:]:
                    x.append(float(line.split(';')[2]))
                    y.append(float(line.split(';')[-1]))
            x = np.array(x)
            y = np.array(y)

            # Clean up results folder
            os.remove('Results/XRD.ascii')

            return x, y

# Creates an object to control the XRD, each object represents an AISH experiment
class AISHExperiment:
    _SAVE_DIR = './AISH_results'
    
    def __init__(self, name, min_angle, max_angle, prec, temperatures):
        self.results_dir = name
        
        self.min_angle = min_angle
        self.max_angle = max_angle
        self.prec = prec
        self.temperatures = temperatures
        self.temperatures.append(25) #Add room temperature to the end to cool down

        print(f"temperatures {self.temperatures}")

        self.progress = {'cur_step': 0, 'total_steps': len(temperatures), 'cur_temp': 25}

        self.ABORT = False

        #Initialize the XRD controller from the adaptXRD module
        self.diffrac = Diffractometer('Bruker')

    def save_data(self, x, y, temp):
        #Save the data to a file
        with open(f'./{self._SAVE_DIR}/{self.results_dir}/temp_{temp}.csv', 'w+') as f:
            for (xval, yval) in zip(x,y):
                f.write(f'{xval} {yval}\n')
        logging.info(f"Saved data for temperature {temp}")

    def run_sequence(self):
        for idx, temp in enumerate(self.temperatures):
            if not self.ABORT:
                #Update the progress
                self.progress['cur_step'] = idx
                self.progress['cur_temp'] = temp
            
                #Run the XRD scan, blocking call
                x,y = self.diffrac.execute_scan(self.min_angle, self.max_angle, self.prec, temp, None)

                #Save the data
                self.save_data(x, y, temp)
            else:
                logging.error("Experiment aborted")
                self.progress['cur_temp'] = temp

                #Run the XRD scan, blocking call, run to 25C to cool down
                x,y = self.diffrac.execute_scan(self.min_angle, self.max_angle, self.prec, 25, None)
                
                #Save the data
                self.save_data(x, y, 25)
                
                return
        logging.info("XRD experiment complete")

    def test_run_sequence(self):
        for idx, temp in enumerate(self.temperatures):
            if not self.ABORT:
                #Update the progress
                self.progress['cur_step'] = idx
                self.progress['cur_temp'] = temp
            
                #Run the XRD scan, blocking call
                time.sleep(5)
                logging.info(f"XRD experiment at {temp}C")
            else:
                logging.error("Experiment aborted, cooling to 25C")
                self.progress['cur_temp'] = 25
                
                #Run the XRD scan, blocking call, run to 25C to cool down
                time.sleep(5)
                logging.info(f"XRD experiment at 25C")

                return
            
        logging.info("XRD experiment complete")

    def get_progress(self):
        return self.progress
    
    def abort(self):
        self.ABORT = True

