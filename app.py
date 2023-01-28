import json
import os
from flask import Flask, flash, jsonify, request
import logging
from random import randint
#from werkzeug import secure_filename
from cvrp import *
from gql import Client, gql
from gql.transport.requests import RequestsHTTPTransport

app = Flask(__name__)
# Check running of instances for reverse proxy
check = randint(0, 255)

# Graphql Client setup
transport = RequestsHTTPTransport(
    # url="http://127.0.0.1:3000/graphql",
    url="https://countries.trevorblades.com/",
    verify=True,
    retries=3,
)
client = Client(transport=transport, fetch_schema_from_transport=True)
 
@app.route("/",methods = ["GET"])
def home():
    if(request.method == "GET"):
        return jsonify({"Instance identifier": check})


@app.route("/route", methods = ["GET", "POST"])
def generate_route():
    # if "file" not in request.files:
    #     return jsonify({"response": "failed"})
    # file = request.files["file"]
    # if file.filename == "":
    #     return jsonify({"response": "failed"})
    # if file:
    #     filename = secure_filename(file.filename)
    #     file.save(os.path.join(app.config["UPLOAD_FOLDER"], filename))

    #     truck_route = find_route()

    #     return jsonify({"response": "success","output":truck_route})
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
    clustered = request.args.get("clustered") == "1"
    gql_result, truck_route = None, None
    if clustered:
        query = gql(
            """
            query getContinents {
                continents {
                    code
                    name
                }
            }
            """
        )
        gql_result = client.execute(query)
        truck_route = find_route()
        return jsonify({
            "clustered": clustered,
            "check": check, 
            "graphql": gql_result,
            "route": truck_route, 
        })
    else:        
        return jsonify({
            "clustered": clustered,
            "check": check, 
            "graphql": gql_result,
            "route": truck_route, 
        })
    # query = gql(
    #         """
    #         mutation updateProblemInfo(id: ) {
    #                 id
    #                 name
    #                 dimension
    #                 vehicles
    #                 optimalValue
    #                 capacity
    #                 depotNode
    #                 nodeData {
    #                     node
    #                     latitude
    #                     longitude
    #                     demand
    #                     priority
    #                 }
    #                 solution {
    #                     routes {
    #                         tour
    #                         tourDistance
    #                     }
    #                     totalDistance
    #                 }
    #                 file
    #         }
    #         """
    #     )

# main driver function
if __name__ == "__main__":
    app.run(debug=os.environ.get("FLASK_DEBUG", True))

if __name__ != "__main__":
	# For logging in prod
    gunicorn_error_logger = logging.getLogger("gunicorn.error")
    app.logger.handlers = gunicorn_error_logger.handlers
    app.logger.setLevel(gunicorn_error_logger.level)
