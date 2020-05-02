# Future Developements
![alt Full scale Product](https://s3.amazonaws.com/wildrydes-yash-chakka/Architecture_New.png)

# Architecture
![alt Minimum Viable Product](https://s3.amazonaws.com/wildrydes-yash-chakka/Architecture_Object_Detection.png)

# General Flow
![general flow](https://s3.amazonaws.com/wildrydes-yash-chakka/General_Flow.png)

# Video Output
![alt output](https://s3.amazonaws.com/tests-road-damage/Pothole.mp4)

# Pothole-deployments
Deployment environment for pothole detection system

# Sagemaker Deployment Notes

Deploying a custom machine learning package to sagemaker.
-	There are quite a few moving parts.  Lets go through the standard workflow.

# Docker Image
-	The key component is to get your setup to compile correctly with docker.
- Install Docker and test hello world example using `docker run hello-world` you should see "Hello from Docker!This message shows that    your installation appears to be working correctly."
-	Run the following standard commands to validate the setup locally:
-	`Docker build -t trial1 .` It will build the environment and download the large models
- `Docker run -p 80:8080 trial1 serve .` This will start the docker container locally. The [serve] program/command is run which starts the wsgi and predictor.py Flask handler.
•	Note: if you get an error “python\r” you may have a bad hard return in the serve file. Run “dos2unix serve” to repair it.
- `cd local_test` and run `./predict.sh`. This will past a standard test request to the docker container.  The input s3 filename will be downloaded and processed by the container.

With the above validated, you’re ready to deploy to sagemaker.

# Push docker to ECR
-	Setup your aws cli environment:  “aws configure” using your key and secret.
-	Ensure you have access to the ECR service (where you push docker).
-	Login to ecr:  “aws ecr get-login”..then run the response to create a login session
-	Run “./build_and_push.sh pothole-docker-image”
o	This does the same docker build as the local test above and then pushes the image to ECR.
o	“pothole-docker-image” can be any name of the container.
-	Log into ECR and note the id of the docker repository ie/ 588698724959.dkr.ecr.us-east-1.amazonaws.com/pothole_docker_image

# CREATE MODEL
-	Log into sagemaker and “create endpoint”
o	Create a new model
o	You’ll need to configure the “endpoint configuration” AND the “endpoint”
o	Once the endpoint is created… it will say “Creating”.  After about 10 minutes the model should be active.  You can see progress by going to the Cloudwatch logs.
	https://console.aws.amazon.com/cloudwatch/home?region=us-east-1#logEventViewer:group=/aws/sagemaker/Endpoints

# CREATE LAMBDA
-	Create a lambda function (ie/ CallPothole)
-	It should run when a new s3 object is place in the bucket.
-	You may need to give it access to access full control of sagemaker (IAMS policy).  This allows it to call the sagemaker_endpoint.
-	Copy and paste the lambda_handler.py script into the lambda editor.
-	Test event.  The lambda_handler.py has an s3 test event in the source code.  You can copy this into a “test” event for lambda.  It simulates an s3 file being placed.
-	Note:  The lambda will timeout after 3 seconds, but sagemaker will continue to run and will complete normally.
o	If wanted, you can add to lambda to send an alert/email once an *_output.mp4 file appears in the bucket.  Or, have a more sophisticated monitoring tool.

That’s it!
-	You can validate it’s running by placing a video file in the s3 bucket directory.  The lambda should see it, call sagemaker, which then processes the file and outputs it as:  input_filename_output.mp4

When ready to fully activate the system, change the lambda variable “is_live” from False to True.  False only processes 0.01s of video.  True processes the entire video but can potentially take ½ day.


# Potential issues or exceptions
-	Note: “server” file controls how many server workers there are.  This can typically be the number of CPUs.  For now, it’s hard coded at 2.  Meaning, it can process two concurrent videos at a time.  Though the exact performance requirements would need to be evaluated.
-	The multithreaded system causes some trouble with the RCNN model.  For this reason, it was necessary to secure the model session before use (see backend.get_session() in video_markup.py)
-	Note, the RCNN model.py file had a concurrency issue as well when creating a directory that may already exist.  This was the only changed needed to the ML library.
-	Parts(Cognito, SES) of the Above listed architecture hasn't been implemented as there weren't super critical, but for full security we definatelt need to implement them

