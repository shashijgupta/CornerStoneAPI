from datetime import datetime, timedelta
from fastapi import HTTPException
from pydantic import BaseModel, Field, ConfigDict
from typing import List, Optional, Any


class ToolRequest(BaseModel):
    event: Optional[str] = None
    data: Optional[Any] = None
    args: Any


# Helper function to generate 15-minute intervals
def generate_intervals(start_time: str, end_time: str):

    try:
        start_dt = datetime.strptime(start_time, "%Y-%m-%d %H:%M")
        end_dt = datetime.strptime(end_time, "%Y-%m-%d %H:%M")
        intervals = []
        while start_dt < end_dt:
            interval_end = start_dt + timedelta(minutes=15)
            if interval_end > end_dt:
                break
            intervals.append(
                {"starttime": start_dt.strftime("%Y-%m-%d %H:%M"), "endtime": interval_end.strftime("%Y-%m-%d %H:%M")}
            )
            start_dt = interval_end
        return intervals
    except ValueError as e:
        raise HTTPException(status_code=400, detail="Invalid date format. Use 'YYYY-MM-DD HH:MM'.")


class Address(BaseModel):
    street: Optional[str] = "1003 W Clark St"
    city: Optional[str] = "Urbana"
    zip: Optional[str] = "61801"

    model_config = ConfigDict(
        extra='allow',
    )



class Location(BaseModel):
    name: str
    address: Address


class CustomerCreateRequest(BaseModel):
    name: str = Field(default="Vanshika", description="Name of the customer")
    type: Optional[str] = "Residential"
    locations: Location = Field(..., description="Locations for the customer")
    


class JobCreateRequest(BaseModel):
    customer: CustomerCreateRequest
    # customerId: int
    # locationId: int
    # jobTypeId: int = Field(default=1, description="ID of the job type")
    jobStartTime: str = Field(
        default=(datetime.now() + timedelta(hours=5)).strftime("%Y-%m-%d %H:%M"),
        description="Scheduled date in YYYY-MM-DD format",
    )
    jobEndTime: str = Field(
        default=(datetime.now() + timedelta(hours=5, minutes=15)).strftime("%Y-%m-%d %H:%M"),
        description="Scheduled date in YYYY-MM-DD format",
    )
    # scheduledDate: str = Field(
    #     default=datetime.now().strftime("%Y-%m-%d"), description="Scheduled date in YYYY-MM-DD format"
    # )
    # scheduledTime: str = Field(default=datetime.now().strftime("%H:%M"), description="Scheduled time in HH:MM format")
    # summary: str = Field(..., description="Summary of the job")
    # description: str = Field(..., description="Detailed description of the job")

class jobCreateToolRequest(ToolRequest):
    args: JobCreateRequest

class getAvailableSlotsRequest(BaseModel):
    start_time: str
    # end_time: str

class getAvailableSlotsToolRequest(ToolRequest):
    args: getAvailableSlotsRequest
    