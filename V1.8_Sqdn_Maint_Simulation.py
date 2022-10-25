"""
Created on Wed Jun 30 13:17:50 2021
Adapted from ED_Model, modeled as
plane arrives -> registration -> troubleshoot
  -> % chance avi -> remaining % chance airframes
@author: Thomas Kline
"""
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

class Aircraft:
    def __init__(self, ac_id):
        self.id = ac_id
        self.q_time_controller = 0
        self.q_time_flightlineMech = 0
        self.q_time_airframeMech = 0
        self.q_time_aviTech = 0
        self.prob_fl = g.gVars['prob_fl']
        self.prob_avi = g.gVars['prob_avi']
        self.prob_af = g.gVars['prob_af']
        self.flight = False
        self.fl_gripe = False
        self.avi_gripe = False
        self.af_gripe = False
        self.flightprob = g.gVars['flight_prob']
        self.totalFlightTime = 0
        self.totalFlights = 0
        self.totalAviRepairTime = 0
        self.totalFLRepairTime = 0
        self.totalAFRepairTime = 0
        self.totalRepairTime = self.totalAviRepairTime + self.totalFLRepairTime +\
            self.totalAFRepairTime
            
#fl_decision randomly assigns a flightline-related gripe to the aircraft. 
    def fl_decision(self):
        if random.random() <= self.prob_fl:
            self.fl_gripe = True
            
#avi_decision randomly assigns an avionics-related gripe to the aicraft.
    def avi_decision(self):
        if random.random() <= self.prob_avi:
            self.avi_gripe = True
            
#af_decision randomly assigns airframes-related gripes to the aircraft.
    def af_decision(self):
        if random.random() <= self.prob_af:
            self.af_gripe = True
            
#flight_decision randomly assigns the aircraft to fly during the iteration.
    def flight_decision(self):
        if random.random() <= self.flightprob:
            self.flight = True

#Squadron_Model is the class that contains the events in the simulation.
#Squadron_Model's run function sends the model into action.

class Squadron_Model:
    def __init__(self, trial_number):
        self.env = simpy.Environment()
        self.aircraft_counter = 0
        self.controller = simpy.Resource(self.env, capacity=g.gVars['numControllers'])
        self.flightlineMech = simpy.Resource(self.env, capacity=g.gVars['numFlightlineMechs'])
        self.airframeMech = simpy.Resource(self.env, capacity=g.gVars['numAirframeMechs'])
        self.aviTech = simpy.Resource(self.env, capacity=g.gVars['numAviTechs'])
        self.pilot = simpy.Resource(self.env, capacity=g.gVars['numPilots'])
        self.trial_number = trial_number
        self.mean_q_time_controller = 0
        self.mean_q_time_flightlineMech = 0
        self.mean_q_time_airframeMech = 0
        self.mean_q_time_aviTech = 0
        self.mean_q_time_flight = 0
        self.comebackthru = False
        self.results_df = pd.DataFrame()
        self.results_df["AC_ID"] = []
        self.results_df["Q_Time_Controller"] = []
        self.results_df["Q_Time_FlightLineMech"] = []
        self.results_df["Q_Time_AirFrameMech"] = []
        self.results_df["Q_Time_aviTech"] = []
        self.results_df["Total_Flight_Time"] = []
        self.results_df["Total_Flights"] = []
        self.results_df["Total_AF_Repair_Time"] = []
        self.results_df["Total_Avi_Repair_Time"] = []
        self.results_df["Total_FL_Repair_Time"] = []
        self.results_df["Total_Repair_Time"] = []
        self.results_df.set_index("AC_ID", inplace=True)
        
