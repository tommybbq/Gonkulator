p"""
Created on Wed Jun 30 13:17:50 2021
@author: Thomas Kline
"""
from dataclasses import dataclass
from enum import Enum, auto
import simpy
import random
import pandas as pd
import csv

""" class to store global parameter values."""
class g:
    gVars = {}
    output_file = f"sq_trial_results.csv"
"""code to ingest input variables"""
with open('inputData.csv', mode='r') as infile:
   reader = csv.reader(infile)
   with open('coors_new.csv', mode='w') as outfile:
       writer = csv.writer(outfile)
       g.gVars = {rows[0]:rows[1] for rows in reader}
g.gVars.pop('Variables')
#print(g.gVars)
"""string to int"""
for key in g.gVars: 
   try:
       g.gVars[key] = int(g.gVars[key])
   except ValueError:
       g.gVars[key] = float(g.gVars[key])
#print(g.gVars)

class Workcenter(Enum):
   """Maintainters' workcenters"""
   FL = auto()
   AF = auto()
   AVI = auto()
   
@dataclass
class MAF:
   tailNum: int
   mcn: int
   workcenter: Workcenter
   timetoComplete : int
   timeWorked: int = 0
   complete: bool = False

class Aircraft:
   def __init__(self, tailNum):
       self.id = tailNum
       self.q_time_controller = 0
       self.q_time_flightlineMech = 0
       self.q_time_airframeMech = 0
       self.q_time_aviTech = 0
       self.q_time_pilot = 0
       self.prob_fl = g.gVars['prob_fl']
       self.prob_avi = g.gVars['prob_avi']
       self.prob_af = g.gVars['prob_af']
       self.onSchedule = True
       self.preFlightComplete = False
       self.maf_counter = 0
       self.mafs: [MAF] = []
       self.gripe = 0
       self.fl_gripe = False
       self.avi_gripe = False
       self.af_gripe = False
       self.prob_preFlight_gripe = g.gVars['prob_preFlight_gripe']
       self.flightprob = g.gVars['flight_prob']
       self.totalFlightTime = 0
       self.totalFlights = 0
       self.totalAviRepairTime = 0
       self.totalFLRepairTime = 0
       self.totalAFRepairTime = 0

   def calculate_timetoComplete(self, workcenter) -> None:
       if workcenter == Workcenter.FL:
           timetoComplete = random.expovariate(1.0/g.gVars['mean_fl_fix'])
       elif workcenter == Workcenter.AF:
           timetoComplete = random.expovariate(1.0/g.gVars['mean_af_fix'])
       elif workcenter == Workcenter.AVI:
           timetoComplete = random.expovariate(1.0/g.gVars['mean_avi_fix']) 
       return timetoComplete

   def add_maf(self, maf: MAF, workcenter) -> None:
       """add a maf to the list of mafs."""
       self.maf_counter += 1
       timetoComplete = self.calculate_timetoComplete(workcenter)
       self.mafs.append(MAF(tailNum=self.id, mcn=self.maf_counter, workcenter=workcenter, timetoComplete=timetoComplete)) #fl_decision randomly assigns a flightline-related gripe to the aircraft. 
   def fl_decision(self):
       if random.random() <= self.prob_fl:
           self.add_maf(self.maf_counter, workcenter=Workcenter.FL) #avi_decision randomly assigns an avionics-related gripe to the aicraft.
   def avi_decision(self):
       if random.random() <= self.prob_avi:
           self.add_maf(self.maf_counter, workcenter=Workcenter.AVI) #af_decision randomly assigns airframes-related gripes to the aircraft.
   def af_decision(self):
       if random.random() <= self.prob_af:
           self.add_maf(self.maf_counter, workcenter=Workcenter.AF) #flight_decision randomly assigns the aircraft to fly during the iteration.
   def flight_decision(self):
       if random.random() <= self.flightprob:
           self.onSchedule = True
   def preFlight_decision(self):
       if random.random() <= self.prob_preFlight_gripe:
           self.gripe = random.randrange(0, 4, 1)
           if self.gripe == 1:
               self.add_maf(self.maf_counter, workcenter=Workcenter.AF)
           elif self.gripe == 2:
               self.add_maf(self.maf_counter, workcenter=Workcenter.AVI)
           elif self.gripe == 3:
               self.add_maf(self.maf_counter, workcenter=Workcenter.AVI)

