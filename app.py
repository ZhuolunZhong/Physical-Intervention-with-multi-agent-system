from flask import Flask, request
from flask_cors import CORS, cross_origin
import os
import json

import logging

app = Flask(__name__)
cors = CORS(app)
app.config['CORS_HEADERS'] = 'Content-Type'

cwd = os.getcwd()
dataFolder = 'participantData'

@app.route("/")
@cross_origin()
def hello_world():
  return "<p>Hello, World!</p>"

@app.route("/api", methods=['GET', 'POST'])
@cross_origin()
def api_call():
  if request.method == 'POST':
    request_data = request.get_json()
    # app.logger.info("REQUEST data: %s", request_data)

    response = {
      "message": "I received a POST request!",
      "request_data": request_data,
    }

    if 'workerId' in request_data.keys() and 'content' in request_data.keys():
      workerId = request_data['workerId']
      content = request_data['content']
      filePath = os.path.join(cwd, dataFolder, workerId+".jsonl")

      with open(filePath, 'a') as outputFile:
        outputFile.write(json.dumps(content) + "\n")

      response["message"] = "Data saved to file at " + filePath
      response["data_saved"] = content

    return response
  else:
    return "I received a GET request!"


if __name__ == "__main__":
  logging.basicConfig(filename='flask_error.log',level=logging.DEBUG)
  app.run(host="localhost", port=8123, debug=True)