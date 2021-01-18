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
from bokeh.io import curdoc
from bokeh.models.widgets import Tabs
from model.model import Model
from view.about import About
from view.managedata import ManageData
from view.runforecast import RunForecast
from view.forecastbytime import ForecastByTime
from view.forecastdistribution import ForecastDistribution
from view.forecastbygeography import ForecastByGeography
from view.forecastbystate import ForecastByState
from view.pollviewer import PollViewer


# %%---------------------------------------------------------------------------
# Controller
# -----------------------------------------------------------------------------
class Controller():
    """The Controller class is part of the model-view-controller architecture.

    Links views and Model and controls interaction between them."
    """

    # %%
    def __init__(self):
        """Initialize the object.

        First part of two-part initialization.
        The initialization done here should be low risk - we need the GUI to
        be built before we can show error messages.
        """
        self.model = Model()

        # Create the panels by instantiating each of the tabs. Note the order
        # in the list is the tab order in the GUI.
        self.about = About(self)
        self.managedata = ManageData(self)
        self.runforecast = RunForecast(self)
        self.forecastbytime = ForecastByTime(self)
        self.forecastdistribution = ForecastDistribution(self)
        self.forecastbygeography = ForecastByGeography(self)
        self.forecastbystate = ForecastByState(self)
        self.pollviewer = PollViewer(self)

        self.panels = [self.about,
                       self.managedata,
                       self.runforecast,
                       self.forecastbytime,
                       self.forecastdistribution,
                       self.forecastbygeography,
                       self.forecastbystate,
                       self.pollviewer]

        # Create tabs, note the order here is the display order.
        self.tabs = Tabs(tabs=[p.panel for p in self.panels])

    # %%
    def setup(self):
        """Set up object. Second part of two-part initialization."""
        for panel in self.panels:
            panel.setup()

    # %%
    def update(self):
        """Update the object."""
        self.model.read_rawdata()
        years = self.model.get_years()
        self.managedata.update(years)
        self.runforecast.update(years)

    # %%
    def cross_check(self):
        """Cross checks the model data."""
        return self.model.cross_check()

    # %%
    def calculate_forecast(self, year):
        """Calculate the forecast for the election year."""
        self.model.calculate_forecast(year)
        if ~self.model.error_status:
            return "Forecast completed without error."
        else:
            return self.model.error_string

    # %%
    def load_forecast(self, year):
        """Load forecast data into model."""
        self.model.load_forecast(year)
        if ~self.model.error_status:
            # Update the plots with the newly loaded data
            self.forecastbytime.update(self.model.electoral_maximum)
            self.forecastdistribution.update(self.model.electoral_distribution)
            self.forecastbygeography.update(self.model.state)
            self.forecastbystate.update(self.model.state, self.model.polls)
            self.pollviewer.update(self.model.polls)
            return "Year forecast loaded without error."
        else:
            return self.model.error_string

    # %%
    def display(self):
        """Display the visualization.

        Calls the Bokeh methods to make the
        application start. Note the server actually renders the GUI in the
        browser.

        Returns
        -------
        None
        """
        curdoc().add_root(self.tabs)
        curdoc().title = 'silkworm'
