from time import strftime
from bmp183 import bmp183
from gps_mtk3339 import gps_mtk3339
import math
import time
import quantities as q

class ride_parameters():
	def __init__(self, occ, simulate = False):
		self.occ = occ
		self.occ.log.info("{}: Initialising GPS".format(__name__))
		self.gps = gps_mtk3339(simulate)
		self.occ.log.info("{}: Starting GPS thread".format(__name__))
		self.gps.start()
		self.occ.log.info("{}: Initialising bmp183 sensor".format(__name__))
		self.bmp183_sensor = bmp183(simulate)

		self.p_desc = {}
		self.p_editable = {}
		self.p_format = {}
		self.p_raw = {}
		self.p_raw_units = {}
		self.params = {}
		self.units = {}
		self.units_allowed = {}

		#Internal params of the ride.
		self.p_raw["time_stamp"] = time.time()
		#Time delta since last p_raw update
		self.p_raw["dtime"] = 1

		self.p_raw["altitude"] = "-"
		self.p_raw["altitude_gps"] = "-"
		self.p_raw["altitude_at_home"] = "-"
		self.p_raw["cadence"] = "-"
		self.p_raw["distance"] = 0
		self.p_raw["gradient"] = "-"
		self.p_raw["heart_rate"] = "-"
		self.p_raw["odometer"] = "-"
		self.p_raw["pressure"] = "-"
		self.p_raw["pressure_at_sea_level"] = "-"
		self.p_raw["rider_weight"] = "-"
		self.p_raw["rtc"] = ""
		self.p_raw["satellites"] = "-"
		self.p_raw["satellites_used"] = "-"
		self.p_raw["satellites_visible"] = "-"
		self.p_raw["speed"] = "-"
		self.p_raw["speed_gps"] = "-"
		self.p_raw["speed_tenths"] =  "-"
		self.p_raw["utc"] = ""

		#Internal units
		self.p_raw_units["altitude_at_home"] = "m"
		self.p_raw_units["altitude_gps"] = "m"
		self.p_raw_units["distance"] = "m"
		self.p_raw_units["latitude"] = ""
		self.p_raw_units["longitude"] = ""
		self.p_raw_units["odometer"] = "m"
		self.p_raw_units["pressure"] = "hPa"
		self.p_raw_units["rider_weight"] = "kg"
		self.p_raw_units["speed"] = "m/s"
		self.p_raw_units["speed_gps"] = "m/s"
		self.p_raw_units["speed_tenths"] = "m/s"
		self.p_raw_units["temperature"] = "C"

		#Params of the ride ready for rendering.
		self.params["altitude"] = "-"
		self.params["altitude_gps"] = "-"
		self.params["cadence"] = "-"
		self.params["distance"] = 0
		self.params["gradient"] = "-"
		self.params["heart_rate"] = "-"
		self.params["latitude"] = "-"
		self.params["longitude"] = "-"
		self.params["pressure"] = "-"
		self.params["pressure_at_sea_level"] = "-" 
		self.params["rtc"] = ""
		self.params["satellites"] = "-"
		self.params["satellites_used"] = "-"
		self.params["satellites_visible"] = "-"
		self.params["speed"] = "-"
		self.params["speed_tenths"] = "-"
		self.params["utc"] = ""

		#Params that can be changed in Settings by user
		self.params["altitude_at_home"] = 89.0
		self.params["odometer"] = 0.0
		self.params["rider_weight"] = 80.0

		#Formatting strings for params.
		self.p_format["altitude"] = "%.1f"
		self.p_format["altitude_at_home"] = "%.0f"
		self.p_format["altitude_gps"] = "%.1f"
		self.p_format["cadence"] = "%.0f"
		self.p_format["distance"] = "%.1f"
		self.p_format["gradient"] = ""
		self.p_format["heart_rate"] = "%.0f"
		self.p_format["latitude"] = "%.4f"
		self.p_format["longitude"] = "%.4f"
		self.p_format["odometer"] = "%.0f"
		self.p_format["pressure"] = "%.0f"
		self.p_format["pressure_at_sea_level"] = "%.0f"
		self.p_format["rider_weight"] = "%.1f"
		self.p_format["rtc"] = ""
		self.p_format["satellites"] = ""
		self.p_format["satellites_used"] = ""
		self.p_format["satellites_visible"] = ""
		self.p_format["speed"] = "%.0f"
		self.p_format["speed_tenths"] = "%.0f"
		self.p_format["temperature"] = "%.0f"
		self.p_format["utc"] = ""

		#Units - name has to be identical as in params
		self.units["altitude"] = "m"
		self.units["altitude_at_home"] = "m"
		self.units["altitude_gps"] = "m"
		self.units["distance"] = "m"
		self.units["gradient"] = "%"
		self.units["heart_rate"] = "BPM"
		self.units["latitude"] = ""
		self.units["longitude"] = ""
		self.units["odometer"] = "km"
		self.units["pressure"] = "hPa"
		self.units["rider_weight"] = "kg"
		self.units["satellites"] = ""
		self.units["satellites_used"] = ""
		self.units["satellites_visible"] = ""
		self.units["speed"] = "km/h"
		#It's just to make handling of speed easier
		self.units["speed_tenths"] = "km/h"

		#Allowed units - user can switch between those when editing value 
		self.units_allowed["odometer"] = ["km", "mi"]
		self.units_allowed["rider_weight"] = ["kg", "st", "lb"]

		#FIXME python-quantities won't like those deg C
		self.units["temperature"] = "C"
		#FIXME Make pretty units for temperature
		#self.units["temperature"] = u'\N{DEGREE SIGN}' + "C"

		#Params description FIXME localisation
		self.p_desc["altitude_at_home"] = "Home altitude"
		self.p_desc["odometer"] = "Odometer" 
		self.p_desc["odometer_units"] = "Odometer units" 
		self.p_desc["rider_weight"] = "Rider weight"
		self.p_desc["rider_weight_units"] = "Rider weight units"

		#Define id a param is editable FIXME editor type - number, calendar, unit, etc.
		self.p_editable["altitude_at_home"] = 1
		self.p_editable["odometer"] = 1 
		self.p_editable["odometer_units"] = 0
		self.p_editable["rider_weight"] = 1
		self.p_editable["rider_weight_units"] = 0

		#Do not record any speed below 3 m/s FIXME units TBC
		self.speed_gps_low = 0
		self.occ.log.info("{}: speed_gps_low treshold set to {}".format(__name__, self.speed_gps_low))

	def stop(self):
		self.gps.stop()
		self.bmp183_sensor.stop()

	def __del__(self):
		self.stop()

	def update_values(self):
		self.occ.log.debug("{}: [F] update_values".format(__name__))
		t = time.time()
		self.p_raw["dtime"] = t - self.p_raw["time_stamp"]
		self.p_raw["time_stamp"] = t
		self.occ.log.debug("{}: update_values timestamp: {}".format(__name__, t))
		self.update_rtc()
		self.read_bmp183_sensor()
		self.read_gps_data()
		self.update_params()
		self.calculate_distance()
		self.force_refresh()
		#FIXME Calc pressure only when gps altitude is known or 
		#when we're at home and the altitude is provided by user
		#self.calculate_pressure_at_sea_level()
		#FIXME Add calculations of gradient, trip time, etc

	def calculate_distance(self):
		self.occ.log.debug("{}: [F] calculate_distance".format(__name__))
		dt = self.p_raw["dtime"]
		#FIXME calculate with speed not speed_gps when bt sensors are set up
		s = self.p_raw["speed_gps"]
		if s > self.speed_gps_low:
			self.occ.log.debug("{}: calculate_distance: speed_gps: {}".format(__name__, s))
			self.occ.log.debug("{}: calculate_distance: distance: {}".format(__name__, self.p_raw["distance"]))
			self.occ.log.debug("{}: calculate_distance: odometer: {}".format(__name__, self.p_raw["odometer"]))
			d = 0
			try:
				d = dt * s
				d = float(d)
			except (TypeError, ValueError):
				#Speed is not set yet - do nothing
				pass
			self.p_raw["distance"] += d
			self.p_raw["odometer"] += d
		else:
			self.occ.log.debug("{}: calculate_distance: speed_gps: below speed_gps_low treshold".format(__name__))

	def force_refresh(self):
		self.occ.force_refresh()

	def get_val(self, func):
		#FIXME try/except for invalid func?
		if func.endswith("_units"):
			return self.units[func[:-6]]
		else:
			return self.params[func]

	def get_unit(self, func):
		#FIXME try/except for invalid func?
		if func.endswith("_units"):
			return None
		else:
			return self.units[func]

	def get_internal_unit(self, func):
		#FIXME try/except for invalid func?
		if func.endswith("_units"):
			return None
		else:
			return self.p_raw_units[func]

	def get_description(self, func):
		#FIXME try/except for invalid func?
		return self.p_desc[func]

	def clean_value(self, variable, empty_string = "-"):
		if not math.isnan(variable):
			return variable
		else:
			return empty_string

	def read_gps_data(self):
		self.occ.log.debug("{}: [F] read_gps_data".format(__name__))
		data = self.gps.get_data()
		lat = data[0]
		lon = data[1]
		alt = data[2]
		spd = data[3]
		self.p_raw["utc"] = data[4]
		sud = data[5]
		svi = data[6]
		sat = data[7]
		self.p_raw["latitude"] = self.clean_value(lat);
		self.p_raw["longitude"] = self.clean_value(lon);
		self.p_raw["altitude_gps"] = self.clean_value(alt);
		self.p_raw["speed_gps"] = self.clean_value(spd);
		self.p_raw["satellites_used"] = self.clean_value(sud);
		self.p_raw["satellites_visible"] = self.clean_value(svi);
		self.p_raw["satellites"] = self.clean_value(sat);

		#FIXME optimise code to use clean_value for speed
		
		spd = self.p_raw["speed_gps"]
		self.occ.log.debug("{}: read_gps_data: p_raw: speed_gps: {}".format(__name__, spd))
		if  spd != "-":
			spd_f = math.floor(spd)
			self.p_raw["speed"] = spd_f
			self.p_raw["speed_tenths"] = math.floor(10 * (spd - spd_f))
		else:
			self.p_raw["speed"] = "-"
			self.p_raw["speed_tenths"] = "-"
		self.occ.log.debug("{}: read_gps_data: p_raw: speed: {}".format(__name__, self.p_raw["speed"]))
		self.occ.log.debug("{}: read_gps_data: p_raw: speed_tenths: {}".format(__name__, self.p_raw["speed_tenths"]))

	def update_speed(self):
		self.occ.log.debug("{}: [F] update_speed".format(__name__))
		#FIXME There has to be a cleaner way. Store _real_ speed without tenths?
		if self.p_raw["speed"] != "-":
			iu = self.get_internal_unit("speed")
			spd_real = self.p_raw["speed"] + (self.p_raw["speed_tenths"] / 10)
			v = q.Quantity(spd_real, iu)
			v.units = self.get_unit("speed")
			spd = float(v.item())
			spd_f = math.floor(spd)
			speed = spd_f
			speed_tenths = math.floor(10 * (spd - spd_f))
			f = self.p_format["speed"]
			self.params["speed"] = f % float(speed)
			self.params["speed_tenths"] = f % float(speed_tenths)
		self.occ.log.debug("{}: update_speed: {} {}".format(__name__, self.params["speed"], self.params["speed_tenths"]))

	def update_params(self):
		self.update_param("latitude")
		self.update_param("longitude")
		self.update_param("altitude_gps")
		self.update_param("distance")
		self.update_speed()
			
		self.params["utc"] = self.p_raw["utc"]
		self.update_param("odometer")
		self.update_param("rider_weight")
		self.update_param("pressure")
		self.update_param("temperature")

	def update_param(self, param_name):
		self.occ.log.debug("{}: [F] update_param".format(__name__))
		self.occ.log.debug("{}: update_param: param_name: {}".format(__name__, param_name))
		try:
			f = self.p_format[param_name]
		except KeyError:
			print "Formatting not available: param_name =", param_name
			f = "%.1f"

		if self.p_raw[param_name] != "-":
			iu = self.get_internal_unit(param_name)
			try:
				v = q.Quantity(self.p_raw[param_name], iu)
				v.units = self.get_unit(param_name)
				self.params[param_name] = f % float(v.item())
				self.occ.log.debug("{}: update_param: {} = {}".format(__name__, param_name, self.params[param_name]))
			except TypeError:
				#Value conversion failed, so don't change anything
				self.occ.log.debug("{}: TypeErroe: update_param exception: {} {} {}".format(__name__ ,param_name, self.params[param_name], self.p_raw[param_name]))
				pass
			except ValueError:
				self.occ.log.debug("{}: ValueError: update_param exception: {} {} {}".format(__name__ ,param_name, self.params[param_name], self.p_raw[param_name]))
			

	def update_rtc(self):
		#FIXME proper localisation would be nice....
		self.params["date"] = strftime("%d-%m-%Y")
		self.params["time"] = strftime("%H:%M:%S")
		self.params["rtc"] = self.params["date"] + " " + self.params["time"]

	def read_bmp183_sensor(self):
		self.occ.log.info("{}: Reading pressure and temperature from bmpBMP183".format(__name__))
		self.bmp183_sensor.measure_pressure()
		self.p_raw["pressure"] = self.bmp183_sensor.pressure/100.0
		self.p_raw["temperature"] = self.bmp183_sensor.temperature
		#Set current altitude based on current pressure and calculated pressure_at_sea_level, cut to meters
		#self.params["altitude"] = int(44330*(1 - pow((self.params["pressure"]/self.params["pressure_at_sea_level"]), (1/5.255))))

	#def calculate_pressure_at_sea_level(self):
	#	#Set pressure_at_sea_level based on given altitude
	#	self.params["pressure_at_sea_level"] = round((self.params["pressure"]/pow((1 - self.params["altitude_at_home"]/44330), 5.255)), 0)
