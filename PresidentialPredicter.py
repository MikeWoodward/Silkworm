# -*- coding: utf-8 -*-
"""
Created on Thu Apr 14 21:48:22 2016

@author: mwoodward

Makes a forecast for who will win the US Presidential Election based on
state polling data.

To get the data:
    1. Run GetPollResponses - this retrieves the data from the Huffington Post
    Pollster API
    2. Run NormalizeResponses - this prepares the poll data for this program
    3. From the command line, run 'bokeh serve'
    4. Now, run this file

"""

# =============================================================================
# Imports
# =============================================================================
from bokeh.client import push_session
from bokeh.document import Document
from bokeh.layouts import row, widgetbox
from bokeh.models import ColumnDataSource, LabelSet
from bokeh.models.widgets import (CheckboxGroup, DataTable, Div,
                                  Panel, Select,
                                  TableColumn, Tabs)
from bokeh.plotting import figure
import datetime
from math import erf, sqrt
import numpy as np
import os.path
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


def array_para(x):

    """Returns a list of array parameters"""
    return [x[0]] + [0]*int(x[1] - 1) + [1 - x[0]]


# =============================================================================
# ElectionDates
# =============================================================================
class ElectionDates(object):

    """Class to store election dates"""

    def __init__(self):

        """Read the election dates"""

        self.dates = pd.read_csv(os.path.join("Input",
                                              "ElectionDates.csv"),
                                 parse_dates=['Election date'])

    def prepare_data(self):

        self.dates['Year'] = self.dates['Election date'].dt.year

    def select(self, year):

        """Returns the election date given teh election year."""

        return self.dates[self.dates['Year'] == year]['Election date'].iloc[0]


# =============================================================================
# Results
# =============================================================================
class Results(object):

    """Class to hold election results data"""

    def __init__(self, previous_election):

        """Read the election results"""

        self.results = pd.read_csv(os.path.join("Input",
                                                "ElectionResults.csv"),
                                   parse_dates=['Election date'])

    def prepare_data(self):

        """Sets the party share of the popular vote and other data prep
        tasks"""

        self.results['Total votes'] = (self.results['Democratic votes'] +
                                       self.results['Other votes'] +
                                       self.results['Republican votes'])

        self.results['Dem share'] = (self.results['Democratic votes'] /
                                     self.results['Total votes'])

        self.results['Rep share'] = (self.results['Republican votes'] /
                                     self.results['Total votes'])

        self.results['Oth share'] = (self.results['Other votes'] /
                                     self.results['Total votes'])

        self.results['Margin'] = (self.results['Dem share'] -
                                  self.results['Rep share'])

        self.results.drop(['Democratic electoral',
                           'Other electoral',
                           'Republican electoral',
                           'Democratic votes',
                           'Other votes',
                           'Republican votes',
                           'Total votes'], axis=1, inplace=True)

    def select(self, election):

        """Returns the results for a given election"""

        return self.results[self.results['Election date'] == election]


# =============================================================================
# CollegeAllocations
# =============================================================================
class CollegeAllocations(object):

    """Class to hold electoral college allocations"""

    def __init__(self):

        """Read in the data file and reformat the data"""
        self.alloc = pd.read_csv(os.path.join("Input",
                                              "ElectoralCollege.csv"))

    def prepare_data(self):

        """Reformats the dataframe"""

        self.alloc = pd.melt(self.alloc,
                             id_vars=['State'],
                             var_name='Election date',
                             value_name='Allocation')

        self.alloc['Election date'] = \
            pd.to_datetime(self.alloc['Election date'])

    def select(self, election):

        """Returns the electoral college allocation for an election"""

        return self.alloc[self.alloc['Election date'] == election]


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
                             'Dem share',
                             'Oth probability',
                             'Oth share',
                             'Rep probability',
                             'Rep share',
                             'Margin sd'], axis=1)

    def write_file(self):

        """Writes the daily file to csv"""
        self.daily.to_csv("Daily.csv")


