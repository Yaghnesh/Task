import asyncio
import websockets
import base64
import json

async def send_data():
    # Read image and audio files in binary mode
    with open("image.jpg", "rb") as image_file:
        image_data = image_file.read()
    with open("audio.wav", "rb") as audio_file:
        audio_data = audio_file.read()
    with open("test.jpg","rb") as frame_file:
        frame_data=frame_file.read()

    # Convert to Base64
    image_data_base64 = base64.b64encode(image_data).decode('utf-8')
    audio_data_base64 = base64.b64encode(audio_data).decode('utf-8')
    frame_data_base64 = base64.b64encode(frame_data).decode('utf-8')

    # Prepare JSON payload
    data = json.dumps({"image": image_data_base64, "audio": audio_data_base64 ,"frame": frame_data_base64})

    # Connect to WebSocket server
    async with websockets.connect("ws://localhost:8765") as websocket:
        print("Connected to server")

        # Send data to the server
        await websocket.send(data)
        print("Data sent to server")

        # Receive results from the server
        response = await websocket.recv()
        results = json.loads(response)
        print(f"Transcript: {results['audio']}")
        print(f"Caption: {results['image']}")
        print(f"Coordinates:{results['coordinates']}")

asyncio.run(send_data())
