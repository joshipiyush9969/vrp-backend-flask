import math
import pandas as pd
import numpy as np
import re
from operator import itemgetter
from ortools_google import *

from math import radians, cos, sin, asin, sqrt
from pprint import pprint
import random
from sklearn.cluster import KMeans

# Default scaling factor for distance matrix is 100
# https://developers.google.com/optimization/routing/tsp#scaling
scalar = 100

def parse_file(file_text):
    data = {}
    parser = re.compile(
        """NAME : (?P<name>.*)
COMMENT : (?P<comment>.*)
TYPE : (?P<type>.*)
DIMENSION : (?P<dimension>.*)
EDGE_WEIGHT_TYPE : (?P<edge_weight_type>.*)
CAPACITY : (?P<capacity>.*)
NODE_COORD_SECTION\s*
(?P<node_coord_section>[\d|\s]+)
DEMAND_SECTION\s*
(?P<demand_section>[\d|\s]+)
DEPOT_SECTION\s*
(?P<depot_node>.*)\s*
""",re.MULTILINE,)

    problemInfo = {}
    matches = parser.match(file_text)
    if matches:
        # trim parsed values
        data = matches.groupdict()
        for key, val in data.items():
            data[key] = val.strip()

        other = re.match(
            ".*No of trucks: (?P<vehicles>\d+).*Optimal value: (?P<optimal_value>\d+).*",
            data["comment"],
        )
        data.update(other.groupdict()) if other else data.update(
            {"vehicles": None, "optimal_value": None}
        )
        data["node_coord_section"] = [
            list(map(int, x))
            for x in map(
                lambda x: x.split(" "), data["node_coord_section"].split("\n ")
            )
        ]
        data["demand_section"] = [
            list(map(int, x))[1:]
            for x in map(
                lambda x: x.split(" "), data["demand_section"].split(" \n")
            )
        ]
        data["priority"] = np.zeros(
            (int(data["dimension"]), 1), dtype=int
        )  # sets all priority col to zero

        combined_cols = np.c_[
            data["node_coord_section"], data["demand_section"], data["priority"]
        ]
        data["node_data"] = pd.DataFrame(
            columns=["node", "latitude", "longitude", "demand", "priority"],
            data=combined_cols,
        )
        # currently capacity is a constant value; change to array for variable truck capacity
        for key in [
            "name",
            "dimension",
            "vehicles",
            "optimal_value",
            "capacity",
            "depot_node",
            "node_data",
        ]:
            problemInfo[key] = data[key]

    class ProblemInfo:
        def __init__(
            self,
            name,
            dimension,
            vehicles,
            optimal_value,
            capacity,
            depot_node,
            node_data,
        ):
            self.name = name
            self.dimension = int(dimension)
            self.vehicles = int(vehicles)
            self.optimal_value = int(optimal_value)
            self.capacity = int(capacity)
            self.depot_node = int(depot_node)
            self.node_data = node_data

    p1 = ProblemInfo(**problemInfo)

    return p1

def distance(lat1, lat2, lon1, lon2):

    # The math module contains a function named
    # radians which converts from degrees to radians.
    lon1 = radians(lon1)
    lon2 = radians(lon2)
    lat1 = radians(lat1)
    lat2 = radians(lat2)

    # Haversine formula
    dlon = lon2 - lon1
    dlat = lat2 - lat1
    a = sin(dlat / 2) ** 2 + cos(lat1) * cos(lat2) * sin(dlon / 2) ** 2

    c = 2 * asin(sqrt(a))

    # Radius of earth in kilometers. Use 3956 for miles
    r = 6371

    # calculate the result
    return c * r


def find_route(node_Data, vehicle_capacity, no_of_vehicles):

    matrix_d = []
    demand = []
    # vehicle_capacity = [100, 100, 100, 100, 100] 
    # no_of_vehicles = 5  

    for lat1, lon1 in zip(node_Data["latitude"], node_Data["longitude"]):
        node = []
        for lat2, lon2 in zip(node_Data["latitude"], node_Data["longitude"]):
            node.append(int(distance(lat1, lat2, lon1, lon2) * scalar))
        matrix_d.append(node)

    # p#print(matrix_d)
    for d in node_Data["demand"]:
        demand.append(d)

    # while sum(vehicle_capacity) < sum(demand):
    #     capacity = []
    #     for i in range(no_of_vehicles):
    #         capacity.append(random.randint(max(demand), 100))
    #     vehicle_capacity = capacity

    # pprint(matrix_d)
    #print("demand =>", demand)
    #print("no.of vehicles =>", no_of_vehicles)
    #print("vehicle capacity =>", vehicle_capacity)

    # or tools
    data = create_data_model(matrix_d, demand, vehicle_capacity, no_of_vehicles)
    route = generate_routes(data)
    return route



def cluster(node_Data, num_of_v, capacity):
    v_sum = 0
    num_of_v = int(num_of_v)
    vehicles = []
    d = {}
    no_clusters = 3
    
    kmeans = KMeans(n_clusters = no_clusters, init ='k-means++', random_state=3425, n_init=1)
    kmeans.fit(node_Data[node_Data.columns[1:3]]) # Compute k-means clustering.
    node_Data['cluster_label'] = kmeans.fit_predict(node_Data[node_Data.columns[1:3]])
    centers = kmeans.cluster_centers_ # Coordinates of cluster centers.
    labels = kmeans.predict(node_Data[node_Data.columns[1:3]]) # Labels of each point
    node_Data.head(10)
    clusters = list(set(node_Data['cluster_label'].tolist()))

    for i in clusters:
        total_demand = node_Data.loc[node_Data['cluster_label'] == i, 'demand'].sum()
        #print(total_demand)
        vehicles.append(math.ceil(total_demand/capacity))
        v_sum += math.ceil(total_demand/capacity)

    if(v_sum>num_of_v):
        num_of_v += 1   
    for i in clusters:
        d[i] = node_Data[node_Data['cluster_label'] == i]

    return [d,vehicles]