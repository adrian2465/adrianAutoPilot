## Adrian Vrouwenvelder
## December 1, 2022
## March 2023
from flask import Flask, jsonify, render_template
import logging
from modules.brain import getInstance as get_brain
from modules.status import DISABLED as STATUS_DISABLED, ENABLED as STATUS_ENABLED

app = Flask(__name__)

brain = get_brain()

log = logging.getLogger('werkzeug')
log.setLevel(logging.ERROR)

print("Note: Web interface is on http://127.0.0.1:5000 (unless otherwise configured)")

@app.route("/")
def index():
    global brain
    return render_template('mainNav.html')

@app.route("/set_status/<newStatus>")
def set_status(newStatus: str):
    global brain
    if newStatus == 'enable':
        brain.set_status(STATUS_ENABLED)
        brain.set_course(brain.get_heading())
    else:
        brain.set_status(STATUS_DISABLED)
    return ""

@app.route("/get_course")
def get_course():
    global brain
    return jsonify(course=f"{brain.get_course():03.0f}")

@app.route("/get_heading")
def get_heading():
    global brain
    return jsonify(heading=f"{brain.get_heading():03.0f}")


@app.route("/get_heel")
def get_heel():
    global brain
    heel = brain.get_heel()
    heel_str = "LEVEL"
    if heel >= 1.5:
        heel_str = f'{heel:03.0f} STBD'
    elif heel <= -1.5:
        heel_str = f'{-heel:03.0f} PORT'
    return jsonify(heel=heel_str)

@app.route("/adjust_course/<courseAdjustment>")
def adjust_course(courseAdjustment: str):
    global brain
    brain.adjust_course(int(courseAdjustment))
    return ""

@app.route("/get_messages")
def get_messages():
    global brain
    return jsonify(messages=brain.get_messages())

@app.route("/get_interface_params")
def get_interface_params():
    global brain
    interface = brain.get_arduino_interface()
    return jsonify(clutch_status=interface.get_status(),
                   starboard_limit=interface.get_stbd_limit(),
                   port_limit=interface.get_port_limit(),
                   motor_speed=interface.get_motor_speed(),
                   motor_direction=interface.get_motor_direction(),
                   rudder_position=interface.get_rudder_position(),
                   rudder_direction=interface.get_rudder_direction())

if __name__ == "__main__":
    app.run()
