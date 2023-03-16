# Simulator for running PID and BOAT code as a simulation.
import logging
import sys
from pid import PID
from config import Config as BoatConfig
from boat import Boat
from island_time import time # Make things simulate faster
from datetime import datetime

Course_Correction_Timeout = 60

def run_simulation(target_value, p_gain, i_gain, d_gain, boat, sampling_interval_ms, produce_csv = False, save_plot = False, show_plot = False):

    def render_plot():
        import matplotlib.pyplot as plt
        logging.getLogger('matplotlib.font_manager').disabled = True
        plt.plot(x, h, label="Heading")
        plt.plot(x, c, label="Course")
        plt.plot(x, e, label="Error")
        plt.plot(x, o, label="Commanded Rudder")
        plt.plot(x, r, label="Actual Rudder Angle")
        plt.plot([], [], ' ', label=f"pGain {pid.p_gain:6.4f}")
        plt.plot([], [], ' ', label=f"iGain {pid.i_gain:6.4f}")
        plt.plot([], [], ' ', label=f"dGain {pid.d_gain:6.4f}")
        plt.plot([], [], ' ', label=f"time  {runtime:6.4f}")
        # plt.plot(x, [float(i.replace('k', 'e3')) for i in y2], '-.')
        plt.xlabel("X-axis data")
        plt.ylabel("Y-axis data")
        # plt.title('multiple plots')
        # plt.legend(loc="upper right")
        plt.legend(bbox_to_anchor=(1.04, 1), loc="upper left")
        plt.subplots_adjust(right=0.6)
        if save_plot: 
            plt.savefig(pltfilename)
            logger.info(f"PNG of run in file {pltfilename}")
        if show_plot: plt.show()
    
    produce_plot = save_plot or show_plot
    current_time = datetime.now()
    if produce_csv: 
        import csv
        csvfilename = f"{current_time.strftime('pid_%Y%m%d-%H%M%S.csv')}"
        csvfile = open(csvfilename, 'w', newline='')
    if save_plot: 
        pltfilename = f"{current_time.strftime('pid_%Y%m%d-%H%M%S.png')}"
    iteration = 0
    initial_heading = boat.sensor.heading
    logger.info(f"Gains: P = {p_gain} I = {i_gain} D = {d_gain} Target = {target_value} Heading = {initial_heading}")
    start_time = time.time()
    if produce_csv: 
        csvwriter = csv.writer(csvfile, delimiter=',')
        csvwriter.writerow([f"{target_value:6.4f}",f"{initial_heading:6.4f}",f"{p_gain:10.8f}",f"{i_gain:10.8f}",f"{d_gain:10.8f}",f"{boat.max_rudder_deflection_deg:6.4f}",f"{boat.rudder_speed_dps:6.4f}",f"{boat.max_boat_turn_rate_dps:6.4f}"])
        csvwriter.writerow(["time","pv","err","correction","rudder","heading","course","p_gain","i_gain","d_gain","max_rudder_deflection","rudder_speed","max_boat_turn_rate"])
    if produce_plot:
        x = []
        c = []
        h = []
        e = []
        o = []
        r = []
    pid = PID(p_gain, i_gain, d_gain, sampling_interval_ms)
    pid.set_target_value(target_value) # Desired heading
    runtime = 0
    # Run as long as the error > tolerated error, and the rudder has not yet straightened out, and the procedure is not taking too long.
    while runtime <= Course_Correction_Timeout:
        pid_correction = -pid.compute_output(process_value=boat.sensor.get_heading()) # Output of comnpute_output is in same direction as error, so we must flip the sign to turn it into a correction.
        direction = "right" if pid_correction > 0 else "left"
        logger.debug(f"Turning {direction}; Requesting rudder angle {pid_correction} to correct from {boat.sensor.get_heading()} to {target_value}")
        boat.request_rudder_angle(pid_correction)
        timestamp = time.time() - start_time
        if produce_csv: 
            csvwriter.writerow([f"{timestamp:6.4f}",f"{boat.sensor.heading:6.4f}",f"{pid.err:6.4f}",f"{pid_correction:6.4f}",f"{boat.current_rudder_deflection_deg:6.4f}",f"{target_value:6.4f}",f"{initial_heading:6.4f}",f"{p_gain:6.4f}",f"{i_gain:6.4f}",f"{d_gain:6.4f}",f"{boat.max_rudder_deflection_deg:6.4f}",f"{boat.rudder_speed_dps:6.4f}",f"{boat.max_boat_turn_rate_dps:6.4f}"])
        if produce_plot:
            x.append(timestamp)
            c.append(pid.target_value)
            h.append(boat.sensor.heading)
            e.append(pid.err)
            o.append(pid_correction)
            r.append(boat.current_rudder_deflection_deg)
        boat.tick() 
        logger.debug(f"time={timestamp:6.4f}, target={pid.target_value:6.4f}, pv={boat.sensor.heading:6.4f}, err={pid.err:6.4f}, output={pid_correction:6.4f}, rudder={boat.current_rudder_deflection_deg:6.4f}")
        pid.wait()
        runtime = time.time()-start_time

    if runtime > 60: logger.warning(f"Runtime exceeded {Course_Correction_Timeout} seconds.") 
    logger.debug(f"Correction from {initial_heading:6.4f} to {target_value:6.4f} took {runtime:6.0f} seconds.")
    if produce_plot: 
        log_level = logger.level
        logger.setLevel(level=logging.INFO)
        render_plot()
        logger.setLevel(level=log_level)
    if produce_csv:
        logger.info(f"CSV of run in file {csvfilename}")
        csvfile.close()

if __name__ == "__main__":
    logging.basicConfig(filename="simulation.log",
                    filemode='a',
                    format='%(asctime)s %(levelname)-8s [%(filename)s] -  %(message)s',
                    datefmt='%Y-%m-%d %H:%M:%S',
                    level=logging.DEBUG)
    # logging.basicConfig(
        # format='%(asctime)s %(levelname)-8s [%(filename)s] -  %(message)s',
        # level = logging.DEBUG,
        # datefmt='%Y-%m-%d %H:%M:%S')
    logger = logging.getLogger(__name__)
    args = sys.argv[1:]
    target_value = 100.0
    initial_heading = 200.0
    boat_config = BoatConfig("config.yaml" if len(args) == 0 else args[0])
    logger.info(f"Using configuration {boat_config.filename}")
    boat = Boat(boat_config)
    boat.sensor.heading = initial_heading # For simulation only - normally, the sensor provides the heading 
    run_simulation(target_value, float(args[1]), float(args[2]), float(args[3]), boat, boat_config.get_sampling_interval_ms(), show_plot=True)