#Squadron_Model is the class that contains the events in the simulation.
#Squadron_Model's run function sends the model into action.
class Squadron_Model:
   def __init__(self, trial_number):
       self.env = simpy.Environment()
       self.aircraft_counter = 0
       self.day = 0
       self.hour = 0
       self.minute = 0
       self.minutesIn1Day = (24*60)
       self.minutesIntoCurrentDay = 0
       self.minutesLeftInShift = 0
       self.controller = simpy.Resource(self.env, capacity=g.gVars['numControllers'])
       self.flightlineMech = simpy.Resource(self.env, capacity=g.gVars['numFlightlineMechs'])
       self.airframeMech = simpy.Resource(self.env, capacity=g.gVars['numAirframeMechs'])
       self.aviTech = simpy.Resource(self.env, capacity=g.gVars['numAviTechs'])
       self.pilot = simpy.Resource(self.env, capacity=g.gVars['numPilots'])
       self.offShiftHr = g.gVars['offShiftHr']
       self.onShiftHr = g.gVars['onShiftHr']
       self.trial_number = trial_number
       self.mean_q_time_controller = 0
       self.mean_q_time_flightlineMech = 0
       self.mean_q_time_airframeMech = 0
       self.mean_q_time_aviTech = 0
       self.mean_q_time_flight = 0
       self.mean_q_time_pilot = 0
       self.preFlightComplete = False
       self.results_df = pd.DataFrame()
       self.results_df["tailNum"] = []
       self.results_df["Q_Time_Controller"] = []
       self.results_df["Q_Time_FlightLineMech"] = []
       self.results_df["Q_Time_AirFrameMech"] = []
       self.results_df["Q_Time_aviTech"] = []
       self.results_df["Total_Flight_Time"] = []
       self.results_df["Total_Flights"] = []
       self.results_df["Total_AF_Repair_Time"] = []
       self.results_df["Total_Avi_Repair_Time"] = []
       self.results_df["Total_FL_Repair_Time"] = []
       self.results_df.set_index("tailNum", inplace=True)

