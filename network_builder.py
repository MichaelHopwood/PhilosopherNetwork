import pickle
import glob
import os
import numpy as np
import argparse
import pandas as pd
import networkx as nx
import dgl
import datefinder
import re
import datetime
import json
import matplotlib.pyplot as plt
import cartopy.crs as ccrs

# Run `python network_builder.py -load_folder data2
# To specify the output folder
# @dev: you can reference this specification by using `args.save_folder`
parser = argparse.ArgumentParser(description='Scrape philosopher data from Wikipedia')
parser.add_argument('-load_folder',
                    '--load_folder',
                    dest='load_folder',
                    type=str,
                    default='data',
                    help='The folder to load data.')
parser.add_argument('-load_file',
                    '--load_file',
                    dest='load_file',
                    type=str,
                    default='michael_algoaddition_adddate.csv',
                    help='The file to load data.')
args = parser.parse_args()

DATE_COL = 'births'
NAME_COL = 'name'

class GraphBuilder:
    def __init__(self, data, num_nodes=100, feature_names=[]):
        self.data = data
        self.num_nodes = num_nodes
        self.feature_names = feature_names
        self._prep()

    def _add_adj(self, val):
        lst = []
        try:
            adjacency_list = val.split(':')
        except:
            adjacency_list = []
        for v in adjacency_list:
            if v in self.codex:
                lst.append(self.codex[v])
        return lst

    def _prep(self):
        '''Prepare data for building graph.
        '''
        def _date_to_int(date):
            '''Convert date to int year.
            '''
            num_AD = len(re.findall('AD', date))
            num_BC = len(re.findall('BC', date))

            datet = datetime.datetime.strptime(date[3:], '%Y-%m-%d %H:%M:%S')
            datet = datet.year
            if num_BC > 0:
                datet *= -1
            return datet

        self.data[DATE_COL] = self.data[DATE_COL].apply(lambda x : _date_to_int(x))

        self.data['num_incoming_links'] = self.data['incoming_links'].apply(lambda x: len(x.split(':')) if isinstance(x, str) else 0)
        self.data['num_outgoing_links'] = self.data['outgoing_links'].apply(lambda x: len(x.split(':')) if isinstance(x, str) else 0)
        
        print("Num people with nonzero incoming links: ", len(self.data[ self.data['num_incoming_links'] > 0 ]))
        print("Num people with nonzero outgoing links: ", len(self.data[ self.data['num_outgoing_links'] > 0 ]))

        self.data = self.data[ self.data['num_outgoing_links'] > 0 ]
        
        del self.data['num_incoming_links']
        del self.data['num_outgoing_links']
        
        #self.A = np.zeros((len(self.data), len(self.data)))
        self.flat_adjacencies = {}

        self.codex = dict(zip(self.data[NAME_COL], self.data.index))
        self.inv_codex = dict(zip(self.data.index, self.data[NAME_COL]))
       
        for ind,row in self.data.iterrows():
            self.flat_adjacencies[self.codex[row[NAME_COL]]] = {
                'out': self._add_adj(row['outgoing_links']),
                'in': self._add_adj(row['incoming_links'])
            }

        self.node_features = dict(zip(self.feature_names, [self.data[feat].values for feat in self.feature_names]))


    def _pre_prep(self):

        self.data['num_incoming_links'] = self.data['incoming_links'].apply(lambda x: len(x.split(':')) if isinstance(x, str) else 0)
        self.data['num_outgoing_links'] = self.data['outgoing_links'].apply(lambda x: len(x.split(':')) if isinstance(x, str) else 0)
        
        print("Num people with nonzero incoming links: ", len(self.data[ self.data['num_incoming_links'] > 0 ]))
        print("Num people with nonzero outgoing links: ", len(self.data[ self.data['num_outgoing_links'] > 0 ]))

        valid_data = self.data[ self.data['num_outgoing_links'] > 0 ]
        valid_data['latitude'] = 'FILL'
        valid_data['longitude'] = 'FILL'
        
        del valid_data['num_incoming_links']
        del valid_data['num_outgoing_links']

        # Shuffle dataframe
        valid_data = valid_data.sample(frac=1)
        alex, michael, randyll = np.array_split(valid_data, 3)
        print(len(michael), len(alex), len(randyll))
        michael.to_csv('michael.csv', index=False)
        alex.to_csv('alexander.csv', index=False)
        randyll.to_csv('randyll.csv', index=False)

        import sys
        sys.exit()

    def build_graph(self, type_graph='dgl'):
        '''Convert numpy arrays to graph.
        This should be called after actually building the adjacency and feature matrices.

        Parameters
        ----------
        type_graph : str
            'dgl' or 'nx'

        Uses internal parameters:
        -------------------------
        A : mxm array
            Adjacency matrix
        node_features : dict
            Optional, dictionary with key=feature name, value=list of size m
            Allows user to specify node features

        Returns

        -------
        Graph of 'type_graph' specification
        '''
        
        G = nx.from_numpy_array(self.A)
        
        if self.node_features != None:
            for n in G.nodes():
                for k,v in self.node_features.items():
                    G.nodes[n][k] = v[n]

        if type_graph == 'nx':
            return G

        G = G.to_directed()

        if self.node_features != None:
            node_attrs = list(self.node_features.keys())
        else:
            node_attrs = []

        g = dgl.from_networkx(G, node_attrs=node_attrs, edge_attrs=['weight'])
        return g

    def draw_line(self, ax, A_name, A_lon, A_lat, B_name, B_lon, B_lat):
        '''Draw a line between two points.
        '''

        ax.plot([A_lon, B_lon], [A_lat, B_lat],
                color='blue', linewidth=2, marker='o',
                transform=ccrs.Geodetic(),
                )

        ax.plot([A_lon, B_lon], [A_lat, B_lat],
                color='gray', linestyle='--',
                transform=ccrs.PlateCarree(),
                )

        ax.text(A_lon - 3, A_lat - 12, A_name,
                horizontalalignment='right',
                transform=ccrs.Geodetic())

        ax.text(B_lon + 3, B_lat - 12, B_name,
                horizontalalignment='left',
                transform=ccrs.Geodetic())

    def visualize(self, n_nodes=100):
        '''Visualize graph.
        '''
        fig = plt.figure(figsize=(15,15))
        ax = plt.axes(projection=ccrs.PlateCarree())
        ax.stock_img()

        self.data.sort_values(inplace=True, by=DATE_COL)

        #self.data = self.data.sample(n=20)
        # for ind,row in self.data.iterrows():
        for i in range(len(self.data)):
            row = self.data.iloc[i]
            ind = self.data.index[i]
            in_ind_name = self.data.loc[ind][NAME_COL]

            for out_ind in self.flat_adjacencies[ind]['in']:
                print(ind, out_ind)
                try:
                    out_row = self.data.loc[out_ind]
                except Exception as e:
                    print(e)
                    continue
                if isinstance(out_row, type(None)):
                    continue

                out_ind_name = out_row[NAME_COL]
                A_lon, A_lat, B_lon, B_lat = (self.data.loc[ind, 'longitude'],
                                            self.data.loc[ind, 'latitude'],
                                            out_row['longitude'],
                                            out_row['latitude'])
                A_name = in_ind_name
                B_name = out_ind_name
                plt.plot([A_lon, B_lon], [A_lat, B_lat],
                        color='blue', linewidth=2, marker='o',
                        transform=ccrs.Geodetic(),
                        )

                plt.text(A_lon - 3, A_lat - 12, A_name,
                        horizontalalignment='right',
                        transform=ccrs.Geodetic())

                plt.text(B_lon + 3, B_lat - 12, B_name,
                        horizontalalignment='left',
                        transform=ccrs.Geodetic())
        
            plt.savefig(f"figs//{i}.png")

def main():
    global args
    data = pd.read_csv(os.path.join(args.load_folder, args.load_file), index_col='Unnamed: 0', na_values=['FILL'])
    del data['birth']
    data = data.dropna(subset=['latitude', 'longitude', 'births'])

    gb = GraphBuilder(data, num_nodes=len(data), feature_names=['latitude', 'longitude', 'births'])
    gb.visualize()
    
        
if __name__ == "__main__":
    main()



