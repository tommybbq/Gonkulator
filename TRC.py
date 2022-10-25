#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Jul 14 13:09:10 2021

@author: samthomas
"""

import pandas as pd
import _g
# after simulation is complete, read the results from g.output_file
# print the results.


class Trial_Results_Calculator:
    def __init__(self):
        self.trial_results_df = pd.DataFrame()

    def print_trial_results(self):
        print("TRIAL RESULTS")
        print("-------------")
        # read in results for each run
        self.trial_results_df = pd.read_csv(_g.output_file)
        # take average over runs
        trial_mean_q_time_controller = (self.trial_results_df["Mean_Q_Time_Controller"].mean())
        trial_mean_q_time_flightlineMech = self.trial_results_df["Mean_Q_Time_FlightLineMech"].mean()
        trial_mean_q_time_airframeMech = (self.trial_results_df["Mean_Q_Time_AirFrameMech"].mean())
        trial_mean_q_time_aviTech = (self.trial_results_df["Mean_Q_Time_aviTech"].mean())
        trial_mean_total_flightTime = self.trial_results_df["Mean_Total_Flight_Time"].mean()
        trial_mean_total_flights = self.trial_results_df["Mean_Total_Flights"].mean()
        trial_mean_total_afRepairTime = self.trial_results_df["Mean_Total_afRepairTime"].mean()
        trial_mean_total_flRepairTime = self.trial_results_df["Mean_Total_flRepairTime"].mean()
        trial_mean_total_aviRepairTime = self.trial_results_df["Mean_Total_aviRepairTime"].mean()
        trial_mean_total_RepairTime = self.trial_results_df["Mean_Total_RepairTime"].mean()
        print("Mean queuing time for controller over trial : ",
              round(trial_mean_q_time_controller, 2))
        print("Mean queuing time for Flight Line Mech over trial : ",
              round(trial_mean_q_time_flightlineMech, 2))
        print("Mean queuing time for Airframe Mech over trial : ",
              round(trial_mean_q_time_airframeMech, 2))
        print("Mean queuing time for Avi Tech over trial : ",
              round(trial_mean_q_time_aviTech, 2))
        print("Mean total flight time per A/C over trial : ",
              round(trial_mean_total_flightTime, 2))
        print("Mean total flights per A/C over trial : ",
              round(trial_mean_total_flights, 2))
        print("Mean total AF repair time per A/C over trial : ",
              round(trial_mean_total_afRepairTime, 2))
        print("Mean total FL repair time per A/C over trial : ",
              round(trial_mean_total_flRepairTime, 2))
        print("Mean total Avi repair time per A/C over trial : ",
              round(trial_mean_total_aviRepairTime, 2))
        print("Mean total repair time per A/C over trial : ",
              round(trial_mean_total_RepairTime, 2))
        