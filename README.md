# Installation
First, download the application and install dependencies:
```bash
git clone https://github.com/BenjaminLam9838/AISHLoader
cd AISHLoader
```

Create a virtual environment and install the dependencies.  This app was built on Python 3.9.13 ([pyFirmata has issues in 3.11 [1]](#1-pyfirmata-has-issues-in-311))
```bash
python3.9 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
```
# To do:
Hardware:
- [ ] Adjust linear rail alignment. Currently, it is slightly misaligned with the alignment rails and does not insert perfectly
- [ ] Increase stiffness of the gripper if the gripping is not consistent.

Software:
- [ ] Test abortion feature.  Currently, the abortion procedure is not quite complete
- [ ] Known bug: pausing the queue when an experiment is running will make the queue pause after the current experiment is done (will not send the next experiment after finish).  But pressing resume before the experiment is done just sends the next experiment, even if the current one is not finished, causing an error. Likely fix: change logic to just toggle the queue pause state, and remove sendNextItem() function in the resume button callback.
- [ ] Test data saving location for XRD data

# Control Interface Guide
![image](https://github.com/user-attachments/assets/515e7cc4-e6b7-4511-bce1-c0119428e87d)

The web UI is broken into 4 main parts:
- Add to queue (Blue) - adds items to the queue with all the experimental parameters.
- Queue (Green) - displays queued items and updates when items are executed. The items can be dragged to reorder.
- System status (Red) - displays the current system state.
- Manual control (Orange) - collapsable menu that contains buttons to manually control all components of the AISH Loader.


# System Diagram
## Top-level Flowchart
![image](https://github.com/user-attachments/assets/fa3d0538-6c92-4429-ad5b-427ea9c7a1e5)
The python/Flask server controls the entire system. It recieves HTTP requests to the API endpoints either from the website (user input), or from ALab; these HTTP requests are intended to work for both cases and be the minimum set of instructions needed to control the system.

The Flask server then communicates over pyFirmata (based on serial) with the Arduino to control the gripper and linear rail, and directly communicates with the Ender3 over serial.  This server runs on the XRD computer and writes to a local directory to control the XRD.

## Wiring Diagram:
![image](https://github.com/user-attachments/assets/186741f4-cccc-475d-b893-e7a39c2f8920)

# CAD
A Solidworks CAD is supplied in the /cad.  A full BOM is left in /documentation.

# Stepper Motor Driver
A `STEPPERONLINE Stepper Motor Driver` controller was used to control the linear rail. It was set to 400 pulses/rotation, meaning that each time the Arduino pulses the motor driver, the motor rotates 1/400 of a rotation.  The pinout used is shown below:

![image](https://github.com/user-attachments/assets/d1e697b1-f1c8-4efd-ad24-dfa8ad17662b)

Errors
===
### Manual adjustment of Ender3
Sometimes, manual adjustment of the Ender3 needs to be done to put it in a position that is good for testing.  The gantry cannot be manipulated when the Ender is powered, so it must be de-powered.  Remember to unplug the Serial connection, then power down the Ender.  Follow the procedure in [Ender3 Connection](#Ender3-Connection).

### Ender3 Connection
When the Ender3 is not connected properly, the unit scale gets changed.  This usually results in the Ender moving about 1/2 the distance that is inputted.  To fix, restart the system, unplug the serial connection to the Ender, and power cycle the Ender.  Make sure to wait for the Ender to start up and be ready, then plug in the serial connection and try the connection.

### Connecting Serial
The system has trouble connecting at first.  Unplug the serial connections, then unpower/repower the extender cables, then reconnect the serial connections.  Basically have to power/unpower the first connector, then connect the next connector, unpower and power that, then can continue connecting.


Notes
===
#### [1] pyFirmata has issues in 3.11
[pyFirmata's Github](https://github.com/tino/pyFirmata/tree/master) says it runs on python 3.7.

When calling ```board = pyfirmata.Arduino('/dev/tty.usbmodem21101')```, an AttributeError is thrown: ```AttributeError: module 'inspect' has no attribute 'getargspec'. Did you mean: 'getargs'?```.
ChatGPT says:
> The error you're encountering is due to the use of the inspect.getargspec method in pyfirmata, which has been deprecated and removed in Python 3.11. Instead, inspect.getfullargspec should be used.
