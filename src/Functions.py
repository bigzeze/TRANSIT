import os
import xml.dom.minidom
import math
import numpy as np
import random
random.seed(2025)
import logging
from CMDInterface import *

class Edge:
    def __init__(self,id):
        self.id = id
        self.fr = []
        self.to = []
    def addfr(self,fr):
        self.fr.append(fr)
    def addto(self,to):
        self.to.append(to)

def get_crossing_connections(net_file):
    dom = xml.dom.minidom.parse(net_file)
    root = dom.documentElement
    connections = root.getElementsByTagName("connection")

    connections_dic = {}
    for connection in connections:
        fr = connection.getAttribute('from')
        to = connection.getAttribute('to')
        tl = connection.getAttribute('tl')
        if tl == '':
            continue
        if fr == '':
            continue
        if to == '':
            continue
        index = eval(connection.getAttribute('linkIndex'))
        if fr not in connections_dic.keys():
            connections_dic[fr] = [[to,index]]
        else:
            connections_dic[fr].append([to,index])
    return connections_dic

def get_crossing_tllogic(net_file):
    dom = xml.dom.minidom.parse(net_file)
    root = dom.documentElement
    logics = root.getElementsByTagName("tlLogic")
    tllogic = {}
    for logic in logics:
        phases_ls = []
        id = logic.getAttribute('id')
        phases = logic.getElementsByTagName("phase")
        for phase in phases:
            duration = phase.getAttribute('duration')
            state = phase.getAttribute('state')
            phases_ls.append([eval(duration),state])
        tllogic[id] = phases_ls
    return tllogic

def capacity_estimate(netfile,busPerc,theta,tlc):
    if tlc:
        connections = get_crossing_connections(netfile)
        logics = get_crossing_tllogic(netfile)
    total_length_eqv = 0  # equivalent total lane length
    speeds = []
    dom = xml.dom.minidom.parse(netfile)
    root = dom.documentElement
    edges = root.getElementsByTagName("edge")

    for edge in edges:
        id = edge.getAttribute('id')
        fr = edge.getAttribute('from')
        to = edge.getAttribute('to')
        fc = edge.getAttribute('function')
        if fr == '':
            continue
        if fc != '':
            continue
        gp = 1
        if tlc:
            if to in logics.keys():
                logic = logics[to]
                idxs = []
                for key,value in connections.items():
                    if id == key: # connection.from
                        for item in value:
                            idxs.append(item[1])
                green_perc = cal_green_perc(logic,idxs)
                gp = np.mean([x for x in green_perc if x<0.9])
                if np.isnan(gp):
                    gp = 1
        lanes = edge.getElementsByTagName("lane")
        for lane in lanes:
            length = eval(lane.getAttribute("length"))
            if length < 5: # it's not the main roads
                continue
            maxspeed = eval(lane.getAttribute("speed"))
            total_length_eqv = total_length_eqv + length*gp
            speeds.append(maxspeed)
    vehiclelength = 5*(1-theta)+10*theta
    minGap = 2.5
    reaction_time = 1
    max_speed = np.percentile(speeds,[95])[0]
    max_density=1/(vehiclelength+minGap+reaction_time*max_speed)
    total_capacity = max_density*total_length_eqv
    simulation_capacity = theta*total_capacity
    bus_factor = 2
    passenger = round(simulation_capacity*(1-busPerc))
    bus = round(simulation_capacity*busPerc/bus_factor)
    #bus = round(simulation_capacity*busPerc)
    return {'passenger':str(passenger),'bus':str(bus)}

