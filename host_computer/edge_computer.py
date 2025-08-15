import os
import pandas as pd
import cv2
import numpy as np

class EdgeComputer:
    """
    Class of edge computer objects. Each edge computer has an Intel RealSense D455 camera
    attached to it.
    """
    
    def __init__(self, edge_computer_name: str, serial_number: int, folder_path: str):
        """
        Constructor.
        
        Parameters
        ----------
        edge_computer_name : str
            The name of the edge computer this object represents.
        serial_number : int
            The serial number of the attached D455 camera.
        folder_path : str
            The folder path containing data collected.
        
        Returns
        ----------
        edge computer : edge_computer
            An edge_computer object.
        """
        
        self.edge_computer_name = edge_computer_name
        self.serial_number = serial_number
        self.folder_path = folder_path
        
        self.camera_intrinsics = self.load_cam_intrinsics()
        self.total_num_depth_frames = self.calculate_total_num_frames("depth")
        self.total_num_colour_frames = self.calculate_total_num_frames("colour")
        self.depth_frame_numbers = self.extract_all_frame_numbers("depth")
        self.colour_frame_numbers = self.extract_all_frame_numbers("colour")
        
        
    def __eq__(self, other) -> bool:
        """
        Checks if two edge computer objects are equal.
        
        Parameters
        ----------
        other : edge_computer
            The other edge computer object to compare with.
        
        Returns
        ----------
        bool : bool
            True if the two edge computer objects are equal, False otherwise.
        """
        
        return (self.edge_computer_name == other.edge_computer_name and 
                self.serial_number == other.serial_number and 
                self.folder_path == other.folder_path)
        
        
    def __str__(self,) -> str:
        """
        Returns a string representation of the edge computer object.
        
        Returns
        ----------
        str : str
            A string representation of the edge computer object.
        """
        return f"Edge Computer: {self.edge_computer_name}, Serial Number: {self.serial_number}, Folder Path: {self.folder_path}"
    
    
    def __repr__(self,) -> str:
        """
        Returns a string representation of the edge computer object for debugging.
        
        Returns
        ----------
        str : str
            A string representation of the edge computer object for debugging.
        """
        return f"edge_computer(edge_computer_name={self.edge_computer_name}, serial_number={self.serial_number}, folder_path={self.folder_path})"
    
    
    def get_edge_computer_name(self,) -> str:
        return self.edge_computer_name
    
    
    def get_serial_number(self,) -> int:
        return self.serial_number
    
    
    def get_total_num_frames(self, data_type: str) -> int:
        if data_type == "depth":
            return self.total_num_depth_frames
        else:
            return self.total_num_colour_frames
    
    
    def get_frame_numbers(self, data_type: str) -> list:
        if data_type == "depth":
            return self.depth_frame_numbers
        else:
            return self.colour_frame_numbers
    
    
    def get_frame_number(self, frame_number_index: int, data_type: str) -> int:
        return self.depth_frame_numbers[frame_number_index] if data_type == "depth" else self.colour_frame_numbers[frame_number_index]
    
    
    def load_cam_intrinsics(self,) -> tuple:
        """
        Loads the camera instrinsics from a .txt file.
        
        Returns
        ----------
        intrinsics : list
            A list of the intrinsics paremeters for the D455 camera connected to 
            this edge computer (fx, fy, ppx, ppy).
        """
    
        # Open the frame_metadata csv
        df = pd.read_csv("camera_intrinsics.csv")
        
        # Search for the correct row
        row_num = 0
        while True:
            if df.loc[row_num, "serial_number"] == self.serial_number:
                break
            else:
                row_num += 1
                        
        return ( df.loc[row_num, "fx"], df.loc[row_num, "fy"], df.loc[row_num, "ppx"], df.loc[row_num, "ppy"] ) 
    
    
    def calculate_total_num_frames(self, data_type: str) -> int:
        """
        Counts the number of frames, of the given data type, captured by the edge computer.
        
        Parameters
        ----------
        data_type : str
            The data type of the frames to count.
        
        Returns
        ----------
        total_num_frames : int
            Total number of frames for collected by the edge computer.
        """
        
        num_frames = 0
        # Store the filename to use when search directory
        filename = ""
        filename += self.edge_computer_name
        
        # Search for depth frames
        if data_type == "depth":
            filename += "_depth"
            
            # Get all the filenames in the directory and loop through them
            for root, dirs, files in os.walk(self.folder_path):
                for file in files: 
                    # Count only the .raw files that match the filename 
                    if file.count(filename) != 0 and file.endswith('.raw'):
                        num_frames += 1
                        
        # Search for colour frames
        else:
            filename += "_colour"
            
            # Get all the filenames in the directory and loop through them
            for root, dirs, files in os.walk(self.folder_path):
                for file in files: 
                    # Count only the .png files that match the filename 
                    if file.count(filename) != 0 and file.endswith('.png'):
                        num_frames += 1
                            
        return num_frames
            
            
    def extract_frame_number(self, filename: str) -> int:
        """
        Extracts the frame number from a given filename.
        
        Parameters
        ----------
        filename : str
            The name of the file to extract the frame number from.
        
        Returns
        ----------
        frame_number : int
            The extracted frame number.
        """
        
        # Split file names based on the _ separator
        split1 = filename.split("_")
        
        # The 3rd item in the first split will be <fnum>.png or <fnum>.raw. Split again using . as separator
        split2 = split1[2].split(".")
        
        # Convert the frame number to an integer
        frame_number = int(split2[0])
        
        return frame_number
    
        
    def extract_all_frame_numbers(self, data_type: str) -> list:
        """
        Extracts all the frame numbers of a given data type for thie edge computer
        in the given folder path. The algorithm uses the file naming convention:
        
        - Colour images: <edge_computer_name>_colour_<fnum>.png
        - Depth images: <edge_computer_name>_depth_<fnum>.raw 
        
        to extract the frame numbers.
        
        Parameters
        ----------
        data_type : str
            The data type of the frame numbers to extract.
        
        Returns
        ----------
        frame_numbers : list
            A list of the frame numbers for the edge computer.
        """
                
        # Scan directory and get an iterator
        obj = os.scandir(self.folder_path)
        
        frame_numbers = []        
        num_frames = self.total_num_depth_frames if data_type == "depth" else self.total_num_colour_frames
        # Loop through each file
        for file in obj:
            # Check if we have already gotten all frame numbers
            if len(frame_numbers) == num_frames:
                break
            
            # Check if the file is for the correct raspi and the file is not metadata
            if (file.name).find(self.edge_computer_name) != -1 and (file.name).find("metadata") == -1:
                
                # Check if the file is a colour image and if we are searching for colour images
                if (file.name).find("colour") != -1 and data_type == "colour":
                    
                    # Extract the frame number
                    frame_number = self.extract_frame_number(file.name)
                    
                    # Store the frame number in the list
                    frame_numbers.append(frame_number)
                    
                # Check if the file is a depth image and if we are searching for depth images
                elif (file.name).find("depth") != -1 and data_type == "depth":
                    
                    # Extract the frame number
                    frame_number = self.extract_frame_number(file.name)
                    
                    # Store the frame number in the list
                    frame_numbers.append(frame_number)
                    
                else:
                    continue
            else:
                continue
                
        # Close iterator
        obj.close()
        
        # Sort frame numbers
        frame_numbers.sort()
        
        return frame_numbers
    
    
    def get_filename(self, data_type: str, frame_number: int, is_metadata: bool = False) -> str:
        """
        Function that compiles the filename into a single string using given information.
        
        Parameters
        ----------
        data_type : str
            Data type of the file: colour or depth.
        frame_number : int
            Frame number of file.
        is_metadata : bool 
            Indicate if the file being extracted is metadata.
        
        Returns
        ----------
        framesets : list
            A list of framesets of closely-matching frames.
        """
        
        filename = self.folder_path + "/" + self.edge_computer_name + "_" + data_type
        frame_num = str(frame_number)
        
        if is_metadata:
            filename += "_metadata_" + frame_num + ".txt"
        else:
            if data_type == "colour":
                filename += "_" + frame_num + ".png"
            else:  
                filename += "_" + frame_num + ".raw"
        
        return filename
    
    
    def extract_ToAt_from_file(self, data_type: str, frame_number: int) -> int: 
        """
        Gets the Time of Arrival timestamp (ToAt) from a metadata file with the given .txt filename.

        Parameters
        ----------
        data_type : str
            Data type of the file: colour or depth.
        frame_number : int
            Frame number of file.
        
        Returns
        ----------
        ToAt : int
            Extracted ToAt.
        """
        
        filename = self.get_filename(data_type, frame_number, is_metadata=True)
        
        if data_type == "colour":
            # Open file and get line 9 (ToAt is always on line 7 of metadata for colour frames)
            with open(filename) as fp:
                for i, line in enumerate(fp):
                    if i == 6:
                        # Split line using comma
                        split = line.split(",")
                        
                        # The ToAt should be the second item in the list
                        return int(split[1])
        else:
            # Open file and get line 7 (ToAt is always on line 9 of metadata for depth frames)
            with open(filename) as fp:
                for i, line in enumerate(fp):
                    if i == 8:
                        # Split line using comma
                        split = line.split(",")
                        
                        # The ToAt should be the second item in the list
                        return int(split[1])
        
        return -1
    
    
    def load_image(self, frame_number: int, grayscale: bool = False):
        """
        Loads an image from the edge computer's folder path. Converts the image to grayscale if specified.
        
        Parameters
        ----------
        frame_number : int
            The frame number of the image to load.
        grayscale : bool
            If True, the image will be loaded in grayscale. Default is False.
        
        Returns
        ----------
        image : any
            The loaded image.
        """
        
        filename = self.get_filename("colour", frame_number)
        
        return cv2.imread(filename, cv2.IMREAD_GRAYSCALE if grayscale else cv2.IMREAD_COLOR)