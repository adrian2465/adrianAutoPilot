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
    app = Flask("Adrian's Autopilot",
                root_path='web/',
                template_folder='templates/',
                static_url_path="/static",
                static_folder='/mnt/mmcblk0p2/apps/adrianAutoPilot/web/static/')
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

    @app.route("/toggle_status")
    def toggle_status():
        global brain, imu, logger
        is_enabling = (brain.course is None)
        logger.info(f"API toggle_status. ({'OFF -> ON' if is_enabling else 'ON -> OFF'})")
        if is_enabling:
            brain.course = imu.compass_deg
        else:
            brain.course = None
        return ""

    @app.route("/poll")
    def poll():
        global brain, imu, rudder, logger
        logger.debug(f"API get_interface_params(): "
                     f"clutch_status={brain.is_engaged}, "
                     f"plim={rudder.hw_port_limit}, "
                     f"slim={rudder.hw_stbd_limit}, "
                     f"raw={rudder.hw_raw_rudder_position}, "
                     f"turn_rate={imu.turn_rate_dps:5.1f}")
        return jsonify(clutch_status=brain.is_engaged,
                       port_limit=rudder.hw_port_limit,
                       starboard_limit=rudder.hw_stbd_limit,
                       motor=rudder.motor_speed,
                       rudder_position=-int(rudder.rudder_position*100),
                       raw_rudder_position=rudder.hw_raw_rudder_position,
                       control_output=brain.control_output,
                       turn_rate=imu.turn_rate_dps,
                       heel=f'{imu.heel_deg:03.0f} STBD' if imu.heel_deg >= 1.5 else \
                            f'{-imu.heel_deg:03.0f} PORT' if imu.heel_deg <= -1.5 else \
                            "LEVEL",
                       messages="",
                       heading=f"{imu.compass_deg:03.0f}",
                       course=f"{brain.course:03.0f}" if brain.course is not None else "NAN")

    @app.route("/get_messages")
    def get_messages():
        global brain, logger
        logger.debug(f"API get_messages => {rudder.hw_messages}")
        return jsonify(messages=rudder.hw_messages)

    setup(app)

finally:
        sleep(5)
        logger.info('INFO: autoPilotWebApp exited.')