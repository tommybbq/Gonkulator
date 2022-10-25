"""
Created on Mon Jul 19 14:45:07 2021.
@author: LtCol Thomas Kline, Divyam Khatri, Sam Thomas """
import simpy
import random
import csv
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
    gVars: array
        Holds all the global variables
    output_file: str
        The string of the name of the file when the output will be reported \
            after the end of the file.

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

    def __init__(self):
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
                    self.env.process(self.inspect(aircraft))
                    
                elif aircraft.getStatus() == "needInspection":
                   self.env.process(self.inspect(aircraft))
                   
                elif aircraft.getStatus() == "doneInspection":
                    self.env.process(self.fly(aircraft))
                    
                elif aircraft.getStatus() == "needsRepair":
                    
                    if any(maf.complete == False for maf in aircraft.mafs):
      
                        ld = aircraft.getMAF() 
                        if ld.workcenter == Workcenter.FL:
                            self.env.process(self.flRepairProcess(aircraft))
                        elif ld.workcenter == Workcenter.AF:
                            self.env.process(self.afRepairProcess(aircraft))
                        elif ld.workcenter == Workcenter.AVI:
                            self.env.process(self.aviRepairProcess(aircraft))
                        else: 
                            raise Exception("mafs complete, status needsRepair")
                        ld = []
                        
                    else: 
                        aircraft.setStatus("doneRepair")
                        self.env.process(self.inspect(aircraft))
       
                elif aircraft.getStatus() == "doneRepair":
                    self.env.process(self.inspect(aircraft))
                    
                elif aircraft.getStatus() == "needPreflight":
                    self.env.process(self.fly(aircraft))
       
                elif aircraft.getStatus() == "doneFlight":
                    aircraft.setStatus("needInspection")
                    self.env.process(self.inspect(aircraft))  
                    
                else:
                    raise Exception("got here")
                    rand = random.randint(0, 1)
                    if rand < 1:
                        aircraft.setStatus("needPreflight")
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
        print(Time.getTime(self.env), "- A/C", aircraft.tailNum,
              "- done inspecting")
        if random.random() <= self.prob_fl:
            aircraft.add_maf(aircraft.maf_counter, workcenter=Workcenter.FL)
            print("    A/C ", aircraft.tailNum, ": cut FL mcn: ", id(aircraft.mafs[-1]))
            aircraft.changeStatus("needsRepair")

        if random.random() <= self.prob_avi:
            aircraft.add_maf(aircraft.maf_counter, workcenter=Workcenter.AVI)
            print("    A/C ", aircraft.tailNum, ": cut AVI mcn: ", id(aircraft.mafs[-1]))
            aircraft.changeStatus("needsRepair")

        if random.random() <= self.prob_af:
            aircraft.add_maf(aircraft.maf_counter, workcenter=Workcenter.AF)
            print("    A/C ", aircraft.tailNum, ": cut AF mcn: ", id(aircraft.mafs[-1]))
            aircraft.changeStatus("needsRepair")

        aircraft.changeStatus("doneInspection")
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
                aircraft.changeStatus("needsRepair")
                self.env.process(self.Maint_Control(aircraft))

        else:
            print(Time.getTime(self.env), "- A/C", aircraft.tailNum,
                  "- waiting for pilot")
            
            with self.pilot.request() as req:
                yield req
                # takeoffTime = self.env.now
                aircraft.totalFlights += 1
                # increment aircraft's number of flights
    
                flytimeDur = random.normalvariate(g.gVars['mean_flytime'],
                                                  g.gVars['flytime_sig'])
                print(Time.getTime(self.env), "- A/C", aircraft.tailNum,
                      "- Start Flight")
                yield self.env.timeout(flytimeDur)
                print(Time.getTime(self.env), "- A/C", aircraft.tailNum,
                      "- End Flight")
                # landTime = self.env.now
 #               aircraft.onSchedule = False
                aircraft.changeStatus("doneFlight")
                self.env.process(self.Maint_Control(aircraft))

    def aviRepairProcess(self, aircraft):
        """
        Represent an avionics repair process.
        Parameters
        ----------
        Aircraft
        Returns
        -------
        None
        """
        start_q_aviTech = self.env.now
        workload = [maf for maf in aircraft.mafs if maf.workcenter == Workcenter.AVI and maf.complete == False]
        with self.aviTech.request() as req: #req the resource
            yield req #give the resource once available

            print(f"{Time.getTime(self.env)} - A/C {aircraft.tailNum} - avi working mcn {id(workload[0])}.")
            end_q_aviTech = self.env.now

            aircraft.q_time_aviTech = aircraft.q_time_aviTech + \
                (end_q_aviTech - start_q_aviTech)
            timeleft = Time.getMinLeftInShift(self.env)
            if int(workload[0].timetoComplete) < Time.getMinLeftInShift(self.env):
                print(f"    shift time left {Time.getMinLeftInShift(self.env)} > time to complete {workload[0].timetoComplete}")
                yield self.env.timeout(workload[0].timetoComplete) #timeout
                setattr(workload[0], "timeWorked", workload[0].timetoComplete)
                setattr(workload[0], "complete", True)
                print(f"{Time.getTime(self.env)} - A/C {aircraft.tailNum} - avi completed mcn {id(workload[0])}.")
                aircraft.totalAviRepairTime = aircraft.totalAviRepairTime + \
                    workload[0].timetoComplete
                self.env.process(self.Maint_Control(aircraft))

            elif 0 <= timeleft <=5:
                self.env.process(self.downtime(aircraft))

            else:
                print(f"    shift time left {Time.getMinLeftInShift(self.env)} < repair time {workload[0].timetoComplete}")
                setattr(workload[0], "timeWorked", workload[0].timetoComplete + timeleft)
                setattr(workload[0], "timetoComplete", workload[0].timetoComplete - timeleft)
                yield self.env.timeout(timeleft)
                print(f"{Time.getTime(self.env)} - A/C {aircraft.tailNum} - Avi end of shift, worked {timeleft} min.")
                aircraft.totalAviRepairTime = aircraft.totalAviRepairTime + timeleft
                self.env.process(self.Maint_Control(aircraft))


    def afRepairProcess(self, aircraft):
        """
        Represent an airframes repair process.
        Parameters
        ----------
        Aircraft
        Returns
        -------
        None
        """
        start_q_airframeMech = self.env.now
        workload = [maf for maf in aircraft.mafs if maf.workcenter == Workcenter.AF and maf.complete == False]
        with self.airframeMech.request() as req: #req the resource
            yield req #give the resource once available
            print(f"{Time.getTime(self.env)}- A/C {aircraft.tailNum} - airframes working mcn {id(workload[0])}.")
            end_q_airframeMech = self.env.now
            aircraft.q_time_airframeMech = aircraft.q_time_airframeMech + \
                (end_q_airframeMech - start_q_airframeMech)
            timeleft = Time.getMinLeftInShift(self.env)
            if int(workload[0].timetoComplete) < timeleft:
                print(f"    shift time left {timeleft}, time to complete {workload[0].timetoComplete}")
                yield self.env.timeout(workload[0].timetoComplete) #timeout
                setattr(workload[0], "timeWorked", workload[0].timetoComplete)
                setattr(workload[0], "complete", True)
                print(f"{Time.getTime(self.env)} - A/C {aircraft.tailNum} - airframes completed mcn {id(workload[0])}.")
                aircraft.totalAFRepairTime = aircraft.totalAFRepairTime + workload[0].timetoComplete
                self.env.process(self.Maint_Control(aircraft))

            elif 0 <= timeleft <=5:
                self.env.process(self.downtime(aircraft))

            else:
                print(f"    shift time left {timeleft} < repair time {workload[0].timetoComplete}")
                setattr(workload[0], "timeWorked", (workload[0].timeWorked + timeleft))
                setattr(workload[0], "timetoComplete", (workload[0].timetoComplete - timeleft))
                yield self.env.timeout(timeleft)
                print(f"{Time.getTime(self.env)} - A/C{aircraft.tailNum} - AF end of shift, worked {timeleft} min.")
                aircraft.totalAFRepairTime = aircraft.totalAFRepairTime + timeleft
                self.env.process(self.Maint_Control(aircraft))

    def flRepairProcess(self, aircraft):
        """
        Represent a flight line repair process.
        Parameters
        ----------
        Aircraft
        Returns
        -------
        None
        """
        start_q_flightlineMech = self.env.now
        workload = [maf for maf in aircraft.mafs if maf.workcenter == Workcenter.FL and maf.complete == False]
        with self.flightlineMech.request() as req: #req the resource
            yield req #give the resource once available
            print(f"{Time.getTime(self.env)} - A/C {aircraft.tailNum}- flightline working mcn {id(workload[0])}.")
            end_q_flightlineMech = self.env.now
            aircraft.q_time_flightlineMech = aircraft.q_time_flightlineMech + \
                (end_q_flightlineMech - start_q_flightlineMech)
            timeleft = Time.getMinLeftInShift(self.env)
            if int(workload[0].timetoComplete) < timeleft:
                print(f"    shift time left {timeleft} > time to complete {workload[0].timetoComplete}")
                yield self.env.timeout(workload[0].timetoComplete) #timeout
                setattr(workload[0], "timeWorked", workload[0].timetoComplete)
                setattr(workload[0], "complete", True)
                print(f"{Time.getTime(self.env)}- A/C {aircraft.tailNum}- flightline completed mcn {id(workload[0])}.")
                aircraft.totalAFRepairTime = aircraft.totalAFRepairTime + workload[0].timetoComplete
                self.env.process(self.Maint_Control(aircraft))
                
            elif 0 <= timeleft <=5:
                self.env.process(self.downtime(aircraft))

            else:
                print(f"    shift time left {timeleft} < repair time {workload[0].timetoComplete}")
                setattr(workload[0], "timeWorked", (workload[0].timeWorked + timeleft))
                setattr(workload[0], "timetoComplete", (workload[0].timetoComplete - timeleft))
                yield self.env.timeout(timeleft)
                print(f"{Time.getTime(self.env)} - A/C{aircraft.tailNum}- FL end of shift, worked {timeleft} min.")
                aircraft.totalAFRepairTime = aircraft.totalAFRepairTime + timeleft
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
        # time = self.env.now