def generate_capacity_dict(netfile,busPerc,alpha,tlc):
    if tlc:
        connections = get_crossing_connections(netfile)
        logics = get_crossing_tllogic(netfile)
    speeds = []

    dom = xml.dom.minidom.parse(netfile)
    root = dom.documentElement
    edges = root.getElementsByTagName("edge")

    capacity_dict = {}
    for edge in edges:
        id = edge.getAttribute('id')
        fr = edge.getAttribute('from')
        to = edge.getAttribute('to')
        fc = edge.getAttribute('function')
        if fr == '':
            continue
        if fc != '':
            continue
        gp = 1
        if tlc:
            if to in logics.keys():
                logic = logics[to]
                idxs = []
                for key,value in connections.items():
                    if id == key: # connection.from
                        for item in value:
                            idxs.append(item[1])
                green_perc = cal_green_perc(logic,idxs)
                gp = np.mean([x for x in green_perc if x<0.9])
                if np.isnan(gp):
                    gp = 1
        lanes = edge.getElementsByTagName("lane")
        total_length_eqv = 0
        for lane in lanes:
            length = eval(lane.getAttribute("length"))
            if length < 5: # it's not the main road
                continue
            maxspeed = eval(lane.getAttribute("speed"))
            total_length_eqv = total_length_eqv + length*gp
            speeds.append(maxspeed)
        vehiclelength = 5*(1-alpha)+10*alpha
        minGap = 2.5
        reaction_time = 1
        max_speed = np.percentile(speeds,[95])[0]
        max_density=1/(vehiclelength+minGap+reaction_time*max_speed)
        total_capacity = max_density*total_length_eqv
        simulation_capacity = alpha*total_capacity
        bus_factor = 2
        passenger = round(simulation_capacity*(1-busPerc))
        bus = round(simulation_capacity*busPerc/bus_factor)
        capacity_dict[id] = [passenger,bus]
    return capacity_dict

def cal_green_perc(logic,idxs):
    cycle = 0
    green = [0]*len(idxs)
    for phase in logic:
        duration = phase[0]
        state = phase[1]
        cycle = cycle + duration
        for n,idx in enumerate(idxs):
            if state[idx] == 'g' or state[idx] == 'G' or state[idx] == 'y':
                green[n] = green[n] + duration
    green_perc = [g/cycle for g in green]
    return green_perc

