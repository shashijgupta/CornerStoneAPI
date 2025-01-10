from fastapi import FastAPI, HTTPException
import requests
from typing import Tuple
from datetime import datetime, timedelta
from fastapi.responses import JSONResponse
from pytz import timezone
import json

app = FastAPI()

from CornerStoneAPI.main import router as service_titan_router
from workiz.main import router as workiz_router

app.include_router(service_titan_router)
app.include_router(workiz_router)
