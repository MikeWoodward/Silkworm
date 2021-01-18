# Silkworm - US presidential election result predictor

## Introduction

Silkworm forecasts who will win the US presidential election using two sets of input data:
* State polls
* Previous election results 

In 2020, my model correctly forecast 48 out of 51 states (including DC). The two that the model called wrongly are Florida and North Carolina, both of which were fairly big misses. Overall, opinion polls took a beating in 2020, and the discussion about what went wrong has already begun (see for example https://www.pewresearch.org/fact-tank/2020/11/13/understanding-how-2020s-election-polls-performed-and-what-it-might-mean-for-other-kinds-of-survey-work/). Until the accuracy of opinion polling improves, the kind of pool aggregation work I'm doing with Silkworm should probably sit on hold.

<img src="https://github.com/MikeWoodward/Silkworm/blob/master/documentation/Geography.png"/> 

You can see a video of my PyData Boston presentation on Silkworm here: https://www.youtube.com/watch?v=5Pnr0wbuUzM&t=23s

I've blogged a lot on forecasting US Presidential elections. Here are some of my blog posts:
* [Fundamentally wrong? Using economic data as an election predictor](https://blog.engora.com/2020/10/fundamentally-wrong-using-economic-data.html)
* [Can you believe the polls?](https://blog.engora.com/2020/09/can-you-believe-polls.html)
* [President Hilary Clinton: what the polls got wrong in 2016 and why they got it wrong](https://blog.engora.com/2020/08/president-hilary-clinton-what-polls-got.html)
* [Poll-axed: disastrously wrong opinion polls](https://blog.engora.com/2020/08/poll-axed-disastrously-wrong-opinion.html)
* [Who will win the election? Election victory probabilities from opinion polls](https://blog.engora.com/2020/08/who-will-win-election-election-victory.html)
* [The dirty little secrets of opinion polling](https://blog.engora.com/2020/08/the-dirty-little-secrets-of-opinion.html)
* [The Electoral College for beginners](https://blog.engora.com/2020/07/the-electoral-college-for-beginners.html)

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

