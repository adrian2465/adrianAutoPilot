## Adrian Vrouwenvelder
## December 1, 2022
## March 2023
from flask import Flask, jsonify, render_template
from modules.brain import Brain
from modules.common.config import Config
from modules.boat import BoatImpl

app = Flask("Adrian's Autopilot")

brain = None
is_debug = True


def setup(app):
    global brain
    if is_debug: print("brain.setup()")
    cfg = Config("../configuration/config.yaml")
    boat = BoatImpl(cfg)
    brain = Brain(cfg, boat)
    brain.set_commanded_rudder(0)
    brain.set_target_course(boat.heading())
    brain._boat_sampling_interval = 1000
    brain.start_daemon()
    print("Note: Web interface is on http://127.0.0.1:5000 (unless otherwise configured)")


@app.route("/")
def index():
    global brain
    if is_debug: print("brain.index()")
    return render_template('mainNav.html')


@app.route("/adjust_course/<course_adjustment>")
def adjust_course(course_adjustment: str):
    global brain
    if is_debug: print(f"brain.adjust_course({course_adjustment})")
    brain.adjust_course(int(course_adjustment))
    return ""


@app.route("/set_status/<new_status>")
def set_status(new_status: str):
    global brain
    if is_debug: print(f"brain.set_status({new_status})")
    if new_status == 'enabled':
        brain.engage_autopilot()
        brain.set_target_course(brain.boat.heading())
    else:
        brain.disengage_autopilot()
    return ""


@app.route("/get_course")
def get_course():
    global brain
    course = brain.target_course()
    if is_debug: print(f"brain.get_course() => {course}")
    return jsonify(course=f"{course:03.0f}")


@app.route("/get_heading")
def get_heading():
    global brain
    heading = brain.boat.heading()
    if is_debug: print(f"get_heading() => {heading}")
    return jsonify(heading=f"{heading:03.0f}")


@app.route("/get_heel")
def get_heel():
    global brain
    heel = brain.boat.heel()
    heel_str = "LEVEL"
    if is_debug: print(f"get_heel() => {heel}")
    if heel >= 1.5:
        heel_str = f'{heel:03.0f} STBD'
    elif heel <= -1.5:
        heel_str = f'{-heel:03.0f} PORT'
    return jsonify(heel=heel_str)


@app.route("/get_interface_params")
def get_interface_params():
    global brain
    port_limit, stbd_limit = brain.arduino.rudder_limits()
    if is_debug: print(f"get_interface_params() => p={port_limit}, s={stbd_limit}, rudder={brain.arduino.get_rudder_position()}")
    return jsonify(clutch_status=brain.is_clutch_engaged(),
                   starboard_limit=stbd_limit,
                   port_limit=port_limit,
                   motor=brain.boat.get_motor_speed(),
                   rudder_position=brain.boat.get_rudder_position())

@app.route("/get_messages")
def get_messages():
    global brain
    messages = brain.arduino.get_message()
    if is_debug: print(f"get_messages => {messages}")
    return jsonify(messages=messages)


setup(app)

if __name__ == "__main__":
    try:
        app.run()
    except KeyboardInterrupt:
        brain.stop()
        print('INFO: autoPilotWebApp exited.')