#Generate_AC creates a number of Aircraft objects and names them by counter
#Each aircraft is given a material condition state through random decisions
#Each aircraft is then given a flight decision to start

    def generate_ac(self):
        for i in range(g.gVars['numAircraft']):
            self.aircraft_counter += 1
            ac_id = Aircraft(self.aircraft_counter)
            #give some of the aircraft a material condition discrepancy 
            #to discover during preflight inspection
            ac_id.fl_decision()
            ac_id.avi_decision()
            ac_id.af_decision()
            ac_id.flight_decision()
            self.env.process(self.Controller(ac_id))
            yield self.env.timeout(0)

#Controller considers material condition, flight schedule, and decides 
#What each A/C next step in the process is
#if A/C has gripe, send to repair process
#if A/C on schedule to fly, send to preflight inspection
#if A/C not on schedule and no gripes, send to downtime

    def Controller(self, aircraft):   
        start_q_controller = self.env.now
        with self.controller.request() as req:
            yield req
            print(round(self.env.now, 1),": A/C:",aircraft.id, " - Controller:", \
                 self.controller.count, "/", self.controller.capacity)
            end_q_controller = self.env.now
            aircraft.q_time_controller = aircraft.q_time_controller + (end_q_controller - start_q_controller)
            sampled_controller_duration = random.normalvariate(g.gVars['mean_controller'], g.gVars['sigma_controller'])
            #use random controller time to conclude process
            yield self.env.timeout(sampled_controller_duration)
            
            if aircraft.fl_gripe == True and self.flightlineMech.count >= 0:
                #give to airframes to repair
                self.env.process(self.afRepairProcess(aircraft))  
                
            elif aircraft.af_gripe == True and self.airframeMech.count >= 0:
                #give to avionics to repair
                self.env.process(self.afRepairProcess(aircraft))
                
            elif aircraft.avi_gripe == True:
                #send to avionics to repair (already counted for resources)
                self.env.process(self.aviRepairProcess(aircraft))
                
            elif aircraft.flight == True:
                #tell simpy to run repair process method
                self.env.process(self.preflightInspection(aircraft))
                
            else:
                self.env.process(self.downtime(aircraft))
                
#V1.6, this clause to records data to dataframe at the controller function
        if self.env.now > g.gVars['warm_up_period']:
            df_to_add = pd.DataFrame({"AC_ID":[aircraft.id],
                                      "Q_Time_Controller":[aircraft.q_time_controller],
                                      "Q_Time_FlightLineMech":[aircraft.q_time_flightlineMech],
                                      "Q_Time_AirFrameMech":[aircraft.q_time_airframeMech],
                                      "Q_Time_aviTech":[aircraft.q_time_aviTech],
                                      "Total_Flight_Time":[aircraft.totalFlightTime],
                                      "Total_Flights":[aircraft.totalFlights],
                                      "Total_AF_Repair_Time":[aircraft.totalAFRepairTime],
                                      "Total_FL_Repair_Time":[aircraft.totalFLRepairTime],
                                      "Total_Avi_Repair_Time":[aircraft.totalAviRepairTime],
                                      "Total_Repair_Time":[aircraft.totalRepairTime]})
            df_to_add.set_index("AC_ID", inplace=True)
            self.results_df = self.results_df.append(df_to_add)
                
