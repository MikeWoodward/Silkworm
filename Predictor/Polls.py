#!/usr/bin/env python2
# -*- coding: utf-8 -*-
"""
Created on Sun Mar  5 21:52:20 2017

@author: mikewoodward

For details of licensing etc, see the Github page:
    https://github.com/MikeWoodward/PresidentialPredictor
"""


# =============================================================================
# Imports
# =============================================================================
import os.path
import pandas as pd


# =============================================================================
# Polls
# =============================================================================
class Polls(object):

    """Class to hold polls"""

    def __init__(self):

        self.polls = pd.read_csv(os.path.join('NormalizedPollResponses',
                                              'NormalizedPollResponses.csv'),
                                 parse_dates=['Election date',
                                              'Poll start date',
                                              'Poll end date'])

        self.polls.sort_values(['Election date', 'State', 'Poll end date'],
                               ascending=[True, True, True],
                               inplace=True)

    def prepare_data(self):

        """Prepare the poll data"""

        # Calculate normalized results - exclude don't knows

        self.polls['Total'] = (self.polls['Democratic'] +
                               self.polls['Republican'] +
                               self.polls['Other'])

        self.polls['Dem share'] = (self.polls['Democratic'] /
                                   self.polls['Total'])

        self.polls['Rep share'] = (self.polls['Republican'] /
                                   self.polls['Total'])

        self.polls['Oth share'] = (self.polls['Other'] /
                                   self.polls['Total'])

        # We'll use the margin for sorting later on
        self.polls['Margin'] = (self.polls['Dem share'] -
                                self.polls['Rep share'])

        # Remove fields we're not using
        self.polls.drop(['Total'],
                        axis=1, inplace=True)

    def select(self, election):

        """Returns the results for a given election"""

        return self.polls[self.polls['Election date'] == election]