# =============================================================================
# CollegeDistribution
# =============================================================================
class CollegeDistribution(object):

    """Class that holds data on the electoral college daily distribution"""

    def __init__(self, dailies, alloc):

        self.dailies = dailies
        self.alloc = alloc

    def calc_dist(self):

        """Calculate the electoral college vote distribution"""

        # Create a merged array that contains the daily data and the
        # allocations
        daily_alloc = self.dailies.merge(self.alloc)

        # Now store the generator polynomial. Create a temp structure first.
        daily_alloc['D temp'] = daily_alloc[['Dem probability',
                                             'Allocation']].values.tolist()

        daily_alloc['R temp'] = daily_alloc[['Rep probability',
                                             'Allocation']].values.tolist()

        daily_alloc['Dem poly'] = daily_alloc['D temp'].apply(array_para)
        daily_alloc['Rep poly'] = daily_alloc['R temp'].apply(array_para)

        # Now work out the electoral college distribution on a daily basis
        dist_ec = []
        for date in daily_alloc['Date'].unique():

            date_alloc = daily_alloc[daily_alloc['Date'] == date]

            cum_dem = [1]
            cum_rep = [1]

            for array in date_alloc['Dem poly']:

                cum_dem = np.convolve(cum_dem, array)

            cum_dem = np.fliplr([cum_dem])[0]

            for array in date_alloc['Rep poly']:

                cum_rep = np.convolve(cum_rep, array)

            cum_rep = np.fliplr([cum_rep])[0]

            dist_ec.append({'Date': date,
                            'Democratic': cum_dem,
                            'Republican': cum_rep,
                            'D_max': np.where(cum_dem == cum_dem.max())[0][0],
                            'R_max': np.where(cum_rep == cum_rep.max())[0][0]})

        self.dist = pd.DataFrame(dist_ec)

    def get_latest(self):

        t = self.dist[self.dist['Date'] ==
                      self.dist['Date'].max()]

        dem_dist = t['Democratic'].values[0].tolist()
        rep_dist = t['Republican'].values[0].tolist()

        return dem_dist, \
            rep_dist, \
            self.dist['Date'].max(), \
            dem_dist.index(max(dem_dist)), \
            rep_dist.index(max(rep_dist))


