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
from k_means_constrained import KMeansConstrained

np.random.seed(3425)

# Default scaling factor for distance matrix is 100
# https://developers.google.com/optimization/routing/tsp#scaling
scalar = 100

# def parse_file(file_text):

#     data = {}
#     parser = re.compile(
#         """NAME : (?P<name>.*)
# COMMENT : (?P<comment>.*)
# TYPE : (?P<type>.*)
# DIMENSION : (?P<dimension>.*)
# EDGE_WEIGHT_TYPE : (?P<edge_weight_type>.*)
# CAPACITY : (?P<capacity>.*)
# NODE_COORD_SECTION\s*
# (?P<node_coord_section>[\d|\.|\-|\s]+)
# DEMAND_SECTION\s*
# (?P<demand_section>[\d|\s]+)
# DEPOT_SECTION\s*
# (?P<depot_node>.*)\s*
# """,re.MULTILINE,)

#     problemInfo = {}
#     matches = parser.match(file_text)
#     if matches:
#         # trim parsed values
#         data = matches.groupdict()
#         for key, val in data.items():
#             data[key] = val.strip()

#         other = re.match(
#             ".*No of trucks: (?P<vehicles>\d+)(, Optimal value: (?P<optimal_value>\d+))?.*",
#             data["comment"],
#         )
#         data.update({
#                 "vehicles": other.groupdict().get("vehicles", None), 
#                 "optimal_value": other.groupdict().get("optimal_value", None)
#             }
#         )
#         data["node_coord_section"] = [
#             list(map(lambda y: float(y.strip()), x))
#             for x in map(
#                 lambda x: x.strip().split(" ", 2), data["node_coord_section"].split("\n")
#             )
#         ]
#         data["demand_section"] = [
#             list(map(lambda y: int(y.strip()), x))[1:]
#             for x in map(
#                 lambda x: x.strip().split(" ", 1), data["demand_section"].split("\n")
#             )
#         ]
#         # sets all priority col to zero
#         # data["priority"] = np.zeros(
#         #     (int(data["dimension"]), 1), dtype=int
#         # )
#         data["priority"] = [2, *np.random.choice(
#             a=[2, 1, 0], 
#             size=(int(data["dimension"])-1),
#             p=[0.93, 0.06, 0.01],
#         )]

#         combined_cols = np.c_[
#             data["node_coord_section"], data["demand_section"], data["priority"]
#         ]
#         data["node_data"] = pd.DataFrame(
#             columns=["node", "latitude", "longitude", "demand", "priority"],
#             data=combined_cols,
#         )
#         # print(data)
#         # currently capacity is a constant value; change to array for variable truck capacity
#         for key in [
#             "name",
#             "dimension",
#             "vehicles",
#             "optimal_value",
#             "capacity",
#             "depot_node",
#             "node_data",
#         ]:
#             problemInfo[key] = data[key]

#     class ProblemInfo:
#         def __init__(
#             self,
#             name,
#             dimension,
#             vehicles,
#             optimal_value,
#             capacity,
#             depot_node,
#             node_data,
#         ):
#             self.name = name
#             self.dimension = int(dimension)
#             self.vehicles = int(vehicles)
#             self.optimal_value = int(optimal_value) if optimal_value else None
#             self.capacity = int(capacity)
#             self.depot_node = int(depot_node)
#             self.node_data = node_data

#     p1 = ProblemInfo(**problemInfo)

def parse_file(file):
    problemInfo={}
    df = pd.read_excel(file)
    capacity = df['capacity'][0]
    vehicles = df['no_of_trucks'][0]
    dimension = df['dimension'][0]
    depot_node = df['depot_node'][0]
    optimal_value = df['optimal_value'][0] 
    name = df['name'][0] 
    node_data =  pd.DataFrame(
            columns=["node", "latitude", "longitude", "demand", "priority"],
            data=df,
        )
    problemInfo["name"] = name
    problemInfo["dimension"] = dimension
    problemInfo["vehicles"] = vehicles
    problemInfo["optimal_value"] = optimal_value
    problemInfo["capacity"] = capacity    
    problemInfo["depot_node"] = depot_node    
    problemInfo["node_data"] = node_data    
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
            self.optimal_value = int(optimal_value) if not pd.isna(optimal_value) else None
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
    c = 2 * asin(sqrt(abs(a)))

    # Radius of earth in kilometers. Use 3956 for miles
    r = 6371

    # calculate the result
    return c * r


def find_route(node_data, vehicle_capacities, no_of_vehicles, timeout):

    matrix_d = []
    demand = []
    priority = []
    # vehicle_capacities = [100, 100, 100, 100, 100] 
    # no_of_vehicles = 5  

    for lat1, lon1 in zip(node_data["latitude"], node_data["longitude"]):
        node = []
        for lat2, lon2 in zip(node_data["latitude"], node_data["longitude"]):
            node.append(int(distance(lat1, lat2, lon1, lon2) * scalar))
        matrix_d.append(node)

    # p#print(matrix_d)
    demand = node_data["demand"].copy()
    priorities = node_data["priority"].copy()

    # while sum(vehicle_capacities) < sum(demand):
    #     capacity = []
    #     for i in range(no_of_vehicles):
    #         capacity.append(random.randint(max(demand), 100))
    #     vehicle_capacities = capacity

    #pprint(matrix_d)
    #print("demand =>", demand)
    #print("no.of vehicles =>", no_of_vehicles)
    #print("vehicle capacity =>", vehicle_capacities)

    # or tools
    data = create_data_model(matrix_d, demand, vehicle_capacities, no_of_vehicles, priorities)
    route = generate_routes(data, timeout)
    return route



def cluster(node_data, num_of_v, capacity):
    vehicles = []
    d = {}
    no_clusters = math.ceil(len(node_data['node']) / 1000)
    min_s = 900
    
    if len(node_data['node']) <= 2*min_s:
        kmeans = KMeans(n_clusters=no_clusters, init ='k-means++', random_state=3425, n_init=1)
    else:
        kmeans = KMeansConstrained(n_clusters=no_clusters, size_min=min_s, size_max=2*min_s, init='k-means++', random_state=3425, n_init=1)
    kmeans.fit(node_data[node_data.columns[1:3]]) # Compute k-means clustering.
    node_data['cluster_label'] = kmeans.fit_predict(node_data[node_data.columns[1:3]])
    centers = kmeans.cluster_centers_ # Coordinates of cluster centers.
    labels = kmeans.predict(node_data[node_data.columns[1:3]]) # Labels of each point
    node_data.head(10)
    clusters = list(set(node_data['cluster_label'].tolist()))

    for i in clusters:
        total_demand = node_data.loc[node_data['cluster_label'] == i, 'demand'].sum()
        vehicles.append(math.ceil(total_demand/capacity))
        # print('Total Demand', total_demand, vehicles[-1], capacity)

    print('Used trucks:', sum(vehicles), ', Available trucks:', num_of_v)
    # if(sum(vehicles) > num_of_v):
    #     num_of_v += 1
    for i in clusters:
        d[i] = node_data[node_data['cluster_label'] == i]

    return [d, vehicles]
