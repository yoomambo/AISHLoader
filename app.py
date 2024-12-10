from flask import Flask, jsonify, render_template, request
from concurrent.futures import ThreadPoolExecutor
from AISHLoader import AISHLoader
from AISHExperiment import AISHExperiment
import logging
import os
import time

print('\n\n\n')

#Set up logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s.%(msecs)03d %(levelname)-8s: %(message)s",
    datefmt='%y-%m-%d %H:%M:%S'
)


# Flask application
app = Flask(__name__, static_url_path='/static')
WEBSITE_TEST_MODE = True
tempvar = 0

# STATE VARIABLES
IS_SAMPLE_LOADED = False
SAMPLE_POS = None       #Saves the sample position of the loaded sample, None if nothing is loaded

SAMPLE_POS_LIST = ()    #Tuple of positions that have been loaded into the buffer

# HARDWARE VARIABLES
PORT_ENDER = '/dev/tty.usbmodem141101'
PORT_ARDUINO = '/dev/tty.usbmodem141201'
if not WEBSITE_TEST_MODE:
    try: 
        aish_loader = AISHLoader(PORT_ENDER, PORT_ARDUINO)
    except:
        raise Exception("Failed to connect to hardware")
else:
    aish_loader = None
logging.info("AISHLoader initialized")

#Variable to store the XRD experiment, starts with no experiment
aish_experiment = None
experiment_thread = ThreadPoolExecutor(max_workers=1)

# Endpoint to get the state of the automated In-situ heating XRD loader
# Intended use is for the frontend to poll the state of the system
@app.route('/api/get_state', methods=['GET'])
def get_state():
    '''
    Returns the state of the automated In-situ heating XRD loader
    '''
    # state = {'aish_loader': aish_loader.get_state() if aish_loader is not None else None,
            #  'aish_experiment': aish_experiment.get_progress() if aish_experiment is not None else None}
    state = {'aish_loader': aish_loader.get_state() if aish_loader is not None else None,
             'aish_experiment': aish_experiment if aish_experiment is not None else None}

    print("AISH EXPERIMENT", aish_experiment)

    return jsonify(state)

# Endpoints to eject/load sample buffer 
@app.route('/api/loading_sample_buffer', methods=['POST'])
def loading_sample_buffer():
    logging.info("Loading sample buffer")
    if not WEBSITE_TEST_MODE:
        aish_loader.eject_sample_buffer(True)
    return jsonify({"success": True})

@app.route('/api/done_loading_sample_buffer', methods=['POST'])
def done_loading_sample_buffer():
    logging.info("Done loading sample buffer")
    if not WEBSITE_TEST_MODE:
        aish_loader.eject_sample_buffer(False)
    return jsonify({"success": True})


@app.route('/api/command', methods=['POST'])
def command():
    '''
    Command package to load sample, run XRD, and unload sample
    This is the HTTP endpoint that the frontend will call to run the XRD
    Frontend pushes the latest item in its queue to this endpoint, also is endpoint
    intended for ALabOS to use.
    '''
    global aish_experiment  #Ensure we are using the global variable to store the experiment
    sample_num = request.json['sample_num']
    xrd_params = request.json['xrd_params']

    logging.info(f"Received command to run XRD on sample \n\t{sample_num} \n\t{xrd_params}")

    
    aish_experiment = {'sample_num': sample_num, 'xrd_params': xrd_params}
    print("OUT OF TEST", aish_experiment)
    def run_test():
        global aish_experiment  #Ensure we are using the global aish_experiment
        print(f"IN TEST {aish_experiment}\n\n")
        logging.info("Starting experiment")
        time.sleep(5)
        
        aish_experiment = "WORLD"
        print(f"IN TEST2 {aish_experiment}\n\n")
        time.sleep(5)

        print(f"IN TEST3 {aish_experiment}\n\n")
        aish_experiment = None
    experiment_thread.submit(run_test)

    # # # Create a new XRD experiment, and loading routine
    # # aish_experiment = AISHExperiment(xrd_params)
    # def run_xrd(sample_num, xrd_params):
    #     global aish_experiment
    #     global aish_loader
    #     # Load the sample
    #     aish_loader.load_sample(sample_num)
    #     aish_experiment.run_sequence(xrd_params)
    #     aish_loader.unload_sample()

    #     #Reset the experiment
    #     aish_experiment = None

    # # Submit the full routine to the executor
    # experiment_thread.submit(run_xrd, sample_num, xrd_params)

    return jsonify({"success": True})

