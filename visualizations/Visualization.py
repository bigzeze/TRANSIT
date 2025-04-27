import os
import networkx as nx
import xml.dom.minidom
import matplotlib.pyplot as plt
from matplotlib.colors import LinearSegmentedColormap as LSC
from mpl_toolkits.mplot3d import Axes3D
from matplotlib import cm
import math
import numpy as np
import pandas as pd
import cartopy.io.img_tiles as cimgt
import cartopy.crs as ccrs
from mpl_toolkits.mplot3d import Axes3D
import sumolib

class Node:
    def __init__(self,x:float,y:float,id:str=''):
        self.id = id
        self.x = x
        self.y = y

    def __repr__(self):
        if self.id == None:
            return "("+str(self.x)+","+str(self.y)+")"
        return "("+self.id+",pos:("+str(self.x)+","+str(self.y)+"))"
    
class Edge:
    def __init__(self,id,fr:Node,to:Node,bias=0):
        self.id = id
        self.fr = fr
        self.to = to
        self.bias = bias
        self.max_speed = None
        self.pass_points = []
        self.fixed_points = []
    
    def set_bias(self,bias):
        self.bias = bias
        self.fix_edge_pos()
    
    def set_max_speed(self,maxspeed):
        self.max_speed = maxspeed
    
    def set_pass_points(self,pass_points:list):
        self.pass_points = pass_points
        self.fix_edge_pos()

    def fix_edge_pos(self):
        self.fixed_points = self.pass_points.copy()
        def fix_points(start,end):
            sx,sy = start.x,start.y
            ex,ey = end.x,end.y
            if sx == ex:
                if sy > ey:
                    fixed_start = Node(sx-self.bias,sy)
                    fixed_end = Node(ex-self.bias,ey)
                else:
                    fixed_start = Node(sx+self.bias,sy)
                    fixed_end = Node(ex+self.bias,ey)
            elif sy == ey:
                if sx > ex:
                    fixed_start = Node(sx,sy+self.bias)
                    fixed_end = Node(ex,ey+self.bias)
                else:
                    fixed_start = Node(sx,sy-self.bias)
                    fixed_end = Node(ex,ey-self.bias)
            else:
                k = (ey-sy)/(ex-sx)
                xbais = self.bias/math.sqrt(1+k*k)*k
                ybais = self.bias/math.sqrt(1+k*k)
                if k>0:
                    if sx < ex:
                        fixed_start = Node(sx+xbais,sy-ybais)
                        fixed_end = Node(ex+xbais,ey-ybais)
                    else:
                        fixed_start = Node(sx-xbais,sy+ybais)
                        fixed_end = Node(ex-xbais,ey+ybais)
                else:
                    if sx < ex:
                        fixed_start = Node(sx+xbais,sy+ybais)
                        fixed_end = Node(ex+xbais,ey+ybais)
                    else:
                        fixed_start = Node(sx-xbais,sy-ybais)
                        fixed_end = Node(ex-xbais,ey-ybais)
            return fixed_start,fixed_end
        for idx in range(len(self.pass_points)-1):
            start = self.pass_points[idx]
            end = self.pass_points[idx+1]
            fixed_start,fixed_end = fix_points(start,end)
            self.fixed_points[idx] = fixed_start
            self.fixed_points[idx+1] = fixed_end
    
    def get_length(self):
        return math.sqrt((self.fr.x-self.to.x)**2+(self.fr.y-self.to.y)**2)
    def __repr__(self):
        return f'(origin:{self.fr}->{self.to}'+f' ,fixed_points:{self.fixed_points})'

class Graph:
    def __init__(self,bias=5):
        self.nodes = {}
        self.edges = {}
        self.bias = bias
    
    def add_node(self,node:Node):
        self.nodes[node.id] = node
    
    def add_node(self,id:str,x:float,y:float):
        self.nodes[id] = Node(x,y,id)

    def add_edge(self,edge:Edge):
        self.edges[edge.id] = edge
    
    def add_edge(self,id:str,fr:str,to:str,pass_points:list):
        self.edges[id] = Edge(id,self.nodes[fr],self.nodes[to])
        self.edges[id].set_pass_points(pass_points)
    
    def get_border(self):
        min_x = min([node.x for node in self.nodes.values()])
        max_x = max([node.x for node in self.nodes.values()])
        min_y = min([node.y for node in self.nodes.values()])
        max_y = max([node.y for node in self.nodes.values()])
        return min_x,max_x,min_y,max_y
    
    def edge_exists(self,fr,to):
        for edge in self.edges.values():
            if fr == edge.fr and to == edge.to:
                return True
        else:
            return False
    
    def set_bias(self,bias):
        for _,edge in self.edges.items():
            edge.set_bias(bias)
    
