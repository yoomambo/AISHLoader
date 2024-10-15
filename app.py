from flask import Flask, jsonify, render_template, request
import asyncio
import datetime
import math
import random
import time
import threading
import os
import numpy as np


print('\n\n\n')

# Flask application
app = Flask(__name__, static_url_path='/static')
app.config['SERVER_NAME'] = 'localhost:5000'  # Replace with your server name and port

# STATE VARIABLES
IS_SAMPLE_LOADED = False
SAMPLE_POS = None       #Saves the sample position of the loaded sample, None if nothing is loaded

SAMPLE_POS_LIST = ()    #Tuple of positions that have been loaded into the buffer

@app.route('/api/load_sample?<sample_num>', methods=['POST'])
def load_sample(sample_num):
    # Check state to see if sample is loaded already
    if IS_SAMPLE_LOADED:
        raise Exception('StateError: Sample already loaded')
        return
    # Check if the sample position is valid
    if sample_num not in SAMPLE_POS_LIST:
        raise Exception(f'StateError: No Sample loaded at position {sample_num}')
        return
    
    # Execute the procedure to load a sample
    SAMPLE_POS = sample_num
    #(1) Move 3D printer to sample in sample buffer
    #Translate plate to position
    #Move head to position

    #(2) Grab Sample with Gripper

    #(3) Move 3D printer to sample stage

    #(4) Release sample with Gripper

    #(5) Return 3D printer to home, elevate sample stage into furnace

    IS_SAMPLE_LOADED = True

@app.route('/api/unload_sample', methods=['POST'])
def unload_sample():
    # Check state to see if sample is loaded already
    if not IS_SAMPLE_LOADED:
        raise Exception('State Error: No Sample loaded')
    
    #(1) Remove sample stage from furnace

    #(2) Move 3D printer to stage

    #(3) Grab Sample with Gripper

    #(4) Move 3D printer to Sample position (where it was originally stored)
    #Translate plate to position
    #Move head to position

    #(5) Release sample with Gripper

    #(6) Return 3D printer to home

    IS_SAMPLE_LOADED = False
    SAMPLE_POS = None
    
@app.route('/api/get_state', methods=['POST'])
def get_state():
    '''
    Returns the state of the automated In-situ heating XRD loader
    '''
    return [IS_SAMPLE_LOADED, SAMPLE_POS]

@app.route('/api/prep_sample_buffer', methods=['POST'])
def prep_sample_buffer():
    if IS_SAMPLE_LOADED:
        raise Exception('StateError: Sample currently loaded, XRD likely running')
    
    #(1) Send 3D printer to home, out of the way

    #(2) Translate the 3D printer plate all the way to make space for loading

@app.route('/api/loaded_sample_buffer', methods=['POST'])
def loaded_sample_buffer():
    requestData = request.get_json()
    sample_positions = requestData.get('sample_positions')

    SAMPLE_POS_LIST = tuple(sample_positions)
    
@app.route('/')
def index():
    return render_template('index.html')

if __name__ == '__main__':
    print(f"App running at: http://{app.config['SERVER_NAME']}")
    app.run(debug=True)