import json
import os
import io
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
check = randint(0, 1000)

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
    """
        NOTE: rproxy means reverse proxy
        *. nodejs to solver at /route (id and file will be sent)
        *. Make clusters only (this is the only time you should ever use the parser)
        *. solver to nodejs: at /graphql trigger the mutation updateProblemInfo
            -> Refer: (https://github.com/jontyparab/vrp-backend-node/blob/main/modules/problem/problemInfo.graphql#L13)
        *. solver to rproxy at /route?clustered=1 (i.e. query param showing clustering is done)
            -> rproxy runs on port 4000
            -> You will have to send multiple requests to rproxy (one request for every cluster formed) with other required problemInfo data.
            -> rproxy will forward it to other instance at port :4000
        *. rproxy to solver: forwards to same or some other solver instance (skip parsing step, use cluster data that is passed)
        *. solver to nodejs: at /graphql trigger the mutation updateProblemInfoSolution and pass id and route only
            -> Refer: (https://github.com/jontyparab/vrp-backend-node/blob/main/modules/problem/problemInfo.graphql#L10)
            -> Total distance for all tour (arc) arjun will calculate in frontend dynamically so you can ignore
        *. 
    """
    if (request.method == "POST"):
        clustered = request.args.get("clustered") == "1"
        gql_result, truck_route = None, None
        if clustered:
            print("Executing /route?clustered=1")
            truck_route = find_route()
            return jsonify({
                "clustered": clustered,
                "identifier": check,
                "route": truck_route,
            })
        else:
            print("Executing /route")
            data = request.get_json()
            id = data.get('id')
            uint8arr = data.get('file').get('data') # [78,65,77,69,32,...]
            # UInt8Array to file that can be given as input to parse_file
            file = io.StringIO(bytes(uint8arr).decode('utf-8')) # in-memory file
            p1 = parse_file(file)
            file.close()
            nodeData = json.loads(p1.node_data.to_json(orient="records"))

            #TO NODEJS
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

            #Clustering
            [clusters,vehicles] = cluster(p1.node_data, p1.vehicles)
            for i in range(len(vehicles)):
                # TODO: Send requests ka code likh bruhhh :(
                print({"num_of_vehicles":vehicles[i], "data":clusters[i].to_json(orient="index")})

            return jsonify({
                "clustered": clustered,
                "identifier": check,
                "query_result": gql_result,
            })
    
    if (request.method == "GET"):
        # Just to check if endpoint is active
        return jsonify({"identifier": check})

# main driver function
if __name__ == "__main__":
    app.run(debug=os.environ.get("FLASK_DEBUG", True))

if __name__ != "__main__":
	# For logging in prod
    gunicorn_error_logger = logging.getLogger("gunicorn.error")
    app.logger.handlers = gunicorn_error_logger.handlers
    app.logger.setLevel(gunicorn_error_logger.level)
