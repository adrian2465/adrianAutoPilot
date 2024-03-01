## Adrian Vrouwenvelder
## December 1, 2022
## March 2023
import logging
from time import sleep

from flask import Flask, jsonify, render_template, request

from modules.common.angle_math import normalize_angle
from modules.common.config import Config


try:
    app = Flask("Adrian's Autopilot",
                root_path='web/',
                template_folder='templates/',
                static_url_path="/static",
                static_folder='/Users/avrouwenve/Private/adrianAutoPilot/web/static/')
    print("Flask started me.  App root path = " + str(app.root_path))
    course = None

    def setup(app):
        global rudder, imu, brain, already_nagged, logger, pid_p, pid_i, pid_d

        Config.init()
        logger = logging.getLogger('web')
        logger.setLevel("DEBUG")
        print("Note: Web interface is on http://127.0.0.1:5000 (unless otherwise configured)")
        already_nagged = False
        pid_p=1.1 # TODO get from brain
        pid_i=1.2
        pid_d=1.3

    @app.route("/")
    def index():
        global logger
        logger.debug("API index()")
        return render_template('mainNav.html')

    @app.route("/configure")
    def configure():
        global logger
        return render_template('configure.html')

    @app.route("/set_pid", methods=['POST'])
    def set_pid():
        global brain, logger, pid_p, pid_i, pid_d
        json = request.json
        pid_p = json.get('pid_p')
        pid_i = json.get('pid_i')
        pid_d = json.get('pid_d')
        # TODO set in brain
        print(f"API set_pid(p={pid_p}, i={pid_i}, d={pid_d})")
        return ""

    @app.route("/get_pid", methods = ['GET'])
    def get_pid():
        global brain, logger, pid_p, pid_i, pid_d
        print(f"API get_pid(p={pid_p}, i={pid_i}, d={pid_d})")
        # TODO get from brain
        return jsonify(pid_p=pid_p, pid_i=pid_i, pid_d=pid_d)

    @app.route("/reset_biases", methods = ['GET'])
    def reset_biases():
        global brain, logger
        print(f"API reset_biases")
        # TODO set in brain
        return ""

    @app.route("/get_biases", methods = ['GET'])
    def get_biases():
        global brain, logger
        print(f"API get_biases(0.1, 0.2, 0.3, 0.4, 0.5, 0.6")
        # TODO get from brain
        return jsonify(gyro_x=0.1, gyro_y=0.2, gyro_z=0.3, accel_x=0.4, accel_y=0.5, accel_z=0.5)

    @app.route("/set_port_limit", methods = ['GET'])
    def set_port_limit():
        global brain, logger
        print(f"API set_port_limit")
        # TODO set in brain
        return ""

    @app.route("/set_stbd_limit", methods = ['GET'])
    def set_stbd_limit():
        global brain, logger
        print(f"API set_stbd_limit")
        # TODO set in brain
        return ""

    @app.route("/adjust_course/<course_adjustment>")
    def adjust_course(course_adjustment: str):
        global course, logger
        logger.info(f"API adjust_course({course_adjustment})")
        course = normalize_angle(course + (int(course_adjustment))) if course is not None else None
        return ""


    @app.route("/toggle_status")
    def toggle_status():
        global course, logger
        is_enabling = (course is None)
        logger.info(f"API toggle_status. ({'OFF -> ON' if is_enabling else 'ON -> OFF'})")
        if is_enabling:
            course = 100
        else:
            course = None
        return ""

    @app.route("/poll")
    def poll():
        global already_nagged
        try:
            with open("/tmp/rudder_position.txt", "r") as f:
                rudder_pos = float(f.readline())
        except:
            rudder_pos = 10
            if not already_nagged:
                print("Set rudder position here: /tmp/rudder_position.txt")
                already_nagged = True
        return jsonify(clutch_status=course is not None,
                       port_limit=100,
                       starboard_limit=934,
                       rudder_position=500,
                       motor=0,
                       control_output=1,
                       turn_rate=3,
                       heel=0,
                       messages="Ok",
                       heading="100",
                       course=f"{course:03.0f}" if course is not None else "NAN")

    @app.route("/get_messages")
    def get_messages():
        global brain, logger
        # logger.debug(f"API get_messages => HEAD-ONLY MODE")
        return jsonify(messages="HEAD-ONLY MODE")

    setup(app)
    logging.getLogger('werkzeug').setLevel(logging.CRITICAL)
    if __name__ == "__main__":
        try:
            app.run()
        except KeyboardInterrupt:
            brain.stop()
            print('INFO: autoPilotWebApp exited.')

except:
    logger.exception(f"Caught exception in autopilot.")

finally:
        sleep(5)
        logger.info('INFO: autoPilotWebApp exited.')
        print("'INFO: autoPilotWebApp exited.'")