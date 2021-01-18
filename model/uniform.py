#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri Sep  4 10:17:07 2020.

@author: mikewoodward
"""

import pandas as pd

from bokeh.plotting import figure, show

dice = pd.DataFrame({'score':[1,2,3,4,5,6],
                     'frequency': [53222, 52118, 52465, 52338, 52244, 53285]})

chart = figure(title="""Labby's dice data.""")
chart.vbar(x=dice['score'], top=dice['frequency'])
show(chart)