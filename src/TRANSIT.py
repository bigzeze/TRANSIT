import argparse
import os
import logging
import glob
from Functions import *
from Simulation import SUMOInterface
from TrafficEvent import *
from xml2csv import xml2csv
from csv2dataset import csv2dataset
from csv2text import csv2text
from multiprocessing import Pool,cpu_count

class TRANSIT(Functions):
    def __init__(self):
        super().__init__()

        # basic configurations
        self.mode = None
        self.sce = None
        self.runs = None
        self.rebuild = None
        self.simulationTime = None
        self.busPerc = None
        self.theta = None
        self.detectorFrequency = None
        self.detectorThreshold = None
        self.detectorSpacing = None
        self.gridNumber = None
        self.gridLength = None
        self.gridLanes = None
        self.networkFile = None

        # anomaly configurations
        self.anomaly = None
        self.anomalyStart = None
        self.anomalyEnd = None
        self.anomalyPos = None
        self.anomalySeverity = None

        # runtime files
        self.roadFile = None
        self.detctorFile = None
        self.routeFile = None
        self.flowFiles = []

        # output files
        self.detctorOutFile = None
        self.statisticsFile = None
        self.tripinfoFile = None
        self.trajectoryOutput = None
        self.trajectoryFile = None
        self.detectorCSVFile = None
        self.trajectoryCSVFile = None
        self.eventThreshold = None

    def parse_args(self):  # command line mode
        self.parser = argparse.ArgumentParser()
        # overall simulation config
        self.parser.add_argument('-m','--mode', type=str, default = 'generate') # mode: test, generate
        self.parser.add_argument('-s','--scenario', type=str) # scenario: theoretical_streets, real_world_streets, real_world_expressways

        self.parser.add_argument('-r','--runs', type=int) # runs:  simulation runs if the mode is generate
        self.mode = self.parser.parse_args().mode
        self.sce = self.parser.parse_args().scenario

        self.runs = self.parser.parse_args().runs

        self.parser.add_argument('-t','--time', type=int) # time: simulation time
        self.simulationTime = self.parser.parse_args().time

        self.parser.rebuild = self.parser.parse_args().rebuild # rebuild: whether to rebuildure the network
        self.rebuild = self.parser.parse_args().rebuild

        # anomaly config
        self.parser.add_argument('-a','--anomaly', type=str) # anomaly: abrupt_flow, speed_limit, traffic_light_failure
        self.parser.add_argument('--anomalyStart', type=int) # anomalyStart: start time of the anomaly
        self.parser.add_argument('--anomalyEnd', type=int) # anomalyEnd: end time of the anomaly
        self.parser.add_argument('--anomalyPos', type=str) # anomalyPos: position of the anomaly
        self.parser.add_argument('--anomalySeverity', type=float) # anomalySeverity: severity of the anomaly
        self.anomaly = self.parser.parse_args().anomaly
        self.anomalyStart = self.parser.parse_args().anomalyStart
        self.anomalyEnd = self.parser.parse_args().anomalyEnd
        self.anomalyPos = self.parser.parse_args().anomalyPos
        self.anomalySeverity = self.parser.parse_args().anomalySeverity
        
        # overall flow config
        self.parser.add_argument('--busPerc', type=float) # busPerc: percentage of bus flows
        self.parser.add_argument('--theta', type=float) # theta: ratio of the initial flow to capacity
        self.busPerc = self.parser.parse_args().busPerc
        self.theta = self.parser.parse_args().theta

        # detector config
        self.parser.add_argument('--detectorFrequency', type=int) # detectorFrequency: frequency of detectors
        self.parser.add_argument('--detectorThreshold', type=float) # detectorThreshold: raod length threshold for setting detectors 
        self.parser.add_argument('--detectorSpacing', type=float) # detectorSpacing: spacing between detectors
        self.detectorFrequency = self.parser.parse_args().detectorFrequency
        self.detectorThreshold = self.parser.parse_args().detectorThreshold
        self.detectorSpacing = self.parser.parse_args().detectorSpacing

        # for MMM
        self.parser.add_argument('--gridNumber', type=int, default=5) # gridNumber: number of grids in the grid network
        self.parser.add_argument('--gridLength', type=int, default=200) # gridLength: length of each grid in the grid network
        self.parser.add_argument('--gridLanes', type=int, default=1) # gridLanes: number of lanes in each grid
        self.gridNumber = self.parser.parse_args().gridNumber
        self.gridLength = self.parser.parse_args().gridLength
        self.gridLanes = self.parser.parse_args().gridLanes

        # for realworld
        self.parser.add_argument('--networkFile', type=str) # networkFile: network file for real world scenarios
        self.networkFile = self.parser.parse_args().networkFile

        # output config
        self.parser.add_argument('--trajectoryOutput', type=bool, default=False)
        self.trajectoryOutput = self.parser.parse_args().trajectoryOutput
        self.parser.add_argument('--eventThreshold', type=int, default=0.5)
        self.evetThreshold = self.parser.parse_args().eventThreshold

    def set_args(self,**kwargs):  # run.py mode
        '''
        set the arguments manually
        mode: test, generate
        scenario: theoretical_streets, real_world_streets, real_world_expressways
        anomaly: abrupt_flow, speed_limit, traffic_light_failure
        runs: simulation runs if the mode is generate
        time: simulation time
        busPerc: percentage of bus flows
        theta: ratio of the initial flow to capacity
        detectorFrequency: frequency of detectors
        detectorThreshold: road length threshold for setting detectors
        detectorSpacing: spacing between detectors
        gridNumber: number of grids in the grid network
        gridLength: length of each grid in the grid network
        gridLanes: number of lanes in each grid
        '''
        self.mode = kwargs.get('mode',self.mode)
        self.sce = kwargs.get('scenario',self.sce)
        self.anomaly = kwargs.get('anomaly',self.anomaly)
        self.anomalyStart = kwargs.get('anomalyStart',self.anomalyStart)
        self.anomalyEnd = kwargs.get('anomalyEnd',self.anomalyEnd)
        self.anomalyPos = kwargs.get('anomalyPos',self.anomalyPos)
        self.anomalySeverity = kwargs.get('anomalySeverity',self.anomalySeverity)
        self.runs = kwargs.get('runs',self.runs)
        self.simulationTime = kwargs.get('time',self.simulationTime)
        self.rebuild = kwargs.get('rebuild',self.rebuild)
        self.busPerc = kwargs.get('busPerc',self.busPerc)
        self.theta = kwargs.get('theta',self.theta)
        self.detectorFrequency = kwargs.get('detectorFrequency',self.detectorFrequency)
        self.detectorThreshold = kwargs.get('detectorThreshold',self.detectorThreshold)
        self.detectorSpacing = kwargs.get('detectorSpacing',self.detectorSpacing)
        self.gridNumber = kwargs.get('gridNumber',self.gridNumber)
        self.gridLength = kwargs.get('gridLength',self.gridLength)
        self.gridLanes = kwargs.get('gridLanes',self.gridLanes)
        self.trajectoryOutput = kwargs.get('trajectoryOutput',self.trajectoryOutput)
        self.eventThreshold = kwargs.get('eventThreshold',self.eventThreshold)
        self.networkFile = kwargs.get('networkFile',self.networkFile)
    def check_paths(self):
        self.path = os.path.dirname(os.path.abspath(__file__)) + '/'
        models = self.path + '../models/'
        outputs = self.path + '../datasets/'
        inputs = self.path + '../inputs/'
        if not os.path.exists(models+self.sce + '/'):
            os.mkdir(models+self.sce + '/')
        if not os.path.exists(outputs+self.sce + '/'):
            os.mkdir(outputs+self.sce + '/')
        if not os.path.exists(inputs):
            os.mkdir(inputs)
        self.sce_model = models + self.sce + '/' # + self.anomaly +'/'
        self.sce_output = outputs + self.sce + '/' + self.anomaly + '/'
        self.inputPath = inputs + '/'
        if not os.path.exists(self.sce_model):
            os.mkdir(self.sce_model)
        if not os.path.exists(self.sce_output):
            os.mkdir(self.sce_output)

    def set_verbose(self):
        if self.mode == 'test':
            self.verbose = True
            logging.basicConfig(level=logging.INFO)
        if self.mode == 'generate':
            self.verbose = False
            logging.basicConfig(level=logging.ERROR)

    def packingAnomaly(self):
        if self.anomaly == 'abrupt_flow':
            self.anomalyPack = [AbruptFlow(self.sumoInterface,self.anomalyStart,self.anomalyEnd,self.anomalyPos,self.anomalySeverity)]
        elif self.anomaly == 'speed_limit':
            self.anomalyPack = [SpeedLimit(self.sumoInterface,self.anomalyStart,self.anomalyEnd,self.anomalyPos,self.anomalySeverity)]
        elif self.anomaly == 'traffic_light_failure':
            self.anomalyPack = [TLFailure(self.sumoInterface,self.anomalyStart,self.anomalyEnd,self.anomalyPos,self.anomalySeverity)]
        # multi-anoomalies can be supported by adding more anomaly in anomalyPack
    
    def apply_simulation(self):
        self.set_verbose()
        self.setFilePath()
        self.buildScenario()
        if self.mode == 'test':
            self.one_process_execute()
        if self.mode == 'generate':
            reserved_cpus = 2
            for run in range(self.runs):
                with Pool(processes=min(30,cpu_count()-reserved_cpus)) as p:
                    rtns = []
                    for rtn in p.starmap(self.one_process_execute,run):
                        rtns.append(rtn)
    
    def setFilePath(self):
        # input files
        if self.sce == 'real_world_streets' or self.sce == 'real_world_expressways' or self.sce == 'parallel':
            self.networkInput = self.inputPath + self.networkFile
        # mid files
        self.roadFile = self.sce_model + 'road.net.xml'
        self.routeFile = self.sce_model + 'routes.routes.xml'
        # test mode
        if self.mode == 'test':
            self.detctorFile = self.sce_model + 'detectors.add.xml'
            self.detctorOutFile = self.sce_model + 'detectors.out.xml'
        # generate mode
        if self.mode == 'generate':
            self.detectorFIle = [self.sce_model + 'detectors' + idx +'.add.xml' for idx in range(self.runs)]
            self.detctorOutFile = [self.sce_model + 'detectors'+ idx +'.out.xml' for idx in range(self.runs)]
            
    def buildScenario(self):
        if self.sce == 'theoretical_streets':
            if not self.gridLength or not self.gridNumber:
                logging.error('Please specify the grid length and number for the MMM model.')
                return
            if self.rebuild:
                self.generate_MMM_configuartion()
            self.flowFiles = ','.join(glob.glob(self.sce_model+'*.flow.xml'))
        if self.sce == 'real_world_streets':
            if not self.networkFile:
                logging.error('Please specify the network file for the real world scenario.')
                return
            if self.rebuild:
                self.generate_realworld_configuartion()
        if self.sce == 'real_world_expressways' or self.sce == 'parallel':
            if not self.networkFile:
                logging.error('Please specify the network file for the real world scenario.')
                return
            if self.rebuild:
                self.generate_expressway_configureration()

    def one_process_execute(self,idx=None):
        self.sumo_execution()
        self.data_processing()

    
    def generate_MMM_configuartion(self):
        self.manhattanRoadGenerator(self.roadFile,self.gridNumber,self.gridLength,self.gridLanes,True)
        if self.mode == 'test':
            self.DetectorGenerator(self.roadFile,self.detctorFile,self.detctorOutFile,self.detectorFrequency,self.detectorThreshold,self.detectorSpacing)
        if self.mode == 'generate':
            for idx in range(self.runs):
                self.DetectorGenerator(self.roadFile,self.detectorFIle[idx],self.detctorOutFile,self.detectorFrequency,self.detectorThreshold,self.detectorSpacing)
        self.streetFlowGenerator(self.roadFile,self.sce_model,self.busPerc,self.theta,True)
        self.flowFiles = ','.join(glob.glob(self.sce_model+'*.flow.xml'))
        self.streetRouteGenerator(self.roadFile,self.flowFiles,self.sce_model+'routes.routes.xml')

    def generate_realworld_configuartion(self):
        self.realWorldRoadGenerator(self.networkInput,self.roadFile)
        self.DetectorGenerator(self.roadFile,self.detctorFile,self.detectorFrequency,self.detectorThreshold,self.detectorSpacing)
        self.streetFlowGenerator(self.roadFile,self.sce_model,self.busPerc,self.theta,True)
        self.flowFiles = ','.join(glob.glob(self.sce_model+'*.flow.xml'))
        self.streetRouteGenerator(self.roadFile,self.flowFiles,self.sce_model+'routes.routes.xml')
    
    def generate_expressway_configureration(self):
        self.realWorldRoadGenerator(self.networkInput,self.roadFile)
        self.DetectorGenerator(self.roadFile,self.detctorFile,self.detectorFrequency,self.detectorThreshold,self.detectorSpacing)
        self.expresswayFlowGenerator(self.roadFile,self.routeFile,3000,self.busPerc,self.theta)

    def sumo_execution(self):
        if os.name == 'nt':
            sumoBinary = "sumo-gui"
        else:
            sumoBinary = "sumo"
        self.statisticsFile = self.sce_output + 'statistics.out.xml'
        self.tripInfoFile = self.sce_output + 'tripinfo.out.xml'
        self.trajectoryFile = self.sce_output + 'trajectory.out.xml'
        self.eventSequenceFile = self.sce_output + 'events.txt'
        self.prevent_loot = False
        if self.sce == 'theoretical_streets' or self.sce == 'real_world_streets':
            self.prevent_loot = True
        if not self.trajectoryOutput:
            self.sumoInterface = SUMOInterface(sumoBinary,self.roadFile,self.routeFile,self.statisticsFile,self.tripInfoFile,prevent_loot=self.prevent_loot,verbose=self.verbose,additional_file=self.detctorFile)
        else:
            self.sumoInterface = SUMOInterface(sumoBinary,self.roadFile,self.routeFile,self.statisticsFile,self.tripInfoFile,prevent_loot=self.prevent_loot,verbose=self.verbose,additional_file=self.detctorFile,netoutput_file=self.trajectoryFile)
        self.packingAnomaly()
        # for manually setted multianomalies
        # self.anomalyPack = [SpeedLimit(self.sumoInterface,3000,6000,'C2D2',0.1),\
        #                     TLFailure(self.sumoInterface,9000,12000,'C2',0.2),
        #                     SpeedLimit(self.sumoInterface,15000,18000,'A3A4',0.1),\
        #                     TLFailure(self.sumoInterface,18000,21000,'B2',0.2)
        #                     ]
        self.sumoInterface.closeSUMO()
        self.sumoInterface.startSUMO()
        self.sumoInterface.open_event_file(self.eventSequenceFile)
        self.sumoInterface.simulation(0,self.simulationTime,self.anomalyPack)
        self.sumoInterface.closeSUMO()
        self.sumoInterface.close_event_file()

    def data_processing(self):
        self.detectorCSVFile = self.sce_output+'detectors.csv'
        self.trajectoryCSVFile = self.sce_output+'trajectory.csv'
        self.eventSequenceFile = self.sce_output+'events.txt'
        self.detectorNameFile = self.sce_output+'nodes.npy'
        self.detectorDataFile = self.sce_output+'detectors.npy'
        xml2csv(self.detctorOutFile,self.detectorCSVFile)
        csv2dataset(self.detectorCSVFile,self.roadFile)
        if self.trajectoryOutput:
            xml2csv(self.trajectoryFile,self.trajectoryCSVFile)
            csv2text(self.detectorNameFile,self.detectorDataFile,self.trajectoryCSVFile,self.eventSequenceFile,self.roadFile,self.eventThreshold)

