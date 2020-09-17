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
import pandas as pd
from bokeh.layouts import column, row, Spacer
from bokeh.models.widgets import (Panel,
                                  Select)
from bokeh.plotting import figure
from bokeh.models import ColumnDataSource, HoverTool,  Legend

from random import sample

# %%---------------------------------------------------------------------------
# Functions
# -----------------------------------------------------------------------------


# %%---------------------------------------------------------------------------
# ForecastByState
# -----------------------------------------------------------------------------
class ForecastByState():
    """Shows US electoral college vote forecast by state."""

    # %%
    def __init__(self, controller):
        """Initialize object.

        First part of two-part initialization.
        Put initialization code here that's very unlikely to fail.
        """
        self.controller = controller
        self.state = None
        self.polls = None

        # figure
        # ======
        # Shows the forecast for electoral college votes over time.
        self.statetime = figure(
            title="""Party voter proportions by state""",
            x_axis_type="""datetime""",
            x_axis_label="""Date""",
            y_axis_label="""Respondent proportion""",
            sizing_mode="""stretch_both""")
        # Create dummy data for the plot
        _df = pd.DataFrame({'Date': ['2030-12-31', '2031-12-31'],
                            'Democratic proportion': [0.1, 0.9],
                            'Democratic upper': [0.3, 0.9],
                            'Democratic lower': [0.1, 0.7],
                            'Republican proportion': [0.9, 0.1],
                            'Republican upper': [0.9, 0.3],
                            'Republican lower': [0.7, 0.1]})
        _df['Date'] = pd.to_datetime(_df['Date'])
        self.cds = ColumnDataSource(_df)
        # Draw dummy lines
        _dgl = self.statetime.line(
            x='Date',
            y='Democratic proportion',
            line_color='blue',
            line_width=2,
            source=self.cds)
        _rgl = self.statetime.line(
            x='Date',
            y='Republican proportion',
            line_color='red',
            line_width=2,
            source=self.cds)
        # Add circles for polls
        _df = pd.DataFrame({'Date': ['2030-12-31', '2031-12-31'],
                            'Pollster': ['Good pollster', 'Bad pollster'],
                            'Poll ID': [0, 1],
                            'Democratic proportion': [0.2, 0.8],
                            'Republican proportion': [0.8, 0.2]})
        _df['Date'] = pd.to_datetime(_df['Date'])
        self.cds_polls = ColumnDataSource(_df)
        _dgp = self.statetime.circle(x='Date',
                                     y='Democratic proportion',
                                     size=10,
                                     fill_color='blue',
                                     line_color='blue',
                                     alpha=0.2,
                                     source=self.cds_polls)
        _rgp = self.statetime.circle(x='Date',
                                     y='Republican proportion',
                                     size=10,
                                     fill_color='red',
                                     line_color='red',
                                     alpha=0.2,
                                     source=self.cds_polls)
        # Add upper and lower 95% confidence
        _bandd = self.statetime.varea(
            x='Date',
            y1='Democratic lower',
            y2='Democratic upper',
            source=self.cds,
            fill_color='blue',
            fill_alpha=0.1)
        _bandr = self.statetime.varea(
            x='Date',
            y1='Republican lower',
            y2='Republican upper',
            source=self.cds,
            fill_color='red',
            fill_alpha=0.1)
        # Legend
        # ------
        # Add a legend outside of the plot
        _legend = Legend(items=[('Democratic trend', [_dgl]),
                                ('Democratic 95%', [_bandd]),
                                ('Republican trend', [_rgl]),
                                ('Republican 95%', [_bandr]),
                                ('Democratic poll result', [_dgp]),
                                ('Republican poll result', [_rgp])],
                         location='top_right')
        self.statetime.add_layout(_legend, 'right')
        self.statetime.legend.click_policy = "hide"
        self.statetime.y_range.only_visible = True
        # Hover tip
        # ---------
        # Now set up the hover tool
        hover = HoverTool(point_policy="follow_mouse",
                          renderers=[_dgp, _rgp],
                          tooltips=[("Pollster", "@Pollster"),
                                    ("Poll ID", "@{Poll ID}"),
                                    ("Democratic",
                                     "@{Democratic proportion}{%0.1f}"),
                                    ("Republican",
                                     "@{Republican proportion}{%0.1f}")])
        self.statetime.add_tools(hover)
        # Legend policies
        # ---------------
        self.statetime.legend.click_policy = "hide"
        self.statetime.y_range.only_visible = True

        # Select state
        # ============
        self.selectstate = Select(
            title="""State""",
            options=['dummy1', 'dummy2', 'dummy3'],
            value="""dummy1""",
            sizing_mode="stretch_width")

        # Layout
        # ======
        r1 = row(children=[Spacer(width=10),
                           self.selectstate,
                           Spacer(width=10)],
                 sizing_mode='stretch_width')
        self.layout = column(children=[self.statetime,
                                       r1,
                                       Spacer(height=75,
                                              sizing_mode='scale_width')],
                             sizing_mode='stretch_both')
        self.panel = Panel(child=self.layout,
                           title='Time forecast by state')

    # %%
    def setup(self):
        """Set up object.

        Second part of two-part initialization.
        Place initialization code here that's more likely to fail.
        """
        # Setup the callbacks.
        self.selectstate.on_change(
            "value",
            self.callback_selectstate)

    # %%
    def update(self, state, polls):
        """Update view object."""
        # Make a copy of the state data
        self.state = state.copy()
        self.polls = polls
        self.state['Democratic lower'] =\
            self.state['Democratic proportion'] - self.state['Democratic SE']
        self.state['Democratic upper'] =\
            self.state['Democratic proportion'] + self.state['Democratic SE']
        self.state['Republican lower'] =\
            self.state['Republican proportion'] - self.state['Republican SE']
        self.state['Republican upper'] =\
            self.state['Republican proportion'] + self.state['Republican SE']

        # Update the selection with the states
        _states = self.state['State name'].unique().tolist()
        self.selectstate.options = _states
        self.selectstate.value = sample(_states, 1)[0]

        # Update the chart
        self._update_chart(self.selectstate.value)

    # %%
    def _update_chart(self, state):
        """Update chart based on date."""
        # Trend data
        # ----------
        _slice = self.state[self.state['State name'] == state]

        self.cds.data = {
            'Date': _slice['Date'].to_list(),
            'Democratic proportion': _slice['Democratic proportion'].to_list(),
            'Republican proportion': _slice['Republican proportion'].to_list(),
            'Democratic lower': _slice['Democratic lower'].to_list(),
            'Democratic upper': _slice['Democratic upper'].to_list(),
            'Republican lower': _slice['Republican lower'].to_list(),
            'Republican upper': _slice['Republican upper'].to_list()
            }

        # Poll data
        # ---------
        _slice = self.polls[self.polls['State name'] == state]

        self.cds_polls.data = {
            'Date': _slice['end_date'].to_list(),
            'Pollster': _slice['pollster'].to_list(),
            'Poll ID': _slice['poll_id'].to_list(),
            'Democratic proportion': (_slice['Democratic']/100).to_list(),
            'Republican proportion': (_slice['Republican']/100).to_list()
            }

    # %%
    def callback_selectstate(self,  attrname, old, new):
        """Execute callback for self.callback_selectstate."""
        self._update_chart(self.selectstate.value)
