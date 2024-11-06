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


@app.route('/api/load_sample?<sample_num>', methods=['POST'])
def load_sample(sample_num):
    AISH.load_sample(sample_num)

@app.route('/api/unload_sample', methods=['POST'])
def unload_sample():
    AISH.unload_sample()
    
@app.route('/api/get_state', methods=['POST'])
def get_state():
    '''
    Returns the state of the automated In-situ heating XRD loader
    '''
    pass

@app.route('/api/prep_sample_buffer', methods=['POST'])
def loading_sample_buffer():
    # TODO: Add checks to ensure movement is feasible
    
    AISH.ender3.move_to_rest()
    AISH.ender3.move_eject_bed()

    
@app.route('/')
def index():
    return render_template('index.html')

if __name__ == '__main__':
    print(f"App running at: http://{app.config['SERVER_NAME']}")
    app.run(debug=True)