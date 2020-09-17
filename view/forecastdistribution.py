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
from bokeh.models.widgets import (DateSlider,
                                  Panel)
from bokeh.plotting import figure
from bokeh.models import ColumnDataSource, Legend, Span
from bokeh.layouts import column, row, Spacer
from scipy.stats import norm


# %%---------------------------------------------------------------------------
# ForecastDistribution
# -----------------------------------------------------------------------------
class ForecastDistribution():
    """Shows the forecasted electoral college vote distribution."""

    # %%
    def __init__(self, controller):
        """Initialize object.

        First part of two-part initialization.
        Put initialization code here that's very unlikely to fail.
        """
        self.controller = controller

        self.electoral_distribution = None

        # Shows the forecast for electoral college votes over time.
        self.ecvdistribution = figure(
            title="""Electoral college votes distribution""",
            x_axis_type="""linear""",
            x_axis_label="""Electoral college votes""",
            y_axis_label="""Probability""",
            sizing_mode="""stretch_both""")
        # Fake data to make sure we don't get an empty renderer message
        self.cds = ColumnDataSource(
            data={'Electoral college votes': list(range(539)),
                  'Democratic distribution': norm.pdf(range(539),
                                                      loc=200,
                                                      scale=100),
                  'Republican distribution': norm.pdf(range(539),
                                                      loc=400,
                                                      scale=100)}
            )
        _dg = self.ecvdistribution.vbar(
            x='Electoral college votes',
            top='Democratic distribution',
            fill_color='blue',
            line_color='blue',
            line_width=1,
            width=1,
            alpha=0.2,
            source=self.cds)
        _rg = self.ecvdistribution.vbar(
            x='Electoral college votes',
            top='Republican distribution',
            fill_color='red',
            line_color='red',
            line_width=1,
            width=1,
            alpha=0.2,
            source=self.cds)
        # 270 to win line
        _win270 = Span(location=270, dimension='height')
        self.ecvdistribution.add_layout(_win270)
        # Add a legend outside of the plot
        _legend = Legend(items=[('Democratic', [_dg]),
                                ('Republican', [_rg])],
                         location='top_right')
        self.ecvdistribution.add_layout(_legend, 'right')
        self.ecvdistribution.legend.click_policy = "hide"
        self.ecvdistribution.y_range.only_visible = True

        # The date for charting.
        self.choosethedatefordisplay = DateSlider(
            title="""Choose the date for display""",
            start="""2018-11-13T20:20:39+00:00""",
            end="""2025-11-13T20:20:39+00:00""",
            step=24*60*60*1000,
            value="""2018-11-13T20:20:39+00:00""",
            sizing_mode="stretch_width")

        # Layout the widgets
        r1 = row(children=[Spacer(width=10),
                           self.choosethedatefordisplay,
                           Spacer(width=10)],
                 sizing_mode='stretch_width')
        self.layout = column(children=[self.ecvdistribution,
                                       r1,
                                       Spacer(height=75,
                                              sizing_mode='scale_width')],
                             sizing_mode='stretch_both')
        self.panel = Panel(child=self.layout,
                           title='Vote forecast distribution')

    # %%
    def setup(self):
        """Set up object.

        Second part of two-part initialization.
        Place initialization code here that's more likely to fail.
        """
        # Setup the callbacks.
        self.choosethedatefordisplay.on_change(
            "value",
            self.callback_choosethedatefordisplay)

    # %%
    def update(self, electoral_distribution):
        """Update view object."""
        self.electoral_distribution = electoral_distribution
        self.choosethedatefordisplay.end =\
            self.electoral_distribution['Date'].max()
        self.choosethedatefordisplay.value =\
            self.electoral_distribution['Date'].max()
        self.choosethedatefordisplay.start =\
            self.electoral_distribution['Date'].min()

        self._update_chart(self.choosethedatefordisplay.value_as_datetime)

    # %%
    def _update_chart(self, date):
        """Redraw the chart by updating underlying data."""
        _slice =\
            (self.electoral_distribution[
                self.electoral_distribution['Date'] == date]
                [['Electoral college vote',
                  'Democratic distribution',
                  'Republican distribution']])
        self.cds.data =\
            {'Electoral college votes': _slice['Electoral college vote'],
             'Democratic distribution': _slice['Democratic distribution'],
             'Republican distribution': _slice['Republican distribution']}

    # %%
    def callback_choosethedatefordisplay(self, attrname, old, new):
        """Execute callbackfor the DateSlider self.choosethedatefordisplay."""
        self._update_chart(self.choosethedatefordisplay.value_as_datetime)