#Generate_AC creates a number of Aircraft objects and names them by counter #Each aircraft is given a material condition state through random decisions #Each aircraft is then given a flight decision to start
   def generate_ac(self):
       for i in range(g.gVars['numAircraft']):
           self.aircraft_counter += 1
           tailNum = Aircraft(self.aircraft_counter)
           #give some of the aircraft a material condition discrepancy 
           #to discover during preflight inspection
           tailNum.fl_decision()
           tailNum.avi_decision()
           tailNum.af_decision()
           self.env.process(self.Controller(tailNum))
           yield self.env.timeout(0)

   def timeConverter(self):
      time = self.env.now #recorded in total minutes
      self.day = round(time // (24*60)) # // drops the remainder
      time = time % (24*60) # % only keeps remainder (in minutes)
      self.minutesIntoCurrentDay = time #assignes remainder to variable
      print(self.minutesIntoCurrentDay)
      if ((self.offShiftHr*60) - self.minutesIntoCurrentDay) >0:
          self.minutesLeftInShift = (self.offShiftHr*60) - self.minutesIntoCurrentDay
      else: 
          self.minutesLeftInShift = 0
      self.hour = round(time // 60)
      time %= 60
      self.minute = (time // 1)
#Controller handles A/C's next step in the process:
#if A/C has gripe, send to repair a process #if A/C on schedule to fly, send to preflight inspection #if A/C preflight complete, send to fly
   def Controller(self, aircraft):   
       start_q_controller = self.env.now
       with self.controller.request() as req:
           yield req
           self.timeConverter()
           if self.minutesLeftInShift > 0 or self.hour > self.onShiftHr:
               print(f"D:H:M: {self.day}:{self.hour}:{self.minute}: A/C{aircraft.id} - Controller {self.controller.count} reviewing A/C")
               end_q_controller = self.env.now
               aircraft.flight_decision()
               aircraft.q_time_controller = aircraft.q_time_controller + (end_q_controller - start_q_controller)
               sampled_controller_duration = random.normalvariate(g.gVars['mean_controller'], g.gVars['sigma_controller'])
               yield self.env.timeout(sampled_controller_duration)
               if any(maf.complete == False for maf in aircraft.mafs):
                   print(f"A/C{aircraft.id}: ", end="")
                   for maf in aircraft.mafs:
                       print(f"{maf.mcn}-{maf.complete}, ", end="")
                       if maf.complete == False:
                           if maf.workcenter == Workcenter.FL:
                               self.env.process(self.flRepairProcess(aircraft))
                           elif maf.workcenter == Workcenter.AF:
                               self.env.process(self.afRepairProcess(aircraft))
                           elif maf.workcenter == Workcenter.AVI:
                               self.env.process(self.aviRepairProcess(aircraft))
                           else: 
                               print("oops, must have a bug!")
                   print()
               else:
                   self.env.process(self.preflightInspection(aircraft))
           else:
               self.env.process(self.downtime(aircraft))
#this if statement records data for calculate_trial_results
       if self.env.now > g.gVars['warm_up_period']:
           df_to_add = pd.DataFrame({"tailNum":[aircraft.id],
                                     "Q_Time_Controller":[aircraft.q_time_controller],
                                     "Q_Time_FlightLineMech":[aircraft.q_time_flightlineMech],
                                     "Q_Time_AirFrameMech":[aircraft.q_time_airframeMech],
                                     "Q_Time_aviTech":[aircraft.q_time_aviTech],
                                     "Total_Flight_Time":[aircraft.totalFlightTime],
                                     "Total_Flights":[aircraft.totalFlights],
                                     "Total_AF_Repair_Time":[aircraft.totalAFRepairTime],
                                     "Total_FL_Repair_Time":[aircraft.totalFLRepairTime],
                                     "Total_Avi_Repair_Time":[aircraft.totalAviRepairTime]})
           df_to_add.set_index("tailNum", inplace=True)
           self.results_df = self.results_df.append(df_to_add)
#preflightInspection: process BEFORE flight for discovering discrepancies
   def preflightInspection(self, aircraft):
       start_q_pilot = self.env.now
       self.timeConverter()
       print(f"D:H:M: {self.day}:{self.hour}:{self.minute}: A/C{aircraft.id} - to preflight insp")
       with self.pilot.request() as req:
           yield req
           self.timeConverter()
           print(f"D:H:M: {self.day}:{self.hour}:{self.minute}: A/C{aircraft.id} - preflight, pilot: {self.pilot.count}")
           #once flightlineMech and airframeMech is available, end queue time
           end_q_pilot = self.env.now
           #calculate total queue time
           aircraft.q_time_pilot = aircraft.q_time_pilot + (end_q_pilot - start_q_pilot)
           #apply probability of discovering discrepancy during preflight
           aircraft.preFlight_decision()
           #derive a random preFlight inspection duration
           sampled_preflightInspection_duration = random.expovariate(1.0/g.gVars['mean_preflightInspection'])
           #use random preFlight duration to conclude process
           aircraft.preFlightComplete = True
           yield self.env.timeout(sampled_preflightInspection_duration)
           self.timeConverter()
           #let user know that preflight is complete
           print(f"D:H:M: {self.day}:{self.hour}:{self.minute}: A/C{aircraft.id} - preflight complete:{aircraft.preFlightComplete}")
           if any(maf.complete == False for maf in aircraft.mafs):
               self.env.process(self.Controller(aircraft))
           else:
               self.env.process(self.fly(aircraft))
   def aviRepairProcess(self, aircraft):
       start_q_aviTech = self.env.now
       aviMAF = [maf for maf in aircraft.mafs if maf.workcenter == Workcenter.AVI and maf.complete == False]
       with self.aviTech.request() as req: #req the resource
           yield req #give the resource once available
           self.timeConverter()
           print(f"D:H:M: {self.day}:{self.hour}:{self.minute}: A/C{aircraft.id} - aviTech {self.aviTech.count} repairing.")
           end_q_aviTech = self.env.now
           aircraft.q_time_aviTech = aircraft.q_time_aviTech + \
               (end_q_aviTech - start_q_aviTech) #add to q_time_aviTech
           if aviMAF[0].timetoComplete < self.minutesLeftInShift:
               print(f"time left {self.minutesLeftInShift}, time to complete {aviMAF[0].timetoComplete}")
               sampled_aviTech_duration = aviMAF[0].timetoComplete
               yield self.env.timeout(sampled_aviTech_duration) #timeout
               setattr(aviMAF[0], "timeWorked", aviMAF[0].timetoComplete)
               setattr(aviMAF[0], "complete", True)
               self.avi_gripe = False
               self.timeConverter()
               print(f"D:H:M: {self.day}:{self.hour}:{self.minute}: A/C{aircraft.id} - Avi repair complete.")
               aircraft.totalAviRepairTime = aircraft.totalAviRepairTime + \
                   sampled_aviTech_duration
               #send back to controller
               self.env.process(self.Controller(aircraft))
           else:
               print(f"time left this shift{self.minutesLeftInShift} > repair time {aviMAF[0].timetoComplete}")
               sampled_aviTech_duration = self.minutesLeftInShift
               setattr(aviMAF[0], "timeWorked", sampled_aviTech_duration)
               setattr(aviMAF[0], "timetoComplete", aviMAF[0].timetoComplete-self.minutesLeftInShift)
               yield self.env.timeout(sampled_aviTech_duration)
               self.timeConverter()
               print(f"D:H:M: {self.day}:{self.hour}:{self.minute}: A/C{aircraft.id} - Avi End of Shift, worked {self.minutesLeftInShift}.")
               aircraft.totalAviRepairTime = aircraft.totalAviRepairTime + \
                   sampled_aviTech_duration
               #send back to controller
               self.env.process(self.downtime(aircraft))
   def afRepairProcess(self, aircraft):
       start_q_airframeMech = self.env.now
       afMAF = [maf for maf in aircraft.mafs if maf.workcenter == Workcenter.AF and maf.complete == False]
       with self.airframeMech.request() as req: #req the resource
           yield req #give the resource once available
           self.timeConverter()
           print(f"D:H:M: {self.day}:{self.hour}:{self.minute}: A/C{aircraft.id} - AirframeMech {self.airframeMech.count} repairing.")
           end_q_airframeMech = self.env.now
           aircraft.q_time_airframeMech = aircraft.q_time_airframeMech + \
               (end_q_airframeMech - start_q_airframeMech)
           if afMAF[0].timetoComplete < self.minutesLeftInShift:
               print(f"time left {self.minutesLeftInShift}, time to complete {afMAF[0].timetoComplete}")
               sampled_afMech_duration = afMAF[0].timetoComplete
               yield self.env.timeout(sampled_afMech_duration) #timeout
               setattr(afMAF[0], "timeWorked", afMAF[0].timetoComplete)
               setattr(afMAF[0], "complete", True)
               self.af_gripe = False
               self.timeConverter()
               print(f"D:H:M: {self.day}:{self.hour}:{self.minute}: A/C{aircraft.id} - AF repair complete.")
               aircraft.totalAFRepairTime = aircraft.totalAFRepairTime + \
                   sampled_afMech_duration
               #send back to controller
               self.env.process(self.Controller(aircraft))
           else:
               print(f"time left this shift {self.minutesLeftInShift} > repair time {afMAF[0].timetoComplete}")
               sampled_afMech_duration = self.minutesLeftInShift
               setattr(afMAF[0], "timeWorked", sampled_afMech_duration)
               setattr(afMAF[0], "timetoComplete", afMAF[0].timetoComplete-self.minutesLeftInShift)
               yield self.env.timeout(sampled_afMech_duration)
               self.timeConverter()
               print(f"D:H:M: {self.day}:{self.hour}:{self.minute}: A/C{aircraft.id} - AF End of Shift, worked {self.minutesLeftInShift}.")
               aircraft.totalAFRepairTime = aircraft.totalAFRepairTime + \
                   sampled_afMech_duration
               #send back to controller
               self.env.process(self.downtime(aircraft))
   def flRepairProcess(self, aircraft):
       start_q_flightlineMech = self.env.now
       flMAF = [maf for maf in aircraft.mafs if maf.workcenter == Workcenter.FL and maf.complete == False]
       with self.flightlineMech.request() as req: #req the resource
           yield req #give the resource once available
           self.timeConverter()
           print(f"D:H:M: {self.day}:{self.hour}:{self.minute}: A/C{aircraft.id} - FlightlineMech {self.flightlineMech.count} repairing.")
           end_q_flightlineMech = self.env.now
           aircraft.q_time_flightlineMech = aircraft.q_time_flightlineMech + \
               (end_q_flightlineMech - start_q_flightlineMech)
           if flMAF[0].timetoComplete < self.minutesLeftInShift:
               print(f"time left {self.minutesLeftInShift}, time to complete {flMAF[0].timetoComplete}")
               sampled_flMech_duration = flMAF[0].timetoComplete
               yield self.env.timeout(sampled_flMech_duration) #timeout
               setattr(flMAF[0], "timeWorked", flMAF[0].timetoComplete)
               setattr(flMAF[0], "complete", True)
               self.fl_gripe = False
               self.timeConverter()
               print(f"D:H:M: {self.day}:{self.hour}:{self.minute}: A/C{aircraft.id} - AF repair complete.")
               aircraft.totalFLRepairTime = aircraft.totalFLRepairTime + \
                   sampled_flMech_duration
               #send back to controller
               self.env.process(self.Controller(aircraft))
           else:
               print(f"time left this shift {self.minutesLeftInShift} > repair time {flMAF[0].timetoComplete}")
               sampled_flMech_duration = self.minutesLeftInShift
               setattr(flMAF[0], "timeWorked", sampled_flMech_duration)
               setattr(flMAF[0], "timetoComplete", flMAF[0].timetoComplete-self.minutesLeftInShift)
               yield self.env.timeout(sampled_flMech_duration)
               self.timeConverter()
               print(f"D:H:M: {self.day}:{self.hour}:{self.minute}: A/C{aircraft.id} - FL End of Shift, worked {self.minutesLeftInShift}.")
               aircraft.totalFLRepairTime = aircraft.totalFLRepairTime + \
                   sampled_flMech_duration
               #send back to controller
               self.env.process(self.downtime(aircraft)) 



#downtime represents the large amount of time that the aircraft is not flying, and workers aren't working.
   def downtime(self, aircraft): 
       self.timeConverter()
       print(f"D:H:M: {self.day}:{self.hour}:{self.minute}: A/C{aircraft.id} - starts downtime.")
       downtimeDur  = (self.minutesIn1Day-self.minutesIntoCurrentDay)+\
           (self.onShiftHr*60)
       yield self.env.timeout(downtimeDur)
       aircraft.flight_decision()
       self.env.process(self.Controller(aircraft))
       #print(f"D:H:M: {self.day}:{self.hour}:{self.minute}: A/C{aircraft.id} - ends downtime.") #fly executes flying but also runs random probability that something broke during flight
   def fly(self, aircraft):
       flytimeDur  = random.normalvariate(g.gVars['mean_flytime'], g.gVars['flytime_sig'])
       if flytimeDur < self.minutesLeftInShift:
           with self.pilot.request() as req:
               yield req
               takeoffTime = self.env.now
               aircraft.totalFlights += 1 #increment aircraft's number of flights
               self.timeConverter()
               print(f"D:H:M: {self.day}:{self.hour}:{self.minute}: A/C{aircraft.id} - flying flight {aircraft.totalFlights}.")
               yield self.env.timeout(flytimeDur)
               aircraft.fl_decision()
               aircraft.avi_decision()
               aircraft.af_decision()
               landTime = self.env.now 
               aircraft.onSchedule = False
               #calculate flight time and add to total
               aircraft.totalFlightTime = aircraft.totalFlightTime + (landTime - takeoffTime)
               #self.timeConverter()
               #print(f"D:H:M: {self.day}:{self.hour}:{self.minute}: A/C{aircraft.id} - landed flight {aircraft.totalFlights}")
               self.env.process(self.Controller(aircraft))
       else:
           print(f"A/C{aircraft.id}: not enough time left to fly today.")
           self.env.process(self.downtime(aircraft))
#calculate_mean_q_times takes the dataframe from the simulation #finds the mean for all aicraft
   def calculate_mean_q_times(self):
       self.mean_q_time_controller = self.results_df["Q_Time_Controller"].mean()
       self.mean_q_time_flightlineMech = self.results_df["Q_Time_FlightLineMech"].mean()
       self.mean_q_time_airframeMech = self.results_df["Q_Time_AirFrameMech"].mean()
       self.mean_q_time_aviTech = self.results_df["Q_Time_aviTech"].mean()
       self.mean_total_flightTime = self.results_df["Total_Flight_Time"].mean()
       self.mean_total_flights = self.results_df["Total_Flights"].mean()
       self.mean_total_afRepairTime = self.results_df["Total_AF_Repair_Time"].mean()
       self.mean_total_flRepairTime = self.results_df["Total_FL_Repair_Time"].mean()
       self.mean_total_aviRepairTime = self.results_df["Total_Avi_Repair_Time"].mean()
#write trial run results as new line in g.output_file
   def write_run_results(self):
       with open(g.output_file, "a", newline="") as f:
           writer = csv.writer(f, delimiter=",")
           results_to_write = [self.trial_number,
                               self.mean_q_time_controller,
                               self.mean_q_time_flightlineMech,
                               self.mean_q_time_airframeMech,
                               self.mean_q_time_aviTech,
                               self.mean_total_flightTime,
                               self.mean_total_flights,
                               self.mean_total_afRepairTime,
                               self.mean_total_flRepairTime,
                               self.mean_total_aviRepairTime]
           writer.writerow(results_to_write) #start simulation by calling generate_ac function #run simulation until end #calculate run results using calculate mean_q_times() function #write run results to file
   def run(self):
       self.env.process(self.generate_ac())
       self.env.run(until=(g.gVars['warm_up_period'] + g.gVars['sim_duration']))
       self.calculate_mean_q_times()
       self.write_run_results()
#after simulation is complete, read the results from g.output_file #print the results.
class Trial_Results_Calculator:
   def __init__(self):
       self.trial_results_df = pd.DataFrame()
   def print_trial_results(self):
       print("TRIAL RESULTS")
       print("-------------")
       #read in results for each run
       self.trial_results_df = pd.read_csv(g.output_file)
       #take average over runs
       trial_mean_q_time_controller = (self.trial_results_df["Mean_Q_Time_Controller"].mean())
       trial_mean_q_time_flightlineMech = self.trial_results_df["Mean_Q_Time_FlightLineMech"].mean()
       trial_mean_q_time_airframeMech = (self.trial_results_df["Mean_Q_Time_AirFrameMech"].mean())
       trial_mean_q_time_aviTech = (self.trial_results_df["Mean_Q_Time_aviTech"].mean())
       trial_mean_total_flightTime = self.trial_results_df["Mean_Total_Flight_Time"].mean()
       trial_mean_total_flights = self.trial_results_df["Mean_Total_Flights"].mean()
       trial_mean_total_afRepairTime = self.trial_results_df["Mean_Total_afRepairTime"].mean()
       trial_mean_total_flRepairTime = self.trial_results_df["Mean_Total_flRepairTime"].mean()
       trial_mean_total_aviRepairTime = self.trial_results_df["Mean_Total_aviRepairTime"].mean()
       print(f"Mean flight time per A/C: {round(trial_mean_total_flightTime, 1)}")
       print(f"Mean number of flights per A/C: {round(trial_mean_total_flights, 1)}")
       print("-------------")
       print(f"Mean queue time for controllers: {round(trial_mean_q_time_controller)}")
       print(f"Mean queue time for Flightline Mechs: {round(trial_mean_q_time_flightlineMech)}")
       print(f"Mean queue time for Airframe Mechs: {round(trial_mean_q_time_airframeMech)}")
       print(f"Mean queue time for Avi Techs: {round(trial_mean_q_time_aviTech)}")
       print("-------------")
       print(f"Mean Airframes repair time per A/C: {round(trial_mean_total_afRepairTime)}")
       print(f"Mean Flightline repair time per A/C: {round(trial_mean_total_flRepairTime)}")
       print(f"Mean Avionics repair time per A/C: {round(trial_mean_total_aviRepairTime)}")



""" everything above is definitiion of classes and functions, but here’s where the code will start actively doing things.
For the number of specified runs in the g class, create an instance of the Squadron_Model class, and call its run method"""

#this code is read first, and begins by creating g.output_file

with open(g.output_file, "w", newline="") as f:
   writer = csv.writer(f, delimiter=",")
   column_headers = ["Run", "Mean_Q_Time_Controller",
                     "Mean_Q_Time_FlightLineMech", "Mean_Q_Time_AirFrameMech",
                     "Mean_Q_Time_aviTech", "Mean_Total_Flight_Time", 
                     "Mean_Total_Flights", "Mean_Total_afRepairTime",
                     "Mean_Total_flRepairTime", "Mean_Total_aviRepairTime"]
   writer.writerow(column_headers)

for run in range(g.gVars['numTrials']):
   print("Run ", run+1, " of ", g.gVars['numTrials'], sep="")
   my_sq_model = Squadron_Model(run)
   my_sq_model.run()
   print()
#once trial is complete, we’ll create an instance of the #trial_result_calculator class and run the print_trial_results method my_trial_results_calculator = Trial_Results_Calculator()
my_trial_results_calculator = Trial_Results_Calculator()
my_trial_results_calculator.print_trial_results()