#preflightInspection represents a process BEFORE flight, with the intent of discovering
#discrepancies before the act of flying
            
    def preflightInspection(self, aircraft):
        start_q_flightlineMech = self.env.now
        start_q_airframeMech = self.env.now
        print(round(self.env.now, 1),": A/C:", aircraft.id, "- to preflight insp")
        with self.flightlineMech.request(), self.airframeMech.request() as req:
            yield req
            print(round(self.env.now, 1),": A/C", aircraft.id, "- in preflight, FL:", self.flightlineMech.count, ", AF:", self.airframeMech.count)
            #once flightlineMech and airframeMech is available, end queue time
            end_q_flightlineMech = self.env.now
            end_q_airframeMech = self.env.now
            
            #calculate total queue time
            aircraft.q_time_flightlineMech = aircraft.q_time_flightlineMech + (end_q_flightlineMech - start_q_flightlineMech)
            aircraft.q_time_airframeMech = aircraft.q_time_airframeMech + (end_q_airframeMech - start_q_airframeMech)
            
            #apply probability of discovering discrepancy during preflight
            aircraft.fl_decision()
            aircraft.af_decision()
            aircraft.avi_decision()
            
            #derive a random registration queue time
            sampled_preflightInspection_duration = random.expovariate(1.0/g.gVars['mean_preflightInspection'])
            #use random registration time to conclude process
            yield self.env.timeout(sampled_preflightInspection_duration)
            #let user know that preflight is complete
            print(round(self.env.now, 1),": A/C:", aircraft.id, "- complete preflight")
            
            #this part does the outcome of the inspection
            #if/else represents the outcome of the inspection, if good - fly
            #if gripe discovered, report to controller
            if aircraft.fl_gripe == True or aircraft.avi_gripe == True or aircraft.af_gripe == True:
                #tell simpy env to run the preflightInspection method
                self.env.process(self.Controller(aircraft))
                print(round(self.env.now,1), ": A/C:", aircraft.id, "- gripe discovered during preflight")            
            else:
                self.env.process(self.fly(aircraft))
                print(round(self.env.now, 1), ": A/C:", aircraft.id, ": ready to fly")
                
#V1.8 RepairProcess has been separated by shop

    def aviRepairProcess(self, aircraft):
        
        start_q_aviTech = self.env.now
        with self.aviTech.request() as req: #req the resource
            yield req #give the resource once available
            print(round(self.env.now,1),": A/C:", aircraft.id, \
                  "- aviTech", self.aviTech.count, "repairing.")
            end_q_aviTech = self.env.now
            aircraft.q_time_aviTech = aircraft.q_time_aviTech + \
                (end_q_aviTech - start_q_aviTech) #add to q_time_aviTech
            sampled_aviTech_duration = random.expovariate(1.0/g.gVars['mean_avi_fix'])
            yield self.env.timeout(sampled_aviTech_duration) #timeout
            aircraft.totalAviRepairTime = aircraft.totalAviRepairTime + \
                sampled_aviTech_duration
            #finish the repair, switch the gripe off
            aircraft.avi_gripe == False
            print(round(self.env.now,1),": A/C:", aircraft.id, "- repaired by Avi.")
            #send back to controller
            self.env.process(self.Controller(aircraft))
                
    def afRepairProcess(self, aircraft):
        start_q_airframeMech = self.env.now
        with self.airframeMech.request() as req: #req the resource
            yield req #give the resource once available
            print(round(self.env.now,1), ": A/C:", aircraft.id, \
                  "- airframeMech", self.airframeMech.count, "repairing.")
            end_q_airframeMech = self.env.now
            aircraft.q_time_airframeMech = aircraft.q_time_airframeMech + \
                (end_q_airframeMech - start_q_airframeMech)
            sampled_airframeMech_duration = random.expovariate(1.0/g.gVars['mean_af_fix'])
            yield self.env.timeout(sampled_airframeMech_duration)
            aircraft.totalAFRepairTime = aircraft.totalAFRepairTime + sampled_airframeMech_duration
            aircraft.af_gripe == False #switch A/C state back to false
            print(round(self.env.now, 1), ": A/C:", aircraft.id, "- repaired by AF.")
            #send back to controller
            self.env.process(self.Controller(aircraft))
                
    def flRepairProcess(self, aircraft):
        start_q_flightlineMech = self.env.now
        with self.flightlineMech.request() as req: #req the resource
            yield req #give the resource once available
            print(round(self.env.now,1), ": A/C:", aircraft.id, \
                  "- flightlineMech", self.flightlineMech.count, "repairing.")
            end_q_flightlineMech = self.env.now
            aircraft.q_time_flightlineMech = aircraft.q_time_flightlineMech + \
                (end_q_flightlineMech - start_q_flightlineMech)
            sampled_flightlineMech_duration = random.expovariate(1.0/g.gVars['mean_fl_fix'])
            aircraft.fl_gripe == False #switch A/C state back to false
            yield self.env.timeout(sampled_flightlineMech_duration)
            aircraft.totalFLRepairTime = aircraft.totalFLRepairTime + sampled_flightlineMech_duration
            print(round(self.env.now, 1), ": A/C:", aircraft.id, "- repaired by FL.")
            #send back to controller
            self.env.process(self.Controller(aircraft))    
            
 #downtime represents the large amount of time that the aircraft is not flying, and workers aren't working.
      
    def downtime(self, aircraft): 
        print (round(self.env.now,1),": A/C:", aircraft.id, "- begins downtime.")
        downtimeDur  = random.normalvariate(g.gVars['mean_downtime'], g.gVars['downtime_sig'])
        yield self.env.timeout(downtimeDur)
        aircraft.flight_decision()
        self.env.process(self.Controller(aircraft))

