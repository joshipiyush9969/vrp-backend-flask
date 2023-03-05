import json
import os
import io
import threading
import requests
import traceback
import pandas as pd
import datetime
from datetime import timezone
from flask import Flask, flash, jsonify, request
from flask_cors import CORS
import logging
from random import randint
#from werkzeug import secure_filename
from cvrp import *
from gql import Client, gql
from gql.transport.requests import RequestsHTTPTransport

app = Flask(__name__)
CORS(app)
# Check running of instances for reverse proxy
check = randint(0, 9999)

# Graphql Client setup
transport = RequestsHTTPTransport(
    url=f'{os.environ.get("NODE_URL")}/graphql',
    verify=True,
    retries=3,
)
client = Client(transport=transport, serialize_variables=True, fetch_schema_from_transport=True)
 
@app.route("/", methods = ["GET", "POST"])
def home():
    return jsonify({
        "identifier": check, 
    })



@app.route("/route", methods = ["GET", "POST"])
def generate_route():
    if (request.method == "POST"):
        clustered = request.args.get("clustered") == "1"
        gql_result = None
        if clustered:
            req_data = request.get_json()
            print("Executing /route?clustered=1")
            node_data = pd.read_json(req_data["data"])
            cluster_label = node_data["cluster_label"][0]
            depot = pd.read_json(req_data["depot"])
            node_data = pd.concat([depot, node_data]).reset_index(drop=True)
            
            # find route using ortools
            print(f"-------Solution Route Cluster #{cluster_label} ({req_data['id']}) start time-------", get_timestamp())
            solution = find_route(node_data, req_data["capacity"], req_data["num_of_vehicles"])
            print(f"-------Solution Route Cluster #{cluster_label} ({req_data['id']}) end time-------", get_timestamp())
            
            if solution:
                route_distances = solution[1]
                truck_routes = []
                for sol in solution[0]:
                    route = [node_data['node'][i] for i in sol]
                    truck_routes.append(route)
                print(truck_routes)
                # update the solution
                for i in range(len(truck_routes)):
                    query = gql(
                    """
                        mutation updateProblemInfoSolution(
                                $id: ID!,
                                $tour: [Int],
                                $tourDistance: Int
                            ) {
                            updateProblemInfoSolution(id: $id, input: {
                                tour: $tour,
                                tourDistance: $tourDistance
                            }) {
                                nModified
                                n
                                ok
                            }
                        }
                    """
                    )
                    variables = {
                        "id": req_data['id'],
                        "tour": truck_routes[i],
                        "tourDistance": route_distances[i]
                    }
                    gql_result = client.execute(query, variables)
                    # print("gql -> ", gql_result)
            else:
                return jsonify({
                    "clustered": clustered,
                    "identifier": check,
                    "gql_result": gql_result,
                    "solution": False
                })
            
            return jsonify({
                "clustered": clustered,
                "identifier": check,
                "gql_result": gql_result,
                "solution": True
            })
        else:
            print("Executing /route")
            data = request.get_json()
            id = data.get('id')
            # "id": "6400fe3e977ea378226b4b07"
            # uint8arr = [78,65,77,69,32,58,32,65,45,110,51,54,45,107,53,10,67,79,77,77,69,78,84,32,58,32,40,65,117,103,101,114,97,116,32,101,116,32,97,108,44,32,78,111,32,111,102,32,116,114,117,99,107,115,58,32,53,44,32,79,112,116,105,109,97,108,32,118,97,108,117,101,58,32,55,57,57,41,10,84,89,80,69,32,58,32,67,86,82,80,10,68,73,77,69,78,83,73,79,78,32,58,32,51,54,10,69,68,71,69,95,87,69,73,71,72,84,95,84,89,80,69,32,58,32,69,85,67,95,50,68,32,10,67,65,80,65,67,73,84,89,32,58,32,49,48,48,10,78,79,68,69,95,67,79,79,82,68,95,83,69,67,84,73,79,78,32,10,32,49,32,49,53,32,49,57,10,32,50,32,49,32,52,57,10,32,51,32,56,55,32,50,53,10,32,52,32,54,57,32,54,53,10,32,53,32,57,51,32,57,49,10,32,54,32,51,51,32,51,49,10,32,55,32,55,49,32,54,49,10,32,56,32,50,57,32,57,10,32,57,32,57,51,32,55,10,32,49,48,32,53,53,32,52,55,10,32,49,49,32,50,51,32,49,51,10,32,49,50,32,49,57,32,52,55,10,32,49,51,32,53,55,32,54,51,10,32,49,52,32,53,32,57,53,10,32,49,53,32,54,53,32,52,51,10,32,49,54,32,54,57,32,49,10,32,49,55,32,51,32,50,53,10,32,49,56,32,49,57,32,57,49,10,32,49,57,32,50,49,32,56,49,10,32,50,48,32,54,55,32,57,49,10,32,50,49,32,52,49,32,50,51,10,32,50,50,32,49,57,32,55,53,10,32,50,51,32,49,53,32,55,57,10,32,50,52,32,55,57,32,52,55,10,32,50,53,32,49,57,32,54,53,10,32,50,54,32,50,55,32,52,57,10,32,50,55,32,50,57,32,49,55,10,32,50,56,32,50,53,32,54,53,10,32,50,57,32,53,57,32,53,49,10,32,51,48,32,50,55,32,57,53,10,32,51,49,32,50,49,32,57,49,10,32,51,50,32,54,49,32,56,51,10,32,51,51,32,49,53,32,56,51,10,32,51,52,32,51,49,32,56,55,10,32,51,53,32,55,49,32,52,49,10,32,51,54,32,57,49,32,50,49,10,68,69,77,65,78,68,95,83,69,67,84,73,79,78,32,10,49,32,48,32,10,50,32,49,32,10,51,32,49,52,32,10,52,32,49,53,32,10,53,32,49,49,32,10,54,32,49,56,32,10,55,32,50,32,10,56,32,50,50,32,10,57,32,55,32,10,49,48,32,49,56,32,10,49,49,32,50,51,32,10,49,50,32,49,50,32,10,49,51,32,50,49,32,10,49,52,32,50,32,10,49,53,32,49,52,32,10,49,54,32,57,32,10,49,55,32,49,48,32,10,49,56,32,52,32,10,49,57,32,49,57,32,10,50,48,32,50,32,10,50,49,32,50,48,32,10,50,50,32,49,53,32,10,50,51,32,49,49,32,10,50,52,32,54,32,10,50,53,32,49,51,32,10,50,54,32,49,57,32,10,50,55,32,49,51,32,10,50,56,32,56,32,10,50,57,32,49,53,32,10,51,48,32,49,56,32,10,51,49,32,49,49,32,10,51,50,32,50,49,32,10,51,51,32,49,50,32,10,51,52,32,50,32,10,51,53,32,50,51,32,10,51,54,32,49,49,32,10,68,69,80,79,84,95,83,69,67,84,73,79,78,32,10,32,49,32,32,10,32,45,49,32,32,10,69,79,70,32,10]
            uint8arr = data.get('file').get('data') # [78,65,77,69,32,...]
            file = io.StringIO(bytes(uint8arr).decode('utf-8')) # in-memory file
            contents = file.getvalue()
            
            try:
                p1 = parse_file(contents)
            except Exception:
                traceback.print_exc()
                return jsonify({"message": "Unable to parse file."}), 400
            
            file.close()
            nodeData = json.loads(p1.node_data.to_json(orient="records"))

            # update the problemInfo with data
            query = gql(
                """
                    mutation UpdateProblemInfo(
                            $id: ID!,
                            $name: String
                            $dimension: Int
                            $vehicles: Int
                            $optimalValue: Int
                            $capacity: Int
                            $depotNode: Int
                            $nodeData: [NodeInfoInput]
                        ) {
                        updateProblemInfo(id: $id, input: {
                            name: $name,
                            dimension: $dimension,
                            vehicles: $vehicles,
                            optimalValue: $optimalValue,
                            capacity: $capacity,
                            depotNode: $depotNode,
                            nodeData: $nodeData,
                        }) {
                            nModified
                            n
                            ok
                        }
                    }
                """
            )
            variables = {
                "id": id,
                "name": p1.name,
                "dimension": p1.dimension,
                "vehicles": p1.vehicles,
                "optimalValue": p1.optimal_value,
                "capacity": p1.capacity,
                "depotNode": p1.depot_node,
                "nodeData": nodeData
            }
            gql_result = client.execute(query, variables)

            # return response and continue sending requests in another thread
            thread = threading.Thread(target=distribute_task, kwargs={
                'id': id,
                'p1': p1,
            })
            thread.start()

            return jsonify({
                "clustered": clustered,
                "identifier": check,
                "gql_result": gql_result,
            }), 202
    
    if (request.method == "GET"):
        # just to check if endpoint is active
        return jsonify({"identifier": check})
    
