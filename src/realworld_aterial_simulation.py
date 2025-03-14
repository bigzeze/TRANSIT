from bin.functions import *
import glob
from simulation import SUMOInterface
from TrafficEvent import SpeedLimit,TLFailure
from xml2csv import xml2csv
from csv2dataset import csv2dataset
from congestion_analysis import congestion_analysis
import os

# simulation scenario
current = os.path.dirname(os.path.abspath(__file__)) + '/'
models = current + '../models/'
outputs = current + '../datasets/'
sce_name = 'realarterials_RSL' # RSL: Road Speed Limitation
sce_model = models + sce_name + '/'
sce_output = outputs + sce_name + '/'
#path = current + 'manhattan_TSC' # TSC: Traffic Light Control
#path = current+'realworld_TLS/'
#path = current+'realworld_TLS/'
if not os.path.exists(sce_model):
    os.mkdir(sce_model)
if not os.path.exists(sce_output):
    os.mkdir(sce_output)


# 1
#realWorldRoadGenerator(current+'/../inputs/arterials.osm',sce_model+'roads.net.xml',verbose=True)
realWorldDetectorGenerator(sce_model+'roads.net.xml',sce_model+'detectors.add.xml','detectors.out.xml',60,verbose=True)


# 2
busPerc = 0.2
alpha = 0.6
generate_flows(sce_model+'roads.net.xml',sce_model,busPerc,alpha,True,verbose=True)


flow_files = ','.join(glob.glob(sce_model+'*.flow.xml'))

# 3
generate_routes(sce_model+'roads.net.xml',flow_files,sce_model+'routes.routes.xml',verbose=True)


sumoBinary = "sumo-gui"
netout_file = sce_model + 'net.out.xml'
statistic_file = sce_model + 'statistic.out.xml'
tripinfo_file = sce_model +'tripinfo.out.xml'
# 4
theta = 0.05
rsl_target = '1305344366'
speed = get_speed_limit(sce_model+'roads.net.xml',rsl_target)
new_speed_limit = theta*speed

interface = SUMOInterface(sumoBinary,sce_model+'roads.net.xml',sce_model+'routes.routes.xml',statistic_file,tripinfo_file,verbose=True,additional_file=sce_model+'detectors.add.xml',netoutput_file=sce_model+'vehicles.out.xml')

interface.closeSUMO()
interface.startSUMO()
interface.simulation(0,10800,[SpeedLimit(3600,7200,{rsl_target:new_speed_limit})])
#interface.simulation(0,7200,[TLFailure(1800,5400,['C2'])])
#interface.simulation(0,7200,[EdgeSlow(1800,5400,{'1204342548':0.7})])
#interface.simulation(0,7200,[TLFailure(1800,5400,['cluster_42464941_9820781126_9820781127_9820781128_#1more'])])

interface.closeSUMO()

# 5
xml2csv(sce_model+'detectors.out.xml',sce_output+'detectors.csv',True)
xml2csv(sce_model+'vehicles.out.xml',sce_output+'vehicles.csv',True)

# 6
csv2dataset(sce_output+'detectors.csv',get_max_speed(sce_model+'roads.net.xml'),True)

# 7
beta = congestion_analysis(sce_name,sce_output+'detectors.npy',sce_output+'nodes.npy',sce_model+'roads.net.xml')
print('beta:',beta)
