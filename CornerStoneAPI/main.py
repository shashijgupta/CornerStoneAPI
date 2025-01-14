import requests
from typing import Tuple
import CornerStoneAPI.utils as utils
from datetime import datetime, timedelta
from fastapi.responses import JSONResponse
from pytz import timezone
import json
from fastapi import APIRouter, HTTPException

router = APIRouter()

# Configuration for authentication
AUTH_URL_INT = "https://auth-integration.servicetitan.io/connect/token"
AUTH_URL = "https://auth.servicetitan.io/connect/token"
CLIENT_ID = "cid.g4y7nxozzkzfjamb8dttxh9xj"  # Replace with your client ID
CLIENT_SECRET = "cs1.hp5lbxkaeuznsr0rpnrpldo8gj347rmp7t1rq0ngsoj3q91jom"  # Replace with your client secret
TENANT_ID = 488267682
APP_ID = "ak1.huv221jqp2ky1gsaspj857kjf"


# Function to generate access token: https://developer.servicetitan.io/docs/get-going-first-api-call/
async def get_access_token():
    try:
        response = requests.post(
            AUTH_URL,
            headers={"Content-Type": "application/x-www-form-urlencoded"},
            data={"grant_type": "client_credentials", "client_id": CLIENT_ID, "client_secret": CLIENT_SECRET},
        )
        if response.status_code == 200:
            token_data = response.json()
            return token_data.get("access_token")
        else:
            raise HTTPException(status_code=response.status_code, detail=f"Authentication failed: {response.text}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get access token: {str(e)}")


# Create new customer in system: https://developer.servicetitan.io/api-details/#api=tenant-crm-v2&operation=Customers_Create&definition=Crm.V2.Customers.CustomerAddress
@router.post("/create-customer/")
async def create_customer(customer: utils.CustomerCreateRequest) -> Tuple[str, str]:

    url = f"https://api.servicetitan.io/crm/v2/tenant/{TENANT_ID}/customers"

    # Replace these placeholders with actual token and app key
    access_token = await get_access_token()
    headers = {
        "Authorization": access_token,
        "ST-App-Key": APP_ID,
        "Content-Type": "application/json",
    }

    try:
        # customer.locations.address.street_name = customer.street_name
        # customer.locations.address.city = customer.city
        # customer.locations.address.zip_code = customer.zip_code
        customer.locations.address.state = "NH"
        customer.locations.address.country = "USA"
        customer.locations.name = "Home"
        payload = customer.model_dump(by_alias=True)
        payload["locations"] = [payload["locations"]]
        payload["address"] = customer.locations.address.model_dump()
        response = requests.post(url, headers=headers, json=payload)
        if response.status_code == 200:
            data = response.json()
            customer_id = data.get("id")
            location_id = data.get("locations")[0].get("id")
            return (customer_id, location_id)
        raise HTTPException(
            status_code=response.status_code,
            detail=f"Failed to create customer: {response.text}",
        )
    except requests.RequestException as e:
        raise HTTPException(status_code=500, detail=f"Request error: {str(e)}")


