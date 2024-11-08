from flask import Flask, jsonify, render_template, request
from AISHLoader import AISHLoader


print('\n\n\n')

# Flask application
app = Flask(__name__, static_url_path='/static')
app.config['SERVER_NAME'] = 'localhost:5000'  # Replace with your server name and port

# STATE VARIABLES
IS_SAMPLE_LOADED = False
SAMPLE_POS = None       #Saves the sample position of the loaded sample, None if nothing is loaded

SAMPLE_POS_LIST = ()    #Tuple of positions that have been loaded into the buffer

# HARDWARE VARIABLES
PORT_ENDER = '/dev/tty.usbmodem1401'
PORT_ARDUINO = '/dev/tty.usbmodem1201'
AISH = AISHLoader(PORT_ENDER, PORT_ARDUINO)
    
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
@app.route('/api/load_sample?<sample_num>', methods=['POST'])
def load_sample(sample_num):
    AISH.load_sample(sample_num)

@app.route('/api/unload_sample', methods=['POST'])
def unload_sample():
    AISH.unload_sample()


    
@app.route('/')
def index():
    return render_template('index.html')

if __name__ == '__main__':
    print(f"App running at: http://{app.config['SERVER_NAME']}")
    app.run(debug=True)