class Visualization:

    def __init__(self):
        self.sce = None
        self.anomaly = None
        self.borderwidth = None
        alpha = 0.9
        colors = [(0,(alpha,0,0)),
                  (0.5,(alpha,alpha,0)),
                  (1,(0,alpha,0))]
        self.colorbar = LSC.from_list('mycmap',colors)
        self.anomalyStart = None
        self.anomalyEnd = None
        self.injectPos = None
        self.scatterPos = None
    def check_paths(self):
        self.path = os.path.dirname(os.path.abspath(__file__)) + '/'
        models = self.path + '../models/'
        outputs = self.path + '../datasets/'
        inputs = self.path + '../inputs/'
        visualizations = self.path + '../visualizations/'
        if not os.path.exists(models):
            os.mkdir(models)
        if not os.path.exists(outputs):
            os.mkdir(outputs)
        if not os.path.exists(inputs):
            os.mkdir(inputs)
        if not os.path.exists(visualizations):
            os.mkdir(visualizations)
        if not os.path.exists(models+self.sce + '/'):
            os.mkdir(models+self.sce + '/')
        if not os.path.exists(outputs+self.sce + '/'):
            os.mkdir(outputs+self.sce + '/')
        if not os.path.exists(visualizations+self.sce + '/'):
            os.mkdir(visualizations+self.sce + '/')
        
        self.sce_model = models + self.sce + '/'  
        self.sce_output = outputs + self.sce + '/' + self.anomaly + '/'
        self.inputPath = inputs + '/'
        self.visualization = visualizations + self.sce + '/' + self.anomaly + '/'
        if not os.path.exists(self.sce_model):
            os.mkdir(self.sce_model)
        if not os.path.exists(self.sce_output):
            os.mkdir(self.sce_output)
        if not os.path.exists(self.visualization):
            os.mkdir(self.visualization)
        
        self.netfile = self.sce_model + 'road.net.xml'
    
    def set_args(self,**kwargs):
        self.sce = kwargs.get('scenario',self.sce)
        self.anomaly = kwargs.get('anomaly',self.anomaly)
        self.borderwidth = kwargs.get('borderwidth',0.1)
        self.injectPos = kwargs.get('injectPos',self.injectPos)
        self.anomalyStart = kwargs.get('anomalyStart',self.anomalyStart)
        self.anomalyEnd = kwargs.get('anomalyEnd',self.anomalyEnd)
        self.scatterPos = kwargs.get('scatterPos',self.scatterPos)
        if self.anomaly == 'speed_limit':
            self.scatterPos = self.injectPos
    
    def load_data(self):
        self.dataFile = self.sce_output + 'detectors.npy'
        self.nodeFile = self.sce_output + 'nodes.npy'
        self.trajectoryFile = self.sce_output + 'trajectory.csv'
        data = np.load(self.dataFile)
        nodenames = np.load(self.nodeFile)
        self.flow_df = pd.DataFrame(data[:,0,:].T,columns=nodenames)
        self.occupancy_df = pd.DataFrame(data[:,1,:].T,columns=nodenames)
        self.speed_df = pd.DataFrame(data[:,2,:].T,columns=nodenames)
        if os.path.exists(self.trajectoryFile):
            trajectory = pd.read_csv(self.trajectoryFile,sep=';')
            trajectory.dropna(axis=0,inplace=True)
            trajectory['vehicle_id'] = trajectory['vehicle_id'].apply(lambda x:x.split('_')[0])
            self.trajectory = trajectory.groupby('vehicle_id')

    def position_convert(self,x,y):
        lon,lat = self.libnet.convertXY2LonLat(x,y)
        return lon,lat
    def generate_graph(self):
        self.check_paths()
        self.graph = Graph()
        self.load_data()

        if 'real_world' in self.sce or 'parallel' in self.sce:
            self.libnet = sumolib.net.readNet(self.netfile)

        dom = xml.dom.minidom.parse(self.netfile)
        root = dom.documentElement
        nodes = root.getElementsByTagName("junction")
        edges = root.getElementsByTagName("edge")

        for node in nodes:
            ntype = node.getAttribute('type')
            if ntype == 'internal':
                continue
            id = node.getAttribute('id')
            x = eval(node.getAttribute('x'))
            y = eval(node.getAttribute('y'))
            if 'real_world' in self.sce or 'parallel' in self.sce:
                x,y = self.position_convert(x,y)
            self.graph.add_node(id,x,y)
        for edge in edges:
            id = edge.getAttribute('id')
            fr = edge.getAttribute('from')
            to = edge.getAttribute('to')
            fc = edge.getAttribute('function')
            sp = edge.getAttribute('shape')
            if id not in self.speed_df.columns:
                continue
            if fr == '':
                continue
            if fc != '':
                continue
            def shape2points(sp):
                points = sp.split(' ')
                pass_points = []
                for point in points:
                    if point:
                        x,y = point.split(',')
                        x,y = float(x),float(y)
                        if 'real_world' in self.sce or 'parallel' in self.sce:
                            x,y = self.position_convert(x,y)
                        pass_points.append(Node(x,y))
                if pass_points:
                    return pass_points
                else:
                    return [Node(self.graph.nodes[fr].x,self.graph.nodes[fr].y),Node(self.graph.nodes[to].x,self.graph.nodes[to].y)]
            pass_points = shape2points(sp)
            lanes = edge.getElementsByTagName("lane")
            maxspeed = 0
            for lane in lanes:
                maxspeed = max(eval(lane.getAttribute("speed")),maxspeed)
            self.graph.add_edge(id,fr,to,pass_points)
            self.graph.edges[id].set_max_speed(maxspeed)

    def cal_edge_pos(self,edge_id,pos):
        if 'real_world' in self.sce or 'parallel' in self.sce:
            x,y = sumolib.geomhelper.positionAtShapeOffset(self.libnet.getLane(edge_id+'_0').getShape(), pos)
            return self.libnet.convertXY2LonLat(x, y)
        else:
            edge = self.graph.edges[edge_id]
            total_length = edge.get_length()
            perc = min(max(0,pos/total_length),0.99)
            return edge.fr.x+perc*(edge.to.x-edge.fr.x),edge.fr.y+perc*(edge.to.y-edge.fr.y)
        
    def show_graph(self,steps):
        fig = plt.figure(figsize=(10, 3), dpi= 300)
        for idx,step in enumerate(steps):
            #rows = int(math.sqrt(len(steps)))
            rows = len(steps)
            cols = 1
            if 'real_world' in self.sce or 'parallel' in self.sce:
                ax = fig.add_subplot(cols,rows,idx+1,projection=ccrs.PlateCarree())
            else:
                ax = fig.add_subplot(cols,rows,idx+1)
            # draw nodes
            ax.axis('off')
            ax.set_aspect(1)
            min_x,max_x,min_y,max_y = self.graph.get_border()
            ax.set_xlim(min_x-self.borderwidth*(max_x-min_x),max_x+self.borderwidth*(max_x-min_x))
            ax.set_ylim(min_y-self.borderwidth*(max_y-min_y),max_y+self.borderwidth*(max_y-min_y))
            bias = 0.005*(max_x-min_x)
            self.graph.set_bias(bias)
            #for _,node in self.graph.nodes.items():
                #circle = plt.Circle((node.x,node.y),color='black',radius=bias)
                #ax.add_patch(circle)
            # drawbasemap
            if 'real_world' in self.sce or 'parallel' in self.sce:
                backmap=cimgt.OSM()
                ax.add_image(backmap, 15)
                expandx = 0.1*(max_x-min_x)
                expandy = 0.1*(max_y-min_y)
                extent = [min_x-expandx,max_x+expandx,min_y-expandy,max_y+expandy]
                ax.set_extent(extent,crs=ccrs.PlateCarree())
                # sel_edge = self.graph.edges['1138642069']
                # for idx in range(len(sel_edge.fixed_points)-1):
                #     ax.add_line(plt.Line2D([sel_edge.fixed_points[idx].x,sel_edge.fixed_points[idx+1].x],[sel_edge.fixed_points[idx].y,sel_edge.fixed_points[idx+1].y]))

            def draw_circle():
                if self.anomaly == 'speed_limit':
                    edge = self.graph.edges[self.injectPos]
                    x = (edge.fr.x + edge.to.x)/2
                    y = (edge.fr.y + edge.to.y)/2
                if self.anomaly == 'traffic_light_failure':
                    node = self.graph.nodes[self.injectPos]
                    x = node.x
                    y = node.y
                circle = plt.Circle((x,y),color='red',radius=2*bias,zorder=5)
                ax.add_patch(circle)
            if self.anomaly == 'speed_limit' or self.anomaly == 'traffic_light_failure':
                draw_circle()
            for id,edge in self.graph.edges.items():
                if id in self.speed_df.columns:
                    speed = self.speed_df.loc[step,edge.id]
                    rgb = self.colorbar(min(max(0,speed/edge.max_speed),0.99))
                def draw_edge(edge,rgb=(0,0,0)):
                    #if self.graph.edge_exists(edge.to,edge.fr):
                    print(edge)
                    for idx in range(len(edge.fixed_points)-1):
                        line = plt.Line2D((edge.fixed_points[idx].x,edge.fixed_points[idx+1].x),(edge.fixed_points[idx].y,edge.fixed_points[idx+1].y),color=rgb,linewidth=0.5)
                        ax.add_line(line)
                    # else:
                    #     for idx in range(len(edge.pass_points)-1):
                    #         line = plt.Line2D((edge.pass_points[idx].x,edge.pass_points[idx+1].x),(edge.pass_points[idx].y,edge.pass_points[idx+1].y),color=rgb,linewidth=0.2*bias)
                    #         ax.add_line(line)
                draw_edge(edge,rgb)
            ax.set_title('step:'+str(step*60),fontsize=5)
        #plt.savefig(self.visualization+'speed_graph.png')
        plt.show()
    
    def show_graph_with_trajectory(self,vehicle_ids):
        fig = plt.figure(figsize=(10, 10), dpi= 80)
        ax = fig.add_subplot(111, projection='3d')
        ax.grid(False)
        ax.set_xticks([])
        ax.set_yticks([])   
        ax.xaxis.line.set_visible(False)
        ax.yaxis.line.set_visible(False)
        ax.xaxis.pane.set_visible(False)
        ax.yaxis.pane.set_visible(False)
        def draw_base_graph():
            step = self.anomalyStart
            '''
            if self.sce == 'real_world_streets' or self.sce == 'real_world_expressways':
                min_x,max_x,min_y,max_y = self.graph.get_border()

                osm_tiles = cimgt.OSM()
                crs = ccrs.PlateCarree()
                fig_2d = plt.figure(dpi=10)
                ax_2d = fig_2d.add_subplot(111,projection=ccrs.PlateCarree())
                ax_2d.axis('off')
                ax_2d.set_aspect(1)
                ax_2d.add_image(osm_tiles, 15)
                expandx = 0.1*(max_x-min_x)
                expandy = 0.1*(max_y-min_y)
                extent = [min_x-expandx,max_x+expandx,min_y-expandy,max_y+expandy]
                ax_2d.set_extent(extent,crs=ccrs.PlateCarree())
                fig_2d.canvas.draw()
                map_image = np.array(fig_2d.canvas.renderer.buffer_rgba())   
                plt.close(fig_2d)
                x = np.linspace(extent[0], extent[1], map_image.shape[1])
                y = np.linspace(extent[2], extent[3], map_image.shape[0])
                x, y = np.meshgrid(x, y)
                z = np.full(x.shape,self.anomalyStart-1)  # z=0平面
                ax.plot_surface(x, y, z, rstride=1, cstride=1, facecolors=map_image / 255, shade=False,zorder=0,alpha=0.1)
            '''
            min_x,max_x,min_y,max_y = self.graph.get_border()
            ax.set_xlim(min_x-self.borderwidth*(max_x-min_x),max_x+self.borderwidth*(max_x-min_x))
            ax.set_ylim(min_y-self.borderwidth*(max_y-min_y),max_y+self.borderwidth*(max_y-min_y))
            bias = 0.005*(max_x-min_x)
            self.graph.set_bias(bias)
            for id,edge in self.graph.edges.items():
                def draw_edge(rgb=(0,0,0)):
                    for idx in range(len(edge.fixed_points)-1):
                        ax.plot3D((edge.fixed_points[idx].x,edge.fixed_points[idx+1].x),(edge.fixed_points[idx].y,edge.fixed_points[idx+1].y),(step,step),color=rgb,zorder=1)
                draw_edge()
        draw_base_graph()
        for vehicle_id in vehicle_ids:
            vtrajectory = self.trajectory.get_group(vehicle_id)
            vtrajectory = vtrajectory.drop(vtrajectory[vtrajectory['edge_id'].apply(lambda x:x not in self.graph.edges.keys())].index)
            vtrajectory.sort_values(by='timestep_time')
            vtrajectory.index = range(vtrajectory.shape[0])
            vtrajectory[['x','y']] = vtrajectory.apply(lambda x:self.cal_edge_pos(x['edge_id'],x['vehicle_pos']),axis=1).apply(pd.Series)

            series_sel = vtrajectory[(vtrajectory['timestep_time']>=self.anomalyStart) & (vtrajectory['timestep_time']<=self.anomalyEnd)]
            ax.plot(series_sel['x'],series_sel['y'],series_sel['timestep_time'],zorder=1)

        def draw_3D_surface(edge):
            edge = self.graph.edges[edge]
            x = np.linspace(edge.fr.x,edge.to.x,100)
            z = np.linspace(self.anomalyStart,self.anomalyEnd,self.anomalyEnd-self.anomalyStart)
            x,z = np.meshgrid(x,z)
            y = edge.fr.y + (edge.to.y-edge.fr.y)/(edge.to.x-edge.fr.x)*(x-edge.fr.x)
            ax.plot_surface(x,y,z,color='r',alpha=0.3,zorder=1)
        def draw_3D_line(node):
            node = self.graph.nodes[node]
            ax.plot3D((node.x,node.x),(node.y,node.y),(self.anomalyStart,self.anomalyEnd),color='r',zorder=1)
        if self.anomaly == 'speed_limit':
            draw_3D_surface(self.injectPos)
        if self.anomaly == 'traffic_light_failure':
            draw_3D_line(self.injectPos)
        #plt.savefig(self.visualization+'trajectory.png')
        plt.show()

    def cal_sigma(self,threshold):
        congestion_count = 0
        total_count = 0
        for id,edge in self.graph.edges.items():
            total_count = total_count + 1
            maxspeed = edge.max_speed
            avgspeed = self.speed_df.loc[self.anomalyStart/60:self.anomalyEnd/60,id].mean()
            if avgspeed < threshold*maxspeed:
                congestion_count = congestion_count + 1
        print('sigma:',congestion_count/total_count)
        return congestion_count/total_count

    def show_scatter_plot(self):
        
        speed_data = self.speed_df.loc[:,self.scatterPos].values
        flow_data = self.flow_df.loc[:,self.scatterPos].values
        occupancy_data = self.occupancy_df.loc[:,self.scatterPos].values
        fig = plt.figure(figsize=(16, 10), dpi= 80, facecolor='w', edgecolor='k')
        # flow_speed
        ax = fig.add_subplot(2,2,1)
        ax.scatter(speed_data,flow_data)
        ax.set_xlabel('speed')
        ax.set_ylabel('flow')
        # flow_density
        ax = fig.add_subplot(2,2,2)
        ax.scatter(occupancy_data,flow_data)
        ax.set_xlabel('occupancy')
        ax.set_ylabel('flow')
        # occupancy_speed
        ax = fig.add_subplot(2,2,3)
        ax.scatter(speed_data,occupancy_data)
        ax.set_xlabel('speed')
        ax.set_ylabel('occupancy')
        plt.show()
        


                

    

