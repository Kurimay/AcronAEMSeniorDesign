class state_json:
    """
    Snapshot of all UI-relevant simulation state at a single timestep.

    This class extracts values from the JSBSim FGFDMExec object, converts
    units where appropriate, and stores them as plain Python attributes.
    The state can then be serialized to JSON and consumed by the UI,
    telemetry systems, or logged for AI training and replay.
    """

    def __init__(self, fdm):
        self.fdm = fdm

        # --- Simulation time ---
        self.time_sec = self.fdm['simulation/sim-time-sec']     #Sim time (sec)
        #print(f"Time: {self.time_sec:6.2f} sec")             #USED FOR TESTING, DELETE WHEN DONE

        # --- Attitude ---
        self.roll_deg  = fdm['attitude/phi-deg']        #Roll angle (deg)
        self.pitch_deg = fdm['attitude/theta-deg']      #Pitch angle (deg)
        self.yaw_deg   = fdm['attitude/psi-deg']        #Yaw angle (deg)

        # --- Position ---
        self.lat_deg = fdm['position/lat-geod-deg'] + 44.725801    #Geodetic latitude (deg)
        self.lon_deg = fdm['position/long-gc-deg'] -93.075866     #Geocentric longitude (deg)
        self.alt_ft  = fdm['position/h-agl-ft']         #Height above ground level (ft)

        # --- Velocities ---
        self.tas_kt = self.fdm['velocities/vtrue-fps'] * 0.592484   #True airspeed (kts)
        self.u_fps  = self.fdm['velocities/u-fps']                  #Forward velocity (body frame) (ft/s)
        self.v_fps  = self.fdm['velocities/v-fps']                  #Horizontal velocity (body frame) (ft/s)
        self.w_fps  = self.fdm['velocities/w-fps']                  #Vertical velocity (body frame) (ft/s)
        self.v_down_fps = self.fdm['velocities/v-down-fps'] * -1    #Vertical velocity (earth frame) (ft/s)
        self.vsi_fps = -self.w_fps  #Makes horizontal speed positive upwards

        # --- Angular rates ---
        self.p_rad_s = self.fdm['velocities/p-rad_sec']     #Roll rate (rad/s)
        self.q_rad_s = self.fdm['velocities/q-rad_sec']     #Pitch rate (rad/s)
        self.r_rad_s = self.fdm['velocities/r-rad_sec']     #Yaw rate (rad/s)

        # --- Propulsion ---
                # --- Rotor RPMs ---
        self.rotor_rpm = [      #Individual rotor rpms 
            self.fdm[f'propulsion/engine[{i}]/propeller-rpm']
            for i in range(4)
        ]


        self.rotor_powers_kw = [      #Individual rotor powers (kW)
            self.fdm[f'propulsion/engine[{i}]/power-hp']*0.7457
            for i in range(4)
        ]
        self.total_power_kw = sum(self.rotor_powers_kw)     #Total power (kW)

        # --- Control states ---
        self.roll_cmd = self.fdm['fcs/refPhi_rad']              #Desired roll angle (rad)
        self.pitch_cmd = self.fdm['fcs/refTheta_rad']           #Desired pitch angle (rad)
        self.yaw_rate_cmd = self.fdm['fcs/rudder-cmd-norm']     #Commanded yaw rate
        self.heave_cmd = self.fdm['fcs/cmdHeave_nd']            #Commanded heave

        # --- Derived / synthetic values (placeholders) ---
        self.batt_temp_c = 25.0 + 0.02 * self.total_power_kw
        self.endurance_min = max(0.0, 112.0 - 0.03 * self.total_power_kw)
        self.range_nm = max(0.0, 102.0 - 0.015 * self.total_power_kw)

    def to_dict(self):
        """
        Return a JSON-serializable dictionary containing the full simulation state.
        """

        return {
            "time_sec": self.time_sec,

            "attitude": {
                "roll_deg": self.roll_deg,
                "pitch_deg": self.pitch_deg,
                "yaw_deg": self.yaw_deg,
            },

            "position": {
                "latitude_deg": self.lat_deg,
                "longitude_deg": self.lon_deg,
                "altitude_ft": self.alt_ft,
            },

            "velocities": {
                "tas_kt": self.tas_kt,
                "u_fps": self.u_fps,
                "v_fps": self.v_fps,
                "w_fps": self.w_fps,
                "vsi_fps": self.vsi_fps,
            },

            "rates": {
                "p_rad_s": self.p_rad_s,
                "q_rad_s": self.q_rad_s,
                "r_rad_s": self.r_rad_s,
            },

            "propulsion": {
                "rotor_powers_kw": self.rotor_powers_kw,
                "total_power_kw": self.total_power_kw,
            },

            "rpms": {
                "rotor_rpm": self.rotor_rpm,
            },

            "controls": {
                "roll_cmd": self.roll_cmd,
                "pitch_cmd": self.pitch_cmd,
                "yaw_rate_cmd": self.roll_cmd,
                "heave_cmd": self.heave_cmd
            },

            "energy": {
                "battery_temp_c": self.batt_temp_c,
                "endurance_min": self.endurance_min,
                "range_nm": self.range_nm,
            },
        }
    
    def to_ui_dict(self):
        return {
            # Attitude
            "roll_deg": self.roll_deg,
            "pitch_deg": self.pitch_deg,
            "hdg_deg": self.yaw_deg,

            # Position / motion
            "latitude_deg": self.lat_deg,      
            "longitude_deg": self.lon_deg,

            "alt_ft": self.alt_ft,
            "tas_kt": self.tas_kt,
            "vrate_fps": self.v_down_fps,

            # Propulsion
            "rotor_powers_kw": self.rotor_powers_kw,
            "total_power_kw": self.total_power_kw,
            "rotor_rpm": self.rotor_rpm,

            # Energy
            "batt_temp_c": self.batt_temp_c,
            "endurance_min": self.endurance_min,
            "range_nm": self.range_nm,

            # Controls (optional for UI)
            "rotor_angle_deg": self.roll_cmd * 180.0 / 3.14159,
    }
