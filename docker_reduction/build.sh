#!/bin/bash
set -x
set -e
# TODO move this to instead use $1 and $2, or if not available default to the autoreduction docker repo!
USERNAME=dtasev
TAG=latest

echo $USERNAME
docker build -f DevDB.Dockerfile -t $USERNAME/mysql_autoreduction:$TAG ..