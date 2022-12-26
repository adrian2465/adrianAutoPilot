# Simulator for running PID and BOAT code as a simulation.
import logging
import sys
from pid import PID
from config import Config as BoatConfig
from boat import Boat
from island_time import time # Make things simulate faster

if __name__ == "__main__":
    produce_csv = True
    produce_plt = True
    show_plt = False

    logging.basicConfig(
        format='%(asctime)s %(levelname)-8s [%(filename)s] -  %(message)s',
        level = logging.INFO,
        datefmt='%Y-%m-%d %H:%M:%S')
    logger = logging.getLogger(__name__)
    # logger.setLevel(level=logging.DEBUG)

    from datetime import datetime
    args = sys.argv[1:]
    current_time = datetime.now()
    boat_config = BoatConfig("config.yaml" if len(args) == 0 else args[0])
    if produce_csv: 
        import csv
        csvfilename = f"{current_time.strftime('pid_%Y%m%d-%H%M%S.csv')}"
        csvfile = open(csvfilename, 'w', newline='')
    if produce_plt: 
        import matplotlib.pyplot as plt
        pltfilename = f"{current_time.strftime('pid_%Y%m%d-%H%M%S.png')}"
    iteration = 0
    logger.debug(f"Using configuration {boat_config.filename}")
    logger.debug(f"Gains: P = {boat_config.get_P_gain()} I = {boat_config.get_I_gain()} D = {boat_config.get_D_gain()}")
    boat = Boat(boat_config)
    target_value = 100.0
    initial_heading = 200.0
    logger.debug(f"target = {target_value} heading = {initial_heading}")
    pid = PID(boat_config.get_P_gain(), boat_config.get_I_gain(), boat_config.get_D_gain(), boat_config.get_sampling_interval_ms())
    start_time = time.time()
    if produce_csv: 
        csvwriter = csv.writer(csvfile, delimiter=',')
        csvwriter.writerow([f"{target_value:6.2f}",f"{initial_heading:6.2f}",f"{boat_config.get_P_gain():6.4f}",f"{boat_config.get_I_gain():6.4f}",f"{boat_config.get_D_gain():6.4f}",f"{boat.max_rudder_deflection_deg:6.2f}",f"{boat.rudder_speed_dps:6.2f}",f"{boat.max_boat_turn_rate_dps:6.2f}"])
        csvwriter.writerow(["time","pv","err","output","rudder","heading","course","p_gain","i_gain","d_gain","max_rudder_deflection","rudder_speed","max_boat_turn_rate"])
        pid.set_target_value(target_value) # Desired heading
    boat.sensor.heading = initial_heading # For testing - normally, the sensor provides the heading asynchronously
    logger.debug(f"info,timestamp, target_value, heading, err, pid_output, rudder_angle")
    if produce_plt:
        x = []
        c = []
        h = []
        e = []
        o = []
        r = []
    while abs(pid.err) > 1:
        boat.request_rudder_angle(pid.compute_output(process_value=boat.sensor.get_heading()))
        timestamp = time.time() - start_time
        if produce_csv: 
            csvwriter.writerow([f"{timestamp:6.2f}",f"{boat.sensor.heading:6.2f}",f"{pid.err:6.2f}",f"{pid.output:6.4f}",f"{boat.current_rudder_deflection_deg:6.2f}",f"{target_value:6.2f}",f"{initial_heading:6.2f}",f"{boat_config.get_P_gain():6.4f}",f"{boat_config.get_I_gain():6.4f}",f"{boat_config.get_D_gain():6.4f}",f"{boat.max_rudder_deflection_deg:6.2f}",f"{boat.rudder_speed_dps:6.2f}",f"{boat.max_boat_turn_rate_dps:6.2f}"])
        if produce_plt:
            x.append(timestamp)
            c.append(pid.target_value)
            h.append(boat.sensor.heading)
            e.append(pid.err)
            o.append(pid.output)
            r.append(boat.current_rudder_deflection_deg)
        boat.tick() 
        logger.debug(f"time={timestamp:6.2f}, target={pid.target_value:6.2f}, pv={boat.sensor.heading:6.2f}, err={pid.err:6.2f}, output={pid.output:6.4f}, rudder={boat.current_rudder_deflection_deg:6.2f}")
        pid.wait()

    runtime = time.time()-start_time
    logger.debug(f"Correction from {initial_heading:6.2f} to {target_value:6.2f} took {runtime:6.0f} seconds.")
    logger.setLevel(level=logging.INFO)
    if produce_plt:
        logging.getLogger('matplotlib.font_manager').disabled = True
        plt.plot(x, h, label="Heading")
        plt.plot(x, c, label="Course")
        plt.plot(x, e, label="Error")
        plt.plot(x, o, label="Commanded Rudder")
        plt.plot(x, r, label="Actual Rudder Angle")
        plt.plot([], [], ' ', label=f"pGain {pid.p_gain:6.2f}")
        plt.plot([], [], ' ', label=f"iGain {pid.i_gain:6.2f}")
        plt.plot([], [], ' ', label=f"dGain {pid.d_gain:6.2f}")
        plt.plot([], [], ' ', label=f"time  {runtime:6.2f}")
        # plt.plot(x, [float(i.replace('k', 'e3')) for i in y2], '-.')
        plt.xlabel("X-axis data")
        plt.ylabel("Y-axis data")
        # plt.title('multiple plots')
        # plt.legend(loc="upper right")
        plt.legend(bbox_to_anchor=(1.04, 1), loc="upper left")
        plt.subplots_adjust(right=0.6)
        plt.savefig(pltfilename)
        logger.info(f"PNG of run in file {pltfilename}")
        if show_plt: plt.show()
    if produce_csv: 
        logger.info(f"CSV of run in file {csvfilename}")
        csvfile.close()
