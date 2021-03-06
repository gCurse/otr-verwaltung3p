# -*- coding: utf-8 -*-
# BEGIN LICENSE
# Copyright (C) 2010 Benjamin Elbers <elbersb@gmail.com>
# This program is free software: you can redistribute it and/or modify it
# under the terms of the GNU General Public License version 3, as published
# by the Free Software Foundation.
#
# This program is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranties of
# MERCHANTABILITY, SATISFACTORY QUALITY, or FITNESS FOR A PARTICULAR
# PURPOSE.  See the GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License along
# with this program.  If not, see <http://www.gnu.org/licenses/>.
# END LICENSE

import base64


class ConfigBinding:
    def __init__(self, widget, config, category, option, data=""):
        self.widget = widget
        self.config = config
        self.category = category
        self.option = option
        self.data = data

        # set intial state
        self.change_value(config.get(category, option))
        # add callback if config option changed
        self.config.connect(category, option, self.change_value)

    def change_value(self, value):
        raise NotImplementedError("This method should be overridden.")


class TextbufferBinding(ConfigBinding):
    def __init__(self, widget, config, category, option, obj):
        ConfigBinding.__init__(self, widget, config, category, option)

        # add signal
        self.widget.connect("changed", self.on_changed)

        self.button = obj("btn_snippets_save")

    def change_value(self, value):
        self.widget.props.text = value

    def on_changed(self, widget, data=None):
        self.button.set_sensitive(True)


class CheckButtonBinding(ConfigBinding):
    def __init__(self, widget, config, category, option):
        ConfigBinding.__init__(self, widget, config, category, option)

        # add signal
        self.widget.connect("toggled", self.on_toggled)

    def change_value(self, value):
        self.widget.set_active(value)

    def on_toggled(self, widget, data=None):
        self.config.set(self.category, self.option, self.widget.get_active())


class EntryBinding(ConfigBinding):
    def __init__(self, widget, config, category, option, encode=False):
        self.encode = encode
        ConfigBinding.__init__(self, widget, config, category, option)

        # add signal
        self.widget.connect("changed", self.on_changed)

    def change_value(self, value):
        if self.encode:
            if not value:
                self.widget.set_text("")
            else:
                try:
                    value.decode("utf-8")
                    self.widget.set_text(base64.b64decode(value.decode("utf-8")).decode("utf-8"))
                except AttributeError:
                    self.widget.set_text(value)
        else:
            self.widget.set_text(value)

    def on_changed(self, widget, data=None):
        if self.encode:
            self.config.set(
                self.category, self.option, base64.b64encode(self.widget.get_text().encode()),
            )
        else:
            self.config.set(self.category, self.option, self.widget.get_text())


class SpinbuttonBinding(ConfigBinding):
    def __init__(self, widget, config, category, option):
        ConfigBinding.__init__(self, widget, config, category, option)

        # add signal
        self.widget.connect("value_changed", self.on_value_changed)

    def change_value(self, value):
        self.widget.set_value(value)

    def on_value_changed(self, widget, data=None):
        self.config.set(self.category, self.option, self.widget.get_value_as_int())


class FileChooserFolderBinding(ConfigBinding):
    def __init__(self, widget, config, category, option):
        ConfigBinding.__init__(self, widget, config, category, option)

        # add signal
        self.widget.connect("current-folder-changed", self.on_folder_changed)
        self.widget.connect("selection-changed", self.on_folder_changed)

    def change_value(self, value):
        if self.widget.get_filename() != value:
            self.widget.set_current_folder(value)

    def on_folder_changed(self, widget, data=None):
        self.config.set(self.category, self.option, self.widget.get_filename())


class RadioButtonsBinding(ConfigBinding):
    def __init__(self, widgets, config, category, option):
        ConfigBinding.__init__(self, widgets, config, category, option)

        for index, radiobutton in enumerate(widgets):
            radiobutton.connect("toggled", self.on_toggled, index)

    def change_value(self, value):
        self.widget[value].set_active(True)

    def on_toggled(self, widget, index):
        if widget.get_active():
            self.config.set(self.category, self.option, index)


class ComboBoxEntryBinding(ConfigBinding):
    def __init__(self, widget, config, category, option, data=None):
        ConfigBinding.__init__(self, widget, config, category, option, data)

        self.data = data
        self.widget.connect("changed", self.on_changed)

    def change_value(self, value):
        if self.data is not None:
            if len(self.data) == 1:
                if self.data[0] == "cut_default":
                    self.widget.set_active(value)
        else:
            self.widget.set_active_id(value)
        # self.widget.append_text(value)

    def on_changed(self, widget):
        if self.data is not None:
            if len(self.data) == 1:
                if self.data[0] == "cut_default":
                    model_dict = {}
                    for row in widget.get_model():
                        model_dict[row[0]] = int(row[1])
                    self.config.set(self.category, self.option, model_dict[widget.get_active_text()])
            elif len(self.data) == 2:
                self.config.set(self.category, self.option, widget.get_active_text())
                if self.data[0] == "normalize_audio":
                    first = "AAC" in self.config.get("smartmkvmerge", "first_audio_stream")
                    second = "AAC" in self.config.get("smartmkvmerge", "second_audio_stream")
                    if first or second:
                        self.data[1].set_sensitive(True)
                    else:
                        self.data[1].set_sensitive(False)

        else:
            self.config.set(self.category, self.option, widget.get_active_text())