# Main API endpoint: https://developer.servicetitan.io/api-details/#api=tenant-dispatch-v2&operation=Capacity_GetList
@router.post("/get-available-slots/")
async def get_available_slots(availabilityRequest: utils.getAvailableSlotsToolRequest):
    start_time = availabilityRequest.args.start_time
    jobTypeId = availabilityRequest.args.jobTypeId
    
    # Calculate end datetime skipping weekends
    start_datetime = datetime.strptime(start_time, "%Y-%m-%d %H:%M")
    remaining_hours = 36  # 2160 minutes = 36 hours
    end_datetime = start_datetime

    while remaining_hours > 0:
        end_datetime += timedelta(hours=1)
        # Skip if it's weekend (5 = Saturday, 6 = Sunday)
        if end_datetime.weekday() not in [5, 6]:
            remaining_hours -= 1
            
    end_time = end_datetime.strftime("%Y-%m-%d %H:%M")

    access_token = await get_access_token()
    intervals = utils.generate_intervals(start_time, end_time)

    external_api_url = f"https://api.servicetitan.io/dispatch/v2/tenant/{TENANT_ID}/capacity"
    headers = {
        "Authorization": access_token,
        "ST-App-Key": APP_ID,
        "Content-Type": "application/json",
    }

    available_slots = []
    # Iterate over intervals and call the external API
    for interval in intervals:
        payload = {
            "startsOnOrAfter": start_time,  # interval["starttime"],
            "endsOnOrBefore": end_time,  # interval["endtime"],
            # "businessUnitIds": [
            #     1097
            # ],  # get business unit list: https://developer.servicetitan.io/api-details/#api=tenant-settings-v2&operation=BusinessUnits_GetList
            "jobTypeId": jobTypeId,
            "skillBasedAvailability": True,
        }
        response = requests.post(external_api_url, json=payload, headers=headers)

        if response.status_code == 200:
            data = response.json()
            availabilities = data.get("availabilities")
            print("Len of availabilities: ", len(availabilities))
            for slot in availabilities:
                print("start: ", slot["start"], "end: ", slot["end"])
                print(slot)
                if slot["isAvailable"]:
                    print("slots are available")
                    # if previous_slot and previous_slot["endtime"] == interval["starttime"]:
                    #     # Extend the previous slot's end time
                    #     previous_slot["endtime"] = interval["endtime"]
                    # else:
                    # # Add a new slot
                    #     previous_slot = interval
                    available_slot = {
                        "starttime": slot["start"],
                        "endtime": slot["end"]
                    }
                    available_slots.append(available_slot)
                # Ensure Service Length Fits:
                # Filter out slots that don’t meet the required service duration (e.g., 30 minutes).

        else:
            raise HTTPException(
                status_code=response.status_code,
                detail=f"External API call failed with status code {response.status_code}: {response.text}",
            )
        break

    # Return available slots in string format
    return {"available_slots": available_slots}


@router.post("/create-job/")
async def create_job(job_request: utils.jobCreateToolRequest):
    job_request = job_request.args

    # Convert UTC times to EST
    est = timezone('US/Eastern')
    start_time = datetime.fromisoformat(job_request.jobStartTime).astimezone(est).strftime('%Y-%m-%dT%H:%M:%S%z')
    end_time = datetime.fromisoformat(job_request.jobEndTime).astimezone(est).strftime('%Y-%m-%dT%H:%M:%S%z')

    url = f"https://api.servicetitan.io/jpm/v2/tenant/{TENANT_ID}/jobs"
    access_token = await get_access_token()

    headers = {
        "Authorization": access_token,
        "ST-App-Key": APP_ID,
        "Content-Type": "application/json",
    }

    try:
        customer_id, location_id = await create_customer(job_request.customer)
        payload = {
            "customerId": customer_id,
            "locationId": location_id,
            "jobTypeId": job_request.jobTypeId,
            "priority": "Normal",
            "businessUnitId": 3619517,
            "campaignId": 82014707,
            "appointments": [
                {
                    "start": start_time,
                    "end": end_time,
                    "arrivalWindowStart": start_time,
                    "arrivalWindowEnd": end_time,
                    # "technicianIds": [0],
                }
            ],
            "scheduledDate": datetime.now().strftime("%Y-%m-%d"),
            "scheduledTime": datetime.now().strftime("%H:%M"),
        }
        response = requests.post(url, headers=headers, json=payload)
        if response.status_code == 200:
            return {"status": "Job request booked"}
        else:
            raise HTTPException(
                status_code=response.status_code,
                detail=f"External API call failed with status code {response.status_code}: {response.text}",
            )
    except requests.exceptions.HTTPError as http_err:
        raise HTTPException(
            status_code=response.status_code,
            detail=f"HTTP error occurred: {http_err}",
        )
    except Exception as err:
        raise HTTPException(
            status_code=500,
            detail=f"An error occurred: {err}",
        )
