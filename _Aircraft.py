#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Jul 14 12:24:52 2021

@author: samthomas
"""
import random
import _g


class Aircraft:
    def __init__(self, ac_id):
        self.id = ac_id
        self.q_time_controller = 0
        self.q_time_flightlineMech = 0
        self.q_time_airframeMech = 0
        self.q_time_aviTech = 0
        self.prob_fl = _g.gVars['prob_fl']
        self.prob_avi = _g.gVars['prob_avi']
        self.prob_af = _g.gVars['prob_af']
        self.flight = False
        self.fl_gripe = False
        self.avi_gripe = False
        self.af_gripe = False
        self.flightprob = _g.gVars['flight_prob']
        self.totalFlightTime = 0
        self.totalFlights = 0
        self.totalAviRepairTime = 0
        self.totalFLRepairTime = 0
        self.totalAFRepairTime = 0
        self.totalRepairTime = self.totalAviRepairTime\
            + self.totalFLRepairTime + self.totalAFRepairTime

# fl_decision randomly assigns a flightline-related gripe to the aircraft.
    def fl_decision(self):
        if random.random() <= self.prob_fl:
            self.fl_gripe = True

# avi_decision randomly assigns an avionics-related gripe to the aicraft.
    def avi_decision(self):
        if random.random() <= self.prob_avi:
            self.avi_gripe = True

# af_decision randomly assigns airframes-related gripes to the aircraft.
    def af_decision(self):
        if random.random() <= self.prob_af:
            self.af_gripe = True

# flight_decision randomly assigns the aircraft to fly during the iteration.
    def flight_decision(self):
        if random.random() <= self.flightprob:
            self.flight = True
