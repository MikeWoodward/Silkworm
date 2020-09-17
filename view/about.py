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
import os
from bokeh.models.widgets import (Div,
                                  Panel)
from bokeh.layouts import column

# %%---------------------------------------------------------------------------
# Constants
# -----------------------------------------------------------------------------


# %%---------------------------------------------------------------------------
# About
# -----------------------------------------------------------------------------
class About():
    """Introduce software."""

    # %%
    def __init__(self, controller):
        """Initialize object.

        First part of two-part initialization.
        Put initialization code here that's very unlikely to fail.
        """
        self.controller = controller

        # First column HTML.
        self.column1 = Div(
            text="Placeholder",
            sizing_mode="""stretch_width""")

        # Layout the widgets
        self.layout = column(children=[self.column1],
                             sizing_mode='scale_width')
        self.panel = Panel(child=self.layout,
                           title='About')

    # %%
    def setup(self):
        """Set up object.

        Second part of two-part initialization.
        Place initialization code here that's more likely to fail.
        """
        view_folder = os.path.dirname(os.path.realpath(__file__))

        # Read in HTML from disk
        with open(os.path.join(view_folder, 'about_html.html'),
                  'r') as html:
            text = html.read()

        self.column1.text = text

    # %%
    def update(self):
        """Update view object.

        By default, just a stub. Depending
        on your implementation, it might not be needed.
        """
        pass
