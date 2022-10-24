import imp
import pandas as pd
import numpy as np
import re
from operator import itemgetter

from ortools_google import *

def find_route():
  with open("./upload/A-n36-k5.vrp", "r") as cvrp_file:
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
  """, re.MULTILINE)
    problemInfo = {}
    text = cvrp_file.read()
    matches = parser.match(text)
    if matches:
      # trim parsed values
      data = matches.groupdict()
      for key, val in data.items():
        data[key] = val.strip()

      other = re.match('.*No of trucks: (?P<vehicles>\d+).*Optimal value: (?P<optimal_value>\d+).*', data['comment'])
      data.update(other.groupdict()) if other else data.update({"vehicles":None, "optimal_value":None})
      
      data['node_coord_section'] = [list(map(int, x)) for x in map(lambda x: x.split(' '), data['node_coord_section'].split('\n '))]
      data['demand_section'] = [list(map(int, x))[1:] for x in map(lambda x: x.split(' '), data['demand_section'].split(' \n'))]
      data['priority'] = np.zeros((int(data['dimension']), 1), dtype=int)  # sets all priority col to zero
      
      combined_cols = np.c_[data['node_coord_section'], data['demand_section'], data['priority']]
      data['node_data'] = pd.DataFrame(columns=['node', 'latitude', 'longitude', 'demand', 'priority'], data=combined_cols)
      # currently capacity is a constant value; change to array for variable truck capacity
      for key in ['name', 'dimension', 'vehicles', 'optimal_value', 'capacity', 'depot_node', 'node_data']:
        problemInfo[key] = data[key]


  class ProblemInfo:
    def __init__(self, name, dimension, vehicles, optimal_value, capacity, depot_node, node_data):
      self.name = name
      self.dimension = dimension
      self.vehicles = vehicles
      self.optimal_value = optimal_value
      self.capacity = capacity
      self.depot_node = depot_node
      self.node_data = node_data
    
  p1 = ProblemInfo(**problemInfo)
      
  node_Data = (p1.node_data)
  print(node_Data)



  #Distance one to node to another (Many to many)
  from math import radians, cos, sin, asin, sqrt
  from pprint import pprint
  import random
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
      a = sin(dlat / 2)**2 + cos(lat1) * cos(lat2) * sin(dlon / 2)**2
  
      c = 2 * asin(sqrt(a))
      
      # Radius of earth in kilometers. Use 3956 for miles
      r = 6371
        
      # calculate the result
      return(c * r)

  matrix_d = []
  demand = []
  vehicle_capacity = [] #from frontend
  no_of_vehicles = 5    #from frontend

  for lat1,lon1 in zip(node_Data['latitude'],node_Data['longitude']): 
    node = []
    for lat2,lon2 in zip(node_Data['latitude'], node_Data['longitude']):
      node.append(distance(lat1, lat2, lon1, lon2))
    matrix_d.append(node)

  #pprint(matrix_d)
  for d in node_Data['demand']:
    demand.append(d)

  while(sum(vehicle_capacity) < sum(demand)):
    capacity = []  
    for i in range(no_of_vehicles):
      capacity.append(random.randint(max(demand),100))   
    vehicle_capacity = capacity

  #pprint(matrix_d)
  print("demand =>",demand)
  print("no.of vehicles =>",no_of_vehicles)
  print("vehicle capacity =>",vehicle_capacity)





  #or tools
  data = create_data_model(matrix_d,demand,vehicle_capacity,no_of_vehicles)
  route = main(data)
  return route