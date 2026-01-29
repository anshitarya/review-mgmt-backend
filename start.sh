#!/bin/bash
# Render deployment startup script
cd /opt/render/project/src
exec uvicorn app.main:app --host 0.0.0.0 --port $PORT --workers 1
