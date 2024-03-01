## Adrian Vrouwenvelder
## December 1, 2022
## March 2023
import logging
from time import sleep

from flask import Flask, jsonify, render_template, request
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
        global rudder, imu, brain, logger
        cfg = Config.init()
        logger = logging.getLogger('web')
        rudder = RudderInterface()
        rudder.start_daemon()
        imu = Imu(bus=1)
        imu.start_daemon()
        brain = Brain(rudder, imu)
        brain.course = None
        brain.start_daemon()
        print("Note: Web interface is on http://127.0.0.1:5000 (unless otherwise configured)")


    ################################################################################################################
    ###### MAIN PAGE
    ################################################################################################################

    @app.route("/")
    def index():
        global logger
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
        # logger.debug(f"API get_interface_params(): "
        #              f"clutch_status={brain.is_engaged}, "
        #              f"rudder_port_limit={rudder.hw_port_limit}, "
        #              f"rudder_stbd_limit={rudder.hw_stbd_limit}, "
        #              f"rudder_pos={rudder.hw_raw_rudder_position}, "
        #              f"turn_rate={imu.turn_rate_dps:5.1f}")
        return jsonify(clutch_status=brain.is_engaged,
                       port_limit=rudder.hw_port_limit,
                       starboard_limit=rudder.hw_stbd_limit,
                       rudder_position=rudder.hw_raw_rudder_position,
                       motor=rudder.motor_speed,
                       control_output=brain.control_output,
                       turn_rate=f'{imu.turn_rate_dps:5.1f}',
                       heel=f'{imu.heel_deg:03.0f} STBD' if imu.heel_deg >= 1.5 else \
                           f'{-imu.heel_deg:03.0f} PORT' if imu.heel_deg <= -1.5 else \
                               "LEVEL",
                       messages="",
                       heading=f"{imu.compass_deg:03.0f}",
                       course=f"{brain.course:03.0f}" if brain.course is not None else "NAN")

    @app.route("/get_messages")
    def get_messages():
        global logger
        logger.debug(f"API get_messages => {rudder.hw_messages}")
        return jsonify(messages=rudder.hw_messages)


    ################################################################################################################
    ######## CONFIGURATION PAGE
    ################################################################################################################

    @app.route("/configure")
    def configure():
        global logger
        return render_template('configure.html')

    @app.route("/set_pid", methods=['POST'])
    def set_pid():
        global brain, logger
        json = request.json
        logger.debug(f"API set_pid(p={json.get('pid_p')}, i={json.get('pid_i')}, d={json.get('pid_d')})")
        brain.controller.set_pid_values(float(json.get('pid_p')),
                                        float(json.get('pid_i')),
                                        float(json.get('pid_d')))
        return ""

    @app.route("/get_pid", methods = ['GET'])
    def get_pid():
        global brain, logger
        p, i, d = brain.controller.get_pid_values()
        logger.debug(f"API get_pid(p={p}, i={i}, d={d})")
        return jsonify(pid_p=p, pid_i=i, pid_d=d)

    @app.route("/reset_biases", methods = ['GET'])
    def reset_biases():
        global brain, logger
        logger.debug(reset_biases)
        brain.imu.reset_biases()
        return ""

    @app.route("/get_biases", methods = ['GET'])
    def get_biases():
        global brain, logger
        g, a = brain.imu.gyro_biases, brain.imu.accel_biases
        logger.debug(f"API get_biases(gyro={g}, accel={a})")
        return jsonify(gyro_x=g[0], gyro_y=g[1], gyro_z=g[2], accel_x=a[0], accel_y=a[1], accel_z=a[2])

    @app.route("/set_port_limit", methods = ['GET'])
    def set_port_limit():
        global brain, logger
        logger.debug(f"API set_port_limit")
        brain.rudder.set_port_raw_rudder_limit(None)
        return ""

    @app.route("/set_stbd_limit", methods = ['GET'])
    def set_stbd_limit():
        global brain, logger
        logger.debug(f"API set_stbd_limit")
        brain.rudder.set_starboard_raw_rudder_limit(None)
        return ""


    setup(app)
    logging.getLogger('werkzeug').setLevel(logging.CRITICAL)

except:
    logger = logging.getLogger('adrianAutoPilot')
    logger.exception(f"Caught exception in autopilot.")

finally:
    logger = logging.getLogger('adrianAutoPilot')
    sleep(5)
    logger.info('INFO: autoPilotWebApp exited.')
