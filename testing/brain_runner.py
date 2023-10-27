import time

from modules.brain import Brain
from modules.common.config import Config
from modules.common.file_logger import Logger

_log = Logger(config_path="brain", dest=None, who="brain")

def test_motor_direction(cfg):
    test_boat = BoatImpl(cfg)
    brain = Brain(cfg, test_boat)
    test_boat.engage_autopilot(1)
    brain._commanded_rudder = 0.5
    brain._boat.set_rudder(0.5)
    if brain.get_recommended_motor_direction() != 0:
        raise Exception("Recommended motor direction is not 0 (stbd)")
    brain._commanded_rudder = -0.5
    brain._boat.set_rudder(-0.5)
    if brain.get_recommended_motor_direction() != 0:
        raise Exception("Recommended motor direction is not 0 (port)")
    brain._commanded_rudder = 1.0
    brain._boat.set_rudder(0.5)
    if brain.get_recommended_motor_direction() != 1:
        raise Exception("Recommended motor direction is not starboard")
    brain._commanded_rudder = -1.0
    brain._boat.set_rudder(-0.5)
    if brain.get_recommended_motor_direction() != -1:
        raise Exception("Recommended motor direction is not port")
    brain._commanded_rudder = 1.0
    brain._boat.set_rudder(-0.5)
    if brain.get_recommended_motor_direction() != 1:
        raise Exception("Recommended motor direction is not starboard 2")
    brain._commanded_rudder = -1.0
    brain._boat.set_rudder(0.5)
    if brain.get_recommended_motor_direction() != -1:
        raise Exception("Recommended motor direction is not port 2")
    brain._boat.cl
    brain._commanded_rudder = 1
    brain._boat.set_rudder(0.5)
    if brain.get_recommended_motor_direction() != 0:
        raise Exception("Recommended motor direction is not 0 when clutch is off")
    _log.info("test_motor_direction passed")


if __name__ == "__main__":
    from modules.simulator.boat_simulator import BoatImpl
    cfg = Config("configuration/config.yaml")
    log = Logger(config_path="brain", dest=None, who="brain")
    if "log_level" in cfg.boat: _log.set_level(cfg.boat["log_level"])
    test_motor_direction(cfg)

    test_boat = BoatImpl(cfg)
    brain = Brain(cfg, test_boat)
    brain.set_commanded_rudder(0)
    course = 10
    brain.set_target_course(course)
    brain._boat_sampling_interval = 1000

    brain.start()

    try:
        controller = brain._controller
        gains_file_suffix = controller.get_gains_as_csv().replace(",", "_")
        with open(f"output/brain_simulator_output_crs{course:03d}_hdg{test_boat.heading():03d}_p{gains_file_suffix}.csv", 'a') as outfile:
            # outfile.write("elapsed_time, p_gain, i_gain, d_gain, course, heading, rudder, motor_direction, on/off course\n")
            _log.info("ctrl-C to stop")
            brain.engage_autopilot()
            interval = 0.1
            start_time = time.time()
            while True:
                brain.set_commanded_rudder(controller.compute_commanded_rudder(course, test_boat.heading()))
                motor_direction = brain.get_recommended_motor_direction()
                test_boat.update_rudder_and_heading(motor_direction)
                _log.info(f"Current course={course:5.1f} {test_boat} commanded_rudder={brain.commanded_rudder()} recommended_motor_direction={motor_direction} {'ON course' if brain.is_on_course() else 'OFF course'}")
                # outfile.write(f"{time.time() - start_time:5.1f}, {controller.get_gains_as_csv()}, {course:5.1f}, {test_boat.heading():5.1f}, {brain.commanded_rudder():4.2f}, {motor_direction}, {'ON course' if brain.is_on_course() else 'OFF course'}\n")
                time.sleep(interval)
                if motor_direction == 0 and brain.is_on_course():
                    break
            _log.info(f"Elapsed time {time.time()-start_time:0.1f}s")

    except KeyboardInterrupt:
        brain.disengage_autopilot()
        brain.stop()
        _log.info('Bye')
