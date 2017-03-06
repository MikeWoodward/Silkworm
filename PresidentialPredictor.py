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

For details of licensing etc, see the Github page:
    https://github.com/MikeWoodward/PresidentialPredictor

"""


# =============================================================================
# Imports
# =============================================================================
from Predictor.CollegeAllocations import CollegeAllocations
from Predictor.CollegeDistribution import CollegeDistribution
from Predictor.Display import Display
from Predictor.ElectionDates import ElectionDates
from Predictor.Polls import Polls
from Predictor.Results import Results
from Predictor.States import States


# =============================================================================
# Main
# =============================================================================
if __name__ == '__main__':

    # Announce software
    # =================

    YEAR = 2016

    print "\nPresidential Predictor"
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