# =============================================================================
# Display
# =============================================================================
class Display(object):

    """Class that displays the results - uses Bokeh."""

    def __init__(self, current, previous, polls, states, college,
                 current_allocations):

        self.page_width = 1300
        self.page_height = 720

        self.current = current
        self.previous = previous

        self.polls = polls
        self.states = states
        self.college = college
        self.alloc = current_allocations

        self.d_dist, self.r_dist, self.ec_date, self.d_max, self.r_max = \
            self.college.get_latest()

        tabs = Tabs(tabs=[self.splash_page(),
                          self.ec_dist_page(),
                          self.ec_time_page(),
                          self.state_table(),
                          self.poll_page(),
                          self.state_polls(),
                          self.margin_weight(),
                          self.status_page()])

        document = Document()
        document.title = "Presidential predicter"
        document.add_root(tabs)
        session = push_session(document)
        session.show()

        session.loop_until_closed()

    def splash_page(self):

        with open(os.path.join("HTML templates", "splash.html"), 'r') as h:
            html = h.read()

        html = html.format(self.ec_date.date(),
                           self.d_max,
                           self.r_max,
                           self.current.date(),
                           self.previous.date())

        d = Div(text=html, width=self.page_width, height=self.page_height)

        return Panel(child=widgetbox(d), title="Title")

    def status_page(self):

        html = "<h1>Status</h1>"
        html += "<p>Number of opinion polls used: {0}</p>"\
                .format(self.polls['Poll ID'].nunique())
        html += "<p>{0}</p>".format(self.states.get_status().replace('\n',
                                                                     '<br>'))

        d = Div(text=html, width=self.page_width, height=self.page_height)

        return Panel(child=widgetbox(d), title="Status")

    def state_table(self):

        margin = self.states.get_latest_results()
        margin_alloc = margin.merge(self.alloc)
        margin_alloc['Margin %'] = 100*margin_alloc['Margin']

        source = ColumnDataSource(margin_alloc)

        columns = [
                TableColumn(field="State", title="State", ),
                TableColumn(field="Method", title="Method"),
                TableColumn(field="Margin %", title="Margin %"),
                TableColumn(field="Closeness", title="Closeness"),
                TableColumn(field="Winner", title="Winner"),
                TableColumn(field="Allocation", title="Allocation")
            ]

        data_table = DataTable(source=source,
                               columns=columns,
                               width=self.page_width,
                               height=self.page_height)

        return Panel(child=widgetbox(data_table), title="State")

    def ec_time_page(self):

        p2 = figure(plot_width=self.page_width,
                    plot_height=self.page_height,
                    title="Electoral College over time",
                    x_axis_type="datetime")

        p2.multi_line([self.college.dist['Date'],
                       self.college.dist['Date'],
                       self.college.dist['Date']],
                      [self.college.dist['D_max'],
                       self.college.dist['R_max'],
                       len(self.college.dist['Date'])*[270]],
                      line_width=2,
                      color=["blue", "red", "black"],
                      alpha=[0.5, 0.5, 0.1])

        p2.xaxis.axis_label = 'Date'
        p2.yaxis.axis_label = "Electoral College votes"

        return Panel(child=p2, title="Electoral College over time")

    def ec_dist_page(self):

        dem = pd.DataFrame(range(len(self.d_dist)), columns=['EC'])
        dem['prob'] = self.d_dist
        dem = dem[dem['prob'] > 0]

        rep = pd.DataFrame(range(len(self.r_dist)), columns=['EC'])
        rep['prob'] = self.r_dist
        rep = rep[rep['prob'] > 0]

        p1 = figure(plot_width=self.page_width,
                    plot_height=self.page_height,
                    title="Electoral College distribution")

        p1.vbar(x=dem['EC'],
                width=1,
                bottom=0,
                top=dem['prob'].tolist(),
                color='blue',
                alpha=0.5)

        p1.vbar(x=rep['EC'],
                width=1,
                bottom=0,
                top=rep['prob'].tolist(),
                color='red',
                alpha=0.5)

        p1.xaxis.axis_label = 'Electoral College votes'
        p1.yaxis.axis_label = "Probability"

        return Panel(child=p1, title="Electoral College distribution")

    def poll_page(self):

        p1 = figure(plot_width=self.page_width,
                    plot_height=self.page_height,
                    title="Polls over time",
                    x_axis_type="datetime")

        polls = self.polls.groupby('Poll end date')['Poll ID'].count()

        p1.vbar(x=polls.index.tolist(),
                width=1,
                bottom=0,
                top=polls.values.tolist(),
                color='green',
                alpha=0.5)

        p1.xaxis.axis_label = 'Date'
        p1.yaxis.axis_label = "Poll count"

        return Panel(child=p1, title="Polls over time")

    def sp_state_changed(self, attrname, old, new):

        polls = ColumnDataSource(self.polls[self.polls['State'] == new])

        self.sp_poll_data.data = polls.data

        daily = ColumnDataSource(self.daily[self.daily['State'] == new])

        self.sp_states.data = daily.data

    def sp_responses_changed(self, active):

        for index in range(len(self.sp_resp_q)):

            self.sp_resp_q[index].visible = index in active

    def sp_lines_changed(self, active):

        for index in range(len(self.sp_line)):

            self.sp_line[index].visible = index in active

    def state_polls(self):

        # Sizing for display
        f_w = 0.75
        c_w = 0.25

        # Initial selections
        # ------------------
        state_selected = 'FL'
        self.sp_poll_data = ColumnDataSource(self.polls[self.polls['State'] ==
                                             state_selected])

        self.daily = self.states.get_daily_modified()
        self.sp_states = ColumnDataSource(self.daily[self.daily['State'] ==
                                          state_selected])

        # Charts
        # ------
        # Polls figure
        p1 = figure(plot_width=int(self.page_width*f_w),
                    plot_height=self.page_height,
                    title="Polls by state",
                    x_axis_type="datetime")

        self.sp_resp_q = 4*[None]

        # Democratic
        self.sp_resp_q[0] = p1.circle('Poll end date',
                                      'Democratic',
                                      color="blue",
                                      source=self.sp_poll_data)

        # Undecided
        self.sp_resp_q[1] = p1.circle('Poll end date',
                                      'Undecided',
                                      color="black",
                                      source=self.sp_poll_data)

        # Other
        self.sp_resp_q[2] = p1.circle('Poll end date',
                                      'Other',
                                      color="green",
                                      source=self.sp_poll_data)

        # Republican
        self.sp_resp_q[3] = p1.circle('Poll end date',
                                      'Republican',
                                      color="red",
                                      source=self.sp_poll_data)

        self.sp_line = 3*[None]

        self.sp_line[0] = p1.line('Date',
                                  'Democratic',
                                  color='blue',
                                  source=self.sp_states)

        self.sp_line[1] = p1.line('Date',
                                  'Other',
                                  color='green',
                                  source=self.sp_states)

        self.sp_line[2] = p1.line('Date',
                                  'Republican',
                                  color='red',
                                  source=self.sp_states)

        # Controls
        # --------
        # State dropdown list
        options = self.polls['State'].unique().tolist()
        states = Select(name='State',
                        value=state_selected,
                        options=options,
                        title='State')
        states.on_change('value', self.sp_state_changed)

        # Checkbox for parties
        resp_b = [0, 1, 2, 3]
        d_r = Div(text="Responses")
        responses = CheckboxGroup(labels=["Democratic",
                                          "Don't know",
                                          "Other",
                                          "Republican"],
                                  active=resp_b,
                                  name="Responses")

        responses.on_click(self.sp_responses_changed)

        # Checkbox for lines
        line_b = [0, 1, 2]
        d_l = Div(text="Lines")
        lines = CheckboxGroup(labels=["Democratic",
                                      "Other",
                                      "Republican"],
                              active=line_b,
                              name="Lines")

        lines.on_click(self.sp_lines_changed)

        d_le = Div(text="Note the lines have been normalized to exclude "
                        "undecided voters. This means the lines and the poll "
                        "responses won't line up.")

        # Layout
        w = widgetbox(states,
                      d_r,
                      responses,
                      d_l,
                      lines,
                      d_le,
                      width=int(self.page_width*c_w))

        l = row(w, p1)

        return Panel(child=l, title="State polls")

    def margin_weight(self):

        margin = self.states.get_latest_results()
        margin_alloc = margin.merge(self.alloc)
        margin_alloc['Margin %'] = 100*margin_alloc['Margin']

        p1 = figure(plot_width=int(self.page_width),
                    plot_height=self.page_height,
                    title="Margin and Electoral College votes")

        p1.xaxis.axis_label = 'Margin %'
        p1.yaxis.axis_label = 'Electoral College votes'

        dem = ColumnDataSource(margin_alloc[margin_alloc['Winner'] == 'Dem'])

        p1.vbar(x='Margin %',
                width=0.5,
                bottom=0,
                top='Allocation',
                color='blue',
                source=dem,
                alpha=0.5)

        labels = LabelSet(x='Margin %',
                          y='Allocation',
                          x_offset=-8,
                          y_offset=5,
                          text='State',
                          text_font_size="8pt",
                          source=dem)

        p1.add_layout(labels)

        rep = ColumnDataSource(margin_alloc[margin_alloc['Winner'] == 'Rep'])

        p1.vbar(x='Margin %',
                width=0.5,
                bottom=0,
                top='Allocation',
                color='red',
                source=rep,
                alpha=0.5)

        labels = LabelSet(x='Margin %',
                          y='Allocation',
                          x_offset=-8,
                          y_offset=5,
                          text='State',
                          text_font_size="8pt",
                          source=rep)

        p1.add_layout(labels)

        rep = ColumnDataSource(margin_alloc[margin_alloc['Winner'] ==
                                            'TOO CLOSE'])

        p1.vbar(x='Margin %',
                width=0.5,
                bottom=0,
                top='Allocation',
                color='green',
                source=rep,
                alpha=0.5)

        labels = LabelSet(x='Margin %',
                          y='Allocation',
                          x_offset=-8,
                          y_offset=5,
                          text='State',
                          text_font_size="8pt",
                          source=rep)

        p1.add_layout(labels)

        l = row(p1)
        return Panel(child=l, title="Margin and EC")


