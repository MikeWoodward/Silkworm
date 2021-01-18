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
import json
import os
import random

from bokeh.models.widgets import (DateSlider,
                                  Panel)
from bokeh.plotting import figure
from bokeh.models import ColumnDataSource, HoverTool
from bokeh.layouts import column, row, Spacer
from bokeh.palettes import brewer

import pandas as pd
import numpy as np

# %%---------------------------------------------------------------------------
# Constants
# -----------------------------------------------------------------------------
MAP_FOLDER = 'maps'


# %%---------------------------------------------------------------------------
# ForecastByGeography
# -----------------------------------------------------------------------------
class ForecastByGeography():
    """Shows US map and electoral college votes by state."""

    # %%
    def __init__(self, controller):
        """Initialize object.

        First part of two-part initialization.
        Put initialization code here that's very unlikely to fail.
        """
        self.controller = controller
        self.state = None
        self.state_src = None

        # State maop of the US.
        self.stateusmap = figure(
            title="""Electoral college votes by time and geography""",
            x_axis_location=None,
            y_axis_location=None,
            x_axis_type="""linear""",
            sizing_mode="""stretch_both""")
        self.stateusmap.xgrid.visible = False
        self.stateusmap.ygrid.visible = False

        # The date for charting.
        self.choosethedatefordisplay = DateSlider(
            title="""Choose the date for display""",
            start="""2018-11-13T20:20:39+00:00""",
            end="""2025-11-13T20:20:39+00:00""",
            step=24*60*60*1000,
            value="""2018-11-13T20:20:39+00:00""",
            sizing_mode="stretch_width")

        # Layout the widgets
        row1 = row(children=[Spacer(width=10),
                             self.choosethedatefordisplay,
                             Spacer(width=10)],
                   sizing_mode='stretch_width')
        self.layout = column(children=[self.stateusmap,
                                       row1,
                                       Spacer(height=75,
                                              sizing_mode='scale_width')],
                             sizing_mode='stretch_both')
        self.panel = Panel(child=self.layout,
                           title='Forecast by geography')

    # %%
    def setup(self):
        """Set up object.

        Second part of two-part initialization.
        Place initialization code here that's more likely to fail.
        """
        # Load the files containing the state outlines and the Alaska/Hawaii
        # dividing lines
        _folder = os.path.dirname(os.path.realpath(__file__))
        _state_j = json.load(
            open(os.path.join(_folder, MAP_FOLDER, "state.json"), 'r'))
        _state = pd.DataFrame(_state_j['data'])
        _state = _state.sort_values('State abbreviation')
        _state['color'] = random.choices(brewer['RdBu'][11],
                                         k=_state.shape[0])
        _state['Democratic percentage'] = np.random.rand(_state.shape[0])
        _state['Republican percentage'] = np.random.rand(_state.shape[0])

        _frame_j = json.load(
            open(os.path.join(_folder, MAP_FOLDER, "frame.json"), 'r'))
        # Set up the sources
        self.state_src = ColumnDataSource(_state)
        frame_src = ColumnDataSource(data=dict(x=_frame_j['data']['x'],
                                               y=_frame_j['data']['y']))
        # Draw the states and the lines
        states = self.stateusmap.patches(xs='x',
                                         ys='y',
                                         source=self.state_src,
                                         fill_alpha=0.5,
                                         fill_color='color',
                                         line_color="gray",
                                         line_width=0.5)
        # The frame that separates AK, HI from the rest of the US
        self.stateusmap.multi_line(xs='x',
                                   ys='y',
                                   source=frame_src,
                                   line_color="gray",
                                   line_width=1.0)
        # Now set up the hover tool - so the state name is given
        hover = HoverTool(point_policy="follow_mouse",
                          renderers=[states],
                          tooltips=[("State name",
                                     "@{State name}"),
                                    ("State abbreviation",
                                     "@{State abbreviation}"),
                                    ("Democratic",
                                     "@{Democratic percentage}{%0.1f}"),
                                    ("Republican",
                                     "@{Republican percentage}{%0.1f}")])
        self.stateusmap.add_tools(hover)

        # Setup the callbacks.
        self.choosethedatefordisplay.on_change(
            "value",
            self.callback_choosethedatefordisplay)

    # %%
    def update(self, state):
        """Update view object."""
        # Make a copy of the state data and change the copy
        self.state = state.copy()
        self.state['color index'] = self.state['Spread D-R']*100
        self.state['color index'] = pd.cut(
            self.state['color index'],
            [-100, -10, -5, -2, -1, -0.5, 0.5, 1, 2, 5, 10, 100],
            labels=[10, 9, 8, 7, 6, 5, 4, 3, 2, 1, 0])
        self.state['color'] =\
            self.state['color index'].map(
                {k: v for k, v in enumerate(brewer['RdBu'][11])})

        self.choosethedatefordisplay.start = self.state['Date'].min()
        self.choosethedatefordisplay.value = self.state['Date'].max()
        self.choosethedatefordisplay.end = self.state['Date'].max()

        self._update_chart(self.choosethedatefordisplay.value_as_datetime)

    # %%
    def _update_chart(self, date):
        """Update chart based on date."""
        _slice = self.state[self.state['Date'] == date]

        self.state_src.data['color'] = \
            _slice[['State abbreviation',
                    'color']].sort_values(
                        'State abbreviation')['color'].to_list()
        self.state_src.data['Democratic percentage'] = \
            _slice[['State abbreviation',
                    'Democratic proportion']].sort_values(
                        'State abbreviation')[
                            'Democratic proportion'].to_list()
        self.state_src.data['Republican percentage'] = \
            _slice[['State abbreviation',
                    'Republican proportion']].sort_values(
                        'State abbreviation')[
                            'Republican proportion'].to_list()

    # %%
    def callback_choosethedatefordisplay(self, attrname, old, new):
        """Execute callback method for self.choosethedatefordisplay."""
        # pylint: disable=W0613
        self._update_chart(self.choosethedatefordisplay.value_as_datetime)
