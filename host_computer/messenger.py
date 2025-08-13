import os
import shutil
import socket
import time
from flask import Flask, request, jsonify
import argparse

# Initialise flask server
app = Flask(__name__)

# Store commands
CAPTURE_MESSAGE = {1: "CAPTURE_1s",
                   2: "CAPTURE_2s",
                   5: "CAPTURE_5s",
                   10: "CAPTURE_10s",
                   15: "CAPTURE_15s",
                   20: "CAPTURE_20s",
                   25: "CAPTURE_25s",
                   30: "CAPTURE_30s",
                   60: "CAPTURE_60s",
                   100: "CAPTURE_100s"}

SETUP_MESSAGE = "SETUP_DEVICE"

REBOOT_MESSAGE = "REBOOT"   


def broadcast_message(message: str) -> None:  
    """
    Broadcasts a message to all devices in the network.
    
    Parameters
    ----------
    message : str
        The message to broadcast.
    """
    
    # Broadcast address to send to all devices in the subnet
    BROADCAST_IP = "192.168.249.255"
    
    # Port to broadcast on
    PORT = 5005

    # Create a UDP socket
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
    
    # Broadcast the message
    try:
        sock.sendto(message.encode(), (BROADCAST_IP, PORT))
        print(f"Broadcast message sent: {message}")
        time.sleep(5)  # Wait for a short time to ensure the message is sent
                
    except KeyboardInterrupt:
        print("Broadcasting stopped.")
    finally:
        sock.close()


@app.route('/uploads', methods=['POST'])
def upload_file():
    """
    Runs the flask server.
    """
    if 'file' not in request.files:
        return jsonify({"error": "No file part in the request"})
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({"error": "No file selected"})

    # Save the uploaded file in the uploads directory
    file_path = os.path.join(app.config['UPLOAD_FOLDER'], file.filename)
    file.save(file_path)
    
    return jsonify({"message": f"File {file.filename} saved at {file_path}"})


def receive_files():
    """
    Receives the files sent from the edge computers. A flask server is created and the program
    waits for files from the pis. The server is terminated by inputting: Ctrl + C, into the 
    terminal.
    """
    
    # Delete previous uploads folder and then create a new one
    UPLOAD_FOLDER = './uploads'
    if os.path.exists(f"uploads"):
        shutil.rmtree(UPLOAD_FOLDER)
    os.makedirs(UPLOAD_FOLDER, exist_ok=True)
    
    # Tell which folder to use
    app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
    
    # Start Flask server
    app.run(host='0.0.0.0', port=5000)



if __name__ == "__main__":
    
    # Create argument parser
    parser=argparse.ArgumentParser(prog="Messenger", 
                                   description="Sends messages to edge computer(s) over the network.")
    
    # Get the mode of operation, mandatory argument
    parser.add_argument("mode", 
                        choices=['capture', 'setup', 'reboot'],
                        type=str,
                        help="Mode of operation: 'capture' to capture images, 'setup' to setup edge computers: ensure NTP and serial numbers, 'reboot' to reboot the edge computers.")
    
    # Get the folder name to save the captured data
    parser.add_argument("--folder_name", 
                        type=str, 
                        default="uploads", 
                        help="Name of the folder to save the captured data.")
    
    # Get the duration of capture
    parser.add_argument("--duration", 
                        choices=['1', '2', '5', '10', '15', '20', '25', '30', '60', '100'], 
                        type=int, 
                        default=5, 
                        help="Duration of capture in seconds.")
    
    # Parse the arguments
    args=parser.parse_args()
    
    # Mode handling
    if args.mode == 'capture':
        # Broadcast the capture message
        broadcast_message(CAPTURE_MESSAGE[args.duration])
        print(f"Capture command sent for {args.duration} seconds.")
    elif args.mode == 'setup':
        # Broadcast the setup message
        broadcast_message(SETUP_MESSAGE)
        print(f"Setup command sent.")  
    elif args.mode == 'reboot':
        # Send reboot message
        broadcast_message(REBOOT_MESSAGE)
        print("Reboot command sent to edge computers.")
        exit(0) 
    else:
        print("Invalid mode. Use 'capture', 'setup', or 'reboot'.")
        exit(0)   
        
    # Receive the images from the edge computers
    print("Waiting for files from edge computers...")
    receive_files()
    
    # Rename uploads folder
    os.rename("uploads", args.filename)
        
