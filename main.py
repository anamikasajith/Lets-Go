import sqlite3
import os

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from groq import Groq
from dotenv import load_dotenv
import uvicorn

# -----------------------------
# Load Environment Variables
# -----------------------------
load_dotenv()

# -----------------------------
# Groq Client
# -----------------------------
client = Groq(
    api_key=os.getenv("GROQ_API_KEY")
)

# -----------------------------
# FastAPI App
# -----------------------------
app = FastAPI()

# Templates & Static Files
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

templates = Jinja2Templates(
    directory=os.path.join(BASE_DIR, "templates")
)

app.mount(
    "/static",
    StaticFiles(directory=os.path.join(BASE_DIR, "static")),
    name="static"
)

# -----------------------------
# SQLite Database
# -----------------------------
conn = sqlite3.connect("travelmate.db", check_same_thread=False)
cursor = conn.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS trips(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    destination TEXT,
    days INTEGER,
    budget INTEGER,
    itinerary TEXT
)
""")

conn.commit()

# -----------------------------
# Request Models
# -----------------------------
class TripRequest(BaseModel):
    destination: str
    days: int
    budget: int


class PackingRequest(BaseModel):
    destination: str
    season: str
    days: int


# -----------------------------
# Frontend Homepage
# -----------------------------
@app.get("/home", response_class=HTMLResponse)
def homepage(request: Request):
    return templates.TemplateResponse(
        "index.html",
        {"request": request}
    )


# -----------------------------
# API Home
# -----------------------------
@app.get("/")
def home():
    return {
        "message": "Welcome to TravelMate AI"
    }


# -----------------------------
# AI Trip Planner
# -----------------------------
@app.post("/plan-trip")
def plan_trip(data: TripRequest):

    prompt = f"""
    Create a detailed travel itinerary.

    Destination: {data.destination}
    Number of Days: {data.days}
    Budget: ₹{data.budget}

    Include:
    - Day-by-day itinerary
    - Tourist attractions
    - Local food recommendations
    - Budget-saving tips
    """

    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[
            {
                "role": "user",
                "content": prompt
            }
        ]
    )

    itinerary = response.choices[0].message.content

    cursor.execute(
        "INSERT INTO trips(destination, days, budget, itinerary) VALUES(?,?,?,?)",
        (
            data.destination,
            data.days,
            data.budget,
            itinerary
        )
    )

    conn.commit()

    return {
        "destination": data.destination,
        "days": data.days,
        "budget": data.budget,
        "itinerary": itinerary
    }


# -----------------------------
# AI Packing List
# -----------------------------
@app.post("/packing-list")
def packing_list(data: PackingRequest):

    prompt = f"""
    Create a travel packing checklist.

    Destination: {data.destination}
    Season: {data.season}
    Days: {data.days}

    Include:
    - Clothing
    - Travel essentials
    - Electronics
    - Medicines
    """

    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[
            {
                "role": "user",
                "content": prompt
            }
        ]
    )

    return {
        "packing_list": response.choices[0].message.content
    }


# -----------------------------
# View All Trips
# -----------------------------
@app.get("/trips")
def get_trips():

    cursor.execute("SELECT * FROM trips")

    trips = cursor.fetchall()

    return {
        "saved_trips": trips
    }


# -----------------------------
# Search Trips
# -----------------------------
@app.get("/search-trip/{destination}")
def search_trip(destination: str):

    cursor.execute(
        "SELECT * FROM trips WHERE destination=?",
        (destination,)
    )

    trips = cursor.fetchall()

    return {
        "results": trips
    }


# -----------------------------
# Delete Trip
# -----------------------------
@app.delete("/delete-trip/{trip_id}")
def delete_trip(trip_id: int):

    cursor.execute(
        "DELETE FROM trips WHERE id=?",
        (trip_id,)
    )

    conn.commit()

    return {
        "message": "Trip deleted successfully"
    }


# -----------------------------
# Run App
# -----------------------------
if __name__ == "__main__":
    uvicorn.run(
        app,
        host="127.0.0.1",
        port=8000
    )