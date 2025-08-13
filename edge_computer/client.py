import os
import shutil
import socket
import subprocess
import requests
import time
                          
# Set constants
FPS = 15  # Frames per second for the camera
CLIENT_NAME = socket.gethostname() # Get and store the name of the edge computer
HOST_IP = "192.168.249.155" # Store IP address of the host computer


def create_file_directories():
    """
    Deletes previously captured data, if any, and creates new file directories for 
    the new data.
    """
    
    # Checkes if directories exist
    if os.path.exists(f"colour"):
        shutil.rmtree(f"colour")
    if os.path.exists(f"depth"):
        shutil.rmtree(f"depth")
    if os.path.exists(f"colour_metadata"):
        shutil.rmtree(f"colour_metadata")
    if os.path.exists(f"depth_metadata"):
        shutil.rmtree(f"depth_metadata")
    
    # Creates new directories for the camera data       
    os.makedirs(f"colour", exist_ok=True)
    os.makedirs(f"depth", exist_ok=True)
    os.makedirs(f"colour_metadata", exist_ok=True)
    os.makedirs(f"depth_metadata", exist_ok=True)
    
    
def wait_for_command_from_host() -> str:
    """
    Waits for broadcast message from the host computer.
    
    Returns
    ----------
    message : str
        The message received from the host computer.
    """
    
    # Port to listen on
    PORT = 5005
    
    # Max size for incoming messages
    BUFFER_SIZE = 1024

    # Create a UDP socket for listening
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    
    # Bind to all interfaces
    sock.bind(("", PORT))

    print(f"Listening for broadcast messages on port {PORT}...")
    
    # Initialise empty message
    message = "empty"
    
    # Wait until command is received
    command_not_received = True
    while command_not_received:
        # Get data from the socket
        data, addr = sock.recvfrom(BUFFER_SIZE)
        
        # If no data is received, continue waiting
        if not data:
            print("No data received, waiting for command...")
            continue
        # Else, decode the data and strip any whitespace
        else:
            message = data.decode().strip()
            command_not_received = False
            
            print(f"Received message: {message} from {addr}")
            
        sock.close()
        print("Socket closed.")
    
    return message
    

def capture(duration: int):
    """
    Capture a num_frames amount of frames using capture script.
    
    Parameters
    ----------
    duration : int
        The actual duration of capture in seconds.
    """
    
    # Convert num frames to an integer
    total_frames = str(duration * FPS)
    
    try:
        arguments = [total_frames, CLIENT_NAME]
        subprocess.run(["./capture"] + arguments, check=True)
        print("Capture " + total_frames + " frames (" + str(duration) + "s) complete successfully.")
    except subprocess.CalledProcessError as e:
        print(f"Error executing Python script: {e}")


def get_serial_number():
    """
    Get the serial number of the connected D455.
    """
    
    # Delete previous serial number file, if it exists
    filename = CLIENT_NAME + "_serial.txt"
    if os.path.exists(filename):
        os.remove(filename)
    
    try:
        print("Getting serial number...")
        subprocess.run("rs-enumerate-devices -s >> " + filename, shell=True, check=True)
    except subprocess.CalledProcessError as e:
        print(f"Error getting serial number: {e}")
    

def ensure_ntp_running():
    """
    Ensure that NTP is running on the system.
    """
    
    try:
        print("Running NTP...")
        subprocess.run("sudo ntpdate " + HOST_IP, shell=True, check=True)
        print("NTP is running.")
    except subprocess.CalledProcessError as e:
        print(f"Error running NTP: {e}")


def reboot_system():
    """
    Reboot the raspberry pi.
    """
    
    try:
        print("Rebooting system...")
        subprocess.run(["sudo", "reboot"], check=True)
    except subprocess.CalledProcessError as e:
        print(f"Error rebooting system: {e}")
     

def send_serial_to_host():
    """ 
    Use HTTP REST API POST command to send serial number to host computer.
    """

    # Address to send the files
    url = "http://" + HOST_IP + ":5000/uploads"
    
    filename = CLIENT_NAME + "_serial.txt"
    # Ensure it's a file
    if os.path.isfile(filename):
        with open(filename, "rb") as file:
            # Send the file with its original name
            file = {"file": (filename, file)}
            response = requests.post(url, files=file)
            
            # Print response
            print(f"Uploaded {filename}: {response.status_code} - {response.text}")


def send_data_to_host():
    """ 
    Use HTTP REST API POST command to send all captured data to host computer.
    """

    # Address to send the files
    url = "http://" + HOST_IP + ":5000/uploads"

    # List of file paths to send
    folder_paths_to_Send = [
        f"colour",
        f"depth",
        f"colour_metadata",
        f"depth_metadata"
    ]

    for folder_path in folder_paths_to_Send:
        for filename in os.listdir(folder_path):
            file_path = os.path.join(folder_path, filename)
            
            # Ensure it's a file
            if os.path.isfile(file_path):
                with open(file_path, "rb") as file:
                    # Send the file with its original name
                    files = {"file": (filename, file)}
                    response = requests.post(url, files=files)
                    
                    # Print response
                    print(f"Uploaded {filename}: {response.status_code} - {response.text}")
                


if __name__ == "__main__":
      
    # Create file directories, deleting any previous data (if any)
    create_file_directories()  
      
    while(True):
        
        message = wait_for_command_from_host()
        
        # Message handling
        if message == "SETUP_DEVICE":
            get_serial_number()
            ensure_ntp_running()
            send_serial_to_host()
            
        else:
            if message == "CAPTURE_1s":
                capture(1)
                
            elif message == "CAPTURE_2s":
                capture(2)
                
            elif message == "CAPTURE_5s":
                capture(5)
                
            elif message == "CAPTURE_10s":
                capture(10)
                
            elif message == "CAPTURE_15s":
                capture(15)
                
            elif message == "CAPTURE_20s":
                capture(20)
                
            elif message == "CAPTURE_25s":
                capture(25)
                
            elif message == "CAPTURE_30s":
                capture(30)
                
            elif message == "CAPTURE_60s":
                capture(60)
                
            elif message == "CAPTURE_100s":
                capture(100)
                            
            elif message == "REBOOT":
                reboot_system()
                
            else:
                print(f"Unknown command: {message}")
                continue
            
            send_data_to_host()
            
            # Wait for a short time to ensure the data is sent
            time.sleep(2)
            
            # Print confirmation message
            print("Data sent to host computer.")
