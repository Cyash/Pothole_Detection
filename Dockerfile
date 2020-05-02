# Build an image that can do training and inference in SageMaker
# This is a Python 2 image that uses the nginx, gunicorn, flask stack
# for serving inferences in a stable way.

FROM ubuntu:16.04

#FOR GPU:
#option 1/   nvidia/cuda:8.0-cudnn6-runtime-ubuntu16.04
#option 2/  (smile case)#  FROM nvidia/cuda:9.0-base-ubuntu16.04
#option 3/  for docker gpu on local cpu:  github.com/NVIDIA/nvidia-docker

#**always run apt-get update with next command to fix caching issues
RUN apt-get update && apt-get install -y unzip
#libgcc option
RUN apt-get install -y --no-install-recommends \
         wget \
         python3.5 \
         nginx \
         ca-certificates \
         libgcc-5-dev \
    && rm -rf /var/lib/apt/lists/*


#For cv2:
RUN apt-get update && apt-get install -y libxrender1 libsm6 libglib2.0 libxext6 
#For matlabplot:
RUN apt-get install -y python3-tk
RUN apt-get install -y vim


#Python
RUN wget https://bootstrap.pypa.io/3.3/get-pip.py && python3.5 get-pip.py
RUN pip3 install --upgrade pip


#https://medium.com/smileinnovation/sagemaker-bring-your-own-algorithms-719dd539607d
#cuda-command-line-tools-9<96>0
#cuda-cublas-dev-9<96>0
#cuda-cudart-dev-9<96>0
#cuda-cufft-dev-9<96>0
#cuda-curand-dev-9<96>0
#cuda-cusolver-dev-9<96>0
#cuda-cusparse-dev-9<96>0
#libcudnn7=7.0.5.15<96>1+cuda9.0
#libcudnn7-dev=7.0.5.15<96>1+cuda9.0


#?Both tensorflows?
#So, what I did is to detect if the <93>import<94> of tensorflow raises an exception. 
#If it does, I uninstall <93>tensorflow-gpu<94> and install 
#<93>tensorflow<94> at the Docker container startup. 
#It results in a few more seconds to start up the instance, but this 
#<93>hack<94> is working perfectly fine in this scenario. I<92>m pretty sure 
#there are other ways to do it, feel free to comment if you have one in your mind.

#std pothole requirements.txt
RUN pip3 install tensorflow>=1.5.1
#GPU - requires blas libs etc#  RUN pip3 install tensorflow-gpu>=1.5.1
RUN pip3 install keras>=2.0.8
RUN pip3 install numpy
RUN pip3 install scipy
RUN pip3 install Pillow
RUN pip3 install cython
RUN pip3 install matplotlib
RUN pip3 install scikit-image
RUN pip3 install opencv-python
RUN pip3 install h5py
RUN pip3 install imgaug
RUN pip3 install IPython[all]
RUN pip3 install moviepy
RUN pip3 install pytesseract

RUN pip3 install flask gevent gunicorn
RUN pip3 install boto3
RUN pip3 install configparser
RUN pip3 install imageio


# Set some environment variables. PYTHONUNBUFFERED keeps Python from buffering our standard
# output stream, which means that logs can be delivered to the user quickly. PYTHONDONTWRITEBYTECODE
# keeps Python from writing the .pyc files which are unnecessary in this case. We also update
# PATH so that the train and serve programs are found when the container is invoked.

ENV PYTHONUNBUFFERED=TRUE
ENV PYTHONDONTWRITEBYTECODE=TRUE
ENV PATH="/opt/program:${PATH}"

#OTHER ENV options:
#zero#  ENV MODELS_PATH=/opt/ml/model

# Set up the program in the image
COPY pothole_base /opt/program

RUN chmod +x /opt/program/train /opt/program/serve

RUN wget https://tests-road-damage.s3.amazonaws.com/sagemaker/mask_rcnn_pothole_0005.h5
RUN mv mask_rcnn_pothole_0005.h5 /opt/program/pothole

# install ffmpeg from imageio.
RUN python3.5 -c "import imageio; imageio.plugins.ffmpeg.download()"

#add soft link so that ffmpeg can executed (like usual) from command line
RUN ln -s /root/.imageio/ffmpeg/ffmpeg.linux64 /usr/bin/ffmpeg

WORKDIR /opt/program

#set default python version to 3.5
RUN touch ~/.bash_aliases \
	  && echo alias python=\'python3.5\' > ~/.bash_aliases
RUN alias python=python3.5