#!/usr/bin/env python2
# -*- coding: utf-8 -*-
"""
Created on Sun Mar  5 21:57:22 2017

@author: mikewoodward

For details of licensing etc, see the Github page:
    https://github.com/MikeWoodward/PresidentialPredictor
"""


# =============================================================================
# Imports
# =============================================================================
import datetime
from math import erf, sqrt
import pandas as pd


# =============================================================================
# Functions
# =============================================================================
def std_dev(proportion, observations):

    """Returns the standard deviation of the proportion"""

    return sqrt((proportion*(1.0-proportion)) / observations)


def win_prob(margin, std_dev):

    """Returns the win probability for a candidate. Margin is that candidates
    margin over their closest rival. std_dev is the std_dev of the
    proportion"""

    return 0.5*(1.0 + erf(margin / (sqrt(2.0)*std_dev)))


# =============================================================================
# States
# =============================================================================
class States(object):

    """Hold state level forecasts"""

    def __init__(self, previous_results, current_polls,
                 previous_election_date, current_election_date):

        self.results = previous_results
        self.polls = current_polls
        self.current = current_election_date
        self.previous = previous_election_date

        self.poll_limit = 10
        self.poll_sum = 10

        # Arbitrary campaign start date of May 1
        self.start_date = datetime.datetime(self.current.year, 5, 1)

    def prepare_data(self):

        """Prepare the data structures"""

        # Find how many polls were conducted in each state
        count = self.polls.groupby('State').size()

        # Select state with more than poll_limit polls - any less and the
        # previous election result is a more reliable indicator
        self.states = count[count >= self.poll_limit].index.values

        # Set up the daily data structure - copy the results because we
        # get a warning about modifying slices otherwise
        self.daily = self.results.copy()
        self.daily.rename(columns={'Election date': 'Date'}, inplace=True)

        self.daily['Margin sd'] = 0
        self.daily['Dem probability'] = 1.0*(self.daily['Margin'] > 0)
        self.daily['Oth probability'] = 0  # Hard coded!
        self.daily['Rep probability'] = 1.0*(self.daily['Margin'] < 0)
        self.daily['Method'] = 'Election'

    def averages(self):

        """Averages state polls."""

        # In theory, we could do this in a very Pythonic way, but I couldn't
        # figure out a way of doing it without conditional logic.

        # Get a count of how many polls took place in each state on each date
        date_count = self.polls[self.polls['State'].isin(self.states)] \
                         .groupby(['State', 'Poll end date'])['Poll ID'] \
                         .count() \
                         .reset_index() \
                         .rename(columns={'Poll ID': 'Poll count'})

        # We need an inverse cumsum here - the only good way of doing it
        # is by two sorts - one to put the dates in ascending order...
        date_count.sort_values(['State', 'Poll end date'],
                               ascending=[True, True],
                               inplace=True)

        # ...now do the cumsum...
        date_count['cum sum'] = date_count.groupby('State')['Poll count'] \
                                          .cumsum()

        # ...now sort the dates in the order we want
        date_count.sort_values(['State', 'Poll end date'],
                               ascending=[True, False],
                               inplace=True)

        # The poll averages
        avgs = []

        # We'll produce an average value by looping over all states
        for state in self.states:

            # The dates polls took place in this state
            state_date = date_count[date_count['State'] == state]

            # All the polls that took place in this state
            state_polls = self.polls[self.polls['State'] == state]

            # Loop over all date entries - this is a fast way of doing it
            for idx in range(state_date.shape[0]):

                # If the sum of all poll that took place in this state up to
                # this date is less than poll_limit, don't do any averaging -
                # it's too unreliable.
                if state_date.iloc[idx]['cum sum'] < self.poll_limit:
                    break

                # We're going to take an average value by summing up the polls
                cum_sum = 0
                date_list = []

                # Sum over at least the last self.poll_sum polls
                # n is an index offset - we go backwards from the current entry
                # day by day until we have at least the needed number of polls.
                # date_list is list of the dates we need to sum over.
                n = 0
                while cum_sum < self.poll_sum:

                    element = state_date.iloc[idx - n]
                    cum_sum += element['Poll count']
                    date_list.append(element['Poll end date'])
                    n -= 1

                # date_set is the set of polls we're going to take the median
                # of. Note we're sorting on margin.
                date_set = state_polls[state_polls['Poll end date']
                                       .isin(date_list)].sort_values('Margin')

                # This is the fraction of the total set each observation
                # is for - used for median calculations.
                date_set['fraction'] = 1 - (date_set['Observations'].cumsum() /
                                            date_set['Observations'].sum())

                # Weighted median calculation
                w_med = date_set[date_set['fraction'] > 0.5].iloc[-1]

                # Built in assumption here is that 'other' is always third
                margin = w_med['Dem share'] - w_med['Rep share']
                obs = w_med['Observations']

                # Democratic and Republican standard deviations
                d_std_dev = std_dev(w_med['Dem share'], obs)
                r_std_dev = std_dev(w_med['Rep share'], obs)

                # Democratic and Republican win probabilities
                d_prob = win_prob(margin, d_std_dev)
                r_prob = win_prob(-margin, r_std_dev)

                # Standard deviation of the margin
                m_std_dev = std_dev(abs(margin), obs)

                avgs.append({'State': state,
                             'Date': state_date.iloc[idx]['Poll end date'],

                             'Dem share': w_med['Dem share'],
                             'Oth share': w_med['Oth share'],
                             'Rep share': w_med['Rep share'],

                             'Margin': margin,
                             'Margin sd': m_std_dev,

                             'Dem probability': d_prob,
                             'Oth probability': 1 - (d_prob + r_prob),
                             'Rep probability': r_prob})

        # Set up the daily data structure

        states_avgs = pd.DataFrame(avgs).sort_values(['State', 'Date'])

        states_avgs['Method'] = 'Poll average'

        self.daily = self.daily.append(states_avgs)

        # Rates the results in one of several categories:
        # safe (>5%), marginal (5-2.5%), tight (<2.5%).
        self.daily['Closeness'] = self.daily['Margin']\
                                      .apply(lambda x:
                                             'safe' if abs(x) > 0.05 else
                                             'marginal' if abs(x) > 0.025 else
                                             'tight')

        # Calculates a winner for each day
        self.daily['Winner'] = self.daily['Margin']\
                                   .apply(lambda x:
                                          'Dem' if x > 0 else
                                          'Rep' if x < 0 else
                                          'TOO CLOSE')

        # Sorting by date, state
        self.daily.sort_values(['Date', 'State'])

    def interpolate(self):

        """Interpolates the data on a daily basis"""

        # Now work out the ranges. We need two. The first is the full range
        # from the previous election. The second is a truncated range. We
        # use the full range for correct interpolation and the second range to
        # show a subset of data for analysis.

        full_days = pd.date_range(self.previous,
                                  self.daily['Date'].max())

        short_days = pd.date_range(self.start_date,
                                   self.daily['Date'].max())

        # Set up the index - we need to do this for interpolations
        self.daily.set_index(['Date', 'State'], inplace=True)

        # Now we're going to do some interpolation - unstacking, filling,
        # and restacking
        self.daily = self.daily.unstack().reindex(full_days).ffill()\
                         .reindex(short_days).stack()\
                         .sort_index(level=[1, 0]).reset_index()

        self.daily.columns.values[0] = 'Date'

    def get_daily_modified(self):

        """Returns the daily results as a percentage"""

        daily = self.daily

        daily['Democratic'] = daily['Dem share']*100
        daily['Other'] = daily['Oth share']*100
        daily['Republican'] = daily['Rep share']*100

        return daily

    def get_status(self):

        """Returns a status string"""

        # Find how many states are too close to call or show a change of
        # control

        winner = self.daily.groupby('State')['Winner'].unique()

        near = winner[winner.apply(lambda x: 'TOO CLOSE' in x)].index.tolist()

        coc = winner[winner.apply(lambda x: 'Dem' in x and
                                            'Rep' in x)].index.tolist()

        # States that are very tight

        close = self.daily.groupby('State')['Closeness'].unique()

        tight = close[close.apply(lambda x: 'tight' in x)].index.tolist()

        # Build warning string

        warnings = "States with at least one 'TOO CLOSE': {0}\n" \
                   "States with a change of control: {1}\n"  \
                   "States that are tight {2}\n".format(near,
                                                        coc,
                                                        tight)

        return warnings

    def get_latest_results(self):

        """Returns the results"""

        interim = self.daily[self.daily['Date'] ==
                             self.daily['Date'].max()].sort_values('Margin')

        return interim.drop(['Date',
                             'Dem probability',
                             'Oth probability',
                             'Oth share',
                             'Rep probability',
                             'Margin sd'], axis=1)

    def write_file(self):

        """Writes the daily file to csv"""
        self.daily.to_csv("Daily.csv")
