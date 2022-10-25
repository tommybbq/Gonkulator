"""
Created on Mon Jul 19 14:45:07 2021.
@author: LtCol Thomas Kline, Divyam Khatri, Sam Thomas """
import simpy
import random
import csv
import pandas as pd
from dataclasses import dataclass
from enum import Enum, auto

class g:
    """
    A class that holds the global variables.
    ...
    Attributes
    ----------
    gVars: array
        Holds all the global variables
    output_file: str
        The string of the name of the file when the output will be reported \
            after the end of the file.
    Methods
    -------
    None
    """

    gVars = {}
    output_file = f"sq_trial_results.csv"

    def readVars():
        """
        Code to ingest input variables.
        Parameters
        ----------
        None
        Returns
        -------
        None
        """
        """code to ingest input variables"""
        with open('inputData.csv', mode='r') as infile:
            reader = csv.reader(infile)
            with open('coors_new.csv', mode='w') as outfile:
                writer = csv.writer(outfile)
                g.gVars = {rows[0]: rows[1] for rows in reader}
        g.gVars.pop('Variables')

        """string to int"""
        for key in g.gVars:
            try:
                g.gVars[key] = int(g.gVars[key])
            except ValueError:
                g.gVars[key] = float(g.gVars[key])
#       print(g.gVars)

    def getGVars():
        """
        Return gVars.
        Returns
        -------
        returns a list
            list has all of the global variables.
        """
        return g.gVars

class Workcenter(Enum):
    """Maintainters' workcenters"""
    FL = auto()
    AF = auto()
    AVI = auto()

@dataclass
class MAF:
    """
    Maintenance Action Form (MAF) class that represent actions required
    and actions taken on aircraft..
    ...

    Attributes
    ----------
    tailNum: int, relates to aircraft 
    workcenter: Workcenter enum, specifies which workcenter is appropriate.
    timetoComplete: int, uses gVars to predetermine the req completion time.
    timeWorked: int, decrements timetoComplete based on worktime.
    complete: bool, used to indicate if action is complete.

    Methods
    -------

    """
    tailNum: int
    mcn: int
    workcenter: Workcenter
    timetoComplete : int
    timeWorked: int = 0
    complete: bool = False
    priority: int = 1
    
