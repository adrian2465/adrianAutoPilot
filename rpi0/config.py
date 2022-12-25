import yaml
import io

class Config:

    def __init__(self, filename):
        self.filename = filename
        self.gains = None
        self.boat_characteristics = None

    def load_if_necessary(self):
        if self.gains == None:
            with open(self.filename, 'r') as stream:
                data = yaml.safe_load(stream)
                self.boat_characteristics = data["boat_characteristics"]
                self.gains = data["gains"]

    def get_max_rudder_deflection_deg(self):
        self.load_if_necessary()
        return float(self.boat_characteristics["max_rudder_deflection"])

    def get_sampling_interval_ms(self):
        self.load_if_necessary()
        return float(self.boat_characteristics["sampling_interval"])
   
    def get_rudder_speed_dps(self):
        self.load_if_necessary()
        return float(self.boat_characteristics["rudder_speed"])
   
    def get_boat_turn_rate_dps(self):
        self.load_if_necessary()
        return float(self.boat_characteristics["boat_turn_rate"])

    def get_gain(self, gain, sea_state = "default"):
        self.load_if_necessary()
        if gain not in ['P','I','D']: 
            raise ValueError(f"Invalid gain requested ({gain})")
        if sea_state not in self.gains:
            print(f"WARNING Sea state '{sea_state}' was not found in {self.filename}. Using default.") 
            sea_state = "default"
        rc = float(self.gains[sea_state][gain])
        return rc

    def get_P_gain(self, sea_state = "default"): return self.get_gain("P", sea_state)
    def get_I_gain(self, sea_state = "default"): return self.get_gain("I", sea_state)
    def get_D_gain(self, sea_state = "default"): return self.get_gain("D", sea_state)