def distribute_task(**kwargs):
    # time consuming task distribution
    id = kwargs.get('id', None)
    p1 = kwargs.get('p1', {})
    depot = p1.node_data.loc[p1.node_data['node'] == p1.depot_node]
    node_data = p1.node_data.drop(p1.node_data[p1.node_data['node'] == p1.depot_node].index)
    print(f'-------Problem ({id}) clustering start time-------', get_timestamp())
    [clusters,vehicles] = cluster(node_data, p1.vehicles, p1.capacity)
    print(f'-------Problem ({id}) clustering end time-------', get_timestamp(), clusters)

    url = f"{os.environ.get('SOLVER_URL')}/route?clustered=1"
    headers = {'content-type': 'application/json'}
    for i in range(len(vehicles)):
        payload = {
            "id": id,
            "capacity": [p1.capacity for x in range(vehicles[i])], 
            "num_of_vehicles": vehicles[i],
            "depot": depot.to_json(orient="records"),
            "data":clusters[i].to_json(orient="records")
        }
        try:
            # Fire and forget (Hacky)
            requests.post(url, json=payload, headers=headers)
        except requests.exceptions.ReadTimeout:
            pass
        # print("res -> ", response)
        # print({"num_of_vehicles":vehicles[i], "data":clusters[i].to_json(orient="records")})

def get_timestamp():
    dt = datetime.datetime.now(timezone.utc)
    utc_time = dt.replace(tzinfo=timezone.utc)
    return utc_time.timestamp()

# main driver function
if __name__ == "__main__":
    app.run(debug=os.environ.get("FLASK_DEBUG", True))

if __name__ != "__main__":
	# For logging in prod
    gunicorn_error_logger = logging.getLogger("gunicorn.error")
    app.logger.handlers = gunicorn_error_logger.handlers
    app.logger.setLevel(gunicorn_error_logger.level)