#fly executes flying but also runs random probability that something broke during flight

    def fly(self, aircraft):
        takeoffTime = self.env.now
        print (round(self.env.now,1),": A/C:", aircraft.id, "- took off.")
        flytimeDur  = random.normalvariate(g.gVars['mean_flytime'], g.gVars['flytime_sig'])
        yield self.env.timeout(flytimeDur)
        aircraft.fl_decision()
        aircraft.avi_decision()
        aircraft.af_decision()
        landTime = self.env.now 
        #calculate flight time and add to total
        aircraft.totalFlightTime = aircraft.totalFlightTime + (landTime - takeoffTime)
        aircraft.totalFlights += 1 #increment aircraft's number of flights
        print (round(self.env.now, 1),": A/C:", aircraft.id, "- landed flight", aircraft.totalFlights, ".")
        self.env.process(self.downtime(aircraft))

#calculate_mean_q_times takes the dataframe from the simulation
#finds the mean for all aicraft

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
        self.mean_total_repairTime = self.results_df["Total_Repair_Time"].mean()

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
                                self.mean_total_aviRepairTime,
                                self.mean_total_repairTime]
            writer.writerow(results_to_write)
            
#start simulation by calling generate_ac function
#run simulation until end
#calculate run results using calculate mean_q_times() function
#write run results to file
           
    def run(self):
        self.env.process(self.generate_ac())
        self.env.run(until=(g.gVars['warm_up_period'] + g.gVars['sim_duration']))
        self.calculate_mean_q_times()
        self.write_run_results()

#after simulation is complete, read the results from g.output_file
#print the results.
        
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
        
        
""" everything above is definitiion of classes and functions, but here’s where
the code will start actively doing things.
For the number of specified runs in the g class, create an instance of the
Squadron_Model class, and call its run method"""

#this code is read first, and begins by creating g.output_file
        
with open(g.output_file, "w", newline="") as f:
    writer = csv.writer(f, delimiter=",")
    column_headers = ["Run", "Mean_Q_Time_Controller",
                      "Mean_Q_Time_FlightLineMech", "Mean_Q_Time_AirFrameMech",
                      "Mean_Q_Time_aviTech", "Mean_Total_Flight_Time", 
                      "Mean_Total_Flights", "Mean_Total_afRepairTime",
                      "Mean_Total_flRepairTime", "Mean_Total_aviRepairTime",
                      "Mean_Total_RepairTime"]
    writer.writerow(column_headers)

for run in range(g.gVars['numTrials']):
    print("Run ", run+1, " of ", g.gVars['numTrials'], sep="")
    my_sq_model = Squadron_Model(run)
    my_sq_model.run()
    print()
#once trial is complete, we’ll create an instance of the
#trial_result_calculator class and run the print_trial_results method
my_trial_results_calculator = Trial_Results_Calculator()
my_trial_results_calculator.print_trial_results()