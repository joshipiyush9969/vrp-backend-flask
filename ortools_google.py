from ortools.constraint_solver import routing_enums_pb2
from ortools.constraint_solver import pywrapcp

scalar = 100

def create_data_model(matrix_d,demand,vehicle_capacity,no_of_vehicles):
    data = {}
    data["distance_matrix"] = matrix_d
    data["demands"] = demand
    data["vehicle_capacities"] = vehicle_capacity
    data["num_vehicles"] = no_of_vehicles
    data["depot"] = 0
    return data



def print_solution(data, manager, routing, solution):
    vehicle_routes = []
    vehicle_route_distance = []
    
    #vehicle_route_distance = [] Distance coming zero, still have to figure out, whats the problem
    """Prints solution on console."""
    #print(f"Objective: {solution.ObjectiveValue() // scalar}")
    total_distance = 0
    total_load = 0
    for vehicle_id in range(data["num_vehicles"]):
        index = routing.Start(vehicle_id)
        plan_output = "Route for vehicle {}:\n".format(vehicle_id)
        route_distance = 0
        route_load = 0
        current_route = []
        while not routing.IsEnd(index):
            node_index = manager.IndexToNode(index)
            route_load += data["demands"][node_index]
            current_route.append(node_index)
            plan_output += " {0} Load({1}) -> ".format(node_index, route_load)
            previous_index = index
            index = solution.Value(routing.NextVar(index))
            route_distance += routing.GetArcCostForVehicle(
                previous_index, index, vehicle_id) // scalar
        plan_output += " {0} Load({1})\n".format(manager.IndexToNode(index),
                                                 route_load)
        plan_output += "Distance of the route: {}m\n".format(route_distance)
        plan_output += "Load of the route: {}\n".format(route_load)
        vehicle_routes.append(current_route)
        vehicle_route_distance.append(route_distance)
        #print(plan_output)
        total_distance += route_distance
        total_load += route_load
    #print("Total distance of all routes: {}m".format(total_distance))
    #print("Total load of all routes: {}".format(total_load))
    return (vehicle_routes, vehicle_route_distance)






def generate_routes(data, timeout):
    # Instantiate the data problem.

    # Create the routing index manager.
    manager = pywrapcp.RoutingIndexManager(len(data["distance_matrix"]),
                                           data["num_vehicles"], data["depot"])

    # Create Routing Model.
    routing = pywrapcp.RoutingModel(manager)


    # Create and register a transit callback.
    def distance_callback(from_index, to_index):
        """Returns the distance between the two nodes."""
        # Convert from routing variable Index to distance matrix NodeIndex.
        from_node = manager.IndexToNode(from_index)
        to_node = manager.IndexToNode(to_index)
        return data["distance_matrix"][from_node][to_node]

    transit_callback_index = routing.RegisterTransitCallback(distance_callback)

    # Define cost of each arc.
    routing.SetArcCostEvaluatorOfAllVehicles(transit_callback_index)


    # Add Capacity constraint.
    def demand_callback(from_index):
        """Returns the demand of the node."""
        # Convert from routing variable Index to demands NodeIndex.
        from_node = manager.IndexToNode(from_index)
        return data["demands"][from_node]
        

    demand_callback_index = routing.RegisterUnaryTransitCallback(
            demand_callback
        )
    routing.AddDimensionWithVehicleCapacity(
            demand_callback_index,
            0,  # null capacity slack
            data["vehicle_capacities"],  # vehicle maximum capacities
            True,  # start cumul to zero
            "Capacity"
        )

    # Setting first solution heuristic.
    search_parameters = pywrapcp.DefaultRoutingSearchParameters()
    search_parameters.first_solution_strategy = (
        routing_enums_pb2.FirstSolutionStrategy.PATH_CHEAPEST_ARC)
    search_parameters.local_search_metaheuristic = (
        routing_enums_pb2.LocalSearchMetaheuristic.GUIDED_LOCAL_SEARCH)
    search_parameters.time_limit.FromSeconds(timeout)

    # Solve the problem.
    # solution = routing.Solve()
    solution = routing.SolveWithParameters(search_parameters)

    # Print solution on console.
    if solution:
        v_routes = print_solution(data, manager, routing, solution)
        return v_routes




# if __name__ == "__main__":
#     main()
