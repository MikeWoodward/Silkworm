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
import numpy as np
import pandas as pd
import numpy
import scipy
import scipy.special

# %%---------------------------------------------------------------------------
# Constants
# -----------------------------------------------------------------------------
CONFIDENCE95 = 1.96


# %%---------------------------------------------------------------------------
# Functions
# -----------------------------------------------------------------------------
def sigma(spread, observations):
    """Return the standard deviation of the proportion."""
    return numpy.sqrt((1 - pow(spread, 2)) / observations)


def win_prob(spread, observations):
    """Return the win probability for a candidate.

    spread is that candidate's spread over their closest rival.
    std_dev is the std_dev of the proportion.
    """
    return 0.5*(1.0 + scipy.special.erf(
        spread/(numpy.sqrt(2.0)*sigma(spread, observations))))


# %%---------------------------------------------------------------------------
# StateModel
# -----------------------------------------------------------------------------
class StateModel():
    """Models the state election results."""

    # %%
    def __init__(self,
                 results,
                 polls,
                 election_year):
        """Initialize."""
        self.year = election_year
        self.polls = polls
        self.start_date = pd.to_datetime('{0}-01-01'.format(self.year))

        # The state dataframe will hold the results. We're going to seed
        # the state frame with the results from the previous election, hence
        # the -4.
        self.state = results[results['Year'] == election_year - 4].copy()

    # %%
    def setup(self):
        """
        Set up the data structures.

        Riskier setup done here, so init method less likely to fail.
        """
        # Setup the states. Use 1st January of the year as our starting point.
        # Work out a Democratic and Republican probability of winning using
        # the previous election results. The use of the number 100 to get the
        # probabilities is a 'fudge' factor to introduce some uncertainty into
        # the analysis. Because 3rd party candidates haven't come in first
        # or second place in any recent election, I'm going to ignore them
        # here and set the Republican probability to be 1-Democratic
        # probability.
        self.state = (self.state
                      .assign(**{'All votes':
                                 (lambda x:
                                  x['Democratic votes'] +
                                  x['Other votes'] +
                                  x['Republican votes'])})
                      .assign(**{'Democratic proportion':
                                 (lambda x:
                                  (x['Democratic votes']/x['All votes']))})
                      .assign(**{'Republican proportion':
                                 (lambda x:
                                  (x['Republican votes']/x['All votes']))})
                      .assign(**{'Spread D-R':
                                 (lambda x:
                                  (x['Democratic votes'] -
                                   x['Republican votes']) /
                                  x['All votes'])})
                      .assign(**{'Date': self.start_date})
                      .assign(**{"Democratic probability":
                                 lambda x: win_prob(x['Spread D-R'], 100)})
                      .drop(columns=['Democratic votes',
                                     'Other votes',
                                     'Republican votes',
                                     'All votes',
                                     'Democratic electoral',
                                     'Other electoral',
                                     'Republican electoral',
                                     'Year']))

        # Pandas works faster when we pre-allocate memory as opposed
        # to growing dataframes one entry at a time. What we're going to
        # do is add dates to the self.state dataframe to grow to the
        # corect size. This will lead to lots of NAs that we'll overwrite
        # later.
        # Step1. Get the date range
        # The last day we can forecast is the date of the most recent poll.
        _dates = pd.DataFrame(
            {'Date': pd.date_range(start=self.start_date,
                                   end=self.polls['end_date'].max())})
        # Create column to do cartesian join on
        _dates['_m'] = _dates.shape[0]*[1]
        # Get state abbreviations and add column to join on
        _states = pd.DataFrame({'State abbreviation':
                                self.state['State abbreviation'].unique()})
        _states['_m'] = _states.shape[0]*[1]
        # Now do the cartesian join to give every state and every date
        _cartesian = _dates.merge(_states,
                                  on='_m',
                                  how='inner').drop(columns=['_m'])
        # Step 2. Now add it to the state frame to 'reserve' memory.
        # This gives us the January 1 data and NA entries for every
        # subsequent date.
        self.state = self.state.merge(_cartesian,
                                      on=['Date', 'State abbreviation'],
                                      how='outer')

        # We only care about polls that occurred after our start date.
        # Sort the polls by state and end_date.
        self.polls = (self.polls[self.polls['end_date'] >= self.start_date]
                      .sort_values(by=['State abbreviation', 'end_date'],
                                   ascending=[True, True]))

    # %%
    def update(self):
        """
        Update the state forecast with poll data.

        This method re-creates the state-level forecast from scratch each
        time because the new poll data may contain additional polls
        conducted in the past.
        """
        # Setup
        # -----
        # This is the window size, but because we use <= and >=, it's actually
        # the window size -1. This is a safer implementationm
        window = 6

        # Build state frame from polling data
        # -----------------------------------
        # Step through each state
        for state in self.polls['State abbreviation'].unique():
            state_slice = self.polls[self.polls['State abbreviation'] == state]
            # We need to step through each date to calculate an aggregate.
            # Obvously, we'll use the poll dates, but there's a corner case
            # where we have two polls on adjacent days. Using an entirely
            # backwards looking algorthm (poll end_date - 6 days) will
            # give an incorrect result in this case. So we look forward a
            # week to capture the corner case.
            _dummy = state_slice['end_date'].unique()
            _dates = np.unique(np.sort(np.concatenate(
                (_dummy, _dummy + pd.Timedelta(window, unit='d')))))

            # Step through each unique poll date
            for end_date in _dates:
                # Slice the data so there are window + 1 days' polls in the
                # slice. The sort is very important for the median
                # sample size calculation which comes next.
                date_slice = (state_slice[
                    (state_slice['end_date'] <= end_date) &
                    (state_slice['end_date'] >=
                     end_date - pd.Timedelta(window, unit='d'))]).sort_values(
                         'Spread D-R')
                # Aggregate over these window+1 days worth of polls
                spread = date_slice['Spread D-R'].median()

                # Get the sample size for the median, either directly or as
                # an 'estimate'.
                # If the slice is an odd number, the median is the middle
                # value.
                # Note the proportion of Democratic and Republican voters
                # will not sum to 1 in most cases due to 3rd party
                # candidates and don't knows/won't say.
                if date_slice.shape[0] % 2 != 0:
                    observations = date_slice.iloc[
                        date_slice.shape[0]//2]['sample_size']
                    democratic = date_slice.iloc[
                        date_slice.shape[0]//2]['Democratic']/100
                    republican = date_slice.iloc[
                        date_slice.shape[0]//2]['Republican']/100
                # The slice is an even number, so the median is between two
                # values.
                else:
                    upr = date_slice.shape[0]//2
                    lwr = upr - 1
                    observations = int(
                        sum([date_slice.iloc[lwr]['sample_size'],
                             date_slice.iloc[upr]['sample_size']])/2)
                    democratic = (
                        sum([date_slice.iloc[lwr]['Democratic'],
                             date_slice.iloc[upr]['Democratic']])/2)/100
                    republican = (
                        sum([date_slice.iloc[lwr]['Republican'],
                             date_slice.iloc[upr]['Republican']])/2)/100

                probability_democratic = win_prob(spread, observations)

                self.state.loc[
                    (self.state['State abbreviation'] == state) &
                    (self.state['Date'] == end_date),
                    'Observations'] = observations

                self.state.loc[
                    (self.state['State abbreviation'] == state) &
                    (self.state['Date'] == end_date), 'Spread D-R'] = spread

                self.state.loc[
                    (self.state['State abbreviation'] == state) &
                    (self.state['Date'] == end_date),
                    'Democratic probability'] = probability_democratic

                self.state.loc[
                    (self.state['State abbreviation'] == state) &
                    (self.state['Date'] == end_date),
                    'Democratic proportion'] = democratic

                self.state.loc[
                    (self.state['State abbreviation'] == state) &
                    (self.state['Date'] == end_date),
                    'Republican proportion'] = republican

        # Fill in state table
        # -------------------
        self.state['Republican probability'] = \
            1 - self.state['Democratic probability']
        # Using linear interpolation - we might want a smoother function in
        # the future. Important to sort in the correct order first. This
        # line of code relies on the first entry for each state being present.
        self.state.loc[~self.state['Observations'].isna(), 'Democratic SE'] = \
            (CONFIDENCE95*numpy.sqrt(
                (self.state[
                    'Democratic proportion']*(1-self.state[
                        'Democratic proportion']))/self.state['Observations']))
        self.state.loc[~self.state['Observations'].isna(), 'Republican SE'] = \
            (CONFIDENCE95*numpy.sqrt(
                (self.state[
                    'Republican proportion']*(1-self.state[
                        'Republican proportion']))/self.state['Observations']))

        self.state = self.state.sort_values(['State abbreviation', 'Date'])

        _states = []
        for _state in self.state['State abbreviation'].unique():
            _states.append(self.state[self.state['State abbreviation']
                                      == _state].interpolate(method='linear'))
        self.state = pd.concat(_states)
