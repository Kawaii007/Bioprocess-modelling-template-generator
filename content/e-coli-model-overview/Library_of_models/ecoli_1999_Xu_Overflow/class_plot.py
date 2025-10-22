# import packages
from matplotlib import cm
from matplotlib import colors as mcolors
import numpy as np
from scipy.stats import norm
from plotly.subplots import make_subplots
import plotly.graph_objects as go
import plotly.io as pio
import plotly.offline
import plotly.express as px
from plotly.validators.scatter.marker import SymbolValidator
#import ecoli_sim_and_pe
import os
import sys
import math
import copy
from pathlib import Path
#import ecoli_sim_and_pe


class PlotPlotly:
    def __init__(self, allthedata, path, plot_info="", plot_mode="plotly_default", colorscheme="qualitative_plotly",
                 plot_formats=("html", "png")):
        """ Plots the measured and simulated data with plotly.

        :param allthedata: dict with all the measured and simulated data.
        :param path: path to folder where to save plots)
        :param plot_info: plot info for name of saved plots
        :param plot_mode: choose from "plotly_default", "white_w_grid" or "simple_white"
        :param colorscheme: choose from "qualitative_plotly", "qualitative_colorbrewer2", TU_colors, matlab_default or "uniform_viridis"
        :param plot_formats: file formats in which the output images are saved ("html", "png", "svg")
        """
        self.allthedata = allthedata
        self.path = path
        self.plot_info = plot_info
        self.colorscheme = colorscheme
        self.plot_mode = plot_mode
        self.plot_formats = plot_formats

        # Dict with info on which keys not to plot during simulation for which expID
        self.pass_during_simu = dict(dummy_expID=["dummy_key", "dummy_key_2"])

        # Set the area for the graph (excluding the labels) --> this helps to have same sized graphs
        self.domain = [0, 1]

        # Spacing between subplots
        self.vertical_spacing = 0.05

        # Define custom colors
        self.colors = None  #  if argument "list_keys" is used in _set_colors, a custom colors dict can be passed, e.g. dict(exp1 = "black", exp2 = "red")

        # Settings
        self.plot_width = 1000  # width of the plot
        self.plot_height_one_row = 225  # plot height if the plot has only one row
        self.plot_height_multiple_rows = 200  # plot height per row if the plot has multiple rows
        self.use_color_description = False  # whether to use the line color also for the description text ("Black" if False)

        # Data lines
        self.width_line_variables = 2  # width of line for variables (except DOT)
        self.width_marker_line = 1  # width of line for inputs
        self.style_line_dot = "dot"  # line style for DOT simulation
        self.width_line_dot = 1.5  # 0.5 # width of line or DOT data
        self.color_data = None  # color for measured data (if None, color varied by variable or expID)
        self.color_simu = None  # color for simulated data (if None, color varied by variable or expID)
        self.color_SE = None  # color for state estimation data (if None, color varied by variable or expID)
        self.linestyle_simu = "solid"
        self.linestyle_SE = "dash"

        self.if_plot_line_data = False  # if the measurement points are connected by lines

        # Data markers
        self.marker_size = 6  # size of marker for measurements
        self.marker_size_input = 6  # size of marker for input
        self.marker_color = None  # marker color (if None, data color; default if there are no replicates, else color of replicate)
        self.symbol_data = "circle"  # symbol of marker if vary_markers = False
        self.fixed_symbol_by_variable = False  # one symbol for each variable, fixed by inputs in symbol_data

        # Stem options
        self.thickness_stem = 2  # thickness of stems
        self.opacity_stem = 0.5  # opacity of the stem color

        # Titles + text
        self.show_text_vertical_lines = True  # whether to show the text for vertical lines (Feed/Induction)
        self.use_column_title = False  # whether to add a title to the plot columns
        self.x_title = 'Time [h]'

        # x_grid
        self.dtick_x = 5

        # y_grid
        self.n_ticks = None  # number of ticks (default: None)
        if self.n_ticks is None:
            self.at_least_y_grid_count = 4  # minimum number of y grid lines
        self.showticklabels = True  # show the tick labels for the y axis
        self.showticklabels_x = True  # show the tick labels for the x axis
        self.showticks = True  # show the ticks

    def _set_colors(self, n_colors=False, list_keys=False):

        if n_colors:
            n = n_colors
        elif list_keys:
            n = len(list_keys)
        else:
            sys.exit("Wrong input given to _setcolors.")

        self.accent_color = "Grey"

        if self.colorscheme == "matlab_default":
            matlab_colors = [
                '#0072BD',  # blue
                '#D95319',  # orange
                # '#EDB120',  # yellow
                '#7E2F8E',  # violet
                '#77AC30',  # green
                '#4DBEEE',  # light blue
                '#A2142F'  # bordeaux red
            ]
            colors = matlab_colors * math.ceil(n / len(matlab_colors))

        elif self.colorscheme == "rainbow":
            rainbow_colors = [
                '#ff0000',  # red
                '#ffa500',  # orange
                '#ffff00',  # yellow
                '#80ff00',  # chartreuse
                '#008000',  # green
                '#00ff80',  # spring green
                '#00ffff',  # cyan
                '#0080ff',  # dodger blue
                '#0000ff',  # blue
                '#8000ff',  # purple
                # '#4b0082',  # indigo
                '#ff00ff',  # violet
                '#ff0080'  # magenta
            ]
            colors = rainbow_colors * math.ceil(n / len(rainbow_colors))

        elif self.colorscheme == "TU_colors":
            TU_red = "rgba(204, 0, 0, 100)"
            TU_yellow = "rgba(255, 128, 0, 100)"
            TU_green = "rgba(34, 161, 92, 100)"
            TU_blue = "rgba(0, 166, 179, 100)"
            TU_colors = [TU_red, TU_yellow, TU_green, TU_blue]
            colors = TU_colors * math.ceil(n / len(TU_colors))

        elif self.colorscheme == "qualitative_colorbrewer2":
            colors = ["#8da0cb", "#66c2a5", "#e78ac3", "#a6d854", "#fc8d62", "#ffd92f"] * math.ceil(n / 6)

        elif self.colorscheme == "uniform_viridis":
            cmap_viridis = cm.get_cmap('viridis', n)
            colors = [mcolors.rgb2hex(cmap_viridis(i)) for i in range(cmap_viridis.N)]

        elif self.colorscheme == "two_toned":
            black = "#000000"
            grey = "#717171"
            darkgrey = "#293133"
            blue = "#0072BD"
            colors = dict(primary=darkgrey, secondary=blue)

        elif self.colorscheme == "mixed_colors":
            darkgrey = "#293133"
            blue = "#0072BD"
            TU_red = "rgba(204, 0, 0, 100)"
            grey = "#717171"
            lighterblue = "#34aeff"
            colorrrs = [blue, darkgrey, TU_red, lighterblue, grey]
            colors = colorrrs * math.ceil(n / len(colorrrs))

        else:
            colors = px.colors.qualitative.G10 * math.ceil(n / 10)  # self.colorscheme == "qualitative_plotly"

        if n_colors:
            self.colors = colors
        elif self.colorscheme == "two_toned":
            self.colors = colors
        elif list_keys:
            if self.colors is None:  # no custom colors dict passed
                colors_dict = dict.fromkeys(list_keys)
                for i, key in enumerate(list_keys):
                    colors_dict[key] = colors[i]
                self.colors = colors_dict

        # Add info
        if not "color_data" in self.colors.keys():
            self.colors["color_data"] = self.color_data
            self.colors["color_data_default"] = "black"
        if not "color_simu" in self.colors.keys():
            self.colors["color_simu"] = self.color_simu
            self.colors["color_simu_default"] = "grey"
        if not "color_SE" in self.colors.keys():
            self.colors["color_SE"] = self.color_SE
            self.colors["color_SE_default"] = "blue"
        self.colors["text_default"] = "black"

    @staticmethod
    def _set_color_html(color, text):
        return f"<span style='color:{str(color)}'> {str(text)} </span>"

    def _set_markers(self, bool, n=10):
        """

        :param bool: (True/False) if varied markers should be defined
        :param n: number of variables
        :return:
        """
        if bool:
            # define markers
            raw_symbols = SymbolValidator().values
            namestems = []
            namevariants = []
            symbols = []
            for i in range(0, len(raw_symbols), 3):
                name = raw_symbols[i + 2]
                symbols.append(raw_symbols[i])
                namestems.append(name.replace("-open", "").replace("-dot", ""))
                namevariants.append(name[len(namestems[-1]):])

            markers = list(dict.fromkeys(namestems))
            self.markers = [x+"-open" for x in markers] * math.ceil(n / len(markers))
            # self.markers = ['circle-open', 'square-open', 'diamond-open', 'triangle-up-open', 'triangle-down-open', 'triangle-left-open', 'triangle-right-open', 'pentagon-open']
        else:
            # set default
            self.markers = [self.symbol_data] * n

    def _get_feed_start(self, allthedata_expID):
        feed_start = False
        feed_vals = allthedata_expID["inputs"]["Feed"]["vals"]
        if np.size(np.where(feed_vals != 0)) != 0:
            feed_start = allthedata_expID["inputs"]["Feed"]["times"][np.where(feed_vals != 0)[0][0]]
        # TODO: Feed start for conti cultures with data from tables

        return feed_start

    def _add_vertical_lines(self, fig, expID, row, col=1, secondary_y=False, range=(0, 1),
                            type=("Induction", "Feed", "Sample_OD10", "Constant Feed"),
                            if_add_vertical_lines=True, rescale_time={}):

        if if_add_vertical_lines:
            # add line if constant feed is in the inputs
            if "Constant Feed" in self.allthedata[expID]["inputs"].keys() and "Constant Feed" in type:
                if self.allthedata[expID]["inputs"]["Constant Feed"]["times"].size != 0:
                    constant_feed_time = list(self.allthedata[expID]["inputs"]["Constant Feed"]["times"])
                    constant_feed_time_new = constant_feed_time
                    if not rescale_time == {}:
                        constant_feed_time_new = list(self._rescale_time_axis(constant_feed_time, rescale_time))

                    fig.add_shape(
                        go.layout.Shape(
                            type="line", yref="paper", xref="x",
                            x0=constant_feed_time_new[0],
                            x1=constant_feed_time_new[0],
                            y0=range[0], y1=range[1],
                            line=dict(color=self.accent_color, dash="dash", width=2),
                        ),
                        col=col, row=row
                    )

                    if row == 1 and not secondary_y and self.show_text_vertical_lines and not self.added_induction_title:
                        self.added_induction_title = True
                        fig.add_trace(
                            go.Scatter(
                                x=[constant_feed_time_new[0] - 1],  # adjust offset if needed
                                y=[range[1] * 0.9],
                                text=["Constant Feed: " + str(round(constant_feed_time[0], 2)) + " h"],
                                textfont=dict(color=self.accent_color),
                                mode="text", showlegend=False
                            ),
                            col=col, row=row
                        )

            # Add line for induction and feed start
            if "Induction" in self.allthedata[expID]["inputs"].keys() and "Induction" in type:
                if self.allthedata[expID]["inputs"]["Induction"]["times"].size != 0:
                    induction_time = list(self.allthedata[expID]["inputs"]["Induction"]["times"])
                    induction_time_new = induction_time
                    if not rescale_time == {}:
                        induction_time_new = list(self._rescale_time_axis(induction_time, rescale_time))

                    fig.add_shape(go.layout.Shape(type="line", yref="paper", xref="x",
                                                  x0=induction_time_new[0],
                                                  x1=induction_time_new[0],
                                                  y0=range[0], y1=range[1],
                                                  line=dict(color=self.accent_color, dash="longdashdot", width=2), ),
                                  col=col, row=row)

                    if row == 1 and not secondary_y and self.show_text_vertical_lines and not self.added_induction_title:
                        self.added_induction_title = True
                        fig.add_trace(go.Scatter(x=[induction_time_new[0] + 1],  #  - 1.6
                                                 y=[range[1] * 0.9],
                                                 text=["Induction: " + str(round(induction_time[0], 2)) + " h"],
                                                 textfont=dict(color=self.accent_color),
                                                 mode="text", showlegend=False),
                                      col=col, row=row)

            if "Feed" in self.allthedata[expID]["inputs"].keys() and "Feed" in type:
                feed_start = list([self._get_feed_start(self.allthedata[expID])])
                feed_start_new = feed_start
                if not rescale_time == {}:
                    feed_start_new = list(self._rescale_time_axis(feed_start, rescale_time))

                if feed_start:
                    if self.allthedata[expID]["inputs"]["Feed"]["times"].size != 0:
                        fig.add_shape(go.layout.Shape(type="line", yref="paper", xref="x",
                                                      x0=feed_start_new[0], x1=feed_start_new[0],
                                                      y0=range[0], y1=range[1],
                                                      line=dict(color=self.accent_color, dash="dash", width=2), ),
                                      col=col, row=row)

                        if row == 1 and not secondary_y and self.show_text_vertical_lines and not self.added_feed_title:
                            self.added_feed_title = True
                            fig.add_trace(go.Scatter(x=[feed_start_new[0] + 1.5],  #  - 1.6
                                                     y=[range[1] * 0.9],
                                                     text=["Feed start: " + str(round(feed_start[0], 2)) + "h "],
                                                     textfont=dict(color=self.accent_color),
                                                     mode="text", showlegend=False),
                                          col=col, row=row)

            if "Sample_OD10" in self.allthedata[expID]["inputs"].keys() and "Sample_OD10" in type:
                if self.allthedata[expID]["inputs"]["Sample_OD10"]["times"].size != 0:
                    for key in self.allthedata[expID]["inputs"]["Sample_OD10"]["times"][0].keys():
                        fig.add_shape(go.layout.Shape(type="line", yref="paper", xref="x",
                                                      x0=self.allthedata[expID]["inputs"]["Sample_OD10"]["times"][0][key],
                                                      x1=self.allthedata[expID]["inputs"]["Sample_OD10"]["times"][0][key],
                                                      y0=range[0], y1=range[1],
                                                      line=dict(color=self.accent_color, dash="dashdot", width=0.5), ),
                                      col=col, row=row)

                        if row == 1 and not secondary_y and self.show_text_vertical_lines:
                            fig.add_trace(go.Scatter(x=[self.allthedata[expID]["inputs"]["Sample_OD10"]["times"][0][key]],
                                                     y=[range[1] * 0.1],
                                                     text=[key], textfont=dict(color=self.accent_color),
                                                     mode="text", showlegend=False),
                                          col=col, row=row)

        return fig

    def _update_layout(self, fig, plot_height=1000, plot_width=1000, show_legend=False,
                       hovermode=None):
        """
        Currently only used by plot_by_expID
        """

        fig.update_layout(height=plot_height, width=plot_width,
                          showlegend=show_legend,
                          legend=dict(x=1, y=1, borderwidth=0, orientation="v", xanchor="left",
                                      yanchor="top", traceorder="grouped"))
        # , groupclick="toggleitem"))

        axis_title_size = 16

        fig.update_yaxes(title=dict(font=dict(size=axis_title_size)), tickfont=dict(size=14),
                         ticks="outside" if self.showticks else "", tickwidth=2)
        fig.update_xaxes(title=dict(font=dict(size=axis_title_size)), tick0=0, tickfont={"size": 14},
                         ticks="outside" if self.showticks else "", tickwidth=2, showticklabels=self.showticklabels_x,
                         domain=self.domain)

        # Set plot scheme
        if self.plot_mode == "plotly_default":
            plot_bgcolor = None
            showgrid_y = True
            showgrid_x = False

            fig.update_layout(plot_bgcolor=plot_bgcolor)
            fig.update_yaxes(showgrid=showgrid_y)
            fig.update_xaxes(nticks=10, dtick=self.dtick_x, showgrid=showgrid_x)

        if self.plot_mode == "white_w_grid":
            plot_bgcolor = 'rgba(0,0,0,0)'  # default: None
            showgrid_y = True
            showgrid_x = False
            gridcolor = "LightGrey"
            zerolinecolor = "LightGrey"

            fig.update_layout(plot_bgcolor=plot_bgcolor)
            fig.update_yaxes(nticks=self.n_ticks if self.n_ticks is not None else 10, showgrid=showgrid_y, gridcolor=gridcolor, zerolinecolor=zerolinecolor)
            fig.update_xaxes(nticks=10, dtick=self.dtick_x, showgrid=showgrid_x, gridcolor=gridcolor, zerolinecolor=zerolinecolor)

        if self.plot_mode == "white_wo_grid":
            plot_bgcolor = 'rgba(0,0,0,0)'  # default: None
            showgrid_y = False
            showgrid_x = False
            gridcolor = "LightGrey"
            zerolinecolor = "LightGrey"

            fig.update_layout(plot_bgcolor=plot_bgcolor)
            fig.update_yaxes(nticks=self.n_ticks if self.n_ticks is not None else 10, showgrid=showgrid_y,
                             gridcolor=gridcolor, zerolinecolor=zerolinecolor)
            fig.update_xaxes(nticks=10, dtick=self.dtick_x, showgrid=showgrid_x, gridcolor=gridcolor, zerolinecolor=zerolinecolor)

        if self.plot_mode == "simple_white":
            fig.update_layout(template="simple_white")
            fig.update_yaxes(nticks=self.n_ticks if self.n_ticks is not None else 10)
            fig.update_xaxes(nticks=10, dtick=self.dtick_x)

        if hovermode:
            fig.update_layout(hovermode=hovermode)

        # decrease margin around fig
        fig.update_layout(margin=dict(
            l=0,  # left margin
            r=0,  # right margin
            b=70,  # bottom margin
            t=40  # top margin
        )
        )

        return fig

    @staticmethod
    def convert_rgba_to_rgb(rgba, background_color=(255, 255, 255)):
        r_source, g_source, b_source, a_source = rgba
        r_bg, g_bg, b_bg = background_color

        r_target = ((1 - a_source) * r_bg) + (a_source * r_source)
        g_target = ((1 - a_source) * g_bg) + (a_source * g_source)
        b_target = ((1 - a_source) * b_bg) + (a_source * b_source)

        return f"rgb({r_target}, {g_target}, {b_target})"

    def _get_color_stem(self, color_pure):
        # "Add" opacity to pure color -> less bright color as result
        rgba_stem = plotly.colors.hex_to_rgb(color_pure) + (self.opacity_stem,)
        #ecoli_sim_and_pe.
        color_stem = self.convert_rgba_to_rgb(rgba=rgba_stem)

        return color_stem

    def _init_fig(self, expID, plot_multiple_list, split_at_feed_start,
                  replicates=[], plot_replicates=False, plot_title=None, vary_marker=True,
                  plot_sim_data=False, plot_SE_data=False):

        self.added_induction_title = False
        self.added_feed_title = False

        # Select variables and inputs
        variables_plot_all = [key for key in self.allthedata[expID]["variables"].keys()
                              if self.allthedata[expID]["variables"][key]["plotting"]["plot"]]
        inputs_plot_all = [key for key in self.allthedata[expID]["inputs"].keys() if
                           self.allthedata[expID]["inputs"][key]["plotting"]["plot"]]

        # Set colors
        if plot_replicates:
            if self.colorscheme == "two_toned":
                raise ValueError("If plot_replicates is True, colorscheme cannot be two_toned.")
            n = len(replicates)
            self._set_colors(list_keys=replicates)
        else:
            n = len(variables_plot_all + inputs_plot_all)
            self._set_colors(list_keys=variables_plot_all + inputs_plot_all)

        self._set_markers(bool=vary_marker, n=n)

        # Select states with data
        variables_plot = []
        for key in variables_plot_all:
            if len(self.allthedata[expID]["variables"][key]["times"]) != 0:
                variables_plot.append(key)
            if len(self.allthedata[expID]["simulation_data"]["vals"]) != 0:
                if key in self.allthedata[expID]["simulation_data"]["vals"].keys():
                    if len(self.allthedata[expID]["simulation_data"]["vals"][key]) > 1 and key not in variables_plot:
                        variables_plot.append(key)
            if "simulation_data (SE)" in self.allthedata[expID].keys():
                if len(self.allthedata[expID]["simulation_data (SE)"]["vals"][key]) > 1 and key not in variables_plot:
                    variables_plot.append(key)

        inputs_plot = [key for key in inputs_plot_all if len(self.allthedata[expID]["inputs"][key]["times"]) != 0]

        if len(plot_multiple_list) != 0:
            # Check which entries of plot_multiple are in variables_plot
            # Remove entries which are not in variables_plot or inputs_plot
            for i, e in enumerate(plot_multiple_list):
                for im, em in enumerate(plot_multiple_list[i]["members"]):
                    con_not_include_1 = (em not in variables_plot + inputs_plot)
                    con_not_include_2 = (split_at_feed_start and plot_multiple_list[i]["axes"][im] == "right")
                    if con_not_include_1 or con_not_include_2:
                        if not con_not_include_1 and con_not_include_2:
                            print(f"Attention! With split_at_feed_start=True, it is not possible to plot variables on "
                                  f"the right axis. The variable {em} is plotted in a new subplot.")
                        if con_not_include_1:
                            print(f"Attention! For {em} ['plotting']['plot'] is not set to True or there is no data.")
                        plot_multiple_list[i]["members"].pop(im)
                        plot_multiple_list[i]["axes"].pop(im)
            # remove group if empty or with only one entry
            plot_multiple_list = [group for group in plot_multiple_list if len(group["members"]) > 1]

        # collect all descriptions
        descriptions_all = dict()
        for entry in variables_plot:
            descriptions_all[entry] = self.allthedata[expID]["variables"][entry]["description"]
        for entry in inputs_plot:
            descriptions_all[entry] = self.allthedata[expID]["inputs"][entry]["description"]

        for i, group in enumerate(plot_multiple_list):
            plot_multiple_list[i].update(row_plot=False)  # initiate saving of plot position

        # Init plot info dict
        plot_info = dict.fromkeys(variables_plot + inputs_plot)

        # Update plot_info dict
        plot_index = 0
        for i, key in enumerate(plot_info.keys()):
            # print(f"{i} - {key}, plot_index: {plot_index}")
            if key in variables_plot:
                state_type = "variables"
                marker_size = self.marker_size
            else:
                state_type = "inputs"
                marker_size = self.marker_size_input

            secondary_y = False
            opacity = dict(meas=0.9, simu=0.8)

            # Check if stem plot
            if_stem = False
            if "stem" in self.allthedata[expID][state_type][key]["plotting"].keys() and \
                    self.allthedata[expID][state_type][key]["plotting"]["stem"]:
                if_stem = True
                opacity["meas"] = self.opacity_stem

            # Choose color for data
            if not self.colorscheme == "two_toned":
                    if plot_replicates:
                        color_data = self.colors["color_data_default"]
                        color_SE = self.colors["color_SE_default"]
                        color_simu = self.colors["color_simu_default"]
                    else:
                        if state_type == "inputs":
                            color_data = self.colors[key]
                        else:
                            color_data = self.colors[key] if self.colors["color_data"] is None else self.colors["color_data"]

                        if plot_sim_data and plot_SE_data:  # state estimation and simulation
                            color_simu = self.colors["color_simu"] if self.colors["color_simu"] is not None else self.colors["color_simu_default"]
                            color_SE = self.colors[key] if self.colors["color_SE"] is None else self.colors["color_SE"]
                        else:
                            color_simu = self.colors[key]
                            color_SE = self.colors[key]

            if key in self._flatten([group["members"] for group in plot_multiple_list]):
                # Get location of key in plot_multiple
                (entry, position) = self._find_in_list_of_list([group["members"] for group in plot_multiple_list], key)
                if plot_multiple_list[entry]["axes"][position] == "right": secondary_y = True

                # Overwrite color_data for specific colorscheme
                if self.colorscheme == "two_toned":
                    if secondary_y:
                        opacity = dict(meas=0.8, simu=0.8)
                        color_data = color_simu = color_SE = self.colors["secondary"]
                    else:
                        color_data = color_simu = color_SE = self.colors["primary"]

                # Get plot description
                plot_description = ""
                for ie, var in enumerate(plot_multiple_list[entry]["members"]):
                    if plot_multiple_list[entry]["axes"][ie] == plot_multiple_list[entry]["axes"][position]:
                        color_text = "black"  # set default
                        if not plot_replicates:
                            if self.use_color_description:
                                if self.colorscheme == "two_toned":
                                    if plot_multiple_list[entry]["axes"][position] == "right":
                                        color_text = self.colors["secondary"]
                                    else:
                                        color_text = self.colors["primary"]
                                else:
                                    color_text = self.colors[var]
                        if var in descriptions_all.keys():
                            plot_description += f"<br />{self._set_color_html(color=color_text, text=descriptions_all[var])}"

                plot_description = plot_description[6::]  # Remove first \n

                # If first variable to plot from plot multiple, this defines the location in the plot
                if plot_multiple_list[entry]["row_plot"] is False:
                    plot_multiple_list[entry]["row_plot"] = plot_index
                    plot_index += 1  # Add one to subplot counter

                # Define look of plot
                dash = self.linestyle_simu
                if position == 0:
                    if key == "Feed":
                        dash = "solid"
                else:
                    if key == "Feed":
                        dash = "dash"

                # Add one to the index to obtain the row in the plot (starts with 1, not 0)
                row_plot = plot_multiple_list[entry]["row_plot"] + 1
            else:
                # Overwrite color_data for specific colorscheme
                if self.colorscheme == "two_toned":
                    if secondary_y:
                        opacity = dict(meas=0.8, simu=0.8)
                        color_data = color_simu = color_SE = self.colors["secondary"]
                    else:
                        color_data = color_simu = color_SE = self.colors["primary"]

                if not plot_replicates:
                    color_text = self.colors[key]
                else:
                    color_text = self.colors["text_default"]

                plot_description = self._set_color_html(color=color_text, text=descriptions_all[key])
                row_plot = plot_index + 1
                plot_index += 1  # Add one to subplot counter
                dash = self.linestyle_simu

            # Line style
            if "DOT" in key:
                width = self.width_line_dot
            else:
                width = self.width_line_variables

            # Define error settings
            if key == "Biomass_NH3":
                color_error = None
                opacity["error"] = 0.3
            else:
                color_error = "#444"
                opacity["error"] = 0.2

            # Plot mode for measurements
            dash_data = dash

            if key in ["DOTm", "pH"]:
                if not len(self.allthedata[expID][state_type][key]["vals"]) == 1:
                    plot_mode_meas = "lines"
                    width_marker_line = self.width_marker_line
                    dash_data = self.style_line_dot
                else:
                    plot_mode_meas = "markers"
            elif "Feed" in key and not if_stem:
                if not len(self.allthedata[expID][state_type][key]["vals"]) == 1:
                    plot_mode_meas = "lines"
                    width_marker_line = self.width_marker_line
                else:
                    plot_mode_meas = "markers"
            elif state_type == "inputs" and "rate" in key:
                if not len(self.allthedata[expID][state_type][key]["vals"]) == 1:
                    plot_mode_meas = "lines"
                else:
                    plot_mode_meas = "markers"
            elif if_stem:
                plot_mode_meas = "markers"
            else:
                width_marker_line = self.width_marker_line
                if self.if_plot_line_data:
                    plot_mode_meas = "lines+markers"
                else:
                    plot_mode_meas = "markers"

            if vary_marker:
                marker_symbol = self.markers[i]
            else:
                if isinstance(self.symbol_data, dict) and self.fixed_symbol_by_variable:
                    marker_symbol = self.symbol_data[key]
                else:
                    marker_symbol = self.symbol_data

            # Collect plot info
            plot_info[key] = dict(description=plot_description,
                                  row_plot=row_plot,
                                  # if plot_replicates, colors get overwritten anyways
                                  color=dict(data=color_data, simu=color_simu, SE=color_SE, error=color_error,
                                             marker=self.marker_color if self.marker_color is not None else color_data,
                                             text=color_data if self.use_color_description and
                                                                not plot_replicates else "black"),
                                  opacity=opacity,
                                  secondary_y=secondary_y,
                                  range=self.allthedata[expID][state_type][key]["plotting"]["range"],
                                  stem=if_stem,
                                  linestyle=dict(dash=dash, dash_SE=self.linestyle_SE, dash_data=dash_data,
                                                 width=width, width_marker_line=width_marker_line,
                                                 marker_size=marker_size, marker_symbol=marker_symbol),
                                  plot_mode=dict(simu="lines", meas=plot_mode_meas))

            if split_at_feed_start:
                plot_info[key].update(range_fedbatch=self.allthedata[expID][state_type][key]["plotting"]["range_fedbatch"])

        # Init dict to save ranges for each plot later on
        n_plot = max([plot_info[key]["row_plot"] for key in plot_info.keys()])  # number of plots (starting from 1)

        self.ranges_by_plot_no = dict.fromkeys(range(1, n_plot + 1))
        for n in self.ranges_by_plot_no:
            # init dict for storing ranges
            self.ranges_by_plot_no[n] = dict(
                left=dict(x_max=None, y_min=None, y_max=None, y_min_fedbatch=None, y_max_fedbatch=None),
                right=dict(x_max=None, y_min=None, y_max=None, y_min_fedbatch=None, y_max_fedbatch=None))

        # Update specs
        secondary_y_list = [False] * n_plot
        for key in plot_info.keys():
            if plot_info[key]["secondary_y"]:
                secondary_y_list[plot_info[key]["row_plot"] - 1] = True

        # Set plot size layout
        if n_plot == 1:
            self.plot_height = self.plot_height_one_row
        else:
            self.plot_height = self.plot_height_multiple_rows * n_plot

        # Create subplots with shared x-axis
        if self.use_column_title and not split_at_feed_start:
            if plot_title != None:
                column_title = [plot_title]
            else:
                column_title = ["experiment ID = " + str(expID)]
        else:
            column_title = False

        if split_at_feed_start:
            fig = make_subplots(rows=n_plot, cols=2, shared_xaxes=True,
                                vertical_spacing=self.vertical_spacing, x_title=self.x_title,
                                specs=[[dict(secondary_y=entry), dict(secondary_y=entry)] for entry in
                                       secondary_y_list],
                                column_widths=[0.15, 0.85], horizontal_spacing=0.02,
                                subplot_titles=('Batch', 'Fed-batch'), column_titles=column_title)

            fig.update_annotations(font=dict(color=self.accent_color, size=18))  # size=20,
        else:
            fig = make_subplots(rows=n_plot, cols=1, shared_xaxes=True, shared_yaxes=True,
                                vertical_spacing=self.vertical_spacing, x_title=self.x_title,
                                specs=[[dict(secondary_y=entry)] for entry in secondary_y_list],
                                column_titles=column_title)

        return fig, n_plot, variables_plot, inputs_plot, plot_info

    def _flatten(self, nested_list):
        l = [item for sublist in nested_list for item in sublist]

        return l

    def _find_in_list_of_list(self, nested_list, char):
        for sub_list in nested_list:
            if char in sub_list:
                return (nested_list.index(sub_list), sub_list.index(char))
        raise ValueError("'{char}' is not in list".format(char=char))

    def _check_min_max(self, arr, min_val=None, max_val=None):
        """ Update y_min and y_max.
        :param arr:
        :param y_min: (float) current y_min
        :param y_max: (float) current y_max
        """
        # Convert to array
        arr = np.array(arr)

        # Delete None
        arr = arr[arr != np.array(None)]

        if len(arr) != 0:
            if min_val is not None:
                if min(arr) < min_val:
                    min_val = min(arr)
            else:
                min_val = min(arr)
            if max_val is not None:
                if max(arr) > max_val:
                    max_val = max(arr)
            else:
                max_val = max(arr)

        return min_val, max_val

    def _get_range(self, ranges, t_range_end, key, split_at_feed_start, plot_info):
        """

        :param ranges:
        :param t_range_end:
        :param key:
        :param split_at_feed_start:
        :param plot_info:
        :return:
        """

        # Set default values
        y_min_default = 0
        y_max_default = 0.1
        x_max_default = 3

        plot_info_copy = copy.deepcopy(plot_info)  # make copy to not overwrite

        # If the range is joined
        if split_at_feed_start:
            if not plot_info_copy[key]["range_fedbatch"] and isinstance(plot_info_copy[key]["range"], (bool, list)):
                y_min, _ = self._check_min_max(arr=[ranges[key]["y_min"]], min_val=ranges[key]["y_min_fedbatch"])
                _, y_max = self._check_min_max(arr=[ranges[key]["y_max"]], max_val=ranges[key]["y_max_fedbatch"])

                ranges[key]["y_min"] = ranges[key]["y_min_fedbatch"] = y_min
                ranges[key]["y_max"] = ranges[key]["y_max_fedbatch"] = y_max

        # Update entry for plot
        row_plot = plot_info[key]["row_plot"]
        side = "right" if plot_info[key]["secondary_y"] else "left"

        # Update x_max
        if self.ranges_by_plot_no[row_plot][side]["x_max"]:
            _, self.ranges_by_plot_no[row_plot][side]["x_max"] = self._check_min_max(
                arr=[ranges[key]["x_max"]], max_val=self.ranges_by_plot_no[row_plot][side]["x_max"])
        elif ranges[key]["x_max"]:
            self.ranges_by_plot_no[row_plot][side]["x_max"] = ranges[key]["x_max"]
        else:
            self.ranges_by_plot_no[row_plot][side]["x_max"] = x_max_default

        # Update y_min and y_max
        if self.ranges_by_plot_no[row_plot][side]["y_min"]:
            self.ranges_by_plot_no[row_plot][side]["y_min"], _ = self._check_min_max(
                arr=[ranges[key]["y_min"]], min_val=self.ranges_by_plot_no[row_plot][side]["y_min"])
        elif ranges[key]["y_min"] is not None:
            self.ranges_by_plot_no[row_plot][side]["y_min"] = ranges[key]["y_min"]
        else:
            self.ranges_by_plot_no[row_plot][side]["y_min"] = y_min_default

        if self.ranges_by_plot_no[row_plot][side]["y_max"]:
            _, self.ranges_by_plot_no[row_plot][side]["y_max"] = self._check_min_max(
                arr=[ranges[key]["y_max"]], max_val=self.ranges_by_plot_no[row_plot][side]["y_max"])
        elif ranges[key]["y_max"] is not None:
            self.ranges_by_plot_no[row_plot][side]["y_max"] = ranges[key]["y_max"]
        else:
            self.ranges_by_plot_no[row_plot][side]["y_max"] = y_max_default

        if split_at_feed_start:
            if self.ranges_by_plot_no[row_plot][side]["y_min_fedbatch"]:
                self.ranges_by_plot_no[row_plot][side]["y_min_fedbatch"], _ = self._check_min_max(
                    arr=[ranges[key]["y_min_fedbatch"]], min_val=self.ranges_by_plot_no[row_plot][side]["y_min_fedbatch"])
            elif ranges[key]["y_min_fedbatch"] is not None:
                self.ranges_by_plot_no[row_plot][side]["y_min_fedbatch"] = ranges[key]["y_min_fedbatch"]
            else:
                self.ranges_by_plot_no[row_plot][side]["y_min_fedbatch"] = y_min_default

            if self.ranges_by_plot_no[row_plot][side]["y_max_fedbatch"]:
                _, self.ranges_by_plot_no[row_plot][side]["y_max_fedbatch"] = self._check_min_max(
                    arr=[ranges[key]["y_max_fedbatch"]], max_val=self.ranges_by_plot_no[row_plot][side]["y_max_fedbatch"])
            elif ranges[key]["y_max_fedbatch"] is not None:
                self.ranges_by_plot_no[row_plot][side]["y_max_fedbatch"] = ranges[key]["y_max_fedbatch"]
            else:
                self.ranges_by_plot_no[row_plot][side]["y_max_fedbatch"] = y_max_default

        # Adapt under special conditions
        if float(self.ranges_by_plot_no[row_plot][side]["y_min"]) == float(self.ranges_by_plot_no[row_plot][side]["y_max"]):
            if not plot_info[key]["stem"]:
                val_range = float(self.ranges_by_plot_no[row_plot][side]["y_min"])
                self.ranges_by_plot_no[row_plot][side]["y_min"] = val_range - 0.1 * val_range
                self.ranges_by_plot_no[row_plot][side]["y_max"] = val_range + 0.1 * val_range
            else:
                self.ranges_by_plot_no[row_plot][side]["y_min"] = 0

        # Updated figure style properties
        if self.ranges_by_plot_no[row_plot][side]["x_max"] < 1:
            t_max = np.ceil(self.ranges_by_plot_no[row_plot][side]["x_max"] * 100) / 100
        else:
            t_max = self.ranges_by_plot_no[row_plot][side]["x_max"] * 1.05

        # Update range_end
        if t_max > t_range_end:
            t_range_end = t_max

        if plot_info_copy[key]["range"]:
            y_range = plot_info_copy[key]["range"]
            if y_range[0] == np.inf:
                y_range[0] = self.ranges_by_plot_no[row_plot][side]["y_min"] * 1.05
            if y_range[1] == np.inf:
                y_range[1] = self.ranges_by_plot_no[row_plot][side]["y_max"] * 1.05

        else:
            y_range = (self.ranges_by_plot_no[row_plot][side]["y_min"] * 0.95,
                       self.ranges_by_plot_no[row_plot][side]["y_max"] * 1.05)

        y_range_fedbatch = None
        if split_at_feed_start:
            y_range_fedbatch = y_range
            if plot_info_copy[key]["range_fedbatch"]:
                if isinstance(plot_info_copy[key]["range_fedbatch"], bool):
                    # If "True", the value is adapted for the fed-batch
                    y_range_fedbatch = (self.ranges_by_plot_no[row_plot][side]["y_min_fedbatch"] * 1.05,
                                        self.ranges_by_plot_no[row_plot][side]["y_max_fedbatch"] * 1.05)
                elif isinstance(plot_info_copy[key]["range_fedbatch"], list):
                    y_range_fedbatch = plot_info_copy[key]["range_fedbatch"]
                if y_range_fedbatch[0] == np.inf:
                    y_range_fedbatch[0] = self.ranges_by_plot_no[row_plot][side]["y_min_fedbatch"] * 1.05
                if y_range_fedbatch[1] == np.inf:
                    y_range_fedbatch[1] = self.ranges_by_plot_no[row_plot][side]["y_min_fedbatch"] * 1.05

        # default step calculation with at least 4 y-grids
        y_step = None
        y_step_fedbatch = None

        if self.n_ticks is None:
            try:
                y_step = y_range[2]
                if split_at_feed_start:
                    y_step_fedbatch = y_step
            except IndexError:  # IndexError: tuple index out of range (because there are only two entries)
                y_step = int((y_range[1] - y_range[0]) / self.at_least_y_grid_count)
                n = 0
                while y_step < 1:
                    n += 1
                    y_step = int((y_range[1] * 10 ** n - y_range[0] * 10 ** n) / self.at_least_y_grid_count)
                y_step = y_step / 10 ** n

                if split_at_feed_start:
                    y_step_fedbatch = int((y_range_fedbatch[1] - y_range_fedbatch[0]) / self.at_least_y_grid_count)
                    n = 0
                    while y_step_fedbatch < 1:
                        n += 1
                        y_step_fedbatch = int((y_range_fedbatch[1] * 10 ** n - y_range_fedbatch[
                            0] * 10 ** n) / self.at_least_y_grid_count)
                    y_step_fedbatch = y_step_fedbatch / 10 ** n

        return t_range_end, y_range[0:2], y_range_fedbatch, y_step, y_step_fedbatch

    def plot_by_expID(self, plot_replicates=False, plot_biomass_log=False, show_legend=False,
                      plot_sim_data=True,
                      plot_SE_data=False, plot_DOT_actual=False, plot_X_NH3_in_X=False, plot_multiple_list=(),
                      range_end=None, NRMSE=None, k_P=None, k_Q=None, k_R=None, Q_auto=None, filter=None,
                      split_at_feed_start=False,
                      add_vertical_lines=True, use_group_names=False, plot_title=None, vary_markers=True,
                      rescale_time={}, x_tick_interval=2):
        """ Function to plot the data by experiment ID.

        :param plot_replicates: plot all experiments as replicates in one figure (bool)
        :param plot_biomass_log:
        :param show_legend: (bool) show the plot legend
        :param plot_sim_data: (bool) plot the simulated data (cannot be true when plot_SE_data is true)
        :param plot_SE_data: (bool) plot the state estimation data (cannot be true when plot_sim_data is true)
        :param plot_DOT_actual: (bool) plot the actual DOT (not just the measured)
        :param plot_X_NH3_in_X: (bool) plot X_NH3 in the biomass plot
        :param plot_multiple_list: (list) list of dicts of variables to be plotted together in one plot, e.g., [dict(members=["m1", "m2", "m3", axes=["left", "left", "right"]
        :param range_end: (float) optionally pass an end value for x range
        :param NRMSE:
        :param k_P: input for state estimation
        :param k_Q: input for state estimation
        :param k_R: input for state estimation
        :param Q_auto: input for state estimation
        :param filter:  input for state estimation
        :param split_at_feed_start: (bool) split the plot at the start of feeding into two columns
        :param add_vertical_lines: (bool) add vertical lines at feed start and induction
        :param use_group_names: (bool) Every expID with the same 'Group_name' is grouped for toggling data series. Uses the key 'Group_name' in allthedata[expID]['Group_name'] you have to update for being able to toggle data via the legend.
        :param plot_title: (string) headline of your plot is given by this
        :param vary_markers: (bool) whether or not to vary the marker style for each variable/replicate
        :return:
        """

        if plot_replicates and split_at_feed_start:
            split_at_feed_start = False
            raise AttributeError("If plot_replicates = True, split_at_feed_start must be False.")

        if plot_replicates:
            expID = list(self.allthedata.keys())[0]

            fig, len_plots, variables_plot, inputs_plot, plot_info = \
                self._init_fig(expID=expID, plot_multiple_list=plot_multiple_list,
                               split_at_feed_start=split_at_feed_start, replicates=self.allthedata.keys(),
                               plot_replicates=plot_replicates, plot_title=plot_title, vary_marker=vary_markers,
                               plot_sim_data=plot_sim_data, plot_SE_data=plot_SE_data)

        # Loop over all keys
        seen_labels = set()  # Init for storing labels which have already been added

        for ix, expID in enumerate(self.allthedata.keys()):
            if split_at_feed_start:
                feed_start = self._get_feed_start(self.allthedata[expID])
                if not feed_start:
                    split_at_feed_start = False
                elif not rescale_time == {}:
                    feed_start = list(self._rescale_time_axis(feed_start, rescale_time))

            if range_end is None:
                range_end = self.allthedata[expID]["duration"]

            if not plot_replicates:
                ix = 0

                fig, len_plots, variables_plot, inputs_plot, plot_info = \
                    self._init_fig(expID=expID,
                                   plot_multiple_list=copy.deepcopy(plot_multiple_list),
                                   split_at_feed_start=split_at_feed_start, replicates=self.allthedata.keys(),
                                   plot_replicates=plot_replicates, plot_title=plot_title, vary_marker=vary_markers,
                                   plot_sim_data=plot_sim_data, plot_SE_data=plot_SE_data)

            if 'Biomass' in variables_plot and plot_biomass_log:  # create a second biomass plot
                variables_plot.insert(1, 'Biomass_log')

            # Init ranges dict per variable
            ranges = dict.fromkeys(variables_plot + inputs_plot)
            for key in ranges.keys():
                ranges[key] = dict(x_max=None, y_min=None, y_max=None)

                if split_at_feed_start:
                    ranges[key].update(y_min_fedbatch=None, y_max_fedbatch=None)

            # %% VARIABLES
            for index, key in enumerate(variables_plot):

                axes_type = 'linear'
                if key == 'Biomass_log':
                    key = 'Biomass'
                    axes_type = 'log'

                # same name in legend for every variable/input and showing only first entry in plot instead of all (ugly)
                if plot_replicates:
                    # Assign Legend to the correct Group handling
                    if use_group_names:
                        legend_group = f"<b>{self.allthedata[expID]['Group_name']}</b>"
                        name = f"Reactor_{expID}"
                    else:
                        legend_group = "<b>Legend</b>"
                        name = self.allthedata[expID]['description']
                    # only first entry
                    # show_legend = False
                    if index > 0:
                        show_legend = False
                    else:
                        show_legend = True
                else:
                    name = self.allthedata[expID]["variables"][key]["description"]
                    legend_group = "<b>Legend</b>"

                # Check if label is in legend
                show_legend = False if name in seen_labels else show_legend
                seen_labels.add(name)  # Add description to seen_labels

                # %% Plot simulated data
                # Get simulated / SE data
                for i, entry in enumerate([plot_sim_data, plot_SE_data]):
                    if expID in self.pass_during_simu.keys() and key in self.pass_during_simu[key]:
                        pass
                    else:
                        if entry:
                            if plot_sim_data and plot_SE_data and i == 0 and "_SE" in key:
                                pass  # Do not plot params_SE (or similar) if currently i=0 (plot_sim_data)
                            elif plot_sim_data and plot_SE_data and i == 0 and key == "Biomass_NH3":
                                pass  # Do not plot simulated data if currently i=0 (plot_sim_data) and "Biomass_NH3" (should be nearly the same as SE data)
                            else:
                                if plot_sim_data and plot_SE_data and i == 0 or plot_sim_data and i == 0:  # currently simulation
                                    color_simu = plot_info[key]["color"]["simu"] if not plot_replicates else self.colors[expID]
                                    dash = plot_info[key]["linestyle"]["dash"]
                                else:
                                    color_simu = plot_info[key]["color"]["SE"] if not plot_replicates else self.colors[expID]
                                    dash = plot_info[key]["linestyle"]["dash_SE"]

                                # Get data and errors
                                y_sim_err = np.array([])
                                y_sim = np.array([])
                                if i == 1:
                                    sim_data = self.allthedata[expID]["simulation_data (SE)"]
                                    if sim_data["std_dev"][key] is not None:
                                        y_sim_err = sim_data["std_dev"][key]
                                    if key == "Biomass_NH3":
                                        if "std_dev_NH3" in sim_data.keys():
                                            if len(sim_data["std_dev_NH3"]) != 0:
                                                y_sim_err = sim_data["std_dev_NH3"]
                                else:
                                    sim_data = self.allthedata[expID]["simulation_data"]

                                x_sim = sim_data["times"]
                                if not rescale_time == {}:
                                    x_sim = self._rescale_time_axis(x_sim,rescale_time)

                                if len(sim_data["vals"]) != 0:
                                    if key in sim_data["vals"].keys():
                                        y_sim = sim_data["vals"][key]

                                if split_at_feed_start:
                                    x_sim_fedbatch = np.array([])
                                    y_sim_fedbatch = np.array([])
                                    y_sim_err_fedbatch = np.array([])

                                    if any(y_sim):
                                        index_sim_feed_start = np.where(x_sim >= feed_start)[0][0]

                                        x_sim, x_sim_fedbatch = np.split(x_sim, [index_sim_feed_start])
                                        y_sim, y_sim_fedbatch = np.split(y_sim, [index_sim_feed_start])
                                        if plot_SE_data:
                                            if any(y_sim_err):
                                                y_sim_err, y_sim_err_fedbatch = np.split(y_sim_err,
                                                                                         [index_sim_feed_start])

                                if any(x_sim):  # If there is simulation data
                                    # Update ranges
                                    # Update x_max
                                    _, ranges[key]["x_max"] = self._check_min_max(arr=x_sim, max_val=ranges[key]["x_max"])

                                    # Update y_min and y_max
                                    if len(y_sim) == len(y_sim_err):
                                        arr = np.concatenate((np.array(y_sim) + np.array(y_sim_err),
                                                              np.array(y_sim) - np.array(y_sim_err)))
                                    else:
                                        arr = y_sim
                                    ranges[key]["y_min"], ranges[key]["y_max"] = \
                                        self._check_min_max(arr=arr, min_val=ranges[key]["y_min"],
                                                            max_val=ranges[key]["y_max"])

                                    if split_at_feed_start:
                                        if any(x_sim_fedbatch):
                                            # Update x_max
                                            _, ranges[key]["x_max"] = \
                                                self._check_min_max(arr=x_sim_fedbatch, max_val=ranges[key]["x_max"])

                                            # Update y_min and y_max
                                            if len(y_sim_fedbatch) == len(y_sim_err_fedbatch):
                                                arr = np.concatenate((y_sim_fedbatch + y_sim_err_fedbatch,
                                                                      y_sim_fedbatch - y_sim_err_fedbatch))
                                            else:
                                                arr = y_sim_fedbatch
                                            ranges[key]["y_min_fedbatch"], ranges[key]["y_max_fedbatch"] = \
                                                self._check_min_max(arr=arr, min_val=ranges[key]["y_min_fedbatch"],
                                                                    max_val=ranges[key]["y_max_fedbatch"])

                                    # Plot simulated data
                                    if key == "DOTa" and not plot_DOT_actual:
                                        pass
                                    else:
                                        trace_sim = go.Scatter(x=x_sim, y=y_sim,
                                                               name=f'{self.allthedata[expID]["variables"][key]["description"]} '
                                                                    f'(simulated)',
                                                               # name=f'{expID}<sub>{self.allthedata[expID]["variables"][key]["description"]} (simulated)</sub>',
                                                               line=dict(color=color_simu,
                                                                         width=plot_info[key]["linestyle"]["width"],
                                                                         dash=dash),
                                                               showlegend=show_legend,
                                                               mode="lines", opacity=plot_info[key]["opacity"]["simu"])

                                        fig.add_trace(trace_sim, row=plot_info[key]["row_plot"], col=1,
                                                      secondary_y=plot_info[key]["secondary_y"])

                                        if split_at_feed_start:
                                            if any(x_sim_fedbatch):
                                                trace_sim = go.Scatter(x=x_sim_fedbatch, y=y_sim_fedbatch,
                                                                       name=f'{self.allthedata[expID]["variables"][key]["description"]} '
                                                                            f'(simulated)',
                                                                       # name=f'{expID}<sub>{self.allthedata[expID]["variables"][key]["description"]} (simulated)</sub>',
                                                                       line=dict(color=color_simu,
                                                                                 width=plot_info[key]["linestyle"]["width"],
                                                                                 dash=dash),
                                                                       showlegend=show_legend,
                                                                       mode="lines",
                                                                       opacity=plot_info[key]["opacity"]["simu"])

                                                fig.add_trace(trace_sim, row=plot_info[key]["row_plot"], col=2,
                                                              secondary_y=plot_info[key]["secondary_y"])

                                        # Get error of SE data
                                        if plot_SE_data:
                                            if y_sim_err is not None and len(y_sim) == len(y_sim_err):
                                                y_lb = np.array(y_sim) - np.array(y_sim_err)
                                                y_ub = np.array(y_sim) + np.array(y_sim_err)

                                                if key == "Biomass_NH3":
                                                    color_marker = color_simu
                                                else:
                                                    color_marker = plot_info[key]['color']['error']

                                                color_filling = f"rgba{mcolors.to_rgba(color_marker, plot_info[key]['opacity']['error'])}"

                                                trace_err_lb = go.Scatter(name='Lower Bound', x=x_sim, y=y_lb, mode='lines',
                                                                          marker=dict(color=color_marker),
                                                                          line=dict(width=0),
                                                                          showlegend=False)

                                                trace_err_ub = go.Scatter(name='Upper Bound', x=x_sim, y=y_ub,
                                                                          marker=dict(color=color_marker),
                                                                          line=dict(width=0),
                                                                          mode='lines',
                                                                          fillcolor=color_filling, fill='tonexty',
                                                                          showlegend=False)

                                                fig.add_trace(trace_err_lb, row=plot_info[key]["row_plot"], col=1,
                                                              secondary_y=plot_info[key]["secondary_y"])
                                                fig.add_trace(trace_err_ub, row=plot_info[key]["row_plot"], col=1,
                                                              secondary_y=plot_info[key]["secondary_y"])

                                                if split_at_feed_start:
                                                    if any(x_sim_fedbatch):
                                                        y_lb_fedbatch = np.array(y_sim_fedbatch) - np.array(
                                                            y_sim_err_fedbatch)
                                                        y_ub_fedbatch = np.array(y_sim_fedbatch) + np.array(
                                                            y_sim_err_fedbatch)

                                                        trace_err_lb = go.Scatter(name='Lower Bound', x=x_sim_fedbatch,
                                                                                  y=y_lb_fedbatch,
                                                                                  mode='lines',
                                                                                  marker=dict(color=color_marker),
                                                                                  line=dict(width=0),
                                                                                  showlegend=False)

                                                        trace_err_ub = go.Scatter(name='Upper Bound', x=x_sim_fedbatch,
                                                                                  y=y_ub_fedbatch,
                                                                                  marker=dict(color=color_marker),
                                                                                  line=dict(width=0),
                                                                                  mode='lines',
                                                                                  fillcolor=color_filling, fill='tonexty',
                                                                                  showlegend=False)

                                                        fig.add_trace(trace_err_lb, row=plot_info[key]["row_plot"], col=2,
                                                                      secondary_y=plot_info[key]["secondary_y"])
                                                        fig.add_trace(trace_err_ub, row=plot_info[key]["row_plot"], col=2,
                                                                      secondary_y=plot_info[key]["secondary_y"])

                # %% Plot measurements
                # If there is data...
                if not len(self.allthedata[expID]["variables"][key]["times"]) == 0:
                    # Select colors
                    color_data = plot_info[key]["color"]["data"] if not plot_replicates else self.colors[expID]
                    color_marker = plot_info[key]["color"]["marker"] if not plot_replicates else self.colors[expID]
                    marker_symbol = plot_info[key]["linestyle"]["marker_symbol"] if not (plot_replicates and not self.fixed_symbol_by_variable) else self.markers[ix]

                    # Get data for measured data
                    x_meas = np.array(self.allthedata[expID]["variables"][key]["times"])
                    if not rescale_time == {}:
                        x_meas = list(self._rescale_time_axis(x_meas, rescale_time))
                    y_meas = np.array(self.allthedata[expID]["variables"][key]["vals"])
                    y_err = np.array(self.allthedata[expID]["variables"][key]["std"])
                    # Remove nan
                    y_err = y_err[~np.isnan(y_err)]

                    if split_at_feed_start:
                        x_meas_fedbatch = np.array([])
                        y_meas_fedbatch = np.array([])
                        y_err_fedbatch = np.array([])

                        # Check if last time value is after feed start
                        if len(self.allthedata[expID]["variables"][key]["times"]) != 0:
                            if self.allthedata[expID]["variables"][key]["times"][-1] >= feed_start:
                                index_feed_start = \
                                    np.where(x_meas >= feed_start)[0][0]

                                x_meas, x_meas_fedbatch = np.split(x_meas, [index_feed_start])
                                y_meas, y_meas_fedbatch = np.split(y_meas, [index_feed_start])
                                y_err, y_err_fedbatch = np.split(y_err, [index_feed_start])

                    # if any(x_meas):
                    # Update ranges
                    # Update x_max
                    _, ranges[key]["x_max"] = self._check_min_max(arr=x_meas, max_val=ranges[key]["x_max"])

                    # Update y_min and y_max
                    if len(y_meas) == len(y_err):
                        arr = np.concatenate((y_meas + y_err, y_meas - y_err))
                    else:
                        arr = y_meas
                    ranges[key]["y_min"], ranges[key]["y_max"] = \
                        self._check_min_max(arr=arr, min_val=ranges[key]["y_min"], max_val=ranges[key]["y_max"])

                    # Plot data
                    trace_meas = go.Scatter(x=x_meas, y=y_meas,
                                            error_y=dict(type='data', array=y_err, visible=True, color=color_marker),
                                            legendgrouptitle=dict(text=legend_group),
                                            legendgroup=legend_group, showlegend=show_legend, name=name,
                                            line=dict(color=color_data, width=plot_info[key]["linestyle"]["width"],
                                                      dash=plot_info[key]["linestyle"]["dash_data"]),
                                            marker=dict(size=plot_info[key]["linestyle"]["marker_size"],
                                                        symbol=marker_symbol,
                                                        color=color_marker,
                                                        line=dict(color=color_data,
                                                                  width=plot_info[key]["linestyle"]["width_marker_line"])),
                                            mode=plot_info[key]["plot_mode"]["meas"],
                                            opacity=plot_info[key]["opacity"]["meas"])

                    fig.add_trace(trace_meas, row=plot_info[key]["row_plot"],
                                  col=1, secondary_y=plot_info[key]["secondary_y"])

                    if split_at_feed_start:
                        # if any(x_meas_fedbatch):
                        # Update x_max
                        _, ranges[key]["x_max"] = \
                            self._check_min_max(arr=x_meas_fedbatch, max_val=ranges[key]["x_max"])

                        # Update y_min and y_max
                        if len(y_meas_fedbatch) == len(y_err_fedbatch):
                            arr = np.concatenate((y_meas_fedbatch + y_err_fedbatch,
                                                  y_meas_fedbatch - y_err_fedbatch))
                        else:
                            arr = y_meas_fedbatch
                        ranges[key]["y_min_fedbatch"], ranges[key]["y_max_fedbatch"] = \
                            self._check_min_max(arr=arr, min_val=ranges[key]["y_min_fedbatch"],
                                                max_val=ranges[key]["y_max_fedbatch"])

                        trace_meas = go.Scatter(x=x_meas_fedbatch, y=y_meas_fedbatch,
                                                error_y=dict(type='data', array=y_err_fedbatch,
                                                             visible=True, color=color_marker),
                                                legendgrouptitle=dict(text=legend_group),
                                                legendgroup=legend_group, showlegend=show_legend, name=name,
                                                line=dict(color=color_data,
                                                          width=plot_info[key]["linestyle"]["width"],
                                                          dash=plot_info[key]["linestyle"]["dash_data"]),
                                                marker=dict(size=plot_info[key]["linestyle"]["marker_size"],
                                                            symbol=marker_symbol,
                                                            color=color_marker,
                                                            line=dict(color=color_data,
                                                                      width=plot_info[key]["linestyle"][
                                                                          "width_marker_line"])),
                                                mode=plot_info[key]["plot_mode"]["meas"],
                                                opacity=plot_info[key]["opacity"]["meas"])

                        # Append trace to figure
                        fig.add_trace(trace_meas, row=plot_info[key]["row_plot"], col=2,
                                      secondary_y=plot_info[key]["secondary_y"])

                # Get range
                t_range_end, y_range, y_range_fedbatch, y_step, y_step_fedbatch = \
                    self._get_range(ranges=ranges, t_range_end=range_end, key=key,
                                    split_at_feed_start=split_at_feed_start, plot_info=plot_info)

                # Update yaxes
                showticklabels = False
                if split_at_feed_start and plot_info[key]["secondary_y"]:
                    title_text = ""
                    showticklabels = False
                else:
                    title_text = plot_info[key]["description"]
                    if self.showticklabels:
                        showticklabels = True

                if self.n_ticks is None:
                    fig.update_yaxes(title_text=title_text,
                                     row=plot_info[key]["row_plot"], col=1, type=axes_type,
                                     secondary_y=plot_info[key]["secondary_y"],
                                     # color=plot_info[key]["color"]["text"],
                                     tick0=0, range=y_range, dtick=y_step, showticklabels=showticklabels)
                else:
                    fig.update_yaxes(title_text=title_text,
                                     row=plot_info[key]["row_plot"], col=1, type=axes_type,
                                     secondary_y=plot_info[key]["secondary_y"],
                                     # color=plot_info[key]["color"]["text"],
                                     tick0=0, range=y_range, showticklabels=showticklabels)

                if not plot_info[key]["secondary_y"]:
                    fig.update_yaxes(row=plot_info[key]["row_plot"], col=1)#, mirror="ticks")

                if split_at_feed_start:
                    if plot_info[key]["secondary_y"]:
                        title_text = plot_info[key]["description"]
                    else:
                        title_text = ""

                    if self.n_ticks is None:
                        fig.update_yaxes(title_text=title_text,
                                         row=plot_info[key]["row_plot"], col=2, type=axes_type, side="right",
                                         secondary_y=plot_info[key]["secondary_y"],
                                         # color=plot_info[key]["color"]["text"],
                                         tick0=0, range=y_range_fedbatch, dtick=y_step_fedbatch, showticklabels=showticklabels)
                    else:
                        fig.update_yaxes(title_text=title_text,
                                         row=plot_info[key]["row_plot"], col=2, type=axes_type, side="right",
                                         secondary_y=plot_info[key]["secondary_y"],
                                         # color=plot_info[key]["color"]["text"],
                                         tick0=0, range=y_range_fedbatch, showticklabels=showticklabels)

                    if not plot_info[key]["secondary_y"]:
                        fig.update_yaxes(row=plot_info[key]["row_plot"], col=2)#, mirror="ticks")

                    # If split_at_feed_start, plot only line for induction in second col plot
                    if index > 0 and plot_replicates:
                        add_vertical_lines = False
                    fig = self._add_vertical_lines(fig, expID, row=plot_info[key]["row_plot"], col=2,
                                                   secondary_y=plot_info[key]["secondary_y"], range=y_range_fedbatch,
                                                   type=("Induction"), if_add_vertical_lines=add_vertical_lines,
                                                   rescale_time=rescale_time)
                else:
                    if index > 0 and plot_replicates:
                        add_vertical_lines = False
                    fig = self._add_vertical_lines(fig, expID, row=plot_info[key]["row_plot"],
                                                   secondary_y=plot_info[key]["secondary_y"], range=y_range,
                                                   if_add_vertical_lines=add_vertical_lines,rescale_time=rescale_time)

            # %% INPUTS
            for index_inputs, key in enumerate(inputs_plot):
                axes_type = 'linear'

                # same name in legend for every variable/input and showing only first entry in plot instead of all (ugly) # TODO: What?
                if plot_replicates:
                    # Assign Legend to the correct Group handling
                    if use_group_names:
                        legend_group = f"<b>{self.allthedata[expID]['Group_name']}</b>"
                        name = f"Reactor_{expID}"
                    else:
                        legend_group = f"{expID}"
                        name = f"Reactor_{expID}"
                    # only first entry
                    show_legend = False
                else:
                    name = plot_info[key]["description"]
                    legend_group = ""

                # Select colors
                color_data = plot_info[key]["color"]["data"] if not plot_replicates else self.colors[expID]
                color_marker = plot_info[key]["color"]["marker"] if not plot_replicates else self.colors[expID]
                marker_symbol = plot_info[key]["linestyle"]["marker_symbol"] if not (plot_replicates and not self.fixed_symbol_by_variable) else self.markers[ix]

                # Get data
                x_meas = self.allthedata[expID]["inputs"][key]["times"]
                if not rescale_time == {}:
                    x_meas = list(self._rescale_time_axis(x_meas, rescale_time))
                y_meas = self.allthedata[expID]["inputs"][key]["vals"]
                if split_at_feed_start:
                    x_meas_fedbatch = np.array([])
                    y_meas_fedbatch = np.array([])
                    if any(y_meas):
                        if len(np.where(x_meas >= feed_start)[0]) != 0:
                            index_inputs_feed_start = np.where(x_meas >= feed_start)[0][0]
                            x_meas, x_meas_fedbatch = np.split(x_meas, [index_inputs_feed_start])
                            y_meas, y_meas_fedbatch = np.split(y_meas, [index_inputs_feed_start])
                        else:
                            x_meas_fedbatch = np.array([])
                            y_meas_fedbatch = np.array([])

                # If there is data
                if not len(self.allthedata[expID]["inputs"][key]["times"]) == 0:
                    # if any(x_meas):  # If there is data
                    # Update ranges
                    # Update x_max
                    _, ranges[key]["x_max"] = self._check_min_max(arr=x_meas, max_val=ranges[key]["x_max"])

                    # Update y_min and y_max
                    ranges[key]["y_min"], ranges[key]["y_max"] = \
                        self._check_min_max(arr=y_meas, min_val=ranges[key]["y_min"], max_val=ranges[key]["y_max"])

                    # Plot data
                    if self.allthedata[expID]["inputs"][key]["plotting"]["stem"]:
                        opacity = self.opacity_stem
                        error_y = dict(type='data', symmetric=False, array=-y_meas, visible=True, width=0,
                                       thickness=self.thickness_stem, color=self._get_color_stem(color_data))
                        marker_size = 1
                    else:
                        opacity = plot_info[key]["opacity"]["meas"]
                        error_y = dict()
                        marker_size = plot_info[key]["linestyle"]["marker_size"]

                    trace_meas = go.Scatter(x=x_meas, y=y_meas, error_y=error_y,
                                            name=name,
                                            legendgrouptitle=dict(text=legend_group),
                                            legendgroup=legend_group,
                                            showlegend=show_legend,
                                            line=dict(shape="hv", color=color_data),
                                            marker=dict(size=marker_size,
                                                        symbol=marker_symbol,
                                                        color=color_data),
                                            mode=plot_info[key]["plot_mode"]["meas"],
                                            opacity=opacity)

                    fig.add_trace(trace_meas, row=plot_info[key]["row_plot"], col=1,
                                  secondary_y=plot_info[key]["secondary_y"])

                    if split_at_feed_start:
                        # if any(x_meas_fedbatch):  # If there is data for fedbatch
                        # Update ranges
                        # Update x_max
                        _, ranges[key]["x_max"] = \
                            self._check_min_max(arr=x_meas_fedbatch, max_val=ranges[key]["x_max"])

                        # Update y_min and y_max
                        ranges[key]["y_min_fedbatch"], ranges[key]["y_max_fedbatch"] = \
                            self._check_min_max(arr=y_meas_fedbatch, min_val=ranges[key]["y_min_fedbatch"],
                                                max_val=ranges[key]["y_max_fedbatch"])

                        # Plot data
                        if self.allthedata[expID]["inputs"][key]["plotting"]["stem"]:
                            opacity = self.opacity_stem
                            error_y = dict(type='data', symmetric=False, array=-y_meas_fedbatch, visible=True, width=0,
                                           thickness=self.thickness_stem, color=self._get_color_stem(color_data))
                            marker_size = 1
                        else:
                            error_y = dict()
                            marker_size = plot_info[key]["linestyle"]["marker_size"]

                        trace_meas = go.Scatter(x=x_meas_fedbatch, y=y_meas_fedbatch, error_y=error_y,
                                                name=name,
                                                legendgrouptitle=dict(text=legend_group),
                                                legendgroup=legend_group,
                                                showlegend=show_legend,
                                                line=dict(shape="hv", color=color_data),
                                                marker=dict(size=marker_size,
                                                            symbol=marker_symbol,
                                                            color=color_data),
                                                mode=plot_info[key]["plot_mode"]["meas"],
                                                opacity=opacity)

                        # Append trace to figure
                        fig.add_trace(trace_meas, row=plot_info[key]["row_plot"], col=2,
                                      secondary_y=plot_info[key]["secondary_y"])

                # Get range
                t_range_end, y_range, y_range_fedbatch, y_step, y_step_fedbatch = \
                    self._get_range(ranges=ranges, t_range_end=range_end, key=key,
                                    split_at_feed_start=split_at_feed_start, plot_info=plot_info)

                # Update yaxes
                showticklabels = False
                if split_at_feed_start and plot_info[key]["secondary_y"]:
                    title_text = ""
                    showticklabels = False
                else:
                    title_text = plot_info[key]["description"]
                    if self.showticklabels:
                        showticklabels = True

                if self.n_ticks is None:
                    fig.update_yaxes(title_text=title_text,
                                     row=plot_info[key]["row_plot"], col=1, type=axes_type,
                                     secondary_y=plot_info[key]["secondary_y"],
                                     tick0=0, range=y_range, dtick=y_step, showticklabels=showticklabels)
                else:
                    fig.update_yaxes(title_text=title_text,
                                     row=plot_info[key]["row_plot"], col=1, type=axes_type,
                                     secondary_y=plot_info[key]["secondary_y"],
                                     tick0=0, range=y_range, showticklabels=showticklabels)

                if not plot_info[key]["secondary_y"]:
                    fig.update_yaxes(row=plot_info[key]["row_plot"], col=1)#, mirror="ticks")

                if split_at_feed_start:
                    if plot_info[key]["secondary_y"]:
                        title_text = plot_info[key]["description"]
                    else:
                        title_text = ""

                    if self.n_ticks is None:
                        fig.update_yaxes(title_text=title_text,
                                         row=plot_info[key]["row_plot"], col=2, type=axes_type, side="right",
                                         secondary_y=plot_info[key]["secondary_y"],
                                         tick0=0, range=y_range_fedbatch, dtick=y_step_fedbatch,
                                         showticklabels=showticklabels)
                    else:
                        fig.update_yaxes(title_text=title_text,
                                         row=plot_info[key]["row_plot"], col=2, type=axes_type, side="right",
                                         secondary_y=plot_info[key]["secondary_y"],
                                         tick0=0, range=y_range_fedbatch, showticklabels=showticklabels)

                    if not plot_info[key]["secondary_y"]:
                        fig.update_yaxes(row=plot_info[key]["row_plot"], col=2)#, mirror="ticks")

                    # If split_at_feed_start, plot only line for induction in second col plot
                    if index > 0 and plot_replicates:
                        add_vertical_lines = False
                    fig = self._add_vertical_lines(fig, expID, row=plot_info[key]["row_plot"], col=2,
                                                   secondary_y=plot_info[key]["secondary_y"], range=y_range_fedbatch,
                                                   type=("Induction"), if_add_vertical_lines=add_vertical_lines,
                                                   rescale_time=rescale_time)
                else:
                    if index > 0 and plot_replicates:
                        add_vertical_lines = False
                    fig = self._add_vertical_lines(fig, expID, row=plot_info[key]["row_plot"],
                                                   secondary_y=plot_info[key]["secondary_y"], range=y_range,
                                                   if_add_vertical_lines=add_vertical_lines,
                                                   rescale_time=rescale_time)

            # %% Update figure
            # no match in color between y-axes and data points, if replicates are plotted
            if plot_replicates:
                fig.update_yaxes(color="black")
                show_legend = True

            if not rescale_time == {}:
                ticktext = np.arange(sim_data["times"][0], sim_data["times"][-1], x_tick_interval)
                tickvals = self._rescale_time_axis(ticktext, rescale_time)
                fig.update_xaxes(
                        tickmode='array',
                        tickvals=tickvals,
                        ticktext=ticktext
                )

                t_range_end = self._rescale_time_axis([t_range_end], rescale_time)[0]

            self._update_layout(fig, self.plot_height, self.plot_width, show_legend, hovermode="x")
            fig.update_xaxes(range=[0, t_range_end])

            # Adds annotations
            if NRMSE is not None:
                pos_x = 0.57
                pos_y = 0.98
                fig.add_annotation(text=f"NRMSE (Simulation):<br>"
                                        f"----------------------------------------------------------<br>"
                                        f"Biomass   : {NRMSE[expID]['simulation']['Biomass']:10.3f}<br>"
                                        f"Substrate : {NRMSE[expID]['simulation']['Substrate']:10.3f}<br>"
                                        f"Acetate    : {NRMSE[expID]['simulation']['Acetate']:10.3f}<br>"
                                        f"DOTm      : {NRMSE[expID]['simulation']['DOTm']:10.3f}<br>"
                                        f"Mean       : {NRMSE[expID]['simulation']['mean']:10.3f}<br>"
                                        f"Mean_noA: {NRMSE[expID]['simulation']['mean_noA']:10.3f}<br><br><br>"
                                        f"NRMSE (State estimation):<br>"
                                        f"----------------------------------------------------------<br>"
                                        f"Biomass   : {NRMSE[expID]['simulation_SE']['Biomass']:10.3f}<br>"
                                        f"Substrate : {NRMSE[expID]['simulation_SE']['Substrate']:10.3f}<br>"
                                        f"Acetate    : {NRMSE[expID]['simulation_SE']['Acetate']:10.3f}<br>"
                                        f"DOTm      : {NRMSE[expID]['simulation_SE']['DOTm']:10.3f}<br>"
                                        f"Mean       : {NRMSE[expID]['simulation_SE']['mean']:10.3f}<br>"
                                        f"Mean_noA: {NRMSE[expID]['simulation_SE']['mean_noA']:10.3f}<br><br><br>",
                                   xref="paper", yref="paper", x=pos_x, y=pos_y, width=300,
                                   showarrow=False, bordercolor='black', xanchor="center", align="left", font_size=12)

                if k_P is not None or k_Q is not None or k_R is not None or filter is not None:
                    if filter is None:
                        filter = f"KF"

                    text = f"{filter} Matrices:               Qauto = {Q_auto}<br>" \
                           f"----------------------------------------------------------<br>"

                    if k_P is not None:
                        text += f"k_P: {k_P}<br>"

                    if k_Q is not None:
                        text += f"k_Q: {k_Q}<br>"

                    if k_R is not None:
                        text += f"k_R: {k_R}<br>"

                    fig.add_annotation(text=text,
                                       xref="paper", yref="paper", x=pos_x, y=pos_y - 0.45, width=300,
                                       showarrow=False, bordercolor='black', xanchor="center", align="left",
                                       font_size=12)

            if not plot_replicates:
                # Define plot name
                plot_name = f'{self.plot_info}_exp{expID}'
                if plot_SE_data:
                    plot_name = plot_name + '_SE'

                # Save figure
                self._save_fig(fig, plot_name)

        if plot_replicates:
            # Define plot name
            plot_name = f'{self.plot_info}_exp{"-".join(list(self.allthedata.keys()))}'
            if plot_SE_data:
                plot_name = plot_name + '_SE'

            # Save figure
            self._save_fig(fig, plot_name)

    def plot_by_variable(self, n_rows, replicates_from_description=False, plot_SE_data=False):
        """ Function to plot all experiments (for one variable) in one figure (but separate subplots).

        :param n_rows: number of rows, i.e. number of plots in one column
        :param replicates_from_description: flag if to
        """
        # Plot only the states with data
        expID_first = list(self.allthedata.keys())[0]
        variables_plot = [(key, self.allthedata[expID_first]["variables"][key]["description"]) for key in
                          self.allthedata[expID_first]["variables"].keys() if
                          self.allthedata[expID_first]["variables"][key]["plotting"]["plot"]]

        if replicates_from_description:
            # Get unique descriptions of the expIDs to identify replicates
            titles = descriptions_unique = list(
                set([self.allthedata[key]["description"] for key in self.allthedata.keys()]))
            keys_listoflists = [[] for x in range(len(descriptions_unique))]

            for key in self.allthedata.keys():
                index = descriptions_unique.index(self.allthedata[key]["description"])
                keys_listoflists[index].append(key)

            n_exp = len(keys_listoflists)  # number of experiments
            if n_exp < n_rows:
                n_rows = n_exp
            n_cols = math.ceil(n_exp / n_rows)  # number of columns in the plot

        else:
            keys_listoflists = [[key] for key in self.allthedata.keys()]
            n_exp = len(keys_listoflists)  # number of experiments

            if n_exp < n_rows:
                n_rows = n_exp
            n_cols = math.ceil(n_exp / n_rows)  # number of columns in the plot
            titles = [f"expID: {expID} ({self.allthedata[expID]['description']})" for expID in self.allthedata.keys()]

        # TODO: Update the scaling depending on number of subplots
        if n_rows < 4:
            scaling_factor_height = 400
        else:
            scaling_factor_height = 200
        if n_cols < 3:
            scaling_factor_width = 800
        else:
            scaling_factor_width = 400

        # Set colors
        self._set_colors(n_colors=len(self.allthedata.keys()))

        for (variable, description) in variables_plot:
            # Create subplots with shared x-axis
            fig = make_subplots(rows=n_rows, cols=n_cols, shared_xaxes=True,
                                vertical_spacing=0.02,
                                y_title=description,
                                x_title=self.x_title,
                                subplot_titles=titles)

            self._update_layout(fig, plot_height=n_rows * scaling_factor_height,
                                plot_width=n_cols * scaling_factor_width)

            # Update title size
            for i in fig['layout']['annotations']:
                i['font'] = dict(size=13)

            x_range_end = 0  # maximum x value (i.e. time), gets overwritten during looping through expIDs
            for ix_group, expID_group in enumerate(keys_listoflists):
                # Get location on plot
                row = math.floor(ix_group / n_cols)
                col = ix_group - row * n_cols

                for ix, expID in enumerate(expID_group):
                    # Show legend only for first entry
                    # if ix_group == 0 and ix == 0:
                    #     show_legend = True
                    # else:
                    #     show_legend = False
                    show_legend = False

                    # Get data for measured data
                    x_meas = self.allthedata[expID]["variables"][variable]["times"]
                    y_meas = self.allthedata[expID]["variables"][variable]["vals"]
                    y_err = self.allthedata[expID]["variables"][variable]["std"]

                    if not len(self.allthedata[expID]["variables"][variable]["times"]) == 0:
                        plot_description = "data"

                        if variable == "DOTm":  # TODO: Hardcoded
                            trace_meas = go.Scatter(x=x_meas,
                                                    y=y_meas,
                                                    name=plot_description,
                                                    line=dict(color=self.colors[ix], width=1.5, dash="dot"),
                                                    # legendgroup="data",
                                                    showlegend=show_legend,
                                                    marker=dict(size=5, symbol=plot_info[key]["linestyle"]["marker_symbol"], color=self.colors[ix]),
                                                    mode="lines+markers")
                        else:
                            trace_meas = go.Scatter(x=x_meas,
                                                    y=y_meas,
                                                    error_y=dict(type='data', array=y_err, visible=True),
                                                    name=plot_description,
                                                    # legendgroup="data",
                                                    showlegend=show_legend,
                                                    marker=dict(size=8, symbol=plot_info[key]["linestyle"]["marker_symbol"], color=self.colors[ix]),
                                                    mode="markers")

                        # Append trace to figure
                        fig.append_trace(trace_meas, row=row + 1, col=col + 1)

                    if plot_SE_data:
                        sim_data = self.allthedata[expID]["simulation_data (SE)"]
                    else:
                        sim_data = self.allthedata[expID]["simulation_data"]

                    if sim_data["times"]:
                        if replicates_from_description:
                            color = "black"
                        else:
                            color = self.colors[ix]

                        # Get data for simulated data

                        trace_sim = go.Scatter(x=sim_data["times"], y=sim_data["vals"][variable],
                                               name=f'(simulated)',
                                               line=dict(color=color, width=3, dash="solid"),
                                               # legendgroup=f"simu",
                                               showlegend=show_legend,
                                               mode="lines", opacity=.6)

                        # Append trace to figure
                        fig.append_trace(trace_sim, row=row + 1, col=col + 1)

                        # Get x_range
                        if sim_data["times"][-1] < 1:
                            x_range_end_current = np.ceil(sim_data["times"][-1] * 100) / 100
                        else:
                            x_range_end_current = np.ceil(sim_data["times"][-1])

                    else:
                        # Updated figure style properties
                        if x_meas[-1] < 1:
                            x_range_end_current = np.ceil(x_meas[-1] * 100) / 100
                        else:
                            x_range_end_current = np.ceil(x_meas[-1])

                    # Update ranges (if applicable)
                    if x_range_end_current > x_range_end:
                        x_range_end = x_range_end_current

            fig.update_xaxes(range=[0, x_range_end], dtick=x_range_end / 10)

            # Define plot name
            plot_name = f'{self.plot_info}_{variable}'
            if plot_SE_data:
                plot_name = plot_name + '_SE'

            # Save figure
            self._save_fig(fig, plot_name)

    def plot_sensitivities(self, n_rows, n_cols, plot_method, log=False, lb=0):
        """ Function to plot all chosen sensitivities.

        :param n_rows: number of rows, i.e. number of plots in one column
        :param n_cols: number of columns, i.e. number of plots in one row
        :param plot_method: 'states'/'parameter' - plots all states/parameter in a single plot
        :param log: False - linear scaling / True - logarithmic scaling
        :param lb: if log == True set lower bounds for log scale
        """
        # TODO: Update the scaling depending on number of subplots
        if n_rows < 4:
            scaling_factor_height = 400
        else:
            scaling_factor_height = 200
        if n_cols < 3:
            scaling_factor_width = 800
        else:
            scaling_factor_width = 400

        if log:
            scale = 'log'
        else:
            scale = 'linear'

        for expID in self.allthedata.keys():
            # States and parameters
            states = list(self.allthedata[expID]['simulation_data']['sensitivities'].keys())
            params = list(self.allthedata[expID]['simulation_data']['sensitivities'][states[0]].keys())

            # Determine number of pages and number of subplots per page
            n_states = len(states)
            n_params = len(params)

            if plot_method == 'states':
                N = n_params  # Total number of subplots
                n_lines = n_states  # Number of line per subplot
                self._set_colors(n_colors=n_states)  # Set colors
            else:
                N = n_states
                n_lines = n_params  # Number of line per subplot
                self._set_colors(n_colors=n_params)  # Set colors

            n_pages = math.ceil(N / (n_cols * n_rows))
            n_subplots = n_cols * n_rows

            i_states = 0
            i_params = 0
            for ix in range(n_pages):
                # Create subplots with shared x-axis
                fig = make_subplots(rows=n_rows, cols=n_cols, shared_xaxes=True,
                                    vertical_spacing=0.02,
                                    y_title=f'Sensitivities [{scale}]',
                                    x_title=self.x_title,
                                    subplot_titles='')

                for subplot in range(ix * n_subplots, (ix + 1) * n_subplots):
                    # Update title size
                    for i in fig['layout']['annotations']:
                        i['font'] = dict(size=13)

                    # Get location on plot
                    row = math.floor(subplot / n_cols) - ix * n_rows
                    col = subplot - ix * n_cols * n_rows - row * n_cols

                    show_legend = True

                    n = 0  # Counter for colours
                    x_range_end = 0  # maximum x value per subplot (i.e. time)

                    # get data for subplot
                    for line in range(n_lines):
                        color = self.colors[line]  # self.colors[n % 9]
                        state = states[i_states]
                        param = params[i_params]

                        # Get data from simulated data
                        x_sim = self.allthedata[expID]["simulation_data"]["times"]
                        if log:  # only positive values if log == True
                            y_sim = abs(
                                np.array(self.allthedata[expID]["simulation_data"]["sensitivities (weighted)"][state][param]))
                            y_sim[y_sim <= lb] = lb  # set lower boundary for log scale
                        else:
                            y_sim = np.array(
                                self.allthedata[expID]["simulation_data"]["sensitivities (weighted)"][state][param])

                        trace_sim = go.Scatter(x=x_sim, y=y_sim,
                                               name=f'{state}:{param}_{expID}',
                                               line=dict(color=color, width=3, dash="solid"),
                                               # legendgroup=f"{subplot}_{state}:{param}_{expID}",
                                               showlegend=show_legend,
                                               mode="lines", opacity=.6)

                        # Append trace to figure
                        fig.append_trace(trace_sim, row=row + 1, col=col + 1)

                        # Get x_range
                        if x_sim[-1] < 1:
                            x_range_end_current = np.ceil(x_sim[-1] * 100) / 100
                        else:
                            x_range_end_current = np.ceil(x_sim[-1])

                        # Update ranges (if applicable)
                        if x_range_end_current > x_range_end:
                            x_range_end = x_range_end_current

                        if plot_method == 'states':
                            i_states += 1
                        else:
                            i_params += 1

                    fig.update_yaxes(row=row + 1, col=col + 1, type=scale)
                    fig.update_xaxes(range=[0, x_range_end], dtick=x_range_end / 10)

                    if plot_method == 'states':
                        i_params += 1
                        i_states = 0
                    else:
                        i_states += 1
                        i_params = 0

                # Set legend layout
                fig = self._update_layout(fig, plot_height=n_rows * scaling_factor_height,
                                          plot_width=n_cols * scaling_factor_width, show_legend=show_legend)

                # Save figure
                self._save_fig(fig, plot_name=f'{self.plot_info}_sensitivities_{ix + 1}')

    def plot_covariance(self, error_method='CI', confidence=95, sample_interval=5, cov_method='bootstrap',
                        params_names=None, result_as_table=False):
        """ Function to plot results from bootstrap analysis or fisher matrix.
        """
        cov_method = cov_method.lower()
        expID = list(self.allthedata.keys())[0]

        # Initialization
        if cov_method == 'bootstrap':
            runs = self.allthedata[expID]['statistics']['bootstrap']['runs']
            if params_names is None:
                params_names = self.allthedata[expID]['statistics']['bootstrap']['params_names']
            init_params = self.allthedata[expID]['statistics']['bootstrap']['init_params']
            init_params_normalized = self.allthedata[expID]['statistics']['bootstrap']['init_params (normalized)']
            params = self.allthedata[expID]['statistics']['bootstrap']['params']
            params_normalized = self.allthedata[expID]['statistics']['bootstrap']['params (normalized)']
            params_mean = self.allthedata[expID]['statistics']['bootstrap']['params_mean']
            params_mean_normalized = self.allthedata[expID]['statistics']['bootstrap']['params_mean (normalized)']
            cov_params = self.allthedata[expID]['statistics']['bootstrap']['cov_params']
            cov_params_normalized = self.allthedata[expID]['statistics']['bootstrap']['cov_params (normalized)']
            corr_params = self.allthedata[expID]['statistics']['bootstrap']['corr_params']
            params_std_dev = np.sqrt(cov_params.diagonal())
            params_std_dev_normalized = np.sqrt(cov_params_normalized.diagonal())
            bounds = self.allthedata[expID]['statistics']['bootstrap']['params_bounds']

        elif cov_method == 'fisher':
            runs = 0
            params_names = self.allthedata[expID]['statistics']['fisher']['params_names']
            params_mean = self.allthedata[expID]['statistics']['fisher']['params_value']
            params_mean_normalized = self.allthedata[expID]['statistics']['fisher']['params_value (normalized)']
            bounds = self.allthedata[expID]['statistics']['fisher']['params_bounds']
            cov_params = self.allthedata[expID]['statistics']['fisher']['inverse_matrix']
            cov_params_scaled = self.allthedata[expID]['statistics']['fisher']['inverse_matrix (scaled)']
            params_std_dev = self.allthedata[expID]['statistics']['fisher']['std_dev']
            params_std_dev_normalized = self.allthedata[expID]['statistics']['fisher']['std_dev (normalized)']

        else:
            raise RuntimeError(f'Invalid cov_method! cov_method should be either "bootstrap" or "fisher".')

        if result_as_table:
            import pandas as pd
            bootstrap_table = pd.DataFrame(index=params_names)
            bootstrap_table['params_mean'] = params_mean
            bootstrap_table['params_std_dev'] = params_std_dev
            bootstrap_table.to_csv(path_or_buf=Path(self.path, f"Result_Bootstrap.csv"))

        # Set text for annotation in mean value plot
        string_params = ''
        string_min = ''
        string_max = ''
        for index, key in enumerate(params_names):
            string_params += f'{key}<br>'
            string_min += f'{bounds[index, 0]:.2e}<br>'
            string_max += f'{bounds[index, 1]:.2e}<br>'

        # %% Plot parameter mean values with standard deviations and visualization of covariance matrix
        # Create subplots with shared x-axis
        # Define subplot title
        if error_method == 'CI':
            string_title = f'{confidence} % confidence intervals (CI)'
        else:
            string_title = 'standard deviations (SD)'

        if cov_method == 'bootstrap':
            fig = make_subplots(rows=2, cols=3, shared_xaxes=True, vertical_spacing=0.05, horizontal_spacing=0.12,
                                subplot_titles=[f'Parameter mean values with {string_title}',
                                                'Parameter covariance matrix', '', '',
                                                'Parameter correlation matrix', ''])
        elif cov_method == 'fisher':
            fig = make_subplots(rows=2, cols=3, shared_xaxes=True, vertical_spacing=0.05, horizontal_spacing=0.12,
                                subplot_titles=[f'Parameter mean values with {string_title}',
                                                'Fisher information matrix', '', '',
                                                'Fisher information matrix (scaled)', ''])

        # Update title size
        for i in fig['layout']['annotations']:
            i['font'] = dict(size=13)

        self._set_colors(n_colors=len(self.allthedata.keys()))

        # Subplot [1, 1]: bar plot of parameter mean values and standard deviations (SD) or confidence intervals (CI)
        x_data = params_names  # Get x-axis labels (parameter names)
        y_data = np.transpose(params_mean).tolist()[0]  # Get y-axis values (mean values)

        if error_method == 'CI':  # Confidence interval
            if cov_method == 'fisher':  # symmetric CI
                error_bars = np.transpose(params_mean)[0] - \
                             norm.interval(confidence / 100, loc=np.transpose(params_mean)[0],
                                           scale=np.transpose(params_std_dev)[0])[0]
                error_bars_minus = error_bars
            else:  # Asymmetric CI
                n_params = len(params_names)
                N = params.shape[1]
                factor = (100 - confidence) / 200

                error_bars = np.zeros(n_params)
                error_bars_minus = np.zeros(n_params)
                for i in range(n_params):
                    p = np.sort(np.array(params[i])[0])
                    n_cut = int(factor * N)
                    error_bars[i] = p[-n_cut] - params_mean[i, 0]
                    error_bars_minus[i] = params_mean[i, 0] - p[n_cut]
        else:
            error_bars = params_std_dev  # Get error bars (standard deviation)
            error_bars_minus = error_bars

        trace_mean = go.Scatter(x=x_data, y=y_data, mode='markers',
                                name='Parameter mean value',
                                error_y=dict(type='data',
                                             array=error_bars,
                                             arrayminus=error_bars_minus,
                                             color=self.colors[0],
                                             thickness=2.5,
                                             width=3
                                             ),
                                marker=dict(color=self.colors[0], size=8, opacity=.6),
                                legendgroup="Parameter mean value",
                                showlegend=False
                                )
        fig.add_trace(trace_mean, row=1, col=1)

        # Subplot [2, 1]: bar plot of parameter mean values (normalized) and SD or CI (normalized)
        y_data = np.transpose(np.array(params_mean_normalized))[0]
        if error_method == 'CI':  # Confidence interval
            if cov_method == 'fisher':  # symmetric CI
                error_bars = np.transpose(params_mean_normalized)[0] - \
                             norm.interval(confidence / 100, loc=np.transpose(params_mean_normalized)[0],
                                           scale=np.transpose(params_std_dev_normalized)[0])[0]
                error_bars_minus = error_bars
            else:  # Asymmetric CI
                n_params = len(params_names)
                N = params.shape[1]
                factor = (100 - confidence) / 200

                error_bars = np.zeros(n_params)
                error_bars_minus = np.zeros(n_params)
                for i in range(n_params):
                    p = np.sort(np.array(params_normalized[i])[0])
                    n_cut = int(factor * N)
                    error_bars[i] = p[-n_cut] - params_mean_normalized[i, 0]
                    error_bars_minus[i] = params_mean_normalized[i, 0] - p[n_cut]
        else:
            error_bars = params_std_dev_normalized  # Get error bars (standard deviation)
            error_bars_minus = error_bars

        trace_mean_normalized = go.Scatter(x=x_data, y=y_data, mode='markers', name='Parameter mean value (normalized)',
                                           error_y=dict(type='data',
                                                        array=error_bars,
                                                        arrayminus=error_bars_minus,
                                                        color=self.colors[0],
                                                        thickness=2.5,
                                                        width=3,
                                                        ),
                                           marker=dict(color=self.colors[0], size=8, opacity=.6),
                                           legendgroup="Parameter mean value (normalized)",
                                           showlegend=False
                                           )
        fig.add_trace(trace_mean_normalized, row=2, col=1)

        # Subplot [1, 2]: circle plot of parameter covariance
        x_data = np.concatenate(np.transpose(np.array([params_names] * len(params_names))))
        y_data = np.concatenate(np.array([params_names] * len(params_names)))
        color = np.concatenate(np.asarray(cov_params))
        scaling = np.abs(color)
        marker_size = 5 + (scaling - np.min(scaling)) * 16 / (np.max(scaling) - np.min(scaling))

        trace_cov = go.Scatter(x=x_data, y=y_data, mode='markers',
                               name='Parameter covariance',
                               marker=dict(size=marker_size, color=color, opacity=.8,
                                           colorbar=dict(title="Value", len=0.4, x=0.63, y=.8),
                                           colorscale="balance"),
                               legendgroup="Parameter covariance",
                               showlegend=False
                               )
        fig.add_trace(trace_cov, row=1, col=2)

        # Subplot [2, 2]: circle plot of parameter covariance scaled
        if cov_method == 'bootstrap':
            matrix = corr_params
            text1 = f"<b>Number of parameter estimations:</b> {runs}<br><br>"
        elif cov_method == 'fisher':
            matrix = cov_params_scaled
            text1 = f"<b>Analysis with fisher information matrix:</b><br><br>"
        color = np.concatenate(np.asarray(matrix))
        scaling = np.abs(color)
        marker_size = 5 + (scaling - np.min(scaling)) * 16 / (np.max(scaling) - np.min(scaling))

        trace_corr = go.Scatter(x=x_data, y=y_data, mode='markers',
                                name='Parameter covariance (normalized)',
                                marker=dict(size=marker_size, color=color, opacity=.8,
                                            colorbar=dict(title="Value", len=0.4, x=0.63, y=.26),
                                            colorscale="balance"),
                                legendgroup="Parameter covariance (normalized)",
                                showlegend=False
                                )
        fig.add_trace(trace_corr, row=2, col=2)

        # Update axes
        fig.update_xaxes(type="category", tickangle=45)

        fig.update_xaxes(row=2, col=1, title="Parameter")
        fig.update_xaxes(row=2, col=2, title="Parameter")

        fig.update_yaxes(exponentformat="power")

        fig.update_yaxes(row=1, col=1, title="Mean value")
        fig.update_yaxes(row=2, col=1, title="Mean value (normalized)", range=[0, 1])
        fig.update_yaxes(row=1, col=2, title="Parameter", type="category", autorange="reversed", tickangle=45)
        if cov_method == 'bootstrap':
            fig.update_yaxes(row=2, col=2, title="Parameter (normalized)", type="category", autorange="reversed",
                             tickangle=45)
        elif cov_method == 'fisher':
            fig.update_yaxes(row=2, col=2, title="Parameter (scaled)", type="category", autorange="reversed",
                             tickangle=45)

        # Adds annotations to the plot with information about the number of PEs and parameter bounds
        pos_x = 0.83
        pos_y = 0.95
        fig.add_annotation(text=f"{text1}"
                                f"Parameter bounds:<br>"
                                f"----------------------------------------------------------<br>"
                                f"{string_params}",
                           xref="paper", yref="paper", x=pos_x, y=pos_y, width=300,
                           showarrow=False, bordercolor='black', xanchor="center", align="left", font_size=10)
        fig.add_annotation(text=f"    min<br><br>"
                                f"{string_min}",
                           xref="paper", yref="paper", x=pos_x + 0.02, y=pos_y - 0.04,
                           showarrow=False, xanchor="center", align="left", font_size=10)
        fig.add_annotation(text=f"    max<br><br>"
                                f"{string_max}",
                           xref="paper", yref="paper", x=pos_x + 0.08, y=pos_y - 0.04,
                           showarrow=False, xanchor="center", align="left", font_size=10)

        # Set legend layout
        fig = self._update_layout(fig, plot_height=900, plot_width=1600)

        # Save figure
        if cov_method == 'bootstrap':
            self._save_fig(fig, plot_name=f'{self.plot_info}_parameter_mean_bootstrap')
        else:
            self._save_fig(fig, plot_name=f'{self.plot_info}_parameter_mean_fisher')

        # %% Plot parameter and initial parameter of PE
        if cov_method == 'bootstrap':
            # Create subplots with shared x-axis
            fig2 = make_subplots(rows=2, cols=3, shared_xaxes=True, shared_yaxes=True,
                                 vertical_spacing=0.05, horizontal_spacing=0.05,
                                 subplot_titles=['Initial Parameter for PEs',
                                                 'Optimal parameter from PEs (solution)', '', ''])

            # Update title size
            for i in fig2['layout']['annotations']:
                i['font'] = dict(size=13)

            # Subplot [1, 1]: plot of initial parameter values for PEs
            x_data = np.concatenate(
                np.transpose(np.array([params_names] * runs)))  # Get x-axis labels (parameter names)
            y_data = np.concatenate(np.array(init_params))  # Get y-axis values (parameter initial values)

            trace_inital = go.Scatter(x=x_data, y=y_data, mode='markers',
                                      name='Parameter initial value',
                                      marker=dict(color=self.colors[0], size=8, opacity=.6),
                                      legendgroup="Parameter initial value",
                                      showlegend=False
                                      )
            fig2.add_trace(trace_inital, row=1, col=1)

            # Subplot [2, 1]: plot of normalized initial parameter values for PEs
            y_data = np.concatenate(np.array(init_params_normalized))

            trace_inital_normalized = go.Scatter(x=x_data, y=y_data, mode='markers',
                                                 name='Parameter initial value (normalized)',
                                                 marker=dict(color=self.colors[0], size=8, opacity=.6),
                                                 legendgroup="Parameter initial value (normalized)",
                                                 showlegend=False
                                                 )
            fig2.add_trace(trace_inital_normalized, row=2, col=1)

            # Subplot [1, 2]: plot of optimal parameter values from PEs
            x_data = np.concatenate(np.transpose(np.array([params_names] * (runs + 1))))  # Get x-axis (parameter names)
            y_data = np.concatenate(np.array(params))  # Get y-axis values (parameter initial values)

            trace_params = go.Scatter(x=x_data, y=y_data, mode='markers',
                                      name='Parameter initial value',
                                      marker=dict(color=self.colors[0], size=8, opacity=.6),
                                      legendgroup="Parameter initial value",
                                      showlegend=False
                                      )
            fig2.add_trace(trace_params, row=1, col=2)

            # Subplot [2, 2]: plot of normalized optimal parameter values from PEs
            y_data = np.concatenate(np.array(params_normalized))

            trace_params_normalized = go.Scatter(x=x_data, y=y_data, mode='markers',
                                                 name='Parameter initial value (normalized)',
                                                 marker=dict(color=self.colors[0], size=8, opacity=.6),
                                                 legendgroup="Parameter initial value (normalized)",
                                                 showlegend=False
                                                 )
            fig2.add_trace(trace_params_normalized, row=2, col=2)

            # Adds annotations to the plot with information about the number of PEs and parameter bounds
            pos_x = 0.83
            pos_y = 0.95
            fig2.add_annotation(text=f"<b>Number of parameter estimations:</b> {runs}<br><br>"
                                     f"Parameter bounds:<br>"
                                     f"----------------------------------------------------------<br>"
                                     f"{string_params}",
                                xref="paper", yref="paper", x=pos_x, y=pos_y, width=300,
                                showarrow=False, bordercolor='black', xanchor="center", align="left", font_size=10)
            fig2.add_annotation(text=f"    min<br><br>"
                                     f"{string_min}",
                                xref="paper", yref="paper", x=pos_x + 0.02, y=pos_y - 0.04,
                                showarrow=False, xanchor="center", align="left", font_size=10)
            fig2.add_annotation(text=f"    max<br><br>"
                                     f"{string_max}",
                                xref="paper", yref="paper", x=pos_x + 0.08, y=pos_y - 0.04,
                                showarrow=False, xanchor="center", align="left", font_size=10)

            # Update axes
            fig2.update_xaxes(type="category", tickangle=45)

            fig2.update_xaxes(row=2, col=1, title="Parameter")
            fig2.update_xaxes(row=2, col=2, title="Parameter")

            fig2.update_yaxes(exponentformat="power")

            fig2.update_yaxes(row=1, col=1, title="Value")
            fig2.update_yaxes(row=2, col=1, title="Value (normalized)", range=[0, 1])

            # Set legend layout
            fig2 = self._update_layout(fig2, plot_height=900, plot_width=1600)

            # Save figure
            self._save_fig(fig2, plot_name=f'{self.plot_info}_parameter_PE')

            # %% Plot parameter (single) in a barplot with SD or CI and results from fisher
            # Create subplots with shared x-axis
            used_array = np.transpose(np.array(np.min(params, 1) != np.max(params, 1)))[0]
            params_used_names = np.array(params_names)
            params_used_names = params_used_names[used_array]
            params_used = params[used_array]
            std_dev = params_std_dev
            rows = int(np.ceil(len(params_used_names) / 4))
            cols = min(len(params_used_names), 4)
            title = []
            for key in params_used_names:
                title = title + [key]
            fig3 = make_subplots(rows=rows, cols=cols, shared_xaxes=False, shared_yaxes=False,
                                 vertical_spacing=0.08, horizontal_spacing=0.05,
                                 subplot_titles=title)

            # Update title size
            for i in fig3['layout']['annotations']:
                i['font'] = dict(size=13)

            # All Subplots: plot of parameter values for PEs in density distribution
            N = params_used.shape[1]
            row = 1
            col = 0
            show_legend = True
            for i in range(len(params_used_names)):
                p = np.array(params_used[i])[0]
                p_min = np.min(p)
                p_max = np.max(p)
                p_sample = (p_max - p_min) * sample_interval / 100
                if p_sample == 0:
                    val = np.array(p_min)
                    dist_density = np.array(1)
                else:
                    p_range = np.arange(p_min, p_max, p_sample)
                    val = p_range + p_sample / 2
                    p_range = np.concatenate((p_range, [p_max + 1]))
                    p_range[0] = p_range[0] - 1
                    dist_density = np.zeros(len(p_range) - 1)
                    for j in range(len(dist_density)):
                        p_j = p[p >= p_range[j]]
                        p_j = p_j[p_j < p_range[j + 1]]
                        dist_density[j] = len(p_j) / N

                # Trace barplots
                x_data = val  # Get x-axis labels (parameter values)
                y_data = dist_density  # Get y-axis values (parameter initial values)
                trace_bar = go.Bar(x=x_data, y=y_data,
                                   name=params_used_names[i],
                                   legendgroup=params_used_names[i],
                                   showlegend=False
                                   )

                # Trace mean and CI (asymmetric)
                x_data = np.array([np.mean(p)])
                y_data = np.array([-0.1 * np.max(dist_density)])

                p = np.sort(p)
                factor = (100 - confidence) / 200
                n_cut = int(factor * N)
                error_bar = p[-n_cut] - x_data
                error_bar_minus = x_data - p[n_cut]

                trace_CI = go.Scatter(x=x_data, y=y_data, mode='markers', line=dict(color='black'),
                                      name=f'{confidence}% (CI)',
                                      error_x=dict(type='data',
                                                   symmetric=False,
                                                   array=error_bar,
                                                   arrayminus=error_bar_minus,
                                                   color='black',
                                                   thickness=2.5,
                                                   width=6,
                                                   ),
                                      marker=dict(color='black', size=8, opacity=.6),
                                      legendgroup=f'{confidence}% CI',
                                      showlegend=show_legend
                                      )

                y_data = np.array([-0.2 * np.max(dist_density)])
                error_bar = np.array([std_dev[i]])

                trace_std = go.Scatter(x=x_data, y=y_data, mode='markers', line=dict(color='darkturquoise'),
                                       name='SD',
                                       error_x=dict(type='data',
                                                    array=error_bar,
                                                    color='darkturquoise',
                                                    thickness=2.5,
                                                    width=6,
                                                    ),
                                       marker=dict(color='darkturquoise', size=8, opacity=.6),
                                       legendgroup='std_dev',
                                       showlegend=show_legend
                                       )

                col += 1
                if col > 4:
                    col = 1
                    row += 1

                fig3.add_trace(trace_bar, row=row, col=col)
                ub = 2
                if bounds[i][1] > 2:
                    ub = bounds[i][1]
                fig3['layout'][f'xaxis{i+1}'].update(range=[0,ub],
                                                     title_text='Parameter value',
                                                     showticklabels=True,
                                                     tick0=0,
                                                     dtick="L0.25",
                                                     nticks=10,
                                                     ticks="outside"
                                                     )
                fig3['layout'][f'yaxis{i + 1}'].update(title_text='Probability distribution')
                fig3.add_trace(trace_CI, row=row, col=col)
                fig3.add_trace(trace_std, row=row, col=col)
                # visualize lower and upper bound
                # lower bound
                fig3.add_vline(x=bounds[i][0], line_dash='dot', line_width=0.7, row=row, col=col,
                               annotation_text='lb', annotation_position="bottom right")
                # upper bound
                fig3.add_vline(x=bounds[i][1], line_dash='dash', line_width=0.7, row=row, col=col,
                               annotation_text='ub', annotation_position="bottom right")
                # Trace mean and fisher covariance (symmetric)
                if 'fisher' in self.allthedata[expID]['statistics'].keys():
                    if params_used_names[i] in self.allthedata[expID]['statistics']['fisher']['params_names']:
                        i_FIM = self.allthedata[expID]['statistics']['fisher']['params_names'].index(
                            params_used_names[i])
                        y_data = np.array([-0.3 * np.max(dist_density)])
                        error_bar = self.allthedata[expID]['statistics']['fisher']['std_dev'][i_FIM]

                        trace_fisher = go.Scatter(x=x_data, y=y_data, mode='markers', line=dict(color='gray'),
                                                  name='FIM',
                                                  error_x=dict(type='data',
                                                               array=error_bar,
                                                               color='gray',
                                                               thickness=2.5,
                                                               width=6,
                                                               ),
                                                  marker=dict(color='gray', size=8, opacity=.6),
                                                  legendgroup='FIM',
                                                  showlegend=show_legend
                                                  )

                        fig3.add_trace(trace_fisher, row=row, col=col)

                show_legend = False

            # Save figure
            fig3 = self._update_layout(fig3, plot_height=900, plot_width=1500)
            #fig3.update_xaxes(showgrid=True)
            fig3.update_yaxes(showgrid=True)
            self._save_fig(fig3, plot_name=f'{self.plot_info}_barplots_PE')

    def _rescale_time_axis(self, times, rescale_time):
        rescale_time_points = np.array([float(x) for x in rescale_time["time_points"]])
        rescale_time_points_new = rescale_time_points.copy()
        rescale_time_factors = np.array([float(x) for x in rescale_time["scaling_factors"]])

        # Process first time point
        times = np.array(times)
        times_new = np.array(times)

        # Rescaling
        times_new[times < rescale_time_points[0]] = times_new[times < rescale_time_points[0]] \
                                                    * rescale_time_factors[0]
        rescale_time_points_old = rescale_time_points_new.copy()
        rescale_time_points_new[0] = rescale_time_points_old[0] * rescale_time_factors[0]

        # Shifting
        delta_t = rescale_time_points_old[0] - rescale_time_points_new[0]
        times_new[times >= rescale_time_points[0]] = times_new[times >= rescale_time_points[0]] - delta_t
        if not times.size == 1:
            rescale_time_points_new[1:] = rescale_time_points_old[1:] - delta_t

            # Process additional time points
            for i in range(1, len(rescale_time_points)):
                # Rescaling
                times_new[(times >= rescale_time_points[i-1]) * (times < rescale_time_points[i])] \
                    = rescale_time_points_new[i-1] \
                      + (times_new[(times >= rescale_time_points[i-1]) * (times < rescale_time_points[i])]
                         - rescale_time_points_new[i-1]) * rescale_time_factors[i]
                rescale_time_points_old = rescale_time_points_new.copy()
                rescale_time_points_new[i] = rescale_time_points_old[i-1] \
                                             + (rescale_time_points_old[i] - rescale_time_points_old[i-1]) \
                                             * rescale_time_factors[i]

                # Shifting
                delta_t = rescale_time_points_old[i] - rescale_time_points_new[i]
                times_new[times >= rescale_time_points[i]] = times_new[times >= rescale_time_points[i]] - delta_t
                rescale_time_points_new[i + 1:] = rescale_time_points_old[i + 1:] - delta_t

        return times_new

    def _save_fig(self, fig, plot_name):
        """ Function to save the figure as png and html file.

        :param fig: figure object
        :param plot_name:
        :return:
        """
        if "html" in self.plot_formats:
            plotly.offline.plot(fig, filename=os.path.join(self.path, plot_name + ".html"), auto_open=True) # Matteo changed to True
        if "png" in self.plot_formats:
            pio.write_image(fig, file=os.path.join(self.path, plot_name + ".png"), scale=3)
        if "svg" in self.plot_formats:
            pio.write_image(fig, file=os.path.join(self.path, plot_name + ".svg"), scale=3)


