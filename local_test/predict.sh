#!/bin/bash

payload=$1
content=${2:-application/json}

#curl -d @${payload} -H "Content-Type: ${content}" -vX POST http://localhost:8080/invocations
curl -XPOST -H "Content-Type: application/json" 'http://127.0.0.1:8081/invocations' -d '{"input": {"s3_source_filename" : "sagemaker/small_pot.mp4", "s3_bucket" : "tests-road-damage", "is_live": false} }'

