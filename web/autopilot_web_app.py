## Adrian Vrouwenvelder
## December 1, 2022
## March 2023
import logging
from time import sleep

from flask import Flask, jsonify, render_template
from modules.brain import Brain
from modules.common.angle_math import normalize_angle
from modules.common.config import Config
from modules.imu_interface import Imu
from modules.rudder_interface import RudderInterface


try:
    app = Flask("Adrian's Autopilot", root_path='web/',
                template_folder='templates/',
                static_folder='static/')
    print(str(app.root_path))

    def setup(app):
        global cfg, rudder, imu, brain, logger

        Config.init()
        cfg = Config.getConfig()
        logger = logging.getLogger('web')
        rudder = RudderInterface()
        rudder.start_daemon()
        imu = Imu(bus=1)
        imu.start_daemon()
        brain = Brain(rudder, imu)
        brain.course = None
        brain.start_daemon()
        print("Note: Web interface is on http://127.0.0.1:5000 (unless otherwise configured)")

    @app.route("/")
    def index():
        global brain, logger
        logger.debug("API index()")
        return render_template('mainNav.html')


    @app.route("/adjust_course/<course_adjustment>")
    def adjust_course(course_adjustment: str):
        global brain, logger
        logger.info(f"API adjust_course({course_adjustment})")
        brain.course = normalize_angle(brain.course + (int(course_adjustment))) if brain.course is not None else None
        return ""


    @app.route("/set_status/<new_status>")
    def set_status(new_status: str):
        global brain, imu, logger
        logger.info(f"API set_status({new_status})")
        is_enabling = (new_status == 'enabled')
        if brain.course is None:
            if is_enabling:
                # Enabling a disabled brain.
                brain.course = imu.compass_deg
            else:
                # Disabling a disable brain.
                logger.error("API Ignoring disabling an already-disabled brain.")
        else:
            if is_enabling:
                # Enabling an enabled brain
                logger.error("API Ignoring enabling an already-enabled brain.")
            else:
                # Disabling an enabled brain
                brain.course = None
        return ""


    @app.route("/get_course")
    def get_course():
        global brain, logger
        course = brain.course
        course_str = f"{course:03.0f}" if course is not None else f"{imu.compass_deg:03.0f}"
        logger.debug(f"API get_course() => {course_str}")
        return jsonify(course=course_str)


    @app.route("/get_heading")
    def get_heading():
        global imu, logger
        heading_str = f"{imu.compass_deg:03.0f}"
        logger.debug(f"API get_heading() => {heading_str}")
        return jsonify(heading=heading_str)


    @app.route("/get_heel")
    def get_heel():
        global imu, logger
        heel = f'{imu.heel_deg:03.0f} STBD' if imu.heel_deg >= 1.5 else \
               f'{-imu.heel_deg:03.0f} PORT' if imu.heel_deg <= -1.5 else \
               "LEVEL"
        logger.debug(f"API get_heel() => {heel}")
        return jsonify(heel=heel)


    @app.route("/get_interface_params")
    def get_interface_params():
        global brain, imu, rudder, logger
        logger.debug(f"API get_interface_params() => "
                     f"clutch_status={brain.is_engaged}"
                     f"plim={rudder.hw_port_limit}, "
                     f"slim={rudder.hw_stbd_limit}, "
                     f"rudder={rudder.rudder_position:6.4f}, "
                     f"turn_rate={imu.turn_rate_dps:5.1f}")
        return jsonify(clutch_status=brain.is_engaged,
                       port_limit=rudder.hw_port_limit,
                       starboard_limit=rudder.hw_stbd_limit,
                       motor=rudder.motor_speed,
                       rudder_position=rudder.rudder_position,
                       turn_rate=imu.turn_rate_dps)


    @app.route("/get_messages")
    def get_messages():
        global brain, logger
        logger.debug(f"API get_messages => {rudder.hw_messages}")
        return jsonify(messages=rudder.hw_messages)

    setup(app)

finally:
        sleep(5)
        logger.info('INFO: autoPilotWebApp exited.')