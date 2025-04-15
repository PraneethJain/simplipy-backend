#!/bin/bash

gcloud builds submit --tag gcr.io/simplipy/backend

gcloud run deploy simplipy-backend \
  --image gcr.io/simplipy/backend \
  --platform managed \
  --region asia-south1 \
  --allow-unauthenticated
