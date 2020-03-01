#!/bin/bash

if [ "$OSTYPE" == "msys" ]; then
  NGROK="winpty ngrok"
else
  NGROK="ngrok"
fi

$NGROK start --all --config=./ngrok-trustee.yml --log=stdout
