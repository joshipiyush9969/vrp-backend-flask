import json
import os
from flask import Flask, flash, jsonify, request
#from werkzeug import secure_filename

from cvrp import *

app = Flask(__name__)
 
@app.route('/',methods = ['GET','POST'])
def home():
    if(request.method == 'GET'):
        data = 'Major OMG'
        return jsonify({'data': data})
 

@app.route('/route', methods = ['GET'])
async def generate_route():
    # if 'file' not in request.files:
    #     return jsonify({"response": "failed"})
    # file = request.files['file']
    # if file.filename == '':
    #     return jsonify({"response": "failed"})
    # if file:
    #     filename = secure_filename(file.filename)
    #     file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))

    #     truck_route = find_route()

    #     return jsonify({"response": "success","output":truck_route})
    truck_route = await find_route()
    return jsonify({"response": "success","output":truck_route})


# main driver function
if __name__ == '__main__':
    app.run(debug=True)