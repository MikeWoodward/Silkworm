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
                                  TextAreaInput)
from bokeh.layouts import column, row

# %%---------------------------------------------------------------------------
# Functions
# -----------------------------------------------------------------------------


# %%---------------------------------------------------------------------------
# ManageData
# -----------------------------------------------------------------------------
class ManageData():
    """Panel to manage data sources."""

    # %%
    def __init__(self, controller):
        """Initialize object safely.

        Put initialization code here that's very unlikely to fail.
        """
        self.controller = controller

        self.help = Div(
            text="""This tab displays the raw data in the system. """
                 """You can run forecasts for any election year where you """
                 """have electoral college, results, and polling data. """
                 """The cross-check button cross checks the data for """
                 """consistency.""",
            sizing_mode="""stretch_width""")

        self.datainsystemheading = Div(
            text="""<span style='font-weight:bold;font-size:14pt'>"""
                 """Data in system.</span>""",
            sizing_mode="""stretch_width""")
        # Displays the Electoral College Vote allocations by year.
        self.ecvyearallocations = TextAreaInput(
            title="""Electoral college vote allocations in system""",
            value="""No allocations in system""",
            rows=1)
        # Displays the election result years in the system.
        self.electionresults = TextAreaInput(
            title="""Presidential election results in system""",
            value="""No allocations in system""",
            rows=1)
        # Displays the Presidential polling in system.
        self.polling = TextAreaInput(
            title="""Presidential election polling in system""",
            value="""No allocations in system""",
            rows=1)
        self.crosscheckheading = Div(
            text="""<span style='font-weight:bold;font-size:14pt'>"""
                 """Cross-check data.</span>""",
            sizing_mode="""stretch_width""")
        # Header to explain what cross-check button does.
        self.headingverification = Div(
            text="""Click the button to start a cross-check that """
                 """the data in the system is both correct and consistent.""",
            width=300)
        # Starts the verification data cross-check..
        self.verificationbutton = Button(
            label="""Cross-check data.""",
            width=300,
            button_type="""success""")
        # Displays the results of the cross-check.
        self.verfificationresults = TextAreaInput(
            title="""Cross-check results""",
            value="""Cross-check verification not run.""",
            rows=6,
            width=610)

        # Layout the widgets
        self.layout = column(
            children=[row(self.help),
                      row(self.datainsystemheading),
                      row(children=[self.ecvyearallocations,
                                    self.electionresults,
                                    self.polling]),
                      row(children=[self.crosscheckheading]),
                      row(children=[self.headingverification,
                                    self.verificationbutton]),
                      row(children=[self.verfificationresults])],
            sizing_mode='scale_width')

        self.panel = Panel(child=self.layout,
                           title='Manage data')

    # %%
    def setup(self):
        """Set up object.

        Second part of two-part initialization.
        Place initialization code here that's more likely to fail.
        """
        # Setup the callbacks.
        self.verificationbutton.on_click(self.callback_verificationbutton)

    # %%
    def update(self, years):
        """Update view object."""
        self.ecvyearallocations.value = \
            ' | '.join([str(y) for y in years['allocations']])
        self.ecvyearallocations.rows = 6

        self.electionresults.value = \
            ' | '.join([str(y) for y in years['results']])
        self.electionresults.rows = 6

        self.polling.value = \
            ' | '.join([str(y) for y in years['polls']])
        self.polling.rows = 6

    # %%
    def callback_verificationbutton(self):
        """Execute callback for Button attribute self.verificationbutton."""
        self.verfificationresults.value = self.controller.cross_check()
        self.verfificationresults.rows = 6
