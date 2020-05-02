import re
import os
import sys
import random
import math
import numpy as np
import scipy.misc
import cv2
import json
from moviepy.editor import VideoFileClip
from IPython.display import HTML
import logging

#import matplotlib
#import matplotlib.pyplot as plt
#import matplotlib.patches as patches
#import matplotlib.lines as lines
from matplotlib.patches import Polygon
import IPython.display
import colorsys

import boto3

#import coco
import csv
from PIL import Image
from pytesseract import *

sys.path.insert(0,'./pothole') #Relative import
import pothole
from mrcnn import utils
from mrcnn import visualize
from mrcnn.visualize import display_images
import mrcnn.model as modellib
from mrcnn.model import log



#0v1# JC Sept 9, 2018  Initial setup


#FIX FOR MULTITHREADED?
from keras import backend  #See get_session()
    #>https://github.com/keras-team/keras/issues/2397
    #tf#  import tensorflow as tf
    #tf#  global graph,model
    #tf#  graph = tf.get_default_graph()
    #tf#      #K.clear_session() 
            

# Root directory of the project
ROOT_DIR = os.getcwd()

# Config ENV
#######################
#import ConfigParser
import configparser as ConfigParser
#BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '.'))
Config = ConfigParser.ConfigParser()
Config.read(ROOT_DIR+"/settings.ini")
AWS_ACCESS_KEY_ID=Config.get('aws','AWS_ACCESS_KEY_ID')
AWS_SECRET_ACCESS_KEY=Config.get('aws','AWS_SECRET_ACCESS_KEY')
os.environ['AWS_ACCESS_KEY_ID'] = AWS_ACCESS_KEY_ID
os.environ['AWS_SECRET_ACCESS_KEY'] = AWS_SECRET_ACCESS_KEY


# Directory to save logs and trained model
MODEL_DIR = os.path.join(ROOT_DIR, "logs")

# Path to trained weights file
# Download this file and place in the root of your 
# project (See README file for details)
COCO_MODEL_PATH = os.path.join(ROOT_DIR, "pothole/mask_rcnn_pothole_0005.h5")

# Directory of images to run detection on
IMAGE_DIR = os.path.join(ROOT_DIR, "images")
config = pothole.PotholeConfig()

TEMP_DIR=ROOT_DIR+"/temp"


# Interface between Sagemaker caller/lambda and backend resources
#- extends flask predictor.py  (context request)
#- implements pothole-detection.ipynb


class InferenceConfig(config.__class__):
    # Set batch size to 1 since we'll be running inference on
    # one image at a time. Batch size = GPU_COUNT * IMAGES_PER_GPU
    GPU_COUNT = 1
    IMAGES_PER_GPU = 1