class Time:
    """
    A class that controls the time for the simulation.
    ...
    Attributes
    ----------
    None
    Methods
    -------
    getTime(env):
        Return environment time.
    getDay(env):
        Returns day in simulation.
    getHour(env):
        Returns hour in simulation.
    getMinute(env):
        Return minute in current hour and day of simulation.
    getMinIntoCurrDay(env):
        Return minutes into current day.
    getMinLeftInShift(env):
        Return minutes left in daily shift.
    """
    def getTime(env):
        """
        Return environment time in days, hours, minutes.
        Parameters
        ----------
        env : int, simpy environment, a running total of minutes at which events 
            are scheduled.
        Returns
        -------
        returns time in a D:H:M format as a string.
        """
        return str(Time.getDay(env)) + ":" + \
            str(Time.getHour(env)) + ":" + str(Time.getMinute(env))

    def getDay(env):
        """
        Return day in simulation.
        Parameters
        ----------
        env : int, simpy environment, a running total of minutes at which events 
            are scheduled. 
        Returns
        -------
        day : int. the current day number in the simulation
        """
        time = env.now  # recorded in total minutes
        day = round(time // (24*60))  # // drops the
        return day

    def getHour(env):
        """
        Return hour of the current day in simulation.
        Parameters
        ----------
        env : int, simpy environment, a running total of minutes at which events 
            are scheduled. 
        Returns
        -------
        hour : int. the current hour in the current day in the simulation
        """
        time = env.now  # recorded in total minutes
        time = time % (24*60)  #discard day, % only keeps remainder (in minutes)
        hour = round(time // 60) #//discards remainder
        return hour

    def getMinute(env):
        """
        Return minute in current hour and day of simulation.
        Parameters
        ----------
        env : int, simpy environment, a running total of minutes at which events 
            are scheduled. 
        Returns
        -------
        minute : int.
        """
        time = env.now  # recorded in total minutes
        time = time % (24*60)  #discard day, % only keeps remainder (in minutes)
        time %= 60 #discard hours, only keep remainder
        minute = round(time // 1)
        return minute
    
    def getMinIntoCurrDay(env):
        """
        Return minute in current day of simulation.
        Parameters
        ----------
        env : int
            Simpy's "clock", a running total of minutes at which events 
            are scheduled.
        Returns
        -------
        minutesIntoCurrentDay : TYPE
            DESCRIPTION.
        """
        time = env.now #recorded in total minutes
        time = time % (24*60) # % only keeps remainder (in minutes)
        minutesIntoCurrentDay = time #assignes remainder to variable
        return minutesIntoCurrentDay
    
    def getMinLeftInShift(env):
        """
        Return minutes left in shift.
        Parameters
        ----------
        env : int
            Simpy's "clock", a running total of minutes at which events 
            are scheduled.
        Returns
        -------
        minutesLeftInShift : int
        """
        time = env.now 
        time = time % (24*60)
        if (g.gVars['offShiftHr']*60) - time > 0:
           minutesLeftInShift = (g.gVars['offShiftHr']*60) - time
        else: 
           minutesLeftInShift = 0
        return minutesLeftInShift

class Squadron_Model:
    """
    The class that contains the events in the simulation.
    ...

    Attributes
    ----------
    self.env(env):
    self.controller(self): int
        Simpy Resource, input variable number of controllers
    self.flightlineMech(self): int
        Simpy Resource, input variable number of flightline mechanics
    self.airframesMech(self): int
        Simpy Resource, input variable number of airframes mechanics
    self.aviTech(self): int
        Simpy Resource, input variable number of avionics technicians
    self.pilot(self): int
        Simpy Resource, input variable number of pilots
    

    Methods
    -------
    def generate_ac(self):
        creates a number of Aircraft objects and names them by counter
    def Controller(self, aircraft)
        onsiders material condition, flight schedule, and decides
    def inspect(self, aircraft):
        randomly break something on the aircraft
    def fly(self, aircraft):
        represents the time spent flying
    def aviRepairProcess(self, aircraft):
        represents the avionics repair process
    def afRepairProcess(self, aircraft):
        represents the airframe repair process
    def flRepairProcess(self, aircraft):
        represents the flightline repair process
    def downtime(self, aircraft):
        represents the large amount of time that the aircraft is not flying, \
            and workers aren't working.
    def run(self):
        run simulation until end
    """

    def __init__(self, trial_number):
        """
        Initialize local variables for Squadron Model.
        Returns
        -------
        None.
        """
        self.env = simpy.Environment()
        self.controller = simpy.Resource(self.env,
                                         capacity=g.gVars['numControllers'])
        self.flightlineMech = \
            simpy.Resource(self.env, capacity=g.gVars['numFlightlineMechs'])
        self.airframeMech = \
            simpy.Resource(self.env, capacity=g.gVars['numAirframeMechs'])
        self.aviTech = simpy.Resource(self.env, capacity=g.gVars[
            'numAviTechs'])
        self.pilot = simpy.Resource(self.env, capacity=g.gVars['numPilots'])
        self.minutesIn1Day = (24*60)
        self.offShiftHr = g.gVars['offShiftHr']
        self.onShiftHr = g.gVars['onShiftHr']
        self.prob_fl = g.gVars['prob_fl']
        self.prob_avi = g.gVars['prob_avi']
        self.prob_af = g.gVars['prob_af']
        self.prob_awp = g.gVars['prob_awp']
        self.trial_number = trial_number
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
        self.results_df["Total_MC_Time"] = []
        self.results_df["Total_NMC_Time"] = []
        self.results_df.set_index("tailNum", inplace=True)

    def generate_ac(self):
        """
        Generate all instances of the aircraft and sends them to controller.
        Yields
        ------
        yields to start controller for each specific aircraft.
        """
        for i in range(g.gVars['numAircraft']):
            tailNum = Aircraft(i+1) #increment tailNum
            self.env.process(self.Maint_Control(tailNum)) #send to Mx Control
            yield self.env.timeout(0) #now until end of range


    def Maint_Control(self, aircraft):
        """
        Controls what actions are appropriate for the aircraft.
        Parameters
        ----------
        aircraft:aircraft class object that each aircraft's attributes
        Yields
        ------
        yields to each process the aircraft goes through in its life

        """
        timeLeft = Time.getMinLeftInShift(self.env)
        if timeLeft > 5:
            with self.controller.request() as req:
                yield req
                self.env.timeout(5)   
                
                if aircraft.getStatus() == "newAircraft":
                    aircraft.startMC = self.env.now
                    self.env.process(self.inspect(aircraft))
                    
                elif aircraft.getStatus() == "needsInspection":
                   self.env.process(self.inspect(aircraft))
                   
                elif aircraft.getStatus() == "passedInspection":
                    self.env.process(self.fly(aircraft))
                    
                elif aircraft.getStatus() == "needsTroubleshooting":    
                    ld = aircraft.get_incompleteMAF() 
                    self.env.process(self.troubleshoot(aircraft, ld))

                    
                elif aircraft.getStatus() == "needsRepair":
                    
                    if any(maf.complete == False for maf in aircraft.mafs):
      
                        ld = aircraft.get_incompleteMAF() 
                        self.env.process(self.repair(aircraft, ld))
                        
                    else: 
                        aircraft.setStatus("doneRepair")
                        aircraft.startMC = self.env.now
                        nmc_time = aircraft.startMC - aircraft.startNMC
                        aircraft.totalNMCTime = aircraft.totalNMCTime + nmc_time
                        print("    ", aircraft.tailNum, ", NMC Time: ", aircraft.totalMCTime, \
                              "status: ", aircraft.status)
                        self.env.process(self.inspect(aircraft))
       
                elif aircraft.getStatus() == "doneRepair":
                    self.env.process(self.inspect(aircraft))
                    
                elif aircraft.getStatus() == "needPreflight":
                    self.env.process(self.fly(aircraft))
       
                elif aircraft.getStatus() == "doneFlight":
                    aircraft.setStatus("needsInspection")
                    self.env.process(self.inspect(aircraft))  
                    
                else:
                    raise Exception("aircraft status not known")
        else:
            self.env.process(self.downtime(aircraft))

    def inspect(self, aircraft):
        """
        Randomly break something on the aircraft.
        Parameters
        ----------
        aircraft : Class object for the aircraft that is being inspected.
        Yields
        ------
        yields a timeout of inspection time
        """

        print(Time.getTime(self.env), "- A/C", aircraft.tailNum,
              "- in inspection")
        yield self.env.timeout(5) #length of inspection in time
        
        if random.random() <= self.prob_fl:
            aircraft.add_maf(aircraft.maf_counter, workcenter=Workcenter.FL)

        if random.random() <= self.prob_avi:
            aircraft.add_maf(aircraft.maf_counter, workcenter=Workcenter.AVI)

        if random.random() <= self.prob_af:
            aircraft.add_maf(aircraft.maf_counter, workcenter=Workcenter.AF)

        if any(maf.complete == False for maf in aircraft.mafs):
            aircraft.changeStatus("needsTroubleshooting")
            aircraft.startNMC = self.env.now
            mc_time = aircraft.startNMC - aircraft.startMC
            aircraft.totalMCTime = aircraft.totalMCTime + mc_time
            print("    ", aircraft.tailNum, ", MC Time: ", aircraft.totalMCTime, \
                  "status: ", aircraft.status)

        else:
            aircraft.changeStatus("passedInspection")
        print(Time.getTime(self.env), "- A/C", aircraft.tailNum,
              "-", aircraft.status)
        self.env.process(self.Maint_Control(aircraft))

    def fly(self, aircraft):
        """
        Simulate flying the aircraft.
        Parameters
        ----------
        aircraft : Class object for the aircraft that is being inspected.
        Yields
        ------
        yields the timeout for flight time
        """
        if any(maf.complete == False for maf in aircraft.mafs):
            raise Exception('Cant fly, {aircraft.tailNum} broken')    

        else:
#            print(Time.getTime(self.env), "- A/C", aircraft.tailNum,
#                  "- getting Pilot")
            
            with self.pilot.request() as req:
                yield req
                takeoffTime = self.env.now
                aircraft.totalFlights += 1
                # increment aircraft's number of flights
    
                flytimeDur = random.normalvariate(g.gVars['mean_flytime'],
                                                  g.gVars['flytime_sig'])
                print(Time.getTime(self.env), "- A/C", aircraft.tailNum,
                      "- departed on flight", aircraft.totalFlights)
                yield self.env.timeout(flytimeDur)
                print(Time.getTime(self.env), "- A/C", aircraft.tailNum,
                      "- completed flight", aircraft.totalFlights)
                landTime = self.env.now
                flightTime = landTime - takeoffTime
                aircraft.totalFlightTime = aircraft.totalFlightTime + flightTime
 #               aircraft.onSchedule = False
                aircraft.changeStatus("doneFlight")
                self.env.process(self.Maint_Control(aircraft))

    def troubleshoot(self, aircraft, ld):
        """
        Represent the troubleshooting process: when inspection reveals that something
        is wrong, troubleshooting process identifies the actions and parts 
        required to correct the discrepancy.
        Parameters
        ----------
        Aircraft
        Returns
        -------
        None
        """
        start_q_mechanic = self.env.now
        if ld.workcenter == Workcenter.AVI:
            mech = self.aviTech.request()
        elif ld.workcenter == Workcenter.FL:
            mech = self.flightlineMech.request()
        elif ld.workcenter == Workcenter.AF:
            mech = self.airframeMech.request()
        else:
            raise Exception('Workcenter unknown {ld.workcenter}')
        troubleshoot_duration = random.normalvariate(g.gVars['mean_troubleshoot'], \
                                                    g.gVars['troubleshoot_sig'])
        with mech as req: #req the resource
            yield req #give the resource once available

            print(f"{Time.getTime(self.env)} - A/C {aircraft.tailNum} - {ld.workcenter} troubleshooting mcn {ld.mcn}")
            
            end_q_mechanic = self.env.now
            q_time = end_q_mechanic - start_q_mechanic
            aircraft.q_time_mechanic = aircraft.q_time_mechanic + q_time
            yield self.env.timeout(troubleshoot_duration)
            parts_req = random.random() < self.prob_awp
            if parts_req:
                self.env.process(self.awp_supply(aircraft, ld))
                print(f"{Time.getTime(self.env)} - A/C {aircraft.tailNum} - mcn {ld.mcn} requires parts")
            
            else: 
                aircraft.changeStatus("needsRepair")
                self.env.process(self.Maint_Control(aircraft))
                print(f"{Time.getTime(self.env)} - A/C {aircraft.tailNum} - {ld.workcenter} troubleshooting mcn {ld.mcn} complete")

    def repair(self, aircraft, ld):
        """
        Represent the repair process.
        Parameters
        ----------
        Aircraft & a MAF object to record attributes
        Returns
        -------
        None
        """
        start_q_time = self.env.now
        if ld.workcenter == Workcenter.AVI:
            mech = self.aviTech.request()
        elif ld.workcenter == Workcenter.FL:
            mech = self.flightlineMech.request()
        elif ld.workcenter == Workcenter.AF:
            mech = self.airframeMech.request()
        else:
            raise Exception('Workcenter unknown {ld.workcenter}')
        with mech as req: #req the resource
            yield req #give the resource once available

            print(f"{Time.getTime(self.env)} - A/C {aircraft.tailNum} - {ld.workcenter} working mcn {ld.mcn}")
            
            end_q_time = self.env.now
            q_time = end_q_time - start_q_time
            if ld.workcenter == Workcenter.AVI:
                aircraft.q_time_aviTech = aircraft.q_time_aviTech + q_time
            elif ld.workcenter == Workcenter.FL:
                aircraft.q_time_flightlineMech = aircraft.q_time_flightlineMech + q_time
            elif ld.workcenter == Workcenter.AF:
                aircraft.q_time_airframesMech = aircraft.q_time_airframesMech + q_time
            else:
                raise Exception('Workcenter unknown {ld.workcenter}')

            timeleft = Time.getMinLeftInShift(self.env)
            
            if 0 <= timeleft <=5:
                self.env.process(self.downtime(aircraft))
            
            else:
                if ld.timetoComplete < timeleft:
                    worktime = ld.timetoComplete
                else:
                    worktime = timeleft
                    
                yield self.env.timeout(worktime)
                
                setattr(ld, "timeWorked", ld.timeWorked + worktime)
                setattr(ld, "timetoComplete", ld.timetoComplete - worktime)
                
                if ld.workcenter == Workcenter.AVI:
                    aircraft.totalAviRepairTime = aircraft.totalAviRepairTime + worktime
                    print("Avi")
                    print(aircraft.totalAviRepairTime)
                elif ld.workcenter == Workcenter.FL:
                    aircraft.totalFLRepairTime = aircraft.totalFLRepairTime + worktime
                    print("FL")
                    print(aircraft.totalFLRepairTime)
                elif ld.workcenter == Workcenter.AF:
                    aircraft.totalAFRepairTime = aircraft.totalAFRepairTime + worktime
                    print("AF")
                    print(aircraft.totalAFRepairTime)
                else:
                    raise Exception('Workcenter unknown {ld.workcenter}')
                
                if ld.timetoComplete == 0:
                    print(f"{Time.getTime(self.env)} - A/C {aircraft.tailNum} - {ld.workcenter} completed mcn {ld.mcn}") 
                    setattr(ld, "complete", True)
                
                else:
                    print(f"{Time.getTime(self.env)} - A/C {aircraft.tailNum} - {ld.workcenter} worked mcn {ld.mcn}, end of shift")
                    
                self.env.process(self.Maint_Control(aircraft))
                
                
    def awp_supply(self, aircraft, ld):
        """
        Represent the troubleshooting process.
        Parameters
        ----------
        Aircraft & a MAF object to record attributes
        Returns
        -------
        None
        """
        awp_time = random.expovariate(1.0/g.gVars['mean_awp'])
        print(f"{Time.getTime(self.env)} - A/C {aircraft.tailNum} - awaiting parts for mcn {ld.mcn}")        
        yield self.env.timeout(awp_time)
        aircraft.totalAWPTime = aircraft.totalAWPTime + awp_time
        print(f"{Time.getTime(self.env)} - A/C {aircraft.tailNum} - mcn {ld.mcn} parts received")
        aircraft.changeStatus("needsRepair")
        self.env.process(self.Maint_Control(aircraft))
        

    def downtime(self, aircraft):
        """
        Accounts for the hours where squadron personnel not working.
        Parameters
        ----------
        aircraft
        Returns
        ------
        None
        """
        downtimeDur = (self.minutesIn1Day-Time.getMinIntoCurrDay(self.env)) + (self.onShiftHr*60)
        yield self.env.timeout(downtimeDur)
        if self.env.now > g.gVars['warm_up_period']:
            df_to_add = pd.DataFrame({"tailNum":[aircraft.tailNum],
                                     "Q_Time_Controller":[aircraft.q_time_controller],
                                     "Q_Time_FlightLineMech":[aircraft.q_time_flightlineMech],
                                     "Q_Time_AirFrameMech":[aircraft.q_time_airframesMech],
                                     "Q_Time_aviTech":[aircraft.q_time_aviTech],
                                     "Total_Flight_Time":[aircraft.totalFlightTime],
                                     "Total_Flights":[aircraft.totalFlights],
                                     "Total_AF_Repair_Time":[aircraft.totalAFRepairTime],
                                     "Total_FL_Repair_Time":[aircraft.totalFLRepairTime],
                                     "Total_Avi_Repair_Time":[aircraft.totalAviRepairTime],
                                     "Total_MC_Time":[aircraft.totalMCTime],
                                     "Total_NMC_Time":[aircraft.totalNMCTime]})
            df_to_add.set_index("tailNum", inplace=True)
            self.results_df = self.results_df.append(df_to_add)
        self.env.process(self.Maint_Control(aircraft))
        
    def calculate_means(self):
        """
        Takes dataframe output to calculate means.
        Parameters
        ----------
        None
        Returns
        ------
        None
        """
        self.mean_q_time_controller = self.results_df["Q_Time_Controller"].mean()
        self.mean_q_time_flightlineMech = self.results_df["Q_Time_FlightLineMech"].mean()
        self.mean_q_time_airframeMech = self.results_df["Q_Time_AirFrameMech"].mean()
        self.mean_q_time_aviTech = self.results_df["Q_Time_aviTech"].mean()
        self.mean_total_flightTime = self.results_df["Total_Flight_Time"].mean()
        self.mean_total_flights = self.results_df["Total_Flights"].mean()
        self.mean_total_afRepairTime = self.results_df["Total_AF_Repair_Time"].mean()
        self.mean_total_flRepairTime = self.results_df["Total_FL_Repair_Time"].mean()
        self.mean_total_aviRepairTime = self.results_df["Total_Avi_Repair_Time"].mean()
        self.mean_total_MCTime = self.results_df["Total_MC_Time"].max()
        self.mean_total_NMCTime = self.results_df["Total_NMC_Time"].mean()
        
    #write trial run results as new line in g.output_file
    def write_run_results(self):
        """
        Writes results of run to csv file.
        Parameters
        ----------
        aircraft
        Returns
        ------
        None
        """
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
                               self.mean_total_MCTime,
                               self.mean_total_NMCTime]
            writer.writerow(results_to_write) 

    def run(self):
        """
        Start the simulation.
        Calls generate ac and runs the simulation for sim duration

        Returns
        -------
        None.
        """
        self.env.process(self.generate_ac())
        self.env.run(until=(g.gVars['warm_up_period'] + g.gVars['sim_duration']))
        print(g.gVars['warm_up_period'] + g.gVars['sim_duration'])
        self.calculate_means()
        self.write_run_results()

class Aircraft:
    """
    A class to represent an aircraft.
    ...
    Attributes
    ----------
    self.tailNum:int
        aircraft tail number
    self.status:str
        aircraft status
    self.lastStatus:str
        last status if aircraft
    self.maf_counter: int
        used in adding a readable mcn integer
    self.mafs: MAF list
        list of MAF objects used in recording maintenance
    self.startMC: int
        used in calculating total MC and NMC time during sim
    self.startNMC: int
        used in calculating total MC and NMC time during sim
    self.q_time_controller: int
        queue time for controller
    self.q_time_mechanic: int
        queue time for mechanic of any type
    self.q_time_flightlineMech : int
        queue time for flightline mechanic
    self.q_time_airframesMech : int
        queue time for airframes mechanic
    self.q_time_aviTech : int
        queue time for avionics technician
    self.q_time_pilot: int
        queue time for pilot
        
    self.totalFlightTime: int
        total flight time in minutes
    self.totalFlights: int
        total number of flight
    self.totalAviRepairTime: int
        total time spent in avionics repairs
    self.totalFLRepairTime: int
        total time spent in flightline repairs
    self.totalAFRepairTime: int
        total time spent in airframes repairs
    self.totalAWPTime: int
        total time waiting for parts (in minutes)
    self.totalMCTime: int
        total time aircraft is mission capable (in minutes)
    self.totalNMCTime: int
        total time aircraft is non-mission capable (in minutes)
        
    self.onSchedule:bool
        whether aircraft is on schedule or not

    Methods
    -------
    def getTailNum(self):
        Gets the tail number.
    def getStatus(self):
        Gets the status.
    def setStatus(self, status):
        Sets the status.
    def changeStatus(self,newStatus):
        Changes the status.
    def calculate_timetoComplete(self, workcenter):
        Choose a time to complete MAF referencing workcenter.
    def add_MAF(self, MAF, workcenter):
        Create a MAF and add it to aircraft's list of MAFs.
    def get_incompleteMAF(self):
        Iterate through aircraft's list of MAFs, return first incomplete.
    det get_lastMAF(self):
        Iterate through aircraft's list of MAFs, return last incomplete.
    """

    def __init__(self, tailNum): #default values on initialization
        self.tailNum = tailNum
        self.status = "newAircraft"
        self.lastStatus = ""
        self.maf_counter = 0
        self.mafs: [MAF] = []
        self.startMC = 0
        self.startNMC = 0

        self.q_time_controller = 0
        self.q_time_mechanic = 0
        self.q_time_flightlineMech = 0
        self.q_time_airframesMech = 0
        self.q_time_aviTech = 0
        self.q_time_pilot = 0

        self.totalFlightTime = 0
        self.totalFlights = 0
        self.totalAviRepairTime = 0
        self.totalFLRepairTime = 0
        self.totalAFRepairTime = 0
        self.totalAWPTime = 0
        self.totalMCTime = 0
        self.totalNMCTime = 0

        self.onSchedule = True

    def getTailNum(self):
        """
        Get the tail number.
        Returns
        -------
        tailNum (int)
        """
        return self.tailNum

    def getStatus(self):
        """
        Get the status.
        Returns
        -------
        status (str)
        """
        return self.status

    def setStatus(self, status):
        """
        Set the status.
        Parameters
        ----------
        status : int
            aircraft status.
        Returns
        -------
        None.

        """
        self.status = status

    def changeStatus(self, newStatus):
        """
        Change the status.
        Parameters
        ----------
        newStatus : str
            status to change to.
        Returns
        -------
        None.
        """
        if newStatus != self.status:
            self.lastStatus = self.status
            self.status = newStatus
        else:
            self.status = newStatus
            
    def calculate_timetoComplete(self, workcenter) -> None:
        """
        Assign timetoComplete for MAF.
        Parameters
        ----------
        workcenter : enum
            uses workcenter to apply random value.
        Returns
        -------
        timetoComplete: int
        """
        if workcenter == Workcenter.FL:
            timetoComplete = random.expovariate(1.0/g.gVars['mean_fl_fix'])
        elif workcenter == Workcenter.AF:
            timetoComplete = random.expovariate(1.0/g.gVars['mean_af_fix'])
        elif workcenter == Workcenter.AVI:
            timetoComplete = random.expovariate(1.0/g.gVars['mean_avi_fix']) 
        return timetoComplete
    
    def add_maf(self, maf: MAF, workcenter) -> None:
        """
        add a maf to the list of mafs.
        Parameters
        ----------
        maf: MAF class
        workcenter: enum
        Returns
        -------
        appends maf into aircraft.mafs list
        """
        self.maf_counter += 1
        timetoComplete = self.calculate_timetoComplete(workcenter)
        self.mafs.append(MAF(tailNum=self.tailNum, mcn=self.maf_counter, workcenter=workcenter, timetoComplete=timetoComplete))
    
                
    def get_incompleteMAF(self):
        """
        evaluates maf.complete == False then returns first object.
        Parameters
        ----------
        None
        Returns
        -------
        ld[0]: list
        """
        ld = []
        for maf in self.mafs:
            if maf.complete == False:
                ld.append(maf)
        return ld[0]

    def get_LastMAF(self):
        """
        evaluates maf.complete == False then returns last object.
        Parameters
        ----------
        None
        Returns
        -------
        ld[-1]: list
        """
        ld = []
        for maf in self.mafs:
            if maf.complete == False:
                ld.append(maf)
        return ld[-1]

g.readVars()
with open(g.output_file, "w", newline="") as f:
   writer = csv.writer(f, delimiter=",")
   column_headers = ["Run", "Mean_Q_Time_Controller",
                     "Mean_Q_Time_FlightLineMech", "Mean_Q_Time_AirFrameMech",
                     "Mean_Q_Time_aviTech", "Mean_Total_Flight_Time", 
                     "Mean_Total_Flights", "Mean_Total_afRepairTime",
                     "Mean_Total_flRepairTime", "Mean_Total_aviRepairTime",
                     "Mean_Total_MCTime", "Mean_Total_NMCTime"]
   writer.writerow(column_headers)

for run in range(g.gVars['numTrials']):
   print("Run ", run+1, " of ", g.gVars['numTrials'], sep="")
   my_sq_model = Squadron_Model(run)
   my_sq_model.run()
   print()
print("End Sim")
