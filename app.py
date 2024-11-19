from flask import Flask, jsonify, render_template, request
from AISHLoader import AISHLoader
import logging

print('\n\n\n')

#Set up logging
logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s.%(msecs)03d %(levelname)-8s: %(message)s",
    datefmt='%y-%m-%d %H:%M:%S'
)


# Flask application
app = Flask(__name__, static_url_path='/static')
TEST_MODE = True

# STATE VARIABLES
IS_SAMPLE_LOADED = False
SAMPLE_POS = None       #Saves the sample position of the loaded sample, None if nothing is loaded

SAMPLE_POS_LIST = ()    #Tuple of positions that have been loaded into the buffer

# HARDWARE VARIABLES
PORT_ENDER = '/dev/tty.usbmodem1401'
PORT_ARDUINO = '/dev/tty.usbmodem1201'
try: 
    AISH = AISHLoader(PORT_ENDER, PORT_ARDUINO)
except:
    if TEST_MODE:
        AISH = None
    else:
        raise Exception("Failed to connect to hardware")
    
@app.route('/api/get_state', methods=['POST'])
def get_state():
    '''
    Returns the state of the automated In-situ heating XRD loader
    '''
    return jsonify(AISH.get_state())

@app.route('/api/loading_sample_buffer', methods=['POST'])
def loading_sample_buffer():
    AISH.eject_sample_buffer(True)

@app.route('/api/done_loading_sample_buffer', methods=['POST'])
def done_loading_sample_buffer():
    AISH.eject_sample_buffer(False)

@app.route('/api/command_package', methods=['POST'])
def command_package():
    '''
    Command package to load sample, run XRD, and unload sample
    This is the HTTP endpoint that the frontend will call to run the XRD
    Frontend pushes the latest item in its queue to this endpoint, also is endpoint
    intended for ALabOS to use.
    '''
    sample_num = request.json['sample_num']
    xrd_params = request.json['xrd_params']
    AISH.command()


############################################################################################################
# MANUAL OPERATION ENDPOINTS
############################################################################################################
@app.route('/api/load_sample', methods=['POST'])
def load_sample():
    data = request.get_json()  # Parse incoming JSON data
    sample_num = data.get('sample_num')  # Extract sample number

    logging.info(f"Loading sample {sample_num}")

    # AISH.load_sample(sample_num)
    return jsonify({"success": True, "sample_num": sample_num})

@app.route('/api/unload_sample', methods=['POST'])
def unload_sample():
    logging.info("Unloading sample")

    # AISH.unload_sample()
    return jsonify({"success": True})

# Ender3 endpoints ############################################################################################################
@app.route('/api/ender3/move_to_sample', methods=['POST'])
def ender3_move_to_sample():
    data = request.get_json()  # Parse incoming JSON data
    sample_num = data.get('sample_num')  # Extract sample number

    logging.debug(f"Received request to move Ender3 to sample {sample_num}")

    # AISH.ender3.move_to_sample(sample_num)
    return jsonify({"success": True, "sample_num": sample_num})

@app.route('/api/ender3/move_to_rest', methods=['POST'])
def ender3_move_to_rest():
    logging.debug("Received request to move Ender3 to rest position")

    # AISH.ender3.move_to_rest()
    return jsonify({"success": True})

@app.route('/api/ender3/move_to_home', methods=['POST'])
def ender3_move_to_home():
    logging.debug("Received request to move Ender3 to home position")

    # AISH.ender3.move_to_home()
    return jsonify({"success": True})

@app.route('/api/ender3/move_to_stage', methods=['POST'])
def ender3_move_to_stage():
    logging.debug("Received request to move Ender3 to stage position")

    # AISH.ender3.move_to_stage()
    return jsonify({"success": True})

@app.route('/api/ender3/move_eject_bed', methods=['POST'])
def ender3_move_eject_bed():
    logging.debug("Received request to move Ender3 to eject bed")

    # AISH.ender3.move_eject_bed()
    return jsonify({"success": True})

@app.route('/api/ender3/home', methods=['POST'])
def ender3_home():
    logging.debug("Received request to home Ender3")

    # AISH.ender3.init_homing()
    return jsonify({"success": True})

# Arduino endpoints ############################################################################################################
@app.route('/api/arduino/gripper/open', methods=['POST'])
def arduino_gripper_open():
    logging.debug("Received request to open Arduino gripper")

    # AISH.arduino.open_gripper()
    return jsonify({"success": True})

@app.route('/api/arduino/gripper/close', methods=['POST'])
def arduino_gripper_close():
    logging.debug("Received request to close Arduino gripper")

    # AISH.arduino.close_gripper()
    return jsonify({"success": True})

@app.route('/api/arduino/linear_rail/move_up', methods=['POST'])
def arduino_linrail_moveup():
    logging.debug("Received request to move Arduino linear rail up")

    # AISH.arduino.move_up()
    return jsonify({"success": True})

@app.route('/api/arduino/linear_rail/move_down', methods=['POST'])
def arduino_linrail_movedown():
    logging.debug("Received request to move Arduino linear rail down")

    # AISH.arduino.move_down()
    return jsonify({"success": True})

@app.route('/api/arduino/linear_rail/home', methods=['POST'])
def arduino_linrail_home():
    logging.debug("Received request to home Arduino linear rail")

    # AISH.arduino.init_homing()
    return jsonify({"success": True})


    
@app.route('/')
def index():
    return render_template('index.html')

if __name__ == '__main__':
    print(f"App running at: http://127.0.0.1:5000/")
    app.run(host='127.0.0.1', port=5000, debug=True)