#        print(Time.getTime(self.env), "- A/C", aircraft.tailNum,
#              "- Start Downtime")
        downtimeDur = (self.minutesIn1Day-Time.getMinIntoCurrDay(self.env)) + (self.onShiftHr*60)
        yield self.env.timeout(downtimeDur)
#        print(Time.getTime(self.env), "- A/C", aircraft.tailNum,
#              "- End Downtime")
        self.env.process(self.Maint_Control(aircraft))

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
        #self.write_run_results()

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
    self.gripe: int
        int to identify gripe
    self.fl_gripe:bool
        whether gripe is flightline
    self.avi_gripe:bool
        whether gripe is aviation
    self.af_gripe:bool
        whether gripe is airframes
    self.q_time_controller: int
        queue time for controller
    self.q_time_flightlineMech : int
        queue time for flightline mechanic
    self.q_time_airframeMech: int
        queue time for airframe mechanic
    self.q_time_aviTech: int
        queue time for avionics techician
    self.q_time_pilot: int
        queue time for pilot
    self.totalFlightTime: int
        total flight time
    self.totalFlights: int
        total number of flight
    self.totalAviRepairTime: int
        total time spent in aviation repair
    self.totalFLRepairTime: int
        total time spent in flightline repair
    self.totalAFRepairTime: int
        total time spent in airframe repair
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
    """

    def __init__(self, tailNum): #default values on initialization
        self.tailNum = tailNum
        self.status = "newAircraft"
        self.lastStatus = ""
        self.maf_counter = 0
        self.mafs: [MAF] = []
#        self.gripe = 0
#        self.fl_gripe = False
#        self.avi_gripe = False
#        self.af_gripe = False

        self.q_time_controller = 0
        self.q_time_flightlineMech = 0
        self.q_time_airframeMech = 0
        self.q_time_aviTech = 0
        self.q_time_pilot = 0

        self.totalFlightTime = 0
        self.totalFlights = 0
        self.totalAviRepairTime = 0
        self.totalFLRepairTime = 0
        self.totalAFRepairTime = 0

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
        self.mafs.append(MAF(tailNum=self.tailNum, mcn=self.maf_counter, workcenter=workcenter, timetoComplete=timetoComplete))
    
                
    def getMAF(self):
        ld = []
        for maf in self.mafs:
            if maf.complete == False:
                ld.append(maf)
        return ld[0]



g.readVars()
# print(g.getGVars())
my_sq_model = Squadron_Model()
my_sq_model.run()
print("End Sim")
