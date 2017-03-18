import logging
import logging.handlers
import lxml.etree as eltree
from shutil import copyfile
from wheel import wheel


class occ_config(object):
    def __init__(self):
        pass

    def read_config(self):
        self.l.debug("[OCC][F] read_config")
        try:
            config_tree = eltree.parse(self.config_path)
        except IOError:
            self.l.exception("[OCC] I/O Error when trying to parse config file. Making copy of base_config")
            copyfile('config/config_base.xml', 'config/config.xml')
            self.config_path = "config/config.xml"
            try:
                config_tree = eltree.parse(self.config_path)
            except IOError:
                self.l.exception("[OCC] I/O Error when trying to parse to default config. Quitting!!")
                self.cleanup()
        self.config = config_tree.getroot()
        try:
            log_level = self.config.find("log_level").text
            self.occ.switch_log_level(log_level)
            self.rp.params["debug_level"] = log_level
        except AttributeError:
            pass
        try:
            self.layout.layout_path = self.config.find("layout_path").text
        except AttributeError:
            self.layout.layout_path = "layouts/default.xml"
            self.l.error("[OCC] Missing layout path, falling back to default.xml")
        error_list = []
        try:
            self.rp.p_raw["riderweight"] = float(self.config.find("riderweight").text)
        except AttributeError:
            error_list.append("riderweight")
        try:
            self.rp.p_raw["wheel_size"] = self.config.find("wheel_size").text
            self.rp.params["wheel_size"] = self.rp.p_raw["wheel_size"]
            w = wheel()
            try:
                self.rp.p_raw["wheel_circ"] = w.get_size(self.rp.p_raw["wheel_size"])
            except KeyError:
                error_list.append("wheel_circ")
            self.rp.params["wheel_circ"] = self.rp.p_raw["wheel_circ"]
        except AttributeError:
            error_list.append("wheel_size")
        try:
            self.rp.units["riderweight"] = self.config.find("riderweight_units").text
        except AttributeError:
            error_list.append("riderweight_units")
        try:
            self.rp.p_raw["altitude_home"] = float(self.config.find("altitude_home").text)
        except AttributeError:
            error_list.append("")
        try:
            self.rp.units["altitude_home"] = self.config.find("altitude_home_units").text
        except AttributeError:
            error_list.append("altitude_home")
        try:
            self.rp.p_raw["odometer"] = float(self.config.find("odometer").text)
        except AttributeError:
            error_list.append("odometer")
        try:
            self.rp.units["odometer"] = self.config.find("odometer_units").text
        except AttributeError:
            error_list.append("odometer")
        try:
            self.rp.p_raw["ridetime_total"] = float(self.config.find("ridetime_total").text)
        except AttributeError:
            error_list.append("ridetime_total")
        try:
            self.rp.p_raw["speed_max"] = float(self.config.find("speed_max").text)
        except AttributeError:
            error_list.append("speed_max")
        try:
            self.rp.units["speed"] = self.config.find("speed_units").text
        except AttributeError:
            error_list.append("speed")
        try:
            self.rp.units["temperature"] = self.config.find("temperature_units").text
        except AttributeError:
            error_list.append("temperature")
        try:
            self.rp.p_raw["ble_hr_name"] = self.config.find("ble_hr_name").text
        except AttributeError:
            error_list.append("ble_hr_name")
        try:
            self.rp.p_raw["ble_hr_addr"] = self.config.find("ble_hr_addr").text
        except AttributeError:
            error_list.append("ble_hr_addr")
        try:
            self.rp.p_raw["ble_sc_name"] = self.config.find("ble_sc_name").text
        except AttributeError:
            error_list.append("ble_sc_name")
        try:
            self.rp.p_raw["ble_sc_addr"] = self.config.find("ble_sc_addr").text
        except AttributeError:
            error_list.append("ble_sc_addr")
        self.rp.update_param("speed_max")
        self.rp.split_speed("speed_max")
        if len(error_list) > 0:
            for item in error_list:
                self.l.error("[OCC] Missing: {} in config file".format(item))
            error_list = []

    def write_config(self):
        self.l.debug("[OCC] Writing config file")
        log_level = logging.getLevelName(self.l.getEffectiveLevel())
        config_tree = eltree.Element("config")
        eltree.SubElement(config_tree, "log_level").text = log_level
        eltree.SubElement(config_tree, "layout_path").text = self.layout.layout_path
        eltree.SubElement(config_tree, "riderweight").text = unicode(self.rp.p_raw["riderweight"])
        eltree.SubElement(config_tree, "riderweight_units").text = unicode(self.rp.units["riderweight"])
        eltree.SubElement(config_tree, "wheel_size").text = self.rp.p_raw["wheel_size"]
        eltree.SubElement(config_tree, "altitude_home").text = unicode(self.rp.p_raw["altitude_home"])
        eltree.SubElement(config_tree, "altitude_home_units").text = unicode(self.rp.units["altitude_home"])
        eltree.SubElement(config_tree, "odometer").text = unicode(self.rp.p_raw["odometer"])
        eltree.SubElement(config_tree, "odometer_units").text = unicode(self.rp.units["odometer"])
        eltree.SubElement(config_tree, "ridetime_total").text = unicode(self.rp.p_raw["ridetime_total"])
        eltree.SubElement(config_tree, "speed_max").text = unicode(self.rp.p_raw["speed_max"])
        eltree.SubElement(config_tree, "speed_units").text = unicode(self.rp.units["speed"])
        eltree.SubElement(config_tree, "temperature_units").text = unicode(self.rp.units["temperature"])
        eltree.SubElement(config_tree, "ble_hr_name").text = self.rp.p_raw["ble_hr_name"]
        eltree.SubElement(config_tree, "ble_hr_addr").text = self.rp.p_raw["ble_hr_addr"]
        eltree.SubElement(config_tree, "ble_sc_name").text = self.rp.p_raw["ble_sc_name"]
        eltree.SubElement(config_tree, "ble_sc_addr").text = self.rp.p_raw["ble_sc_addr"]
        # FIXME error handling for file operation
        eltree.ElementTree(config_tree).write(self.config_path, encoding="UTF-8", pretty_print=True)