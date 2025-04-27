from gc import enable
import traci
from Functions import CMDInterface
import os
import random
random.seed(2024)

'''
class Vehicle():
    def __init__(self,id) -> None:
        self.id = id
        self.org_id = self.get_org_id(id)
        self.current_speed = None
        self.max_speed = None
        #self.record_time = recordtime
        #self.regenerate_interval = None
    def set_current_speed(self,current_speed):
        self.current_speed = current_speed
    def set_max_speed(self,max_speed):
        self.max_speed = max_speed
    
    def get_org_id(self):
        return self.id.split('_')[0]
'''

class Route():
    def __init__(self,id,type):
        self.id = id
        self.type = type
    
class Edge():
    def __init__(self,id) -> None:
        self.id = id
        self.current_speed = None
        self.max_speed = None
    
    def set_current_speed(self,current_speed):
        self.current_speed = current_speed
    
    def set_max_speed(self,max_speed):
        self.max_speed = max_speed

class SUMOInterface:
    def __init__(self,sumoBinary,net_file,route_file,statistic_file,tripinfo_file,prevent_loot=False,verbose=False,**kargs) -> None:
        self.sumoBinary = sumoBinary
        self.net_file = net_file
        self.route_file =route_file
        self.statistic_file = statistic_file
        self.tripinfo_file = tripinfo_file
        self.verbose = verbose
        self.kargs = kargs
        self.routes = {}
        self.vids = {}
        self.edges = {}
        self.prevent_loot = prevent_loot
        self.threshold = 300
        self.eventfile = None
        #self.build_vehicle_table()
    
    '''
    def build_vehicle_table(self):
        dom = xml.dom.minidom.parse(self.route_file)
        root = dom.documentElement
        vehicles = root.getElementsByTagName("vehicle")

        self.vehicle_dict = {}
        for vehicle in vehicles:
            id = vehicle.getAttribute('id')
            type = vehicle.getAttribute('type')
            route = vehicle.getAttribute("route")
            self.vehicle_dict[id] = {'type':type,'route':route}
    '''

    def startSUMO(self):
        '''
        sumoBinary: 'sumo-gui' or 'sumo'
        net_file: network defination file
        route_file: traffic demand defination file
        additional_file: additional infrastructure file, such as fixed detectors
        netoutput_file: output file of netstate-dump
        '''

        net_option = '-n'
        route_option = '-r'
        teleport_option = '--time-to-teleport'
        teleport_time = '-1' # teleport after waiting time
        additional_option = '-a'
        netoutput_option = '--netstate-dump'
        statistic_option = '--statistic-output'
        durationlog_option = '--duration-log.statistics'
        statistic_trip_option = '--tripinfo-output'
        write_unfinished_option = '--tripinfo-output.write-unfinished'
        options = {}
        options[net_option] = self.net_file
        options[route_option] = self.route_file
        options[teleport_option] = teleport_time
        if 'additional_file' in self.kargs.keys():
            additional_file = self.kargs['additional_file']
            options[additional_option] = additional_file
        if 'netoutput_file' in self.kargs.keys():
            netoutput_file = self.kargs['netoutput_file']
            options[netoutput_option] = netoutput_file
        options[statistic_option] = self.statistic_file
        options[statistic_trip_option] = self.tripinfo_file
        options[durationlog_option] = None
        options[write_unfinished_option] = None
        
        interface = CMDInterface(self.sumoBinary,options)
        interface.setVerbose(self.verbose)
        interface.cmdGenerator()

        if not self.verbose:
            f = open(os.devnull,'w')     
            traci.start(interface.optList,verbose=self.verbose,stdout=f)  # Execute sumo-gui from the command line to start the simulation
            f.close()
        else:
            traci.start(interface.optList,verbose=self.verbose)

    def open_event_file(self,filename):
        self.eventfile = open(filename,mode='w')

    def close_event_file(self):
        self.eventfile.close()

    def simulation(self,startStep,endStep,events,qbar=None):
        self.step = startStep
        self.events = events
        while traci.simulation.getMinExpectedNumber() > 0:
            #if step == 10500:
            #    print(traci.vehicle.getRoute('')
            if self.step == startStep:
                if self.eventfile:
                    self.eventfile.write(f'{self.step}\tSimulation starts.\n')
                    self.eids = traci.edge.getIDList()
                    # for eid in self.eids:
                    #     self.edges[eid] = Edge(eid)
                    #     self.edges[eid].set_max_speed(max([traci.lane.getMaxSpeed(eid+'_'+str(i)) for i in range(traci.edge.getLaneNumber(eid))]))
            traci.simulationStep()
            self.regenerate_and_update()
            if self.prevent_loot:
                self.prevent_loot_congetsion(self.threshold)
            #if self.eventfile:
            #    self.object_event_sequence(step)
            for event in events:
                event.stepCheck(self.step)
            if qbar:
                qbar.update(1)
            self.step += 1
            if self.step == endStep:
                self.closeSUMO()
                if self.eventfile:
                    self.eventfile.write(f'{self.step}\tSimulation ends.\n')
                break
        self.closeSUMO()

    def regenerate_and_update(self):
        current_vids = traci.vehicle.getIDList()
        #print(f'last step:{len(self.vids)}, current step:{len(current_vids)}')
        count = 0
        newinjected = []
        for vid in self.vids:
            if vid not in current_vids:
                org_id = vid.split('_')[0]
                if len(vid.split('_'))<2:
                    vehicle_index = 0
                else:
                    vehicle_index = eval(vid.split('_')[1])
                route_id = '.'.join(org_id.split('.')[:2])
                if 'anomaly' in route_id and self.step > max([event.removeTime for event in self.events]):
                    continue
                traci.vehicle.add(vehID=org_id+'_'+str(vehicle_index+1),routeID=self.routes[route_id].id,typeID=self.routes[route_id].type,depart=self.step+1,departSpeed='max',departLane='best')
                count = count+1
                newinjected.append(org_id+'_'+str(vehicle_index+1))
        #print(' '.join(newinjected))
        #print(f'{count} vehicles are regenerated.')
        self.vids = current_vids
        for vid in self.vids:
            org_id = vid.split('_')[0]
            route_id = '.'.join(org_id.split('.')[:2])
            if route_id not in self.routes.keys():
                route = traci.vehicle.getRoute(vid)
                #route = ' '.join(route)
                vtype = traci.vehicle.getTypeID(vid)
                if route not in traci.route.getIDList():
                    traci.route.add(route_id,route)
                self.routes[route_id]=Route(route_id,vtype) #(route name,vechicle type)

    '''
    def get_new_route(self,vehicle_id):
        route = traci.vehicle.getRoute(vehicle_id)
        current_edge = traci.vehicle.getRoadID(vehicle_id)
        remain_route_num = len(route)-traci.vehicle.getRouteIndex(vehicle_id)
        new_route = []
        i = 1
        while i<remain_route_num:
            new_route.append(current_edge)
            to_node = traci.edge.getToJunction(current_edge)
            #print(to_node)
            next_edges = traci.junction.getOutgoingEdges(to_node)
            for edge in next_edges:
                if edge== current_edge or traci.edge.getLastStepMeanSpeed(edge)<0.1:
                    next_edges.remove(edge)
            if next_edges == []:
                return new_route
            current_edge = random.choice(next_edges)
            i = i + 1
            break
        return new_route
    '''


    def prevent_loot_congetsion(self,threshold):
        for vid in self.vids:
            waiting_time = traci.vehicle.getWaitingTime(vid)
            if waiting_time > threshold:
                next = traci.vehicle.getRoute(vid)[traci.vehicle.getRouteIndex(vid)+1]
                if traci.edge.getLastStepMeanSpeed(next) < 0.1:
                    traci.vehicle.remove(vid)
                

    '''
    def object_event_sequence(self,step):
        for vid in self.vids:
            current_speed = traci.vehicle.getSpeed(vid)
            road = traci.vehicle.getRoadID(vid)
            max_speed = self.edges[road].max_speed
            if current_speed < 0.1*max_speed:
                self.eventfile.write(f'{step} vehicle {vid} at {road} drives slowly.\n')
        for edge in self.edges.keys():
            current_speed = traci.edge.getLastStepMeanSpeed(edge)
            if current_speed < 0.1*self.edges[edge].max_speed:
                self.eventfile.write(f'{step} edge {edge} is congested.\n')
    '''
    def closeSUMO(self):
        try:
            traci.close()
        except Exception:
            pass
    
if __name__ == '__main__':
    sumoBinary = "sumo-gui"
    sumoConfig = "manhattan.sumocfg"
    #sumoConfig = '30s.sumocfg'