# =============================================================================
# Main
# =============================================================================
if __name__ == '__main__':

    # Announce software
    # =================

    YEAR = 2016

    print "\nPresidential Predicter"
    print "======================\n"

    # Read in data files
    # ==================
    print "Reading in data files"

    # Read in the election dates
    election_dates = ElectionDates()
    election_dates.prepare_data()

    current_election = election_dates.select(YEAR)
    previous_election = election_dates.select(YEAR - 4)

    print "Current election: {0}\n" \
          "Previous election {1}\n".format(current_election.date(),
                                           previous_election.date())

    # Get the election results for the previous elections
    results = Results(previous_election)
    results.prepare_data()
    previous_results = results.select(previous_election)

    # Create the electoral college allocation object
    college_allocations = CollegeAllocations()
    college_allocations.prepare_data()
    current_allocations = college_allocations.select(current_election)

    # Get the polls data
    polls = Polls()
    polls.prepare_data()
    current_polls = polls.select(current_election)

    print "Number of polls for this election: {0}"\
          .format(current_polls['Poll ID'].nunique())

    # State and Electoral College results
    # ===================================
    print "Calculating state results"
    states = States(previous_results, current_polls,
                    previous_election, current_election)
    states.prepare_data()
    states.averages()
    states.interpolate()

    print states.get_status()
    print states.get_latest_results()

    # Electoral College distributions
    # ===============================
    college = CollegeDistribution(states.daily, current_allocations)
    college.calc_dist()

    # Display the results
    # ===================
    display = Display(current_election,
                      previous_election,
                      current_polls,
                      states,
                      college,
                      current_allocations)
