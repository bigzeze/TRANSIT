import pandas as pd
from scipy.signal import savgol_filter
import matplotlib.pyplot as plt
import numpy as np
import logging
import xml.dom.minidom

def get_speed_with_road(net_file):
    dom = xml.dom.minidom.parse(net_file)
    root = dom.documentElement
    edges = root.getElementsByTagName("edge")
    speeds = {}
    for edge in edges:
        id = edge.getAttribute('id')
        fr = edge.getAttribute('from')
        to = edge.getAttribute('to')
        fc = edge.getAttribute('function')
        if fr == '':
            continue
        if fc != '':
            continue
        lanes = edge.getElementsByTagName("lane")
        lane_speed = []
        for lane in lanes:
            lane_speed.append(eval(lane.getAttribute("speed")))
            speeds[id] = max(lane_speed)
    return speeds
def csv2dataset(input_file,net_file,out_name=''):
    logger = logging.getLogger('TRANSIT')
    logger.info('{0:-^50}'.format('Data Processing'))
    speeds = get_speed_with_road(net_file)
    spl = input_file.rfind('/') + 1
    path = input_file[:spl]
    df = pd.read_csv(input_file,sep=';')
    df['interval_id'] = df['interval_id'].str.split('_',expand=True).loc[:,0]
    idgroups = df.groupby('interval_id')
    names = []
    datalst = []
    for name,idgroup in idgroups:
        idgroup = idgroup.sort_values(by='interval_begin')
        idgroup = idgroup.reset_index()
        def speed_agg(s):
            s = s[s!=-1.0]
            return s.mean()
        
        idgroup = idgroup.groupby('interval_begin').agg({'interval_id':'first','interval_flow':'sum','interval_occupancy':'mean','interval_speed':speed_agg})
        # SpeedClean
        idgroup['interval_speed'] = idgroup['interval_speed'].replace(-1,np.nan) # missing data
        if pd.isna(idgroup.loc[0,'interval_speed']):
            idgroup.loc[0,'interval_speed'] = speeds[name]
        #group['interval_speed'] = group['interval_speed'].fillna(method='ffill')
        idgroup['interval_speed'] = idgroup['interval_speed'].ffill()
        nparry = idgroup[['interval_flow','interval_occupancy','interval_speed']].to_numpy()
        data_new = []
        for i in range(3):
            aspect = nparry[:,i]
            smooth = savgol_filter(aspect,5,3)
            smooth = np.maximum(smooth,0)
            data_new.append(smooth)
        data_new = np.array(data_new)
        names.append(name)
        datalst.append(data_new)

    names = np.array(names)
    data = np.array(datalst)
    #return names,data
    np.save(path+out_name+'nodes.npy',names)
    np.save(path+out_name+'detectors.npy',data)
    logger.info('Dataset Saved Success, file path: '+ path+'nodes.npy' +','+ 'detector.npy')
    logger.info('{0:-^50}'.format(''))

if __name__ =='__main__':
    input_file = 'E:\\TRANSIT\\datasets\\real_world_expressways\\speed_limit\\detectors.csv'
    net_file = 'E:\\TRANSIT\\models\\real_world_expressways\\road.net.xml'
    csv2dataset(input_file,net_file)
