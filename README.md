# Silkworm - US presidential election result predictor

## Introduction

Silkworm forecasts who will win the US presidential election using two sets of input data:
* State polls
* Previous election results 

<img src="https://github.com/MikeWoodward/Silkworm/blob/master/documentation/Geography.png"/> 

## How it works

It aggregates polls using a rolling 7-day window, arranging the polls by candidate spread and choosing the median poll. The prior election result is used to 'seed' the analysis in all cases. Where no polls exist, the prior election result is used. From the polling (or election) data, Silkworm calculates a daily candidate win probability.

The software combines the state/candidate winning probabilities using a generator polynomial. This gives a daily electoral college vote forecast.

The software is based on the work of Sam Wang of the Princeton Election Consortium (http://election.princeton.edu/). I took his MATLAB code and made an extensive series of modifications. The code has diverged so much, they are essentially different projects at this stage.

<img src="https://github.com/MikeWoodward/Silkworm/blob/master/documentation/State.png"/>

## Where the data comes from

Election result data comes from Wikipedia.

2020 opinion poll data comes from 538: https://projects.fivethirtyeight.com/polls/president-general/

Opinion poll data prior to 2020 comes from the Huffington Post Pollster API (http://elections.huffingtonpost.com/pollster/api). This API is no longer updated.

<img src="https://github.com/MikeWoodward/Silkworm/blob/master/documentation/PollViewer.png"/>

# Python libraries used

The software uses the following libraries:
* Pandas - used extensively.
* Bokeh - used for visualization.
* Requests - used to retrieve data from the Huffington Post API.

<img src="https://github.com/MikeWoodward/Silkworm/blob/master/documentation/VotesDistribution.png"/>

# Running the software

1. Install Bokeh version 2.2.1 or higher
2. Download the project to a folder called sikworm
3. From the folder above silkworm, type in `bokeh serve --show silkworm`
4. Navigate to the tab 'Run/load forecast'
5. Load the 2020 analysis.
6. Explore the data!

