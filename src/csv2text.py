import pandas as pd
import numpy as np
import xml.dom.minidom
import warnings
warnings.filterwarnings("ignore")
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
def csv2text(fixed_names,fixed_data, float_csv, text_file, net_file, threshold):
    speeds = get_speed_with_road(net_file)
    fixed_part(speeds, fixed_names, fixed_data, text_file, threshold)
    float_part(speeds, float_csv, text_file, threshold)
    txt_resort(text_file)

def txt_resort(text_file):
    df = pd.read_csv(text_file,sep='\t',header=None)
    df = df.sort_values(by=df.columns[0],axis=0)
    df.to_csv(text_file,sep='\t',index=False,header=False)
def fixed_part(speeds, fixed_names, fixed_data, text_file, threshold):
    txtfile = open(text_file, 'a')
    names = np.load(fixed_names)
    data = np.load(fixed_data)
    df = pd.DataFrame(data[:,2,:].T,columns=names)
    for road in names:
        congestions = df[df[road]<threshold*speeds[road]].index.tolist()
        for time in congestions:
            txtfile.write(f'{time*60}\troad {road} congested.\n')
    txtfile.close()

def float_part(speeds, float_csv, text_file, threshold):
    txtfile = open(text_file, 'a')
    df = pd.read_csv(float_csv,sep=';')
    df['vehicle_speed'].replace(0.0,np.nan,inplace=True)
    df.dropna(axis=0, inplace=True)
    vehiclegroups = df.groupby('vehicle_id')
    for name,group in vehiclegroups:
        group = group[group['edge_id'].apply(lambda x: x in speeds.keys())]
        congestion = group[group['vehicle_speed']<threshold*group['edge_id'].apply(lambda x: speeds[x])]
        if congestion.empty: continue
        congestion['minute'] = pd.cut(congestion['timestep_time'].apply(int),bins=range(0, int(congestion['timestep_time'].max()) + 60, 60),right=False)
        minute_count_group = congestion.groupby('minute').aggregate({'vehicle_speed':'count'},observed=True)
        minute_count_group = minute_count_group.sort_values(by='minute')
        minute_count_group = minute_count_group[minute_count_group['vehicle_speed']>20]
        minute_road_group = congestion.groupby('minute').aggregate({'edge_id':pd.unique},observed=True)
        for idx,row in minute_count_group.iterrows():
            txtfile.write(f'{idx.left}\tvehicle {name} on road ' + ','.join(minute_road_group.loc[idx,'edge_id']) + ' drives slowly.\n')
    txtfile.close()

if __name__ == '__main__':
    net_file = 'models\\real_world_streets\\road.net.xml'
    fixed_names = 'datasets\\real_world_streets\\speed_limit\\nodes.npy'
    fixed_data = 'datasets\\real_world_streets\\speed_limit\\detectors.npy'
    float_csv = 'datasets\\real_world_streets\\speed_limit\\trajectory.csv'
    text_file = 'datasets\\real_world_streets\\speed_limit\\test.txt'
    csv2text(fixed_names,fixed_data,float_csv,text_file,net_file,0.5)