## Adrian Vrouwenvelder
## December 1, 2022
## March 2023
from flask import Flask, jsonify, render_template
import logging
from modules.brain import Brain
from modules.common.config import Config
from modules.real.arduino_serial import get_interface as get_arduino_interface
from modules.real.boat import BoatImpl

app = Flask("Adrian's Autopilot")


# LEFT OFF HERE
# What will this really do?  Why does this code create an arduino interface, and the boat, too? Seems like if the boat does it,
# then we don't need to pass one to the brain, since the brain can get it from the boat.  And why does the real boat create an
# arduino interface instead of a arduino_serial?  That seems wrong.
def setup_app(app):
    global brain
    cfg = Config("configuration/config.yaml")
    arduino_interface = get_arduino_interface()
    brain = Brain(arduino_interface, cfg, BoatImpl())
    log = logging.getLogger('werkzeug')
    log.setLevel(logging.ERROR)
    brain.start()
    print("Note: Web interface is on http://127.0.0.1:5000 (unless otherwise configured)")

@app.route("/")
def index():
    global brain
    return render_template('mainNav.html')

@app.route("/adjust_course/<courseAdjustment>")
def adjust_course(courseAdjustment: str):
    global brain
    brain.adjust_course(int(courseAdjustment))
    return ""

@app.route("/set_status/<newStatus>")
def set_status(newStatus: str):
    global brain
    if newStatus == 'enabled':
        brain.engage_autopilot()
        brain.set_target_course(brain.heading())
    else:
        brain.disengage_autopilot()
    return ""

@app.route("/get_course")
def get_course():
    global brain
    return jsonify(course=f"{brain.target_course():03.0f}")

@app.route("/get_heading")
def get_heading():
    global brain
    return jsonify(heading=f"{brain.boat.heading():03.0f}")


@app.route("/get_heel")
def get_heel():
    global brain
    heel = brain.boat.heel()
    heel_str = "LEVEL"
    if heel >= 1.5:
        heel_str = f'{heel:03.0f} STBD'
    elif heel <= -1.5:
        heel_str = f'{-heel:03.0f} PORT'
    return jsonify(heel=heel_str)


@app.route("/get_interface_params")
def get_interface_params():
    global brain
    port_limit, stbd_limit = brain.arduino.rudder_limits()
    return jsonify(clutch_status=brain.is_clutch_engaged(),
                   starboard_limit=stbd_limit,
                   port_limit=port_limit,
                   motor_direction=brain.arduino.get_motor_direction(),
                   rudder_position=brain.arduino.rudder())

@app.route("/get_messages")
def get_messages():
    global brain
    return jsonify(messages=brain.arduio.get_message())


setup_app(app)

if __name__ == "__main__":
    try:
        app.run()
    except KeyboardInterrupt:
        brain.stop()
        print('INFO: autoPilotWebApp exited.')