def plot_matplotlib(allthedata, path, plot_info=""):
    """
    Function for plotting with matplotlib.pyplot.

    :param allthedata: dict with all the measured and simulated data.
    :param path: path to folder where to save plots
    :param plot_info: plot info for name of saved plots
    """
    from matplotlib import pyplot

    for expID in allthedata.keys():
        variables_plot = [key for key in allthedata[expID]["variables"].keys() if
                          allthedata[expID]["variables"][key]["plotting"]["plot"]]

        fig, axs = pyplot.subplots(nrows=len(variables_plot), ncols=1, sharex=True, figsize=(10, 8))
        for index, key in enumerate(variables_plot):
            if allthedata[expID]["variables"][key]["times"].size != 0:
                # Plot measured data
                axs[index].plot(allthedata[expID]["variables"][key]["times"],
                                allthedata[expID]["variables"][key]["vals"], '.')
            if allthedata[expID]["simulation_data"]["times"]:
                # Plot simulated data
                axs[index].plot(allthedata[expID]["simulation_data"]["times"],
                                allthedata[expID]["simulation_data"]["vals"][key])

            axs[index].set_ylabel(allthedata[expID]["variables"][key]["description"])

        axs[-1].set_xlabel("Time [h]")
        fig.align_ylabels()

        # Save fig as png
        pyplot.savefig(os.path.join(path, f'exp{expID}_{plot_info}.png'))

    # pyplot.show()
    pyplot.close('all')
