import asyncio
import websockets
import threading
import uuid
import json
import requests
import numpy as np
import cv2
from ultralytics import YOLO
import base64

# Dictionary to store the results for each session
session_results = {}

# Function to process audio and generate transcript
def process_audio(session_id, audio_base64):
    # Simulate API call to generate a transcript (replace with actual API call)
    url = "https://cloud.olakrutrim.com/v1/audio/transcriptions"
    payload = json.dumps({
    "file": audio_base64,
    "modelName": "openai/whisper-large-v3",
    "task": "transcribe",
    "language": "english",
    "temperature": 0,
    "responseFormat": "verbose_json"
    })
    headers = {
    'Content-Type': 'application/json',
    'Authorization': 'eet39ADKPg1NS_TdeB1UPaNx4VPwOx'
    }

    response = requests.post(url, headers=headers, data=payload)
    response_json = response.json()
    transcript = response_json.get("predictions", {}).get("text", "Transcript not found")
    print(f"[{session_id}] Transcript generated: {transcript}")
    # Store the result in the session_results dictionary
    session_results[session_id]["audio"] = transcript

# Function to process image and generate caption
def process_image(session_id, image_base64):
    # Simulate API call to generate a caption (replace with actual API call)
    # Create the payload with the Base64 string
    image_base64_url = f"data:image/jpeg;base64,{image_base64}"
    payload = json.dumps({
        "input": {
            "image": image_base64_url,
            "prompt": "What does this image contain?"
        }
    })
    # Define the API endpoint URL
    url = "http://206.1.53.52:8080/predictions"
    # Set the headers
    headers = {
        'Content-Type': 'application/json'
    }
    # Make the API request
    response = requests.post(url, headers=headers, data=payload)
    # Convert the response to JSON
    response_json = response.json()
    # Access the 'output' variable from the JSON response
    caption = response_json.get("output", "Output not found")
    print(f"[{session_id}] Caption generated: {caption}")
    # Store the result in the session_results dictionary
    session_results[session_id]["image"] = caption
def process_frame(session_id,frame_data_base64):
    modelYolo = YOLO("yolov8n.pt")
    classes = [0]
    frame_data = base64.b64decode(frame_data_base64)
    np_arr = np.frombuffer(frame_data, np.uint8)

    # Decode to OpenCV format
    frame = cv2.imdecode(np_arr, cv2.IMREAD_COLOR)

    # Convert BGR to RGB format (YOLO expects RGB)
    frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    results=modelYolo(frame_rgb,classes=classes)
    person_coords = []
    for detection in results[0].boxes.xyxy:
        person_coords.append(detection.tolist())
    print(f"[{session_id}] coordinates: {person_coords}")
    # Store the result in the session_results dictionary
    session_results[session_id]["coordinates"] = person_coords

async def handle_client(websocket, path):
    print("Client connected")
    
    try:
        # Wait for the client to send data
        data = await websocket.recv()
        # Parse the incoming data
        incoming_data = json.loads(data)
        image_data_base64 = incoming_data["image"]
        audio_data_base64 = incoming_data["audio"]
        frame_data_base64 = incoming_data["frame"]

        # Generate a unique session ID
        session_id = str(uuid.uuid4())
        print(f"Session ID: {session_id}")

        # Initialize session data
        session_results[session_id] = {"audio": None, "image": None , "coordinates": None}

        # Create and start threads for parallel processing
        audio_thread = threading.Thread(target=process_audio, args=(session_id, audio_data_base64))
        #image_thread = threading.Thread(target=process_image, args=(session_id, image_data_base64))
        frame_thread = threading.Thread(target=process_frame, args=(session_id,frame_data_base64))
        audio_thread.start()
        #image_thread.start()
        frame_thread.start()

        # Wait for both threads to finish
        audio_thread.join()
        #image_thread.join()
        frame_thread.join()
        # Send results back to the client
        #print(session_results)
        await websocket.send(json.dumps(session_results[session_id]))

    except websockets.ConnectionClosed as e:
        print(f"Client disconnected: {e}")

# Start the WebSocket server
async def main():
    async with websockets.serve(handle_client, "localhost", 8765):
        print("WebSocket server started on ws://localhost:8765")
        await asyncio.Future()  # Run forever

asyncio.run(main())
