## Adrian Vrouwenvelder
## December 1, 2022
## March 2023
import logging
import os
from time import sleep

from flask import Flask, jsonify, render_template, send_from_directory
from modules.brain import Brain
from modules.common.angle_math import normalize_angle
from modules.common.config import Config
from modules.imu_interface import Imu
from modules.rudder_interface import RudderInterface


try:
    app = Flask("Adrian's Autopilot",
                root_path='web/',
                template_folder='templates/',
                static_url_path="/static",
                static_folder='/Users/avrouwenve/Private/adrianAutoPilot/web/static/')
    print("Flask started me again!  App root path = " + str(app.root_path))
    course = None

    def setup(app):
        global cfg, rudder, imu, brain, logger, already_nagged

        Config.init()
        cfg = Config.getConfig()
        logger = logging.getLogger('web')
        print("Note: Web interface is on http://127.0.0.1:5000 (unless otherwise configured)")
        already_nagged = False

    @app.route("/")
    def index():
        global logger
        logger.debug("API index()")
        return render_template('mainNav.html')


    @app.route("/adjust_course/<course_adjustment>")
    def adjust_course(course_adjustment: str):
        global logger, course
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
                       motor=0,
                       rudder_position=rudder_pos,
                       control_output=1,
                       heel=0,
                       messages="Ok",
                       heading="100",
                       course=f"{course:03.0f}" if course is not None else "NAN",
                       turn_rate=10)


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
finally:
        sleep(5)
        logger.info('INFO: autoPilotWebApp exited.')