class Functions:
    def __init__(self):
        self.logger = logging.getLogger('TRANSIT')
        self.verbose = False
    def manhattanRoadGenerator(self,outFile,gridNumber,gridLength,laneNumber,tlc):
        '''
        gridNumber: number of grids in x and y direction
        gridLength: length of each grid
        laneNumber: number of lanes in each edge
        tls: whether to add tls to the network
        '''
        app_path_windows = r"%SUMO_HOME%\bin\netgenerate.exe"
        app_path_linux = r"$SUMO_HOME/bin/netgenerate"
        if os.name == 'nt':
            appPath = app_path_windows
        else:
            appPath = app_path_linux
        grid_option = '-g'
        grid_number_option = '--grid.number'
        grid_length_option = '--grid.length'
        lane_number_option = '-L'
        output_option = '-o'
        junction_option = '-j'
        junction = 'traffic_light'
        tls_option = '--tls.guess'
        tls_configure = 'true'
        tls_join_option = '--tls.group-signals'
        discard_simple_option = '--tls.discard-simple'
        no_turnarounds_option = '--no-turnarounds'
        no_turnarounds_tls_option = '--no-turnarounds.tls'
        no_turnarounds = 'true'
        options = {}
        options[output_option] = outFile
        options[grid_option] = None
        options[grid_number_option] = gridNumber
        options[grid_length_option] = gridLength
        options[lane_number_option] = laneNumber
        options[no_turnarounds_option] = no_turnarounds
        if tlc:
            options[no_turnarounds_tls_option] = no_turnarounds
            options[junction_option] = junction
            options[tls_option] = tls_configure
            options[tls_join_option] = tls_configure
            options[discard_simple_option] = tls_configure

        self.logger.info('{0:-^50}'.format('Network Build'))
        interface = CMDInterface(appPath,options)
        interface.setVerbose(self.verbose)
        result = interface.run()
        if result == 0:
            self.logger.info('Network build success, file path: ' + outFile)
        else:
            self.logger.error('Network build failed!')
        self.logger.info('{0:-^50}'.format(''))

    def DetectorGenerator(self,netfile,savefile,freq,threshold,spacing):
        '''
        netfile: network file path
        freq: frequency of the detector
        threshold: minimum length of the road
        spacing: spacing between detectors
        '''
        detector_out = 'detectors.out.xml'
        self.logger.info('{0:-^50}'.format('Detector Build'))
        dom = xml.dom.minidom.parse(netfile)
        root = dom.documentElement
        edges = root.getElementsByTagName("edge")

        newdom = xml.dom.minidom.Document()
        newroot = newdom.createElement('additional')
        newdom.appendChild(newroot)

        for edge in edges:
            fr = edge.getAttribute('from')
            fc = edge.getAttribute('function')
            if fr == '':
                continue
            if fc != '':
                continue
            lanes = edge.getElementsByTagName("lane")
            for lane in lanes:
                id = lane.getAttribute("id")
                length = eval(lane.getAttribute("length"))

                if length < threshold:
                    continue
                number = int(length // spacing)
                if number == 0 or number == 1:
                    newdet = dom.createElement('inductionLoop')
                    newdet.setAttribute('id',lane.getAttribute('id')+'_'+str(0))
                    newdet.setAttribute('lane',id)
                    newdet.setAttribute('pos',str(length/2))
                    newdet.setAttribute('file',detector_out)
                    newdet.setAttribute('freq',str(freq))
                    newroot.appendChild(newdet)
                else:
                    remain = length % spacing + spacing
                    for i in range(1,number+1):
                        pos = remain/2 + spacing*i
                        newdet = dom.createElement('inductionLoop')
                        newdet.setAttribute('id',lane.getAttribute('id')+'_'+str(i))
                        newdet.setAttribute('lane',id)
                        newdet.setAttribute('pos',str(math.floor(pos)))
                        newdet.setAttribute('file',detector_out)
                        newdet.setAttribute('freq',str(freq))
                        newroot.appendChild(newdet)
        
        with open(savefile, "w", encoding="utf-8") as f:
            newdom.writexml(f, indent='', addindent='\t', newl='\n', encoding="utf-8")
        self.logger.info('Detectors built success, file path: '+savefile)
        self.logger.info('{0:-^50}'.format(''))

    def streetFlowGenerator(self,net_file,output_path,busPerc,theta,tlc):
        '''
        net_file: network file path
        output_path: output file path
        busPerc: percentage of bus
        theta: percentage of inital flow to capacity
        tlc: whether to add tls to the network
        '''
        app_path_windows = r"python %SUMO_HOME%\tools\randomTrips.py"
        app_path_linux = r"python $SUMO_HOME/tools/randomTrips.py"
        if os.name == 'nt':
            appPath = app_path_windows
        else:
            appPath = app_path_linux
        vtype_flows = capacity_estimate(net_file,busPerc,theta,tlc)

        net_option = '-n'
        output_option = '-o'
        begin_option = '--begin'
        end_option = '--end'
        flow_option = '--flows'
        router_option = '--jtrrouter'
        attribute_option = '--trip-attributes'
        vehicle_option = '--vehicle-class'
        begin = '0'
        end = '1'
        attribute = '\"departPos=\'random\' departSpeed=\'max\'\"'
        self.logger.info('{0:-^50}'.format('Flows Generate'))
        output_files = []
        def flow_post_treat(vtype,file):
            file_data = []
            with open(file) as f:
                lines = f.readlines()
                for line in lines:
                    line = line.replace('flow id="','flow id="'+vtype+'.')
                    file_data.append(line)
            with open(file,'w') as f:
                f.writelines(file_data)
        
        for vtype,flow in vtype_flows.items():
            output_file = output_path + '/' + vtype+'.flow.xml'
            output_files.append(output_file)
            options = {}
            options[net_option] = net_file
            options[output_option] = output_file
            options[begin_option] = begin
            options[end_option] = end
            options[vehicle_option] = vtype
            options[flow_option] = flow
            options[router_option] = None
            options[attribute_option] = attribute
            self.logger.info('generating '+ vtype + ' flows......')
            interface = CMDInterface(appPath,options)
            interface.setVerbose(self.verbose)
            result = interface.run()
            if result != 0:
                self.logger.error('Flows generate failed!')
                return
            
            flow_post_treat(vtype,output_file)

        self.logger.info('Flows generate Successful, file paths: '+ ', '.join(output_files))
        self.logger.info('{0:-^50}'.format(''))
    
    def streetRouteGenerator(self,net_file,flowfile_path,output_file):
        app_path_windows = r"%SUMO_HOME%\bin\jtrrouter.exe"
        app_path_linux = r"$SUMO_HOME/bin/jtrrouter"
        if os.name == 'nt':
            appPath = app_path_windows
        else:
            appPath = app_path_linux
        net_option = '-n'
        route_option = '-r'
        output_option = '-o'
        turn_option = '--turn-defaults'
        destination_option = '--accept-all-destinations' # accept-all-destinations
        loop_option = '--allow-loops'
        turn_chance = "25,50,25"
        named_routes_option = '--named-routes'
        named_routes = 'true'
        
        options = {}
        options[net_option] = net_file
        options[route_option] = flowfile_path
        options[output_option] = output_file
        options[turn_option] = turn_chance
        options[destination_option] = None
        options[loop_option] = None
        options[named_routes_option] = named_routes
        self.logger.info('{0:-^50}'.format('Routes generate'))
        interface = CMDInterface(appPath,options)
        interface.setVerbose(self.verbose)
        result = interface.run()
        
        if result == 0:
            self.logger.info('Routes generate success, file path: '+output_file)
        else:
            self.logger.error('Routes generated failed!')
        self.logger.info('{0:-^50}'.format(''))

    def realWorldRoadGenerator(self,inFile,outFile):
        app_path_windows = r"%SUMO_HOME%\bin\netconvert.exe"
        app_path_linux = r"$SUMO_HOME/bin/netconvert"
        if os.name == 'nt':
            appPath = app_path_windows
        else:
            appPath = app_path_linux
        osm_option = '--osm'
        output_option = '-o'
        extend_edge_option = '--plain.extend-edge-shape'
        extend_edge = 'true'
        numeric_ids_option = '--numerical-ids'
        dismis_vclass_option = '--dismiss-vclasses'
        tls_guess_option = '--tls.guess'
        tls_guess_signals_option = '--tls.guess-signals'
        keep_edge_option = '--keep-edges.by-type'
        keep_edge = "highway.motorway,highway.trunk,highway.primary,highway.secondary,highway.tertiary,highway.residential,highway.motorway_link"
        junction_keepclear_option = '--default.junctions.keep-clear'
        junction_keepclear = 'true'
        no_turnarounds_option = '--no-turnarounds'
        no_turnarounds = 'true'
        no_turnarounds_exceptdeadend_option = '--no-turnarounds.except-deadend'
        no_turnarounds_exceptturnlane_option = '--no-turnarounds.except-turnlane'
        joinjunction_option = '--junctions.join'
        joinjunction = 'true'
        joinjunction_dist_option = '--junctions.join-dist'
        joinjunction_dist = '30'
        joinjunction_same = '--junctions.join-same'
        options = {}
        options[osm_option] = inFile
        options[output_option] = outFile
        options[extend_edge_option] = extend_edge
        options[numeric_ids_option] = None
        options[dismis_vclass_option] = None
        options[tls_guess_option] = None
        options[tls_guess_signals_option] = None
        options[keep_edge_option] = keep_edge
        options[junction_keepclear_option] = junction_keepclear
        options[no_turnarounds_option] = no_turnarounds
        options[no_turnarounds_exceptdeadend_option] = no_turnarounds
        options[no_turnarounds_exceptturnlane_option] =no_turnarounds
        options[joinjunction_option] = joinjunction
        options[joinjunction_dist_option] = joinjunction_dist
        options[joinjunction_same] = joinjunction
        self.logger.info('{0:-^50}'.format('Network Build'))
        interface = CMDInterface(appPath,options)
        interface.setVerbose(self.verbose)
        result = interface.run()
        if result == 0:
            self.logger.info('Network build Success, file path: ' + outFile)
        else:
            self.logger.error('Network build failed!')
        self.logger.info('{0:-^50}'.format(''))
        # unfinished: remove deadend edges

    '''
    def realWorldDetectorGenerator(self,netfile,savefile,detector_out,freq,verbose):
        if verbose:
            print('{0:-^50}'.format('Detector building'))
        dom = xml.dom.minidom.parse(netfile)
        root = dom.documentElement
        edges = root.getElementsByTagName("edge")

        newdom = xml.dom.minidom.Document()
        newroot = newdom.createElement('additional')
        newdom.appendChild(newroot)
        for edge in edges:
            fr = edge.getAttribute('from')
            fc = edge.getAttribute('function')
            ty = edge.getAttribute('type')
            if fr == '':
                continue
            if fc != '' or fc == 'internal':
                continue
            if ty == 'highway.residential':
                continue
            lanes = edge.getElementsByTagName("lane")
            for lane in lanes:
                id = lane.getAttribute("id")
                length = eval(lane.getAttribute("length"))
                # if length < 50:
                #     continue
                # #if length < 200:
                # else:
                newdet = dom.createElement('inductionLoop')
                newdet.setAttribute('id',lane.getAttribute('id')+'_0')
                newdet.setAttribute('lane',id)
                newdet.setAttribute('pos',str(math.floor(length/2)))
                newdet.setAttribute('file',detector_out)
                newdet.setAttribute('freq',str(freq))
                newroot.appendChild(newdet)
                # else:
                #     number = int(length // 100)
                #     interval = length/(number+1)
                #     for i in range(number):
                #         pos = interval*(i+1)
                #         newdet = dom.createElement('inductionLoop')
                #         newdet.setAttribute('id',lane.getAttribute('id')+'_'+str(i))
                #         newdet.setAttribute('lane',id)
                #         newdet.setAttribute('pos',str(math.floor(pos)))
                #         newdet.setAttribute('file',detector_out)
                #         newdet.setAttribute('freq',str(freq))
                #         newroot.appendChild(newdet)
    with open(savefile, "w", encoding="utf-8") as f:
        newdom.writexml(f, indent='', addindent='\t', newl='\n', encoding="utf-8")
    if verbose:
        print('Detectors built Successful, file path: '+savefile)
        print('{0:-^50}'.format(''))
    '''

    def expresswayFlowGenerator(self,netfile,flow_file,endtime,busPerc,theta):
        dom = xml.dom.minidom.parse(netfile)
        root = dom.documentElement
        connections = root.getElementsByTagName("connection")

        connections_dic = {}
        for connection in connections:
            fr = connection.getAttribute('from')
            to = connection.getAttribute('to')
            if fr == '' or fr[0]==':':
                continue
            if to == '' or to[0]==':':
                continue

            if fr not in connections_dic.keys():
                connections_dic[fr] = Edge(fr)
            if to not in connections_dic.keys():
                connections_dic[to] = Edge(to)
            connections_dic[fr].addto(to)
            connections_dic[to].addfr(fr)

        edges = root.getElementsByTagName("edge")

        edgeids = []
        lanenumbers = {}
        edgetypes = {}
        for edge in edges:
            fr = edge.getAttribute('from')
            fc = edge.getAttribute('function')
            if fr == '':
                continue
            if fc != '':
                continue
            lanenumber = len(edge.getElementsByTagName("lane"))
            edgetypes[edge.getAttribute('id')] = edge.getAttribute('type')
            edgeids.append(edge.getAttribute('id'))
            lanenumbers[edge.getAttribute('id')] = lanenumber
        
        beginings = []
        for edgeid in edgeids:
            if edgeid not in connections_dic.keys():
                continue
            if connections_dic[edgeid].fr == []:
                beginings.append(edgeid)
        
        totoal_capacity = capacity_estimate(netfile,busPerc,theta,False)
        capacity_dict = generate_capacity_dict(netfile,busPerc,theta,False)
        flows = []
        edgelist = list(connections_dic.keys())
        def dfs(path,visit):
            #print(path)
            current = path[-1]
            if visit[current]:
                return
            visit[current] = True
            if current not in connections_dic.keys() or not connections_dic[path[-1]].to:
                flows.append(path.copy())
                return
            for nextedge in connections_dic[current].to:
                path.append(nextedge)
                dfs(path,visit)
                path.pop()
            return
        
        for begining in beginings:
            path = [begining]
            visit = {}
            for edge in edgelist:
                visit[edge] = False
            #print('beginning',begining)
            dfs(path,visit)
        #print(flows)

        # wrong try
        # calculate min lane for each path
        # path_minlane = [] 
        # for path in flows:
        #     minlane = lanenumbers[path[0]]
        #     for edge in path:
        #         minlane = min(minlane,lanenumbers[edge])
        #     path_minlane.append(minlane)
        # print(path_minlane)

        path_reduce_factors = []
        for path in flows:
            reduce_factor = 1
            for edge in path:
                if edgetypes[edge] == 'highway.motorway_link':
                    reduce_factor = reduce_factor * 0.5
            path_reduce_factors.append(reduce_factor)
        # 基于累加
        # collection = {}
        # for idx,path in enumerate(flows):
        #     for edge in path:
        #         if edge not in collection:
        #             collection[edge] = path_minlane[idx]/lanenumbers[path[0]]
        #         else:
        #             collection[edge] = collection[edge] + path_minlane[idx]
        for i in zip(flows,path_reduce_factors):
            print(i)
        capacitys = []
        for idx,path in enumerate(flows):
            pathc = []
            for edge in path:
                pathc.append([i*path_reduce_factors[idx] for i in capacity_dict[edge]])
            capacitys.append(pathc)
        final_capacitys = []
        unfixed_capacity = [[],[]]
        for idx,path in enumerate(flows):
            cap = [sum([i[0] for i in capacitys[idx]]),sum([i[1] for i in capacitys[idx]])]
            final_capacitys.append([path,cap])
            unfixed_capacity[0].append(cap[0])
            unfixed_capacity[1].append(cap[1])
        unfixed_capacity = [sum(unfixed_capacity[0]),sum(unfixed_capacity[1])]
        for cap_pair in final_capacitys:
            cap_pair[1][0] = round(cap_pair[1][0]/unfixed_capacity[0]*eval(totoal_capacity['passenger']))
            cap_pair[1][1] = round(cap_pair[1][1]/unfixed_capacity[1]*eval(totoal_capacity['bus']))
            cap_pair[1][0] = round(cap_pair[1][0])
            cap_pair[1][1] = round(cap_pair[1][1])
        
        def writeroute():
            doc = xml.dom.minidom.Document()
            root = doc.createElement('additional')
            doc.appendChild(root)
            vtype = doc.createElement('vType')
            vtype.setAttribute('id','passenger')
            vtype.setAttribute('vClass','passenger')
            root.appendChild(vtype)
            vtype = doc.createElement('vType')
            vtype.setAttribute('id','bus')
            vtype.setAttribute('vClass','bus')
            root.appendChild(vtype)
            i = 1
            cap_name = ['passenger','bus']
            for path,cap_pair in final_capacitys:
                for idx,cap in enumerate(cap_pair):
                    id = cap_name[idx]+'.'+str(i)
                    flow = doc.createElement('flow')
                    flow.setAttribute('id',id)
                    flow.setAttribute('departSpeed','max')
                    flow.setAttribute('departLane','best')
                    flow.setAttribute('number',str(cap))
                    flow.setAttribute('type',cap_name[idx])
                    flow.setAttribute('begin','0')
                    flow.setAttribute('end',str(1))

                    route = doc.createElement('route')
                    route.setAttribute('id',id)
                    route.setAttribute('edges',' '.join(path))
                    flow.appendChild(route)
                    root.appendChild(flow)
                i = i + 1
            with open(flow_file, "w", encoding="utf-8") as f:
                doc.writexml(f, indent='', addindent='\t', newl='\n', encoding="utf-8")
        writeroute()








    





'''
def randomEdge(netfile):
    dom = xml.dom.minidom.parse(netfile)
    root = dom.documentElement
    edges = root.getElementsByTagName("edge")

    edgeids = []
    for edge in edges:
        fr = edge.getAttribute('from')
        fc = edge.getAttribute('function')
        if fr == '':
            continue
        if fc != '':
            continue
        edgeids.append(edge.getAtrribute('id'))
    random.seed(0)
    selected = random.choice(edgeids)
    return randomEdge

def get_speed_limit(net_file,edge_id):
    dom = xml.dom.minidom.parse(net_file)
    root = dom.documentElement
    edges = root.getElementsByTagName("edge")
    speeds = []
    for edge in edges:
        id = edge.getAttribute('id')
        fr = edge.getAttribute('from')
        to = edge.getAttribute('to')
        fc = edge.getAttribute('function')
        if fr == '':
            continue
        if fc != '':
            continue
        if edge_id == id:
            lanes = edge.getElementsByTagName("lane")
            for lane in lanes:
                length = eval(lane.getAttribute("length"))
                if length < 20: # it's not the main roads
                    continue
                maxspeed = eval(lane.getAttribute("speed"))
                speeds.append(maxspeed)
    return np.mean(speeds)

def get_max_speed(net_file):
    dom = xml.dom.minidom.parse(net_file)
    root = dom.documentElement
    edges = root.getElementsByTagName("edge")
    speeds = []
    for edge in edges:
        id = edge.getAttribute('id')
        fr = edge.getAttribute('from')
        to = edge.getAttribute('to')
        fc = edge.getAttribute('function')
        if fr == '':
            continue
        if fc != '':
            continue
        green_perc = 1
        lanes = edge.getElementsByTagName("lane")
        for lane in lanes:
            length = eval(lane.getAttribute("length"))
            if length < 20: # it's not the main roads
                continue
            maxspeed = eval(lane.getAttribute("speed"))
            speeds.append(maxspeed)
    max_speed = np.percentile(speeds,[95])[0]
    return max_speed

'''