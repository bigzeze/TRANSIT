import traci
import copy
from Simulation import SUMOInterface

import traci._trafficlight
# TLFailuer and AbruptFlow needs to be modified

class Event():
    def __init__(self,sumoInterface:SUMOInterface,injectTime:int,removeTime:int,pos:str):
        self.sumoInterface = sumoInterface
        self.enable_print = False
        self.injectTime = injectTime
        self.removeTime = removeTime
        self.sumoInterface.eventfile = None
        self.pos = pos
    
    def set_print(self,state):
        self.enable_print = state

    def setInjectTime(self,injectTime:int):
        self.injectTime = injectTime
    def setRemoveTime(self,removeTime:int):
        self.removeTime = removeTime

    def stepCheck(self,step:int):
        self.step = step
        if step == self.injectTime:
            self.inject()
        if step == self.removeTime:
            self.remove()
    def inject(self):
        if self.sumoInterface.eventfile:
            self.sumoInterface.eventfile.write(f'{self.step}\tAnomaly {self.__class__.__name__} is injected at {self.pos}.\n')
        pass

    def remove(self):
        if self.sumoInterface.eventfile:
            self.sumoInterface.eventfile.write(f'{self.step}\tAnomaly {self.__class__.__name__} at {self.pos} is removed .\n')
        pass

'''
(original edition: allows multiple edges)
class EdgeSlow(Event):
    def __init__(self, injectTime:int,removeTime:int,location_speed:dict):
        super().__init__(injectTime,removeTime)
        self.location_speed = location_speed
        self.location = list(self.location_speed.keys())
    
    def inject(self):
        self.original_speed = {}
        for location,speed in self.location_speed.items():
            lane_number = traci.edge.getLaneNumber(location)
            for lane_n in range(lane_number):
                lane_id = location + '_' +str(lane_n)
                self.original_speed[lane_id] = traci.lane.getMaxSpeed(lane_id) # temporary
                traci.lane.setMaxSpeed(laneID=lane_id,speed=speed)
        
    def remove(self):
        for lane_name,speed in self.original_speed.items():
            traci.lane.setMaxSpeed(laneID=lane_name,speed=speed)
'''

class SpeedLimit(Event):
    def __init__(self, sumoInterface,injectTime:int,removeTime:int,pos,beta):
        super().__init__(sumoInterface,injectTime,removeTime,pos)
        self.beta = beta
    def inject(self):
        super().inject()
        s0 = 7.5
        tr = 1
        self.original_speed = {}
        lane_number = traci.edge.getLaneNumber(self.pos)
        for lane_n in range(lane_number):
            lane_id = self.pos + '_' +str(lane_n)
            orgspeed =  traci.lane.getMaxSpeed(lane_id)
            self.original_speed[lane_id] = orgspeed
            newspeed = (orgspeed*s0*self.beta/(s0+tr*orgspeed))/(1-orgspeed*tr*self.beta/(s0+tr*orgspeed))
            traci.lane.setMaxSpeed(laneID=lane_id,speed=newspeed)
    
    def remove(self):
        super().remove()
        for lane_name,speed in self.original_speed.items():
            traci.lane.setMaxSpeed(laneID=lane_name,speed=speed)

'''         
class VehicleStop(Event):
    def __init__(self, injectTime:int,removeTime:int,location:list):
        super().__init__(injectTime,removeTime)
        self.location = location
    
    def inject(self):
        #self.original_speed = {}
        self.vehicles = []
        for i,location in enumerate(self.location):
            lane_number = traci.edge.getLaneNumber(location)
            for lane_n in range(lane_number):
                lane_id = location + '_' +str(lane_n)
                vehicles = traci.lane.getLastStepVehicleIDs(lane_id)
                if len(vehicles) == 0:
                    self.injectTime = self.injectTime+1
                    if self.enable_print:
                        print('vehicles not found in setp',self.injectTime,', will inject in next step')
                    return
                firstVehicle = vehicles[0]
                if firstVehicle !="":
                    #self.original_speed[location] = (firstVehicle,traci.vehicle.getSpeed(firstVehicle))
                    self.vehicles.append(firstVehicle)
                    traci.vehicle.setSpeed(firstVehicle,'0')
                else:
                    self.injectTime = self.injectTime+1
                    if self.enable_print:
                        print('vehicles not found in setp',self.injectTime,', will inject in next step')
                    return

    def remove(self):
        for vehicle in self.vehicles:
            traci.vehicle.setSpeed(vehicle,'-1')
'''

