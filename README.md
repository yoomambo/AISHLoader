# To Do:
- [ ] Make statechart diagram of system - list all states. This documents the flow/architecture of the system
- [ ] Document Installation
- [ ] Sync CAD
- [ ] Document UI

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

# Control Interface Guide
`pass`

# System Control Flow
`pass`

# Schematic
Wiring Diagram:
![image](https://github.com/user-attachments/assets/186741f4-cccc-475d-b893-e7a39c2f8920)



# CAD
A Solidworks CAD is supplied...

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
