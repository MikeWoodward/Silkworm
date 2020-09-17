#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Project: silkworm.

Description:
Silkworm is a poll-based US Presidential Election forecaster.

Author: Mike Woodward

Created on: 2020-07-26

"""

# %%---------------------------------------------------------------------------
# Module metadata
# -----------------------------------------------------------------------------
__author__ = "Mike Woodward"
__license__ = "MIT"


# %%---------------------------------------------------------------------------
# Imports
# -----------------------------------------------------------------------------
from bokeh.models.widgets import (Button,
                                  Div,
                                  Panel,
                                  Select,
                                  TextAreaInput)
from bokeh.layouts import column, row, Spacer


# %%---------------------------------------------------------------------------
# RunForecast
# -----------------------------------------------------------------------------
class RunForecast():
    """Run the forecast."""

    # %%
    def __init__(self, controller):
        """Initialize object.

        First part of two-part initialization.
        Put initialization code here that's very unlikely to fail.
        """
        self.controller = controller

        # Explains how to run the model.
        self.headingrunexplain = Div(
            text="""You can run an analysis or load an existing analysis. """
                 """Select the year for analysis then run the forecast.""",
            sizing_mode="""stretch_width""")

        self.loadedheading = Div(
            text="""<span style='font-weight:bold;font-size:14pt'>"""
                 """Year currently loaded.</span>""",
            sizing_mode="""stretch_width""")

        self.loaded = Div(
            text="""<span style='color:red;font-size:12pt'>"""
                 """No analysis year loaded.</span>""",
            sizing_mode="""stretch_width""")

        self.datainsystemheading = Div(
            text="""<span style='font-weight:bold;font-size:14pt'>"""
                 """Analysis years in system.</span>""",
            sizing_mode="""stretch_width""")

        self.datainsystem = TextAreaInput(
            title="""Elections years analyzed in system""",
            value="""No years in system""",
            rows=1)

        self.selecttheyeartoload = Select(
            title="""Year to load and display""",
            options=['dummy1', 'dummy2', 'dummy3'],
            value="""dummy1""")

        # Load year button
        self.loadyear = Button(
            label="""Load year""",
            width=300,
            button_type="""success""")

        self.forecastheading = Div(
            text="""<span style='font-weight:bold;font-size:14pt'>"""
                 """Election year to forecast.</span>""",
            sizing_mode="""stretch_width""")

        # Menu of available Presidential elections to forecast.
        self.selecttheyeartoforecast = Select(
            title="""Year to forecast""",
            options=['dummy1', 'dummy2', 'dummy3'],
            value="""dummy1""")
        # Run forecast button
        self.runforecast = Button(
            label="""Run forecast""",
            width=300,
            button_type="""success""")
        # Shows status of the forecast model.
        self.statusreport = TextAreaInput(
            title="""Forecast run response""",
            value="""No forecast results run.""",
            sizing_mode="""stretch_width""",
            rows=6)

        # Layout the widgets
        r1 = row(children=[self.headingrunexplain])
        c1 = column(children=[self.forecastheading,
                              self.selecttheyeartoforecast,
                              self.runforecast,
                              self.statusreport])
        c2 = column(children=[self.datainsystemheading,
                              self.datainsystem,
                              self.selecttheyeartoload,
                              self.loadyear])
        c3 = column(children=[self.loadedheading,
                              self.loaded])

        self.layout = column(children=[r1,
                                       row(children=[c1,
                                                     Spacer(width=40),
                                                     c2,
                                                     Spacer(width=40),
                                                     c3])],
                             sizing_mode='scale_width')
        self.panel = Panel(child=self.layout,
                           title='Run/load forecast')

    # %%
    def setup(self):
        """Set up object.

        Second part of two-part initialization.
        Place initialization code here that's more likely to fail.
        """
        # Setup the callbacks.
        self.runforecast.on_click(
            self.callback_runforecast)
        self.selecttheyeartoload.on_change(
            "value",
            self.callback_selecttheyeartoload)
        self.loadyear.on_click(
            self.callback_loadyear)
        self.selecttheyeartoforecast.on_change(
            "value",
            self.callback_selecttheyeartoforecast)

    # %%
    def update(self, years):
        """Update view object."""
        self.datainsystem.value =  \
            ' | '.join([str(y) for y in years['analysis']])

        _available = list(set(years['summary']) &
                          set(years['allocations']) &
                          set(years['polls']))

        self.selecttheyeartoforecast.options = [str(year) for year
                                                in _available]
        self.selecttheyeartoforecast.value = str(max(_available))

        self.selecttheyeartoload.options = [str(year) for year
                                            in _available]
        self.selecttheyeartoload.value = str(max(_available))

    # %%
    def callback_runforecast(self):
        """Execute callback for the Button attribute self.runforecast."""
        self.statusreport.value = self.controller.calculate_forecast(
            int(self.selecttheyeartoforecast.value))

        self.controller.update()

    # %%
    def callback_loadyear(self):
        """Execute callback for the Button attribute self.loadyear."""
        _year = int(self.selecttheyeartoload.value)
        _text = self.controller.load_forecast(_year)
        self.loaded.text = ("""<span style='font-weight:bold;"""
                            """color:purple;font-size:64pt'>{0}"""
                            """</span>"""
                            """<br>"""
                            """<span style='font-size:10pt'>"""
                            """{1}</span>""").format(_year, _text)

    # %%
    def callback_selecttheyeartoload(self,  attrname, old, new):
        """Execute callback for self.selecttheyeartoload."""
        self.loadyear.label = """Load year {0}""".format(new)

    # %%
    def callback_selecttheyeartoforecast(self,  attrname, old, new):
        """Execute callback for self.selecttheyeartoforecast."""
        self.runforecast.label = """Run forecast for year {0}""".format(new)
