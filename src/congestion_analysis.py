import numpy as np
import matplotlib.pyplot as plt
from bin.functions import get_max_speed

def congestion_analysis(sce_name,dataset_path,node_path,net_file):
    dataset = np.load(dataset_path)
    nodes = np.load(node_path)
    plt.plot(dataset.T)
    plt.title(sce_name+' speed plot')
    plt.xlabel('time(min)')
    plt.ylabel('speed(m/s)')
    plt.show()

    speed = get_max_speed(net_file)
    congestion = dataset<0.5*speed
    count = 0
    for i in range(congestion.shape[0]):
        congestion_seires = moving_average(congestion[i,:],5)
        if np.any(congestion_seires>0.8):
            count = count + 1
    return count/len(nodes)

def moving_average(x, w):
    return np.convolve(x, np.ones(w), 'valid') / w
    