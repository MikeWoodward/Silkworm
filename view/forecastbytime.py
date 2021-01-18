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
from bokeh.models.widgets import (Panel)
from bokeh.plotting import figure
from bokeh.models import ColumnDataSource, HoverTool, Legend, Span
from bokeh.layouts import column, Spacer

import pandas as pd


# %%---------------------------------------------------------------------------
# ForecastByTime
# -----------------------------------------------------------------------------
class ForecastByTime():
    """Shows the forecasted electoral college votes over time."""

    # %%
    def __init__(self, controller):
        """Initialize object.

        First part of two-part initialization.
        Put initialization code here that's very unlikely to fail.
        """
        self.controller = controller

        # Shows the forecast for electoral college votes over time.
        self.electoralcollegevotesbytime = figure(
            title="""Electoral college votes by date""",
            x_axis_type="""datetime""",
            x_axis_label="""Date""",
            y_axis_label="""Electoral college votes""",
            sizing_mode="""stretch_both""")
        # Create dummy data for the plot
        _df = pd.DataFrame({'Date': ['2030-12-31', '2031-12-31'],
                            'Democratic maximum': [300, 238],
                            'Republican maximum': [238, 300]})
        _df['Date'] = pd.to_datetime(_df['Date'])
        self.cds = ColumnDataSource(_df)
        # Draw dummy lines
        _dg = self.electoralcollegevotesbytime.line(
            x='Date',
            y='Democratic maximum',
            line_color='blue',
            line_width=2,
            source=self.cds)
        _rg = self.electoralcollegevotesbytime.line(
            x='Date',
            y='Republican maximum',
            line_color='red',
            line_width=2,
            source=self.cds)
        # 270 to win line
        _win270 = Span(location=270, dimension='width')
        self.electoralcollegevotesbytime.add_layout(_win270)
        # Add a legend outside of the plot
        _legend = Legend(items=[('Democratic', [_dg]),
                                ('Republican', [_rg])],
                         location='top_right')
        self.electoralcollegevotesbytime.add_layout(_legend, 'right')
        self.electoralcollegevotesbytime.legend.click_policy = "hide"
        self.electoralcollegevotesbytime.y_range.only_visible = True

        # Hover tip
        # ---------
        # Now set up the hover tool
        hover = HoverTool(point_policy="follow_mouse",
                          renderers=[_dg, _rg],
                          tooltips=[("Date", '@Date{%F}'),
                                    ("Democratic",
                                     "@{Democratic maximum}"),
                                    ("Republican",
                                     "@{Republican maximum}")],
                          formatters={'@Date': 'datetime'})
        self.electoralcollegevotesbytime.add_tools(hover)

        # Layout the widgets
        self.layout = column(children=[self.electoralcollegevotesbytime,
                                       Spacer(sizing_mode='scale_width',
                                              height=50)],
                             sizing_mode="stretch_both")
        self.panel = Panel(child=self.layout,
                           title='Vote forecast by time')

    # %%
    def setup(self):
        """Set up object.

        Second part of two-part initialization.
        Place initialization code here that's more likely to fail.
        """
        # No widgets on this tab have a callback, so this is an empty method.
        pass

    # %%
    def update(self, electoral_maximum):
        """Update view object."""
        self.cds.data = {'Date': electoral_maximum['Date'],
                         'Democratic maximum':
                             electoral_maximum['Democratic maximum'],
                         'Republican maximum':
                             electoral_maximum['Republican maximum']}
