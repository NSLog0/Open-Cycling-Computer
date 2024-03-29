#!/usr/bin/python
# -*- coding: utf-8 -*-
## @package ride_parameters
#  Module for handling all ride parameters. This is the main module responsible for pulling all data together and preparing values for displaying, logging and saving.
from time import strftime
from units import units
import logging
import math
import time

## @var INF_MIN
# helper variable, minus infinity
INF_MIN = float("-inf")

## @var INF
# helper variable, infinity
INF = float("inf")

## @var BLE_RECONNECT_DELAY
# Disconnect time in seconds. After this time the sensor is considered to be disconnected.
BLE_RECONNECT_DELAY = 10


## Class for handling all ride parameters
class ride_parameters():

    ## The constructor
    #  @param self The python object self
    #  @param occ OCC instance
    #  @param simulate Decides if ride_parameters runs in simulation mode or real device mode.
    def __init__(self, occ, simulate=False):
        ## @var occ
        # OCC Handle
        self.occ = occ
        ## @var l
        # System logger handle
        self.l = logging.getLogger('system')
        ## @var r
        # Ride logger handle
        self.r = self.setup_ridelog()
        ## @var uc
        # Units converter
        self.uc = units()
        self.l.info("[RP] Initialising sensors")
        ## @var sensors
        # Handle of sensors instance
        self.sensors = occ.sensors
        ## @var ble_sc
        # Handle of BLE speed and cadence sensor
        self.ble_sc = self.sensors.get_sensor('ble_sc')
        ## @var ble_hr
        # Handle of BLE heart rate sensor
        self.ble_hr = self.sensors.get_sensor('ble_hr')
        ## @var gps
        # Handle of GPS sensor
        self.gps = self.sensors.get_sensor('gps')
        ## @var bmp183
        # Handle of bmp183 sensor
        self.bmp183 = self.sensors.get_sensor('bmp183')

        self.suffixes = ("_digits", "_tenths", "_hms")

        self.p_raw = dict(time_stamp=time.time(),
                          # Time delta since last p_raw update
                          dtime=1, time_adjustment_delta=0.0,
                          altitude=0.0, altitude_gps=0.0, altitude_home=0.0, altitude_max=INF_MIN, altitude_min=INF, altitude_previous=0.0,
                          pressure=0.0, pressure_at_sea_level=0.0,
                          climb=0.0, daltitude=0.0, daltitude_cumulative=0.0,
                          odometer=0.0, ddistance=0.0, ddistance_cumulative=0.0, distance=0.0,
                          eps=0.0, ept=0.0, epv=0.0, epx=0.0, gps_strength=0, fix_mode_gps='', fix_time_gps=0.0, latitude=0.0, longitude=0.0, satellites=0.0, satellitesused=0.0,
                          ble_state=0,
                          ble_hr_ts=0,
                          heart_rate=0.0, heart_rate_min=INF, heart_rate_avg=0.0, heart_rate_max=INF_MIN,
                          cadence=0.0, cadence_avg=0.0, cadence_max=INF_MIN,
                          cadence_time_stamp=time.time(), ble_data_expiry_time=1.5, time_of_ride_reset=0.0001,
                          ble_hr_name='', ble_hr_addr='',
                          ble_sc_name='', ble_sc_addr='',
                          rider_weight=0.0,
                          ridetime=0.0, ridetime_total=0.0,
                          slope=0.0,
                          speed=0.0, speed_avg=0.0, speed_gps=0.0, speed_max=0.0,
                          speed_gps_low=2.5, speed_gps_noise=1.0, speed_low=1.0,
                          temperature=0.0, temperature_avg=0.0, temperature_max=INF_MIN, temperature_min=INF,
                          track_gps=0,
                          timeon=0.0001, utc='', rtc='')

        # Internal units
        self.p_raw_units = dict(
            altitude='m', cadence='RPM', climb='m/s', distance='m', eps='', ept='', epv='', epx='',
            dtime='s', fix_gps='', latitude='', longitude='', odometer='m', pressure='Pa', rider_weight='kg', wheel_size='',
            ridetime='s', ridetime_total='s', satellites='', satellitesused='', slope='m/m', speed='m/s',
            temperature='C', timeon='s', time_of_ride_reset='s', heart_rate='BPM', track_gps='')

        # Params of the ride ready for rendering.
        self.params = dict(
            altitude='-', altitude_gps='-', altitude_home='-', altitude_max='-', altitude_min='-',
            cadence='-', cadence_avg='-', cadence_max='-', heart_rate='-', heart_rate_min='-', heart_rate_avg='-', heart_rate_max='-',
            climb='-', distance=0, eps='-', ept='-', epv='-', epx='-',
            dtime=0, fix_gps='-', fix_gps_time='-', latitude='-', longitude='-', odometer=0.0,
            pressure='-', pressure_at_sea_level='-', rider_weight=0.0, wheel_size='', wheel_circ='', ridetime='', ridetime_hms='', ridetime_total='',
            ridetime_total_hms='', rtc='', satellites='-', satellitesused='-', slope='-', speed='-', speed_avg='-',
            speed_avg_digits='-', speed_avg_tenths='-', speed_digits='-', speed_max='-', speed_max_digits='-',
            speed_max_tenths='-', speed_tenths='-', temperature='', temperature_avg='', temperature_max='',
            temperature_min='', timeon='', timeon_hms='', time_of_ride_reset='', track_gps='-', utc='',
            ble_hr_name='', ble_hr_addr='', ble_sc_name='', ble_sc_addr='',
            # Editor params
            editor_index=0, variable=None,
            variable_description=None, variable_raw_value=None, variable_unit=None, variable_value=None,
            # System params
            debug_level='')

        # Formatting strings for params.
        self.p_format = dict(
            altitude='%.0f', altitude_gps='%.0f', altitude_home='%.0f', altitude_max='%.0f', altitude_min='%.0f',
            cadence='%.0f', cadence_avg='%.0f', cadence_max='%.0f', climb='%.1f', distance='%.1f', eps='%.4f', epx='%.4f', epv='%.4f', ept='%.4f',
            dtime='%.2f', fix_gps='', fix_gps_time='',
            heart_rate='%.0f', heart_rate_min='%.0f', heart_rate_avg='%.0f', heart_rate_max='%.0f',
            latitude='%.4f', longitude='%.4f', odometer='%.0f',
            pressure='%.0f', pressure_at_sea_level='%.0f', rider_weight='%.1f', ridetime='%.0f', ridetime_hms='', ridetime_total='.0f',
            ridetime_total_hms='', rtc='', satellites='%.0f', satellitesused='%.0f', slope='%.0f', speed='%.1f', speed_avg='%.1f',
            speed_avg_digits='%.0f', speed_avg_tenths='%.0f', speed_digits='%.0f', speed_max='%.1f', speed_max_digits='%.0f', speed_max_tenths='%.0f',
            speed_tenths='%.0f', temperature='%.0f', temperature_avg='%.1f', temperature_max='%.0f', temperature_min='%.0f',
            timeon='%.0f', timeon_hms='', time_of_ride_reset='%.0f', track_gps='%.1f', utc='')

        # Units - name has to be identical as in params
        self.units = dict(
            altitude='m', cadence='RPM', climb='m/s', distance='km', eps='', epx='', epv='', ept='',
            dtime='s', fix_gps='', fix_gps_time='', heart_rate='BPM', latitude='', longitude='', odometer='km', pressure='hPa',
            rider_weight='kg', wheel_size='', ridetime='s', ridetime_hms='', ridetime_total='s', ridetime_total_hms='', satellites='',
            satellitesused='', slope='%', speed='km/h', temperature='C', timeon='s', timeon_hms='', time_of_ride_reset='s',
            track_gps='')

        # Allowed units - user can switch between those when editing value
        # FIXME switch to mi when mi/h are set for speed
        # FIXME switch to mi/h when mi are set for odometer
        self.units_allowed = dict(
            odometer=['km', 'mi'], rider_weight=['kg', 'st', 'lb'],
            # slope=['%', 'C'],
            wheel_size=[''],
            speed=['km/h', 'm/s', 'mi/h'], temperature=['C', 'F', 'K'])

        # Params description FIXME localisation
        self.p_desc = dict(
            altitude_home='Home altitude', odometer='Odometer', odometer_units='Odometer units',
            rider_weight='Rider weight', rider_weight_units='Rider weight units', wheel_size='Wheel size', speed_units='Speed units',
            temperature_units='Temp. unit')

        # Params that can be changed in Settings by user
        self.editors = dict(editor_units=('odometer_units', 'rider_weight_units', 'speed_units', 'temperature_units'),
                            editor_numbers=('altitude_home', 'odometer', 'rider_weight'),
                            editor_string=('wheel_size',),
                            ble_selector=('ble_hr_name', 'ble_sc_name'))

        self.p_resettable = dict(distance=1, odometer=1, ridetime=1, speed_max=1,
                                 cadence=1, cadence_avg=1, cadence_max=1,
                                 heart_rate_min=1, heart_rate_avg=1, heart_rate_max=1)

        # FIXME Use set_nav_speed_threshold(self, treshold=0) from gps module
        self.l.info("[RP] GPS low speed treshold preset to {} [NOT USED]".format(self.p_raw['speed_gps_low']))
        self.l.info("[RP] GPS speed noise level treshold preset to {}".format(self.p_raw['speed_gps_noise']))
        self.l.info("[RP] Speed below {} m/a treshold won't be recorded".format(self.p_raw['speed_low']))

        self.update_param("speed_max")
        self.split_speed("speed_max")
        self.update_param("altitude_home")
        self.l.info("[RP] altitude_home set to {}".format(self.params["altitude_home"]))

    def start_sensors(self):
        self.l.debug("[RP] Starting sensors thread")
        self.sensors.start()

    def setup_ridelog(self):
        ride_log_filename = "log/ride." + \
            strftime("%Y-%m-%d-%H:%M:%S") + ".log"
        logging.getLogger('ride').setLevel(logging.INFO)
        ride_log_handler = logging.handlers.RotatingFileHandler(
            ride_log_filename)
        ride_log_format = '%(time)-8s,%(dtime)-8s,%(speed)-8s,%(cadence)-8s,%(pressure)-8s,%(temperature)-8s,%(altitude)-8s,%(altitude_gps)-8s,%(distance)-8s,%(slope)-8s,%(climb)-8s,%(track_gps)-8s,%(eps)-8s,%(epx)-8s,%(epv)-8s,%(ept)-8s'
        ride_log_handler.setFormatter(logging.Formatter(ride_log_format))
        logging.getLogger('ride').addHandler(ride_log_handler)
        ride_logger = logging.getLogger('ride')
        ride_logger.info('', extra={'time': "Time", 'dtime': "Delta", 'speed': "Speed",
                                    'cadence': "Cadence", 'heart_rate': "Heart RT",
                                    'pressure': "Pressure", 'temperature': "Temp",
                                    'altitude': "Altitude", 'altitude_gps': "Alt GPS",
                                    'distance': "Distance", 'slope': "Slope", 'climb': "Climb",
                                    'track_gps': "Track", 'eps': "eps", 'epx': "epx", 'epv': "epv",
                                    'ept': "ept"})
        return ride_logger

    def stop(self):
        self.l.debug("[RP] Stopping sensors thread")
        self.sensors.stop()

    def __del__(self):
        self.stop()

    def update_values(self):
        self.read_bmp183_data()
        t = time.time()
        self.p_raw["dtime"] = t - self.p_raw["time_stamp"]
        self.p_raw["time_stamp"] = t
        self.read_gps_data()
        # FIXME Move this to gps module?
        dt_adjustment = self.p_raw['time_adjustment_delta']
        if dt_adjustment > 0:
            self.p_raw["dtime"] = self.p_raw["dtime"] - dt_adjustment
            self.l.info("[RP] dtime adjusted by {}".format(dt_adjustment))
            self.sensors['gps'].time_adjustment_delta = 0
            # FIXME Correct other parameters like ridetime
        self.l.debug("[RP] timestamp: {} dtime {}".format(t, self.p_raw["dtime"]))
        self.read_ble_data()
        self.read_bmp183_data()
        self.calculate_altitude()
        self.calculate_time_related_parameters()
        self.p_raw["daltitude_cumulative"] += self.p_raw["daltitude"]
        self.p_raw["ddistance_cumulative"] += self.p_raw["ddistance"]
        if self.p_raw["ddistance_cumulative"] == 0:
            self.p_raw["slope"] = 0
        # FIXME make proper param for tunning. Calculate slope if the distance
        # delta was grater than 8,4m
        elif self.p_raw["ddistance_cumulative"] > 8.4:
            self.p_raw["slope"] = self.p_raw["daltitude_cumulative"] / self.p_raw["ddistance_cumulative"]
            self.l.debug("[RP] daltitude_cumulative: {} ddistance_cumulative: {}".
                         format(self.p_raw["daltitude_cumulative"], self.p_raw["ddistance_cumulative"]))
            self.p_raw["daltitude_cumulative"] = 0
            self.p_raw["ddistance_cumulative"] = 0
        self.l.debug("[RP] slope: {}".format(self.p_raw["slope"]))
        self.update_params()

    def calculate_time_related_parameters(self):
        dt = self.p_raw["dtime"]
        self.p_raw["timeon"] += dt
        s = self.p_raw["speed"]
        if (s > self.p_raw['speed_low']):
            d = float(dt * s)
            self.p_raw["ddistance"] = d
            self.p_raw["distance"] += d
            self.p_raw["odometer"] += d
            self.p_raw["ridetime"] += dt
            self.p_raw["ridetime_total"] += dt
            self.p_raw["speed_avg"] = self.p_raw["distance"] / self.p_raw["ridetime"]
            self.update_param("speed_avg")
            self.split_speed("speed_avg")
            self.l.debug("[RP] speed_gps: {}, distance: {}, odometer: {}".format(
                s, self.p_raw["distance"], self.p_raw["odometer"]))
        else:
            self.p_raw["ddistance"] = 0
            self.l.debug("[RP] speed_gps: below speed_low {} m/s treshold".format(self.p_raw['speed_low']))

    def force_refresh(self):
        self.occ.force_refresh()

    def get_raw_val(self, param):
        if param.endswith("_units"):
            return 0
        else:
            return self.p_raw[param]

    def set_param(self, param_name, value):
        self.l.debug("[RP] Setting {} to {} ".format(param_name, value))
        self.params[param_name] = value

    def get_param(self, param):
        value = None
        try:
            if param.endswith("_units"):
                value = self.get_unit(param[:-6])
            elif param in self.params:
                value = self.params[param]
        except KeyError:
            self.l.debug("[RP] No unit for {}".format(param))
        finally:
            return value

    def get_unit(self, param_name):
        suffixes = ("_min", "_max", "_avg", "_gps", "_home")
        p = self.strip_end(param_name, suffixes)
        if p.endswith("_units"):
            return None
        else:
            try:
                return self.units[p]
            except KeyError:
                return None

    def get_internal_unit(self, param_name):
        suffixes = ("_min", "_max", "_avg", "_gps", "_home")
        p = self.strip_end(param_name, suffixes)
        if p.endswith("_units"):
            return None
        else:
            return self.p_raw_units[p]

    def get_description(self, param_name):
        if param_name in self.p_desc:
            return self.p_desc[param_name]
        else:
            self.l.error("[RP] {} has no description defined".format(param_name))
            return "No description"

    def clean_value(self, variable, empty=0):
        if not math.isnan(variable):
            return variable
        else:
            return empty

    def read_ble_data(self):
        self.p_raw['ble_state'] = self.sensors.get_ble_state()
        if self.ble_sc:
            data = self.ble_sc.get_data()
            tt = time.time()
            self.params['ble_sc_name'] = data['name']
            if data['addr'] is not None:
                self.l.info('[RP] BLE SC new address {}'.format(data['addr']))
                self.params['ble_sc_addr'] = data['addr']
            self.p_raw['wheel_time_stamp'] = self.clean_value(data['wheel_time_stamp'])
            if (tt - self.p_raw['wheel_time_stamp']) < self.p_raw['ble_data_expiry_time']:
                self.p_raw['wheel_rev_time'] = self.clean_value(data['wheel_rev_time'])
            else:
                self.p_raw["wheel_rev_time"] = INF
            if self.p_raw['wheel_rev_time']:
                self.p_raw['speed'] = self.p_raw['wheel_circ'] / self.p_raw['wheel_rev_time']
            self.p_raw['cadence_time_stamp'] = self.clean_value(data['cadence_time_stamp'])
            delay = tt - self.p_raw['cadence_time_stamp']
            if delay < self.p_raw['ble_data_expiry_time']:
                self.p_raw['cadence'] = self.clean_value(data['cadence'])
            else:
                self.p_raw["cadence"] = 0
            if delay > BLE_RECONNECT_DELAY:
                # Force reconnect
                self.ble_sc = None
                self.sensors.reconnect_sensor('ble_sc')
        else:
            self.l.info('[RP] BLE SC sensor not set, trying to get it...')
            self.ble_sc = self.sensors.get_sensor('ble_sc')

        if self.ble_hr:
            data = self.ble_hr.get_data()
            tt = time.time()
            self.params['ble_hr_name'] = data['name']
            if data['addr'] is not None:
                self.l.info('[RP] BLE HR new address {}'.format(data['addr']))
                self.params['ble_hr_addr'] = data['addr']
            self.p_raw['ble_hr_ts'] = data['time_stamp']
            self.p_raw['heart_rate'] = data['heart_rate']
            self.l.debug('[RP] BLE HR = {} at {}'.format(
                self.p_raw['heart_rate'], self.p_raw['ble_hr_ts']))
            delay = tt - self.p_raw['ble_hr_ts']
            if delay > BLE_RECONNECT_DELAY:
                # Force reconnect
                self.ble_hr = None
                self.sensors.reconnect_sensor('ble_hr')
        else:
            self.l.info('[RP] BLE HR sensor not set, trying to get it...')
            self.ble_hr = self.sensors.get_sensor('ble_hr')

    def read_gps_data(self):
        if self.gps:
            data = self.gps.get_data()
            self.p_raw['altitude_gps'] = self.clean_value(data['altitude_gps'])
            self.p_raw['climb_gps'] = self.clean_value(data['climb_gps'])
            self.p_raw['eps'] = self.clean_value(data['eps'])
            self.p_raw['ept'] = self.clean_value(data['ept'])
            self.p_raw['epv'] = self.clean_value(data['epv'])
            self.p_raw['epx'] = self.clean_value(data['epx'])
            self.p_raw['fix_mode_gps'] = data['fix_mode_gps']
            self.p_raw['fix_time_gps'] = data['fix_time_gps']
            self.p_raw['latitude'] = self.clean_value(data['latitude'])
            self.p_raw['longitude'] = self.clean_value(data['longitude'])
            self.p_raw['satellites'] = self.clean_value(data['satellites'])
            self.p_raw['satellitesused'] = self.clean_value(data['satellitesused'])
            self.p_raw['speed_gps'] = self.clean_value(data['speed_gps'])
            self.p_raw['track_gps'] = self.clean_value(data['track_gps'])
            self.p_raw['utc'] = data['utc']
            self.p_raw['time_adjustment_delta'] = data['time_adjustment_delta']

            gps_str = self.p_raw["satellitesused"] - 3
            if gps_str < 0:
                gps_str = 0
            if gps_str > 3:
                gps_str = 3
            self.p_raw["gps_strength"] = gps_str
            self.p_raw["speed_gps"] = self.clean_value(self.p_raw["speed_gps"])
            if self.p_raw["speed_gps"] < self.p_raw['speed_gps_noise']:
                self.p_raw["speed_gps"] = 0
        else:
            self.l.info('[RP] GPS sensor not set, trying to set it...')
            self.gps = self.sensors.get_sensor('gps')

    def split_speed(self, speed_name):
        # FIXME No hardcoded formatting, move to dict
        self.params[speed_name + "_digits"] = self.params[speed_name][:-2]
        self.params[speed_name + "_tenths"] = self.params[speed_name][-1:]

    def update_max_speed(self):
        if self.p_raw["speed"] > self.p_raw["speed_max"]:
            self.p_raw["speed_max"] = self.p_raw["speed"]
        self.split_speed("speed_max")

    def update_fix_gps(self):
        self.params["fix_mode_gps"] = self.p_raw["fix_mode_gps"]
        self.params["fix_time_gps"] = self.p_raw["fix_time_gps"]

    def set_max(self, param):
        self.p_raw[param + "_max"] = max(self.p_raw[param], self.p_raw[param + "_max"])

    def set_min(self, param):
        self.p_raw[param + "_min"] = min(self.p_raw[param], self.p_raw[param + "_min"])

    def calculate_avg_temperature(self):
        dt = self.p_raw["dtime"]
        t = self.p_raw["temperature"]
        ta = self.p_raw["temperature_avg"]
        tt = self.p_raw["ridetime"]
        ta_new = (t * dt + ta * tt) / (tt + dt)
        self.p_raw["temperature_avg"] = ta_new

    def calculate_avg_cadence(self):
        dt = self.p_raw["dtime"]
        c = self.p_raw["cadence"]
        ca = self.p_raw["cadence_avg"]
        tt = self.p_raw["ridetime"]
        ca_new = (c * dt + ca * tt) / (tt + dt)
        self.p_raw["cadence_avg"] = ca_new

    def calculate_avg_heart_rate(self):
        dt = self.p_raw["dtime"]
        hr = self.p_raw["heart_rate"]
        hra = self.p_raw["heart_rate_avg"]
        # FIXME ridetime doesn't seem to be right
        tt = self.p_raw["ridetime"]
        hr_new = (hr * dt + hra * tt) / (tt + dt)
        self.p_raw["heart_rate_avg"] = hr_new

    def update_altitude(self):
        self.update_param("altitude_gps")
        self.update_param("altitude_home")
        self.update_param("altitude")
        self.set_max("altitude")
        self.set_min("altitude")
        self.update_param("altitude_min")
        self.update_param("altitude_max")

    def update_params(self):
        self.update_rtc()
        self.update_fix_gps()
        self.update_param("dtime")
        self.update_param("latitude")
        self.update_param("longitude")
        self.update_altitude()
        self.update_cadence()
        self.update_heart_rate()
        self.update_param("climb")
        self.update_param("distance")
        self.update_param("ridetime")
        self.update_hms("ridetime")
        self.update_hms("ridetime_total")
        self.update_hms("timeon")
        self.update_param("timeon")
        self.update_max_speed()
        self.update_param("speed")
        self.update_param("speed_max")
        self.split_speed("speed")
        self.params["utc"] = self.p_raw["utc"]
        self.update_param("odometer")
        self.update_param("rider_weight")
        self.update_param("pressure")
        self.update_temperatures()
        self.update_param("satellitesused")
        self.update_param("satellites")
        self.update_param("slope")
        self.add_ridelog_entry()
        self.l.debug("[RP] speed: {}, speed_max: {}, average speed: {} {}, cadence {} {}".
                     format(self.params["speed"], self.params["speed_max"],
                            self.params["speed_avg"], self.units["speed"],
                            self.params["cadence"], self.units["cadence"]))
        self.force_refresh()

    def add_ridelog_entry(self):
        slp = self.params["slope"]
        hrt = self.params["heart_rate"]
        tme = self.params["timeon_hms"]
        spd = self.params["speed"]
        cde = self.params["cadence"]
        dte = self.params["dtime"]
        pre = round(self.p_raw["pressure"], 1)
        tem = self.p_raw["temperature"]
        alt = self.p_raw["altitude"]
        alg = self.p_raw["altitude_gps"]
        dst = round(self.p_raw["distance"], 0)
        clb = self.p_raw["climb"]
        trk = self.p_raw["track_gps"]
        eps = self.p_raw["eps"]
        epx = self.p_raw["epx"]
        epv = self.p_raw["epv"]
        ept = self.p_raw["ept"]
        self.r.info('', extra={'time': tme, 'dtime': dte, 'speed': spd, 'cadence': cde,
                               'heart_rate': hrt, 'pressure': pre, 'temperature': tem,
                               'altitude': alt, 'altitude_gps': alg, 'distance': dst,
                               'slope': slp, 'climb': clb, 'track_gps': trk, 'eps': eps,
                               'epx': epx, 'epv': epv, 'ept': ept})

    def strip_end(self, param_name, suffix=None):
        # Make sure there is no _digits, _tenths, _hms at the end
        if suffix is None:
            suffix = self.suffixes
        for s in suffix:
            if param_name.endswith(s):
                l = -1 * len(s)
                param_name = param_name[:l]
        return param_name

    def reset_ride(self):
        self.p_raw["distance"] = 0.0
        self.p_raw["ridetime"] = 0.0
        self.reset_cadence()
        self.reset_heart_rate()

    def reset_cadence(self):
        self.p_raw["cadence"] = 0.0
        self.p_raw["cadence_avg"] = 0.0
        self.p_raw["cadence_max"] = INF_MIN
        self.p_raw["time_of_ride_reset"] = time.time()

    def reset_heart_rate(self):
        self.p_raw["heart_rate"] = 0.0
        self.p_raw["heart_rate_min"] = INF
        self.p_raw["heart_rate_avg"] = 0.0
        self.p_raw["heart_rate_max"] = INF_MIN
        self.p_raw["time_of_ride_reset"] = time.time()

    def reset_param(self, param_name):
        self.l.debug("[RP] Resetting {}".format(param_name))
        self.p_raw[param_name] = 0
        if param_name in ("ridetime", "distance", "cadence", "heart_rate"):
            self.reset_ride()
        self.force_refresh()

    def update_param(self, param_name):
        if param_name in self.p_format:
            f = self.p_format[param_name]
        else:
            self.l.error("[RP] Formatting not available: param_name = {}".format(param_name))
            f = "%.1f"

        if self.p_raw[param_name] != "-":
            unit_raw = self.get_internal_unit(param_name)
            unit = self.get_unit(param_name)
            value = self.p_raw[param_name]
            if unit_raw != unit:
                value = self.uc.convert(value, unit)
            self.params[param_name] = f % float(value)
        else:
            self.params[param_name] = '-'
            self.l.debug("[RP] param_name {} = -".format(param_name))

    def add_zero(self, value):
        if value < 10:
            value = "0" + unicode(value)
        return value

    def update_hms(self, param):
        t = divmod(int(self.p_raw[param]), 3600)
        hrs = t[0]
        sec = t[1]
        t = divmod(t[1], 60)
        mins = t[0]
        sec = t[1]
        hrs = self.add_zero(hrs)
        mins = self.add_zero(mins)
        sec = self.add_zero(sec)
        self.params[param + "_hms"] = "{}:{}:{}".format(hrs, mins, sec)

    def update_rtc(self):
        # FIXME proper localisation would be nice....
        self.params["date"] = strftime("%d-%m-%Y")
        self.params["time"] = strftime("%H:%M:%S")
        self.params["rtc"] = self.params["date"] + " " + self.params["time"]

    def read_bmp183_data(self):
        if self.bmp183:
            data = self.bmp183.get_data()
            self.p_raw['pressure'] = data['pressure']
            self.p_raw['temperature'] = data['temperature']
        else:
            self.l.info('[RP] BMP183 sensor not set, trying to set it...')
            self.bmp183 = self.sensors.get_sensor('bmp183')

    def calculate_altitude(self):
        def calc_alt():
            alt = 0
            if self.p_raw["pressure"] != 0:
                alt = round(44330.0 * (1 - pow((self.p_raw["pressure"] /
                                                self.p_raw["pressure_at_sea_level"]), (1 / 5.255))), 2)
            return alt

        if self.p_raw["pressure_at_sea_level"] == 0:
            self.calculate_pressure_at_sea_level()
            if self.p_raw["pressure_at_sea_level"] != 0:
                self.p_raw["altitude"] = calc_alt()
                self.p_raw["altitude_previous"] = self.p_raw["altitude"]
        else:
            self.p_raw["altitude_previous"] = self.p_raw["altitude"]
            self.p_raw["altitude"] = calc_alt()
            self.p_raw["daltitude"] = self.p_raw["altitude"] - self.p_raw["altitude_previous"]
        self.l.debug("[RP] altitude: {}, daltitude {}".format(
            self.p_raw["altitude"], self.p_raw["daltitude"]))

    def calculate_pressure_at_sea_level(self):
        # Set pressure_at_sea_level based on given altitude
        pressure = self.p_raw["pressure"]
        altitude_home = self.p_raw["altitude_home"]
        if altitude_home < 43300:
            self.p_raw["pressure_at_sea_level"] = float(
                pressure / pow((1 - altitude_home / 44330), 5.255))
        self.l.debug("[RP] pressure_at_sea_level: {}".format(self.p_raw["pressure_at_sea_level"]))

    def update_temperatures(self):
        self.set_min("temperature")
        self.set_max("temperature")
        self.calculate_avg_temperature()
        self.update_param("temperature")
        self.update_param("temperature_avg")
        self.update_param("temperature_min")
        self.update_param("temperature_max")

    def no_zero(self, param_name):
        if self.params[param_name] == '0' or self.params[param_name] == '-0':
            self.params[param_name] = '-'

    def update_cadence(self):
        self.calculate_avg_cadence()
        self.set_max("cadence")
        self.update_param("cadence")
        self.no_zero("cadence")
        self.update_param("cadence_avg")
        self.no_zero("cadence_avg")
        self.update_param("cadence_max")
        self.no_zero("cadence_max")

    def update_heart_rate(self):
        self.set_min("heart_rate")
        self.set_max("heart_rate")
        self.calculate_avg_heart_rate()
        self.update_param("heart_rate")
        self.no_zero("heart_rate")
        self.update_param("heart_rate_min")
        self.no_zero("heart_rate_min")
        self.update_param("heart_rate_avg")
        self.no_zero("heart_rate_avg")
        self.update_param("heart_rate_max")
        self.no_zero("heart_rate_max")

    def get_editor_name(self, parameter):
        self.l.debug("[RP] get_editor_name searching for editor for parameter {}".format(parameter))
        editor = None
        for e in self.editors:
            if parameter in self.editors[e]:
                editor = e
                break
        if editor:
            self.l.debug("[RP] get_editor_name found editor {} for parameter {}".format(editor, parameter))
        else:
            self.l.debug("[RP] get_editor_name didn't find any editor for parameter {}".format(parameter))
        return editor