@app.route('/api/abort', methods=['POST'])
def abort():
    #Stop XRD acquisition
    aish_experiment.abort()

    # Unload the sample
    
    aish_experiment = None

############################################################################################################
# MANUAL OPERATION ENDPOINTS
############################################################################################################
@app.route('/api/load_sample', methods=['POST'])
def load_sample():
    data = request.get_json()  # Parse incoming JSON data
    sample_num = int(data.get('sample_num'))  # Extract sample number

    logging.info(f"Loading sample {sample_num}")

    if not WEBSITE_TEST_MODE:
        aish_loader.load_sample(sample_num)
        
    return jsonify({"success": True, "sample_num": sample_num})

@app.route('/api/unload_sample', methods=['POST'])
def unload_sample():
    logging.info("Unloading sample")

    if not WEBSITE_TEST_MODE:
        aish_loader.unload_sample()
        
    return jsonify({"success": True})

# Ender3 endpoints ############################################################################################################
@app.route('/api/ender3/move_to_sample', methods=['POST'])
def ender3_move_to_sample():
    data = request.get_json()  # Parse incoming JSON data
    sample_num = int(data.get('sample_num'))  # Extract sample number

    logging.debug(f"Received request to move Ender3 to sample {sample_num}")

    if not WEBSITE_TEST_MODE:
        aish_loader.ender3.move_to_sample(sample_num)
        
    return jsonify({"success": True, "sample_num": sample_num})

@app.route('/api/ender3/move_to_rest', methods=['POST'])
def ender3_move_to_rest():
    logging.debug("Received request to move Ender3 to rest position")

    if not WEBSITE_TEST_MODE:
        aish_loader.ender3.move_to_rest()
        
    return jsonify({"success": True})

@app.route('/api/ender3/move_to_home', methods=['POST'])
def ender3_move_to_home():
    logging.debug("Received request to move Ender3 to home position")

    if not WEBSITE_TEST_MODE:
        aish_loader.ender3.move_to_home()
        
    return jsonify({"success": True})

@app.route('/api/ender3/move_to_stage', methods=['POST'])
def ender3_move_to_stage():
    logging.debug("Received request to move Ender3 to stage position")

    if not WEBSITE_TEST_MODE:
        aish_loader.ender3.move_to_stage()
        
    return jsonify({"success": True})

@app.route('/api/ender3/move_eject_bed', methods=['POST'])
def ender3_move_eject_bed():
    logging.debug("Received request to move Ender3 to eject bed")

    if not WEBSITE_TEST_MODE:
        aish_loader.ender3.move_eject_bed()
        
    return jsonify({"success": True})

@app.route('/api/ender3/home', methods=['POST'])
def ender3_home():
    logging.debug("Received request to home Ender3")

    if not WEBSITE_TEST_MODE:
        aish_loader.ender3.init_homing()
        
    return jsonify({"success": True})

# Arduino endpoints ############################################################################################################
@app.route('/api/arduino/gripper/open', methods=['POST'])
def arduino_gripper_open():
    logging.debug("Received request to open Arduino gripper")

    if not WEBSITE_TEST_MODE:
        aish_loader.arduino.gripper.open()
        
    return jsonify({"success": True})

@app.route('/api/arduino/gripper/close', methods=['POST'])
def arduino_gripper_close():
    logging.debug("Received request to close Arduino gripper")

    if not WEBSITE_TEST_MODE:
        aish_loader.arduino.gripper.close()
        
    return jsonify({"success": True})

@app.route('/api/arduino/linear_rail/move_up', methods=['POST'])
def arduino_linrail_moveup():
    logging.debug("Received request to move Arduino linear rail up")

    if not WEBSITE_TEST_MODE:
        aish_loader.arduino.linear_rail.move_up()
        
    return jsonify({"success": True})

@app.route('/api/arduino/linear_rail/move_down', methods=['POST'])
def arduino_linrail_movedown():
    logging.debug("Received request to move Arduino linear rail down")

    if not WEBSITE_TEST_MODE:
        aish_loader.arduino.linear_rail.move_down()
        
    return jsonify({"success": True})

@app.route('/api/arduino/linear_rail/home', methods=['POST'])
def arduino_linrail_home():
    logging.debug("Received request to home Arduino linear rail")

    if not WEBSITE_TEST_MODE:
        aish_loader.arduino.linear_rail.home()
        
    return jsonify({"success": True})


    
@app.route('/')
def index():
    return render_template('index.html')

if __name__ == '__main__':
    print(f"App running at: http://127.0.0.1:8000/")
    app.run(host='127.0.0.1', port=8000, debug=WEBSITE_TEST_MODE)