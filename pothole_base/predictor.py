from __future__ import print_function

import os
import json
import pickle
import sys
import signal
import traceback
import flask
from flask import request

#0v1#  JC  Sept 10, 2018  

#NOTES:
#> See https://github.com/leongn/model_to_api/blob/master/container/sentiment_analysis/predictor.py
#> https://machine-learning-company.nl/deploy-machine-learning-model-rest-api-using-aws/

prefix = '/opt/ml/'
model_path = os.path.join(prefix, 'model')


#Watch instances of flask
#- swap to function over class
#VNN=Video_NN_Service()
from video_markup import flask_process_video


# The flask app for serving predictions
app = flask.Flask(__name__)

@app.route('/ping', methods=['GET'])
def ping():
    """Determine if the container is working and healthy. In this sample container, we declare
    it healthy if we can load the model successfully."""
    try:
        health=True #default ok
    except:
        health=None
    status = 200 if health else 404
    return flask.Response(response='\n', status=status, mimetype='application/json')

@app.route('/invocations', methods=['POST'])
def transformation():
    # "input"
    #    s3_bucket=''
    #    s3_source_filename=''
    #    live=

    input_json = request.get_json()
    print ("GIVEN RAW JSON: "+str(input_json))
    input_json = input_json['input']
    
    s3_source_filename=input_json.get('s3_source_filename')
    s3_bucket=input_json.get('s3_bucket','tests-road-damage')
    is_live=input_json.get('is_live',False)
    
    # Call service (run in background)
    if s3_source_filename:
        flask_process_video(s3_source_filename=s3_source_filename,s3_bucket=s3_bucket,is_live=is_live)


    # Transform predictions to JSON
    result = {'output': []}
    list_out = []
    result['output'] = list_out
    result = json.dumps(result)
    return flask.Response(response=result, status=200, mimetype='application/json')

@app.route('/debug', methods=['GET','POST'])
def debug():
    s3_source_filename='sagemaker/small_pot.mp4'
    s3_bucket='tests-road-damage'
    is_live=False

    flask_process_video(s3_source_filename=s3_source_filename,s3_bucket=s3_bucket,is_live=is_live)
#    VNN.process_video(source_filename=s3_source_filename,bucket_name=s3_bucket,is_live=is_live)

    # Transform predictions to JSON
    result = {'output': []}
    list_out = []
    for label in predictions:
        row_format = {'label': label}
        list_out.append(row_format)
    result['output'] = list_out
    result = json.dumps(result)
    return flask.Response(response=result, status=200, mimetype='application/json')

#debug#  app.run(host="127.0.0.1",port=5000,debug=True)






