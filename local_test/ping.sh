#!/bin/bash

payload=$1
content=${2:-application/json}

curl -vX GET http://localhost:8081/ping
