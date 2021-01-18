#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Project: silkworm

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
from random import sample
import pandas as pd
from bokeh.models.widgets import (DataTable,
                                  DateRangeSlider,
                                  Panel,
                                  Select,
                                  TableColumn)
from bokeh.models import ColumnDataSource, DateFormatter
from bokeh.layouts import column, row, Spacer


# %%---------------------------------------------------------------------------
# PollViewer
# -----------------------------------------------------------------------------
class PollViewer():
    """Shows the polls in the system for the selected election."""

    # %%
    def __init__(self, controller):
        """Initialize object.

        First part of two-part initialization.
        Put initialization code here that's very unlikely to fail.
        """
        self.controller = controller
        self.polls = None

        # Table
        # =====
        # Stub code for DataTable setup.
        _df = pd.DataFrame(
            {'State name': ['Alaska'],
             'Start date': ['2020-01-01'],
             'End date': ['2020-01-10'],
             'Polling company': ['Good Polls Inc'],
             'Poll ID': [123456],
             'Sample size': [1000],
             'Democratic %': [44.9],
             'Republican %': [45.1]})
        _df['Start date'] = pd.to_datetime(_df['Start date'])
        _df['End date'] = pd.to_datetime(_df['End date'])
        self.pollsource = ColumnDataSource(_df)
        columns = [TableColumn(field='State name', title='State name'),
                   TableColumn(field='Start date',
                               title='State date',
                               formatter=DateFormatter()),
                   TableColumn(field='End date',
                               title='End date',
                               formatter=DateFormatter()),
                   TableColumn(field='Polling company',
                               title='Polling company'),
                   TableColumn(field='Poll ID', title='Poll ID'),
                   TableColumn(field='Sample size', title='Sample size'),
                   TableColumn(field='Democratic %', title='Democratic %'),
                   TableColumn(field='Republican %', title='Republican %')]
        # Opinion polls in the system.
        self.opinionpolls = DataTable(
            source=self.pollsource,
            columns=columns,
            index_position=None,
            sizing_mode="""stretch_both""")
        # Other widgets
        # =============
        # Date range
        self.choosedates = DateRangeSlider(
            title="""Choose the date for display""",
            start="""2018-11-13T20:20:39+00:00""",
            end="""2025-11-13T20:20:39+00:00""",
            step=24*60*60*1000,
            value=("""2018-11-13T20:20:39+00:00""",
                   """2025-11-13T20:20:39+00:00"""),
            sizing_mode="stretch_width")
        # State
        self.selectstate = Select(
            title="""State""",
            options=['dummy1', 'dummy2', 'dummy3'],
            value="""dummy1""",
            sizing_mode="stretch_width")

        # Layout the widgets
        # ==================
        row1 = row(children=[self.choosedates,
                             Spacer(width=50),
                             self.selectstate])
        layout = column(children=[self.opinionpolls,
                                  row1,
                                  Spacer(height=75,
                                         sizing_mode='scale_width')],
                        sizing_mode='stretch_both')
        self.panel = Panel(child=layout,
                           title='Poll viewer')

    # %%
    def setup(self):
        """Set up object.

        Second part of two-part initialization.
        Place initialization code here that's more likely to fail.
        """
        # Setup the callbacks.
        self.choosedates.on_change("value", self.callback_choosedates)
        self.selectstate.on_change("value", self.callback_selectstate)

    # %%
    def update(self, polls):
        """Update view object."""
        self.polls = polls

        _states = sorted(self.polls['State name'].unique().tolist())
        self.selectstate.options = _states
        self.selectstate.value = sample(_states, 1)[0]

        self.choosedates.start = self.polls['start_date'].min()
        self.choosedates.end = self.polls['end_date'].max()
        self.choosedates.value = (
            self.polls['start_date'].min(),
            self.polls['end_date'].max())

        self._update_table()

    # %%
    def _update_table(self):
        """Update table."""
        _slice = self.polls[
            (self.polls['State name'] == self.selectstate.value)
            & (self.polls['start_date']
               >= self.choosedates.value_as_datetime[0])
            & (self.polls['end_date']
               <= self.choosedates.value_as_datetime[1])
            ].sort_values(['start_date', 'end_date'])

        self.pollsource.data = {
            'State name': _slice['State name'].to_list(),
            'Start date': _slice['start_date'].to_list(),
            'End date': _slice['end_date'].to_list(),
            'Polling company': _slice['pollster'].to_list(),
            'Poll ID': _slice['poll_id'].to_list(),
            'Sample size': _slice['sample_size'].to_list(),
            'Democratic %': _slice['Democratic'].to_list(),
            'Republican %': _slice['Republican'].to_list()}

    # %%
    def callback_choosedates(self, attrname, old, new):
        """Execute callback for self.callback_choosedates."""
        # pylint: disable=W0613
        self._update_table()

    # %%
    def callback_selectstate(self, attrname, old, new):
        """Execute callback for self.callback_selectstate."""
        # pylint: disable=W0613
        self._update_table()