'''
class EdgeClose(Event):
    def __init__(self,injectTime:int,removeTime:int,location:list):
        super().__init__(injectTime,removeTime)
        self.location = location
    
    def inject(self):
        for i,location in enumerate(self.location):
            lane_number = traci.edge.getLaneNumber(location)
            for lane_n in range(lane_number):
                traci.lane.setAllowed(location+'_'+str(lane_n),[]) #temporary
    
    def remove(self):
        for i,location in enumerate(self.location):
            lane_number = traci.edge.getLaneNumber(location)
            for lane_n in range(lane_number):
                traci.lane.setDisallowed(location+'_'+str(lane_n),[])
'''

class TLFailure(Event):
    def __init__(self, sumoInterface,injectTime: int, removeTime: int, pos: str, beta):
        super().__init__(sumoInterface,injectTime, removeTime,pos)
        self.pos = pos
        self.beta = beta
    
    def inject(self):
        super().inject()
        self.originalProgram = traci.trafficlight.getProgram(self.pos)
        #print('original program',self.originalProgram)
        
        self.all_logic = traci.trafficlight.getAllProgramLogics(self.pos)
        for logic in self.all_logic:
            if logic.programID == self.originalProgram:
                self.currentLogic = logic
        #print(self.currentLogic)
        
        self.newLogic = copy.deepcopy(self.currentLogic)
        self.newLogic.programID = 'anomaly'

        self.newphase  = []
        for phase in self.newLogic.phases:
            if 'g' in phase.state or  'G' in phase.state:
                add_phase1 = copy.deepcopy(phase)
                add_phase1.duration = int(phase.duration*self.beta)
                add_phase1.minDur = int(phase.minDur*self.beta)
                add_phase1.maxDur = int(phase.maxDur*self.beta)

                add_phase2 = traci.trafficlight.Phase(duration=int(phase.duration*(1-self.beta)),state='r'*len(phase.state)\
                                                     ,minDur=int(phase.minDur*(1-self.beta)),maxDur=int(phase.maxDur*(1-self.beta)))
                
                self.newphase.append(add_phase1)
                self.newphase.append(add_phase2)
            else:
                self.newphase.append(phase)
        self.newphase = tuple(self.newphase)
        self.newLogic.phases = self.newphase
        traci.trafficlight.setProgramLogic(self.pos,self.newLogic)
        '''
        #print('new program',self.currentProgram)
        self.all_logic = traci.trafficlight.getAllProgramLogics(self.location)
        for logic in self.all_logic:
            if logic.programID == self.currentProgram:
                self.currentLogic = logic
        print(self.currentLogic)
        print(self.all_logic[0].phases)
        '''
        '''
        phases(Phase(duration,state,minDur,maxDur))
        '''
    
    def remove(self):
        super().remove()
        traci.trafficlight.setProgram(self.pos,self.originalProgram)


class AbruptFlow(Event):
    def __init__(self, sumoInterface,injectTime, removeTime, pos, alpha):
        super().__init__(sumoInterface, injectTime, removeTime,pos)
        self.alpha = alpha 

    def inject(self):
        super().inject()
        self.injectedVehicles = []
        print(traci.route.getIDList())
        if self.pos in traci.route.getIDList():
            for i in range(int(self.alpha)):        
                traci.vehicle.add(vehID='anomaly'+str(i),routeID=self.pos,depart=self.step+i,departPos='random',departSpeed='max')
                print(f'vehicle {i} injected at step {self.step+i}')
                self.injectedVehicles.append('anomaly'+str(i))
        else:
            vehicles = traci.vehicle.getIDList()
            for vehicle in vehicles:
                if self.pos in vehicle:
                    self.pos = vehicle
            self.routeid = traci.vehicle.getRouteID(self.pos)
            self.route = traci.vehicle.getRoute(self.pos)
            nbottleneck = 0
            for edge in self.route:
                nbottleneck = max(traci.edge.getLastStepVehicleNumber(edge),nbottleneck)
            #vehicleCount = 0
            #vehicles = traci.vehicle.getIDList()
            
            #for vehicle in vehicles:
            #    if traci.vehicle.getRouteID(vehicle) == self.routeid:
            #        vehicleCount = vehicleCount + 1
            anomalCount = int(nbottleneck*self.alpha)
            for i in range(anomalCount):
                traci.vehicle.add(vehID='anomaly'+str(i),routeID=self.routeid,depart=self.step+i,departPos='random',departSpeed='max')
                self.injectedVehicles.append('anomaly'+str(i))
    def remove(self):
        super().remove()
        vehicles = traci.vehicle.getIDList()
        for vehicle in vehicles:
            if 'anomaly' in vehicle:
                traci.vehicle.remove(vehicle)