def process_image(image, RCNN_MODEL='',title="", figsize=(16, 16), ax=None):
    #> pass model through lambda call
    # NOTE: The output you return should be a color image (3 channel) for processing video below
    # you should return the final output (image with lines are drawn on lanes
    #results = VNN.RCNN_MODEL.detect([image], verbose=0)

    with backend.get_session().graph.as_default() as g:
        #model = load_model(MODEL_PATH)
        results = RCNN_MODEL.detect([image], verbose=0) #Throws error if threaded model
    r = results[0]
    
    boxes = r['rois']
    class_ids = r['class_ids']
    scores = r['scores']
    
    N = boxes.shape[0]

    # Show area outside image boundaries.
    font = cv2.FONT_HERSHEY_DUPLEX
    
    for i in range(N):
        class_id = class_ids[i]
        score = scores[i] if scores is not None else None
        label = 'pothole'
        
        y1, x1, y2, x2 = boxes[i]
        #cv2.rectangle(frame, (face_rect.left(),face_rect.top()), (face_rect.right(), face_rect.bottom()), (255,0,0), 3)
        cv2.rectangle(image, (x1, y1), (x2, y2), (255,0,0), 3)
            
        x = random.randint(x1, (x1 + x2) // 2)
        caption = "{} {:.3f}".format(label, score) if score else label
        cv2.putText(image, caption, (x1 + 6, y2 - 6), font, 0.5, (255, 255, 255), 1)
        
        im = Image.fromarray(image)
        text = image_to_string(im)
        data = GetCoordinates.GetDMS(text)
        height = y2-y1
        width = x2-x1
        area = width * height #in pixels, we don't know height and width of known reference to calculate pixels/inch
        if data:
            row = 'pothole' + ',' + str(area) + ',' + str(data) 
            rows.append(row)
    return image



def test_s3():
    branches=['upload']

    #Recall S3_Interface
    bucket_name='tests-road-damage'
    s3 = boto3.client( 's3', aws_access_key_id=AWS_ACCESS_KEY_ID, aws_secret_access_key=AWS_SECRET_ACCESS_KEY)
    
    if 'upload' in branches:
        local_filename="small_pot.mp4"
        target_filename="sagemaker/"+local_filename
        mb_size = os.path.getsize(local_filename) / 1e6
        print ("Uploading "+local_filename+" size: "+str(mb_size)+" MB...")
        s3.upload_file(local_filename, bucket_name, target_filename)
        
    if 'download' in branches:
        local_filename="delthis"
        source_filename="sagemaker/sage_handler.py"
        response = s3.get_object(Bucket=bucket_name,Key=source_filename)
        file_contents = response['Body'].read()
        print ("Loaded: "+str(file_contents))

    print ("DONE test_s3")
    return

def clip_movie():
    #https://zulko.github.io/moviepy/getting_started/videoclips.html
    filename='C:/scripts-18/sagemaker/pothole-master/samples/pothole/datasets/pothole/potholes_42_miles.mp4'
    clip1 = VideoFileClip(filename).subclip(55,58)
    clip1.write_videofile("small_pot.mp4") # the gif will have 30 fps
    return




class Video_NN_Service(object):
    def __init__(self):
        return
    
    def initialize(self):
        #GLOBAL MODEL
        config = InferenceConfig()
        # Create model object in inference mode.
        self.RCNN_MODEL = modellib.MaskRCNN(mode="inference", model_dir=MODEL_DIR, config=config)
        # Load weights trained on MS-COCO
        self.RCNN_MODEL.load_weights(COCO_MODEL_PATH, by_name=True)
        logging.info("Loaded weights...")
        return
    
    def _fetch_filenames(self,source_filename):
        global TEMP_DIR
        if not os.path.exists(TEMP_DIR):hard_fail=no_temp

        target_s3_filename=re.sub(r'\.(.{2,5})$',r'_output.\1',source_filename)
        temp_input_filename=TEMP_DIR+'/'+re.sub(r'.*\/','',source_filename)

        temp_output_filename=re.sub(r'\.(.{2,5})$',r'_output.\1',source_filename)
        temp_output_filename=TEMP_DIR+"/"+re.sub(r'.*\/','',temp_output_filename)
    
        return target_s3_filename,temp_input_filename,temp_output_filename

    def process_video(self,source_filename="sagemaker/small_pot.mp4",bucket_name='tests-road-damage',is_live=False):
        #Generic flow
        
        #Fetch and validate filename
        target_s3_filename,temp_input_filename,temp_output_filename=self._fetch_filenames(source_filename)

        self.s32temp(source_filename,temp_input_filename,bucket_name)
        
        if not is_live: #debug_force_short_clip:
            clip1 = VideoFileClip(temp_input_filename).subclip(0,0.01)      #read()    -- alternatively, via url
        else:
            clip1 = VideoFileClip(temp_input_filename)
        
        print ("loaded video clip duration: "+str(clip1.duration))
        print ("Writing video to temp: "+temp_output_filename)

        #white_clip = clip1.fl_image(process_image) #NOTE: this function expects color images!!s
        white_clip = clip1.fl_image(lambda image: process_image(image,RCNN_MODEL=self.RCNN_MODEL)) #NOTE: this function expects color images!!s
        white_clip.write_videofile(temp_output_filename, audio=False, bitrate="5000k")
                
        print ("Upload results to s3: "+target_s3_filename)
        self.temp2s3(temp_output_filename,target_s3_filename,bucket_name)
        
        if False:
            try: os.remove(temp_input_filename)
            except:pass
            try: os.remove(temp_output_filename)
            except:pass
        return
    
    def ping(self):
        return True
    def shutdown(self):
        #[] release model/memory
        return
    
    def s32temp(self,source_filename,temp_filename,bucket_name,use_cache=True):
        #Ideally not "in mem"
        #> VideoFileClip requires filename (otherwise url) -- but no file objects
        if not os.path.exists(temp_filename) or not use_cache:
            s3 = boto3.client( 's3', aws_access_key_id=AWS_ACCESS_KEY_ID, aws_secret_access_key=AWS_SECRET_ACCESS_KEY)
            print ("Downloading video clip: "+str(source_filename))
            video_source=s3.get_object(Bucket=bucket_name,Key=source_filename)['Body'] #StreamingBody then  #.read() for file byte string
            #Expects filename#  self.reader = FFMPEG_VideoReader(filename, pix_fmt=pix_fmt,
            fp=open(temp_filename,'wb')
            fp.write(video_source.read())
            fp.close()
        return

    def temp2s3(self,local_filename,target_filename,bucket_name):
        s3 = boto3.client( 's3', aws_access_key_id=AWS_ACCESS_KEY_ID, aws_secret_access_key=AWS_SECRET_ACCESS_KEY)
        mb_size = os.path.getsize(local_filename) / 1e6
        print ("Uploading "+local_filename+" size: "+str(mb_size)+" MB...")
        s3.upload_file(local_filename, bucket_name, target_filename)
        return

    
    
#Move out here because of multithreads

VNN=Video_NN_Service()
VNN.initialize()

def flask_process_video(s3_source_filename='',s3_bucket='',is_live=False):
    global VNN
    VNN.process_video(source_filename=s3_source_filename,bucket_name=s3_bucket,is_live=is_live)
    return


def run_process_video(source_filename="sagemaker/small_pot.mp4"):
    global VNN
    VNN=Video_NN_Service()
    VNN.initialize()
    VNN.process_video(source_filename=source_filename)
    VNN.shutdown()
    return

def test():
    dd='{"input": {"s3_source_filename" : "/sagemaker/small_pot.mp4", "s3_bucket" : "tests-road-damange", "is_live": false} }'
    dd=json.loads(dd)
    input_json = dd['input']
    print ("FO: "+str(input_json))

    return

if __name__=='__main__':
    branches=['clip_movie']
    branches=['test_s3']
    branches=['test']
    branches=['run_process_video']
    for b in branches:
        globals()[b]()














