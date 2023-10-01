#!/bin/sh
PORT=${PORT:-8000}
uvicorn --port $PORT api:app --reload