if __name__ == '__main__':
    app = TRANSIT()
    #app.parse_args()
    '''
    theoretical_streets_abrupt_flow:
    configure = {'mode':'test',
                'scenario':'theoretical_streets',
                'time':12000,
                'rebuild':False,
                'anomaly':'speed_limit',
                'anomalyStart':3000,
                'anomalyEnd':9000,
                'anomalyPos':'C2D2',
                'anomalySeverity':0.2,
                'busPerc':0.2,
                'theta':0.6,
                'detectorFrequency':60,
                'detectorThreshold':20,
                'detectorSpacing':200,
                'gridNumber':5,
                'gridLength':200,
                'gridLanes':1,
                'trajectoryOutput':True,
                'eventThreshold':0.5,
    }
    '''
    '''
    theoretical_streets_speed_limit':
    configure = {'mode':'test',
                'scenario':'theoretical_streets',
                'time':12000,
                'rebuild':True,
                'anomaly':'speed_limit',
                'anomalyStart':3000,
                'anomalyEnd':9000,
                'anomalyPos':'C2D2',
                'anomalySeverity':0.2,
                'busPerc':0.2,
                'theta':0.6,
                'detectorFrequency':60,
                'detectorThreshold':20,
                'detectorSpacing':200,
                'gridNumber':5,
                'gridLength':200,
                'gridLanes':1,
                'trajectoryOutput':False
    }
    '''
    '''
    theoretical_streets_traffic_light_failure':
    configure = {'mode':'test',
                'scenario':'theoretical_streets',
                'time':12000,
                'rebuild':True,
                'anomaly':'traffic_light_failure',
                'anomalyStart':3000,
                'anomalyEnd':9000,
                'anomalyPos':'C2',
                'anomalySeverity':0.2,
                'busPerc':0.2,
                'theta':0.6,
                'detectorFrequency':60,
                'detectorThreshold':20,
                'detectorSpacing':200,
                'gridNumber':5,
                'gridLength':200,
                'gridLanes':1,
                'trajectoryOutput':True,
                'eventThreshold':0.5,
    }
    '''

    '''
    real_world_streets_abrupt_flow:
    configure = {'mode':'test',
                'scenario':'real_world_streets',
                'time':12000,
                'rebuild':True,
                'anomaly':'abrupt_flow',
                'anomalyStart':3000,
                'anomalyEnd':9000,
                'anomalyPos':'passenger.5.0',
                'anomalySeverity':5,
                'busPerc':0.2,
                'theta':0.6,
                'detectorFrequency':60,
                'detectorThreshold':20,
                'detectorSpacing':200,
                'networkFile':'streets.osm',
                'trajectoryOutput':False
    }
    '''
    '''
    real_world_expressways_speed_limit':
    configure = {'mode':'test',
                'scenario':'real_world_expressways',
                'time':12000,
                'rebuild':True,
                'anomaly':'speed_limit',
                'anomalyStart':3000,
                'anomalyEnd':9000,
                'anomalyPos':'123867444',
                'anomalySeverity':0.2,
                'busPerc':0.2,
                'theta':0.6,
                'detectorFrequency':60,
                'detectorThreshold':20,
                'detectorSpacing':500,
                'networkFile':'expressways.osm',
                'trajectoryOutput':True,
                'eventThreshold':0.5
    }
    '''
    configure = {'mode':'test',
                'scenario':'real_world_expressways',
                'time':12000,
                'rebuild':True,
                'anomaly':'speed_limit',
                'anomalyStart':3000,
                'anomalyEnd':9000,
                'anomalyPos':'123867444',
                'anomalySeverity':0.2,
                'busPerc':0.2,
                'theta':0.6,
                'detectorFrequency':60,
                'detectorThreshold':20,
                'detectorSpacing':500,
                'networkFile':'expressways.osm',
                'trajectoryOutput':True,
                'eventThreshold':0.5
    }
    app.set_args(**configure)
    app.check_paths()
    app.apply_simulation()