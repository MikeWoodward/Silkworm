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
from controller.controller import Controller


# %%---------------------------------------------------------------------------
# main
# -----------------------------------------------------------------------------
# This code is called by the Bokeh server.
# No if __name__ here because of the way that Bokeh works.
controller = Controller()
controller.setup()
# display must be called after setup or else callbacks don't work
controller.display()
controller.update()
