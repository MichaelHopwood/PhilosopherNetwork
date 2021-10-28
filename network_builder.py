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

import json

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
                    default='philosopher_data.csv',
                    help='The file to load data.')
args = parser.parse_args()

DATE_COL = 'birth'

class GraphBuilder:
    def __init__(self, data, num_nodes=100):
        self.data = data
        self._pre_prep()
        # Initialize adjacency matrix
        self.A = np.zeros((num_nodes, num_nodes))
        # self.node_features = dict(zip(

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
        michael, alex, randyll = np.array_split(valid_data, 3)
        print(len(michael), len(alex), len(randyll))
        michael.to_csv('michael.csv', index=False)
        michael.to_csv('alexander.csv', index=False)
        michael.to_csv('randyll.csv', index=False)

        import sys
        sys.exit()

        self.data.dropna(inplace=True, subset=[DATE_COL])

    def find_date(self, string, default_age_length=100):
        string = re.sub('c\.', '', string)
        string = re.sub('circa', '', string)

        num_AD = len(re.findall('AD', string))
        num_BC = len(re.findall('BC', string))

        string = re.sub('AD', '', string)
        string = re.sub('BC', '', string)

        string = re.sub('\s', '', string)

        if re.search(r"(\d+)–(\d+)", string):
            # Finds dates like "1844-1846"
            year_data = re.findall(r"(\d+)–(\d+)", string)
            y_data = year_data[0]
            birth_date, death_date = int(y_data[0]), int(y_data[1])

        elif re.search(r"\d\d\d\d", string):
            # Finds dates like "born 1944"
            year_data = re.findall(r"\d\d\d\d", string)
            y_data = int(year_data[0])
            birth_date = y_data
            death_date = np.nan

        elif re.search(r"\d\d\d", string):
            # Finds dates like "born 194"
            year_data = re.findall(r"\d\d\d", string)
            y_data = int(year_data[0])
            birth_date = y_data
            death_date = np.nan

        elif re.search(r"\d+(th|rd|st)", string):
            # Get century
            year_data = re.findall(r"\d+", string)
            birth_date = int(year_data[0])*100 - 50
            death_date = np.nan

        if num_AD == 1 and num_BC == 1:
            # Person born in BC and died in AD
            birth_date *= -1
        elif num_BC > 0:
            # Person born and died in BC
            birth_date *= -1
            if np.isnan(death_date):
                death_date = birth_date + default_age_length
            else:
                death_date *= -1

        if np.isnan(death_date):
            death_date = birth_date + default_age_length

        return birth_date, death_date

    def prep_dates(self):
        for idx, row in self.data.iterrows():
            birth_date, death_date = self.find_date(row[DATE_COL])
            # print(json.dumps(dict(zip(['String', 'Birth', 'Death'],[row[DATE_COL], birth_date, death_date]))))

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
        
        if node_features != None:
            for n in G.nodes():
                for k,v in node_features.items():
                    G.nodes[n][k] = v[n]
        
        if type_graph == 'nx':
            return G
        
        G = G.to_directed()
        
        if node_features != None:
            node_attrs = list(node_features.keys())
        else:
            node_attrs = []
            
        g = dgl.from_networkx(G, node_attrs=node_attrs, edge_attrs=['weight'])
        return g

def main():
    global args
    data = pd.read_csv(os.path.join(args.load_folder, args.load_file), encoding='UTF-8', na_values=[''], index_col='Unnamed: 0')
    print(data)

    gb = GraphBuilder(data)
    gb.prep_dates()
        
if __name__ == "__main__":
    main()