if __name__ == '__main__':
    '''
    configures = {
        'scenario':'theoretical_streets',
        'anomaly':'speed_limit',
        'injectPos':'C1D1',
        'anomalyStart':3000,
        'anomalyEnd':9000
    }
    app.show_graph_with_trajectory(['passenger.0.0'])
    '''
    '''
    configures = {
        'scenario':'theoretical_streets',
        'anomaly':'traffic_light_failure',
        'injectPos':'C2',
        'anomalyStart':3000,
        'anomalyEnd':9000,
        'scatterPos':'B2C2'
    }
    app.cal_sigma(0.7)
    app.show_graph([25,100,170])
    app.show_graph_with_trajectory(['passenger.26.0'])
    '''
    '''
    configures = {
        'scenario':'real_world_streets',
        'anomaly':'speed_limit',
        'injectPos':'1138642053',
        'anomalyStart':3000,
        'anomalyEnd':9000,
    }
    app.cal_sigma(0.7)
    app.show_graph([25,100,175])
    app.show_graph_with_trajectory(['passenger.0.0'])
    '''
    '''
    configures = {
        'scenario':'real_world_expressways',
        'anomaly':'speed_limit',
        'injectPos':'123867444',
        'anomalyStart':3710,
        'anomalyEnd':4610,
        'scatterPos':'157607691'
    }
    app = Visualization()
    app.set_args(**configures)
    app.generate_graph()
    #app.cal_sigma(0.7)
    #app.show_graph([25,75,125,175])
    #app.show_graph_with_trajectory(['passenger.26.2'])
    app.show_scatter_plot()
    '''
    '''
    configures = {
        'scenario':'parallel',
        'anomaly':'abrupt_flow',
    }'
    '''
    configures = {
        'scenario':'real_world_expressways',
        'anomaly':'speed_limit',
        'injectPos':'123867444',
        'anomalyStart':3710,
        'anomalyEnd':4610,
        'scatterPos':'157607691'
    }
    app = Visualization()
    app.set_args(**configures)
    app.generate_graph()
    # app.cal_sigma(0.7)
    app.show_graph([25,100,175])
    #app.show_graph_with_trajectory(['passenger.26.2'])
    #app.show_scatter_plot()


