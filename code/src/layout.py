from units import units
import logging
import lxml.etree as eltree
import os
import pygame
import struct
import sys
import time


class layout():
    # def __init__(self, occ, layout_path="layouts/current.xml"):
    # Temporary change

    def __init__(self, occ, layout_path="layouts/default.xml"):
        self.occ = occ
        self.l = occ.l
        self.uc = units()
        self.screen = occ.screen
        self.colorkey = [0, 0, 0]
        self.alpha = 255
        self.font_list = {}
        self.page_list = {}
        self.page_index = {}
        self.function_rect_list = {}
        self.current_function_list = []
        self.current_image_list = {}
        self.layout_path = layout_path
        self.load_layout(layout_path)
        self.render_button = None

    def load_layout(self, layout_path):
        self.max_page_id = 0
        self.max_settings_id = 0
        self.page_list = {}
        self.page_index = {}
        try:
            self.layout_tree = eltree.parse(layout_path)
            self.layout_path = layout_path
        except:
            self.occ.l.error(
                "{} Loading layout {} failed, falling back to default.xml".format(__name__, layout_path))
            sys_info = "Error details: {}".format(sys.exc_info()[0])
            self.occ.l.error(sys_info)
            # Fallback to default layout
            # FIXME - define const file with paths?
            self.layout_tree = eltree.parse("layouts/default.xml")

        self.pages = self.layout_tree.getroot()
        for page in self.pages:
            page_id = page.get('id')
            self.page_list[page_id] = page
            self.page_index[page_id] = page.get('name')
            page_type = page.get('type')
            _no = page.get('no')
            if page_type == 'normal':
                no = int(_no)
                self.max_page_id = max(self.max_page_id, no)
            if page_type == 'settings':
                no = int(_no)
                self.max_settings_id = max(self.max_settings_id, no)
        self.use_page()
        self.write_layout()

    def write_layout(self, layout_path="layouts/current.xml"):
        self.layout_tree.write(layout_path, encoding="UTF-8", pretty_print=True)

    def ble_scan(self):
        self.occ.l.debug("[LY] starting BLE scanning")
        for i in range(5):
            self.occ.rp.params['ble_dev_name_' + str(i)] = "Scanning.."
        import ble_scanner
        bs = ble_scanner.ble_scan()
        bs.scan()
        for i in range(5):
            self.occ.rp.params['ble_dev_name_' + str(i)] = ""
        i = 1
        for dev in bs.get_dev_list():
            self.occ.l.debug("[LY] BLE device found {} {}".format(dev['name'], dev['addr']))
            self.occ.rp.params['ble_dev_name_' + str(i)] = dev['name']
            self.occ.rp.params['ble_dev_addr_' + str(i)] = dev['addr']
            i += 1
        self.occ.l.debug("[LY] BLE scanning finished")

    def ble_dev_helper(self, no, master):
        if master == 'ble_hr_name':
            dev_type = 'hr'
        elif master == 'ble_sc_name':
            dev_type = 'sc'
        name = self.occ.rp.params['ble_dev_name_' + str(no)]
        addr = self.occ.rp.params['ble_dev_addr_' + str(no)]
        self.occ.l.debug("[LY] Selected BLE device {} {}".format(name, addr))
        self.occ.rp.params["variable_value"] = (name, addr, dev_type)

    def ble_dev_name_1(self):
        self.ble_dev_helper(1, self.occ.rp.params["variable"])
        self.ed_accept()

    def ble_dev_name_2(self):
        self.ble_dev_helper(2, self.occ.rp.params["variable"])
        self.ed_accept()

    def ble_dev_name_3(self):
        self.ble_dev_helper(3, self.occ.rp.params["variable"])
        self.ed_accept()

    def ble_dev_name_4(self):
        self.ble_dev_helper(4, self.occ.rp.params["variable"])
        self.ed_accept()

    def use_page(self, page_id="page_0"):
        self.occ.l.debug("[LY][F] use_page {}".format(page_id))
        self.occ.force_refresh()
        self.current_function_list = []
        self.current_button_list = []
        self.current_page = self.page_list[page_id]
        try:
            bg_path = self.current_page.get('background')
            self.bg_image = pygame.image.load(bg_path).convert()
        except pygame.error:
            self.occ.l.critical("{} Cannot load background image! layout_path = {} background path = {} page_id = {}"
                                .format(__name__, self.layout_path, bg_path, page_id))
            # That stops occ but not immediately - errors can occur
            self.occ.running = False
            self.occ.cleanup()
        try:
            bt_path = self.current_page.get('buttons')
            self.bt_image = pygame.image.load(bt_path).convert()
        except pygame.error:
            self.occ.l.critical("{} Cannot load buttons image! layout_path = {} buttons path = {} page_id = {}"
                                .format(__name__, self.layout_path, bt_path, page_id))
            self.occ.running = False
            self.occ.cleanup()
            pass
        self.font = self.current_page.get('font')
        if (self.font == ""):
            self.font = None
        self.fg_colour_rgb = self.current_page.get('fg_colour')
        self.fg_colour = struct.unpack('BBB', self.fg_colour_rgb.decode('hex'))
        for field in self.current_page:
            # print "function name : ", field.get('function')
            self.current_function_list.append(field.get('function'))
            b = field.find('button')
            if (b is not None):
                x0 = int(b.get('x0'))
                y0 = int(b.get('y0'))
                w = int(b.get('w'))
                h = int(b.get('h'))
                name = field.get('function')
                rect = pygame.Rect(x0, y0, w, h)
                self.function_rect_list[name] = rect
                self.current_button_list.append(name)
                text_center = field.find('text_center')
                image_path = text_center.get('file')
                if (image_path is not None):
                    self.load_image(text_center)

    # FIXME text_center isn't really good name
    def load_image(self, text_center):
        image_path = text_center.get('file')
        frames = text_center.get('frames')
        if frames is not None:
            frames = int(frames)
            for i in range(frames + 1):
                image_path_for_frame = self.make_image_key(image_path, i)
                try:
                    image = pygame.image.load(image_path_for_frame).convert()
                    image.set_colorkey(self.colorkey)
                    image.set_alpha(self.alpha)
                    self.current_image_list[image_path_for_frame] = image
                    self.occ.l.debug("[LY] Image {} loaded".format(image_path_for_frame))
                except:
                    self.occ.l.error("[LY] Cannot load image {}".format(image_path_for_frame))
                    self.current_image_list[image_path_for_frame] = None
        else:
            try:
                image = pygame.image.load(image_path).convert()
                image.set_colorkey(self.colorkey)
                image.set_alpha(self.alpha)
                self.current_image_list[image_path] = image
                self.occ.l.debug("[LY] Image {} loaded".format(image_path))
            except:
                self.occ.l.error("[LY] Cannot load image {}".format(image_path))
                self.current_image_list[image_path] = None

    def use_main_page(self):
        self.use_page()

    def render_background(self, screen):
        screen.blit(self.bg_image, [0, 0])

    def render_pressed_button(self, screen, function):
        # FIXME make sure it's OK to skip rendering here
        try:
            r = self.function_rect_list[function]
            screen.blit(self.bt_image, r, r, 0)
        # FIXME required to catch exception?
        except (TypeError, AttributeError):
            pass

    def render_page(self):
        self.render_background(self.screen)
        self.show_pressed_button()
        self.render(self.screen)

    def make_image_key(self, image_path, value):
        suffix = "_" + unicode(value)
        extension = image_path[-4:]
        name = image_path[:-4]
        return (name + suffix + extension)

    def render(self, screen):
        # FIXME Optimisation!
        for field in self.current_page:
            function = field.get('function')
            text_center = field.find('text_center')
            value = self.occ.rp.get_val(function)
            if value is None:
                value = text_center.text
            if value is None:
                value = ""
            uv = unicode(value)
            text_center_x = int(text_center.get('x'))
            text_center_y = int(text_center.get('y'))
            variable = text_center.get('variable')
            image_path = text_center.get('file')
            if variable is not None:
                value = self.occ.rp.get_raw_val(variable)
                image_path_for_frame = self.make_image_key(image_path, value)
                if image_path_for_frame not in self.current_image_list:
                    self.load_image(text_center)
                image = self.current_image_list[image_path_for_frame]
                screen.blit(image, [text_center_x, text_center_y])
            elif image_path is not None:
                if image_path not in self.current_image_list:
                    self.load_image(text_center)
                image = self.current_image_list[image_path]
                screen.blit(image, [text_center_x, text_center_y])
            try:
                fs = float(text_center.get('size'))
            except:
                fs = 0
            if function != "variable_value":
                font_size = int(12.0 * fs)
                if font_size in self.font_list:
                    font = self.font_list[font_size]
                else:
                    font = pygame.font.Font(self.font, font_size)
                    self.font_list[font_size] = font
                # font = pygame.font.Font(self.font, font_size)
                ren = font.render(uv, 1, self.fg_colour)
                x = ren.get_rect().centerx
                y = ren.get_rect().centery
                screen.blit(ren, (text_center_x - x, text_center_y - y))
            else:
                font_size_small = int(12.0 * (fs - 1))
                font_size_large = int(12.0 * (fs + 1))
                if font_size_small in self.font_list:
                    font_s = self.font_list[font_size_small]
                else:
                    font_s = pygame.font.Font(self.font, font_size_small)
                    self.font_list[font_size_small] = font_s
                if font_size_large in self.font_list:
                    font_l = self.font_list[font_size_large]
                else:
                    font_l = pygame.font.Font(self.font, font_size_large)
                    self.font_list[font_size_large] = font_l
                i = self.occ.rp.params["editor_index"]
                rv1 = uv[:i]
                ren1 = font_s.render(rv1, 1, self.fg_colour)
                w1 = ren1.get_rect().width
                y1 = ren1.get_rect().centery
                rv2 = uv[i]
                ren2 = font_l.render(rv2, 1, self.fg_colour)
                w2 = ren2.get_rect().width
                y2 = ren2.get_rect().centery
                rv3 = uv[i + 1:]
                ren3 = font_s.render(rv3, 1, self.fg_colour)
                w3 = ren3.get_rect().width
                y3 = ren3.get_rect().centery
                x = text_center_y - int((w1 + w2 + w3) / 2)
                screen.blit(ren1, (x, text_center_y - y1))
                screen.blit(ren2, (x + w1, text_center_y - y2))
                screen.blit(ren3, (x + w1 + w2, text_center_y - y3))

    def show_pressed_button(self):
        if self.render_button:
            for func in self.current_button_list:
                try:
                    if self.function_rect_list[func].collidepoint(self.render_button):
                        self.render_pressed_button(self.screen, func)
                        break
                except KeyError:
                    self.occ.l.critical(
                        "{} show_pressed_button failed! func ={}".format, __name__, func)
                    self.occ.running = False

    def check_click(self, position, click):
        # print "check_click: ", position, click

        if click == 0:
            # Short click
            # FIXME Search through function_rect_list directly? TBD
            for function in self.current_button_list:
                try:
                    if self.function_rect_list[function].collidepoint(position):
                        self.run_function(function)
                        break
                except KeyError:
                    self.occ.l.debug(
                        "[LY] CLICK on non-clickable {}".format(function))
        elif click == 1:
            # print self.function_rect_list
            # print self.current_button_list
            for function in self.current_button_list:
                try:
                    if self.function_rect_list[function].collidepoint(position):
                        # FIXME I's dirty way of getting value - add some
                        # helper function
                        self.occ.l.debug("[LY] LONG CLICK on {}".format(function))
                        editor_name = self.occ.rp.get_editor_name(function)
                        if editor_name:
                            self.open_editor_page(editor_name, function)
                            break
                        p = self.occ.rp.strip_end(function)
                        if p in self.occ.rp.p_resettable:
                            self.occ.rp.reset_param(p)
                except KeyError:
                    self.occ.l.debug(
                        "[LY] LONG CLICK on non-clickable {}".format(function))
        elif click == 2:  # Swipe RIGHT to LEFT
            self.run_function("next_page")
        elif click == 3:  # Swipe LEFT to RIGHT
            self.run_function("prev_page")
        elif click == 4:  # Swipe BOTTOM to TOP
            self.run_function("page_0")
        elif click == 5:  # Swipe TOP to BOTTOM
            self.run_function("settings")

    def open_editor_page(self, editor_name, function):
        self.occ.l.debug("[LY] Opening editor {} for {}".format(editor_name, function))
        # FIXME move to RP
        self.occ.rp.params["variable"] = function
        self.occ.rp.params["variable_raw_value"] = self.occ.rp.get_raw_val(function)
        self.occ.rp.params["variable_value"] = self.occ.rp.get_val(function)
        self.occ.rp.params["variable_unit"] = self.occ.rp.get_unit(function)
        self.occ.rp.params["variable_description"] = self.occ.rp.get_description(function)
        self.occ.rp.params["editor_index"] = 0

        if editor_name == 'editor_units':
            name = self.occ.rp.params["variable"]
            # FIXME make a stripping function
            na = name.find("_")
            if na > -1:
                n = name[:na]
            else:
                n = name
            unit = self.occ.rp.get_unit(n)
            self.occ.rp.params["variable"] = n
            self.occ.rp.params["variable_unit"] = unit
            self.occ.rp.params["variable_value"] = 0
        self.use_page(editor_name)

    def run_function(self, name):
        functions = {"page_0": self.load_page_0,
                     "settings": self.load_settings_page,
                     "debug_level": self.debug_level,
                     "ed_accept": self.ed_accept,
                     "ed_cancel": self.ed_cancel,
                     "ed_decrease": self.ed_decrease,
                     "ed_increase": self.ed_increase,
                     "ed_next": self.ed_next,
                     "ed_next_unit": self.ed_next_unit,
                     "ed_prev": self.ed_prev,
                     "ed_prev_unit": self.ed_prev_unit,
                     "halt": self.halt,
                     "load_default_layout": self.load_default_layout,
                     "load_current_layout": self.load_current_layout,
                     "next_page": self.next_page,
                     "prev_page": self.prev_page,
                     "reboot": self.reboot,
                     "write_layout": self.write_layout,
                     "ble_scan": self.ble_scan,
                     "ble_dev_name_1": self.ble_dev_name_1,
                     "ble_dev_name_2": self.ble_dev_name_2,
                     "ble_dev_name_3": self.ble_dev_name_3,
                     "ble_dev_name_4": self.ble_dev_name_4,
                     "quit": self.quit}
        functions[name]()

    def force_refresh(self):
        self.occ.force_refresh()

    def load_page_0(self):
        self.use_main_page()

    def load_settings_page(self):
        self.use_page("settings_0")

    def ed_accept(self):
        self.accept_edit()
        self.use_main_page()

    def ed_cancel(self):
        self.use_main_page()

    def ed_decrease(self):
        u = unicode(self.occ.rp.params["variable_value"])
        i = self.occ.rp.params["editor_index"]
        ui = u[i]
        if ui == "0":
            ui = "9"
        else:
            try:
                ui = unicode(int(ui) - 1)
            except ValueError:
                pass
        un = u[:i] + ui + u[i + 1:]
        self.occ.rp.params["variable_value"] = un
        self.force_refresh()

    def ed_increase(self):
        u = unicode(self.occ.rp.params["variable_value"])
        i = self.occ.rp.params["editor_index"]
        ui = u[i]
        if ui == "9":
            ui = "0"
        else:
            try:
                ui = unicode(int(ui) + 1)
            except ValueError:
                pass
        un = u[:i] + ui + u[i + 1:]
        self.occ.rp.params["variable_value"] = un
        self.force_refresh()

    def ed_next(self):
        u = unicode(self.occ.rp.params["variable_value"])
        i = self.occ.rp.params["editor_index"]
        if u[0] == '0':
            u = u[1:]
            self.occ.rp.params["variable_value"] = u
        else:
            i += 1
        l = len(u) - 1
        if i > l:
            i = l
        else:
            ui = u[i]
            # FIXME localisation points to be used here
            if (ui == ".") or (ui == ","):
                i += 1
        self.occ.rp.params["editor_index"] = i
        self.force_refresh()

    def ed_prev(self):
        u = unicode(self.occ.rp.params["variable_value"])
        i = self.occ.rp.params["editor_index"]
        i -= 1
        if i < 0:
            i = 0
            uv = "0" + u
            self.occ.rp.params["variable_value"] = uv
        else:
            ui = u[i]
            # FIXME localisation points to be used here
            if (ui == ".") or (ui == ","):
                i -= 1
        self.occ.rp.params["editor_index"] = i
        self.force_refresh()

    def ed_change_unit(self, direction):
        # direction to be 1 (next) or 0 (previous)
        variable = self.occ.rp.params["variable"]
        variable_unit = self.occ.rp.params["variable_unit"]
        variable_value = self.occ.rp.params["variable_raw_value"]
        current_unit_index = self.occ.rp.units_allowed[
            variable].index(variable_unit)
        if direction == 1:
            try:
                next_unit = self.occ.rp.units_allowed[
                    variable][current_unit_index + 1]
            except IndexError:
                next_unit = self.occ.rp.units_allowed[variable][0]
        else:
            try:
                next_unit = self.occ.rp.units_allowed[
                    variable][current_unit_index - 1]
            except IndexError:
                next_unit = self.occ.rp.units_allowed[variable][-1]
        if next_unit != variable_unit:
            variable_value = self.uc.convert(variable_value, next_unit)
        try:
            f = self.occ.rp.p_format[variable]
        except KeyError:
            self.occ.l.warning(
                "[LY] Formatting not available: function ={}".format(variable))
            f = "%.1f"
        self.occ.rp.params["variable_value"] = float(f % float(variable_value))
        self.occ.rp.params["variable_unit"] = next_unit

    def ed_next_unit(self):
        self.ed_change_unit(1)
        self.force_refresh()

    def ed_prev_unit(self):
        self.ed_change_unit(0)
        self.force_refresh()

    def accept_edit(self):
        variable = self.occ.rp.params["variable"]
        variable_unit = self.occ.rp.params["variable_unit"]
        variable_raw_value = self.occ.rp.params["variable_raw_value"]
        variable_value = self.occ.rp.params["variable_value"]
        if self.occ.rp.params["editor_type"] == 0:
            self.occ.rp.units[variable] = variable_unit
        if self.occ.rp.params["editor_type"] == 1:
            unit_raw = self.occ.rp.get_internal_unit(variable)
            value = variable_value
            if unit_raw != variable_unit:
                value = self.uc.convert(variable_raw_value, variable_unit)
            self.occ.rp.p_raw[variable] = float(value)
            self.occ.rp.units[variable] = self.occ.rp.params["variable_unit"]
            # FIXME - find a better place for it
            if variable == "altitude_home":
                # Force recalculation
                self.occ.rp.p_raw["pressure_at_sea_level"] = 0
        if self.occ.rp.params["editor_type"] == 2:
            self.occ.rp.p_raw[variable] = variable_value
            self.occ.rp.params[variable] = variable_value
        if self.occ.rp.params["editor_type"] == 3:
            (name, addr, dev_type) = variable_value
            self.occ.sensors.set_ble_device(name, addr, dev_type)
        self.force_refresh()

    def get_page(self, page_type, page_no):
        if page_type == 'normal':
            if page_no == -1:
                page_no = self.max_page_id
            if page_no > self.max_page_id:
                page_no = 0
        elif page_type == 'settings':
            if page_no == -1:
                page_no = self.max_settings_id
            if page_no > self.max_settings_id:
                page_no = 0
        for p in self.page_list:
            t = self.page_list[p].get('type')
            n = self.page_list[p].get('no')
            if t == page_type and n == str(page_no):
                return self.page_list[p].get('id')

    def next_page(self):
        # Editor is a special page - it cannot be switched, only cancel or accept
        if not self.current_page.get('type') == 'editor':
            no = int(self.current_page.get('no'))
            page_id = self.current_page.get('id')
            page_type = self.current_page.get('type')
            self.occ.l.debug("[LY][F] next_page {} {} {}".format(page_id, page_type, no))
            next_page_id = self.get_page(page_type, no + 1)
            try:
                self.use_page(next_page_id)
            except KeyError:
                self.occ.l.critical("[LY][F] Page 0 of type {} not found!".format(page_type))

    def prev_page(self):
        # Editor is a special page - it cannot be switched, only cancel or accept
        if not self.current_page.get('type') == 'editor':
            no = int(self.current_page.get('no'))
            page_id = self.current_page.get('id')
            page_type = self.current_page.get('type')
            self.occ.l.debug("[LY][F] prev_page {} {} {}".format(page_id, page_type, no))
            prev_page_id = self.get_page(page_type, no - 1)
            try:
                self.use_page(prev_page_id)
            except KeyError:
                self.occ.l.critical("[LY][F] Page {} of type {} not found!".format(self.max_page_id, page_type))

    def load_layout_by_name(self, name):
        self.load_layout("layouts/" + name)

    def load_current_layout(self):
        self.load_layout_by_name("current.xml")

    def load_default_layout(self):
        self.load_layout_by_name("default.xml")

    def quit(self):
        self.occ.running = False

    def reboot(self):
        self.quit()
        time.sleep(2)
        if not self.occ.simulate:
            os.system("reboot")

    def halt(self):
        self.quit()
        time.sleep(2)
        if not self.occ.simulate:
            os.system("halt")

    def debug_level(self):
        log_level = self.l.getEffectiveLevel()
        log_level -= 10
        if log_level < 10:
            log_level = 40
        log_level_name = logging.getLevelName(log_level)
        self.occ.switch_log_level(log_level_name)
        self.occ.rp.params["debug_level"] = log_level_name
