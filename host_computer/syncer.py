import os
import pandas as pd
from edge_computer import EdgeComputer

class Syncer:
    """
    Class of syncer objects. Each syncer is responsible for synchronizing the image data 
    in the folder path assigned to it. Each syncer will only sync one type of data (either depth 
    or colour).
    """
    
    def __init__(self, edge_computers: list, folder_path: str, data_type: str, threshold: int, delete_unsynced: bool = True):
        """
        Constructor.
        
        Parameters
        ----------
        edge_computers : list
            The list of edge computers whose images will be synced.
        folder_path : str
            The folder path containing data to be synced.
        data_type : str
            The type of data to be synced, either "depth" or "colour".
        threshold : int
            The maximum Time of Arrival (ToAt) allowed between frames for them to be considered
            closely-matching.
        delete_unsynced : bool
            If True, unsynced data will be deleted after syncing. Default is True.
        
        Returns
        ----------
        syncer : Syncer
            A Syncer object.
        """
        
        self.edge_computers = edge_computers
        self.folder_path = folder_path
        self.data_type = data_type
        self.delete_unsynced = delete_unsynced
        self.threshold = threshold
        
        # Create a folder for the synced data
        self.synced_folder = os.path.join(folder_path, f"synced_{data_type}")
        os.makedirs(self.synced_folder, exist_ok=True)
        
        # Sync the data
        self.framesets = self.synchronise()
        
        
    def synchronise(self,):
        """
        Uses the Time of Arrival timestamps (ToAt) of the frame metadata to find framesets
        (closely-matching frames) for the data collected from the given edge computers.
        
        Parameters
        ----------
        
        Returns
        ----------
        """
        
        # Create an empty list to store the framesets
        framesets = []
        
        # Create a list to store the current frame number index for each edge computer
        current_frame_numbers = [0] * len(self.edge_computers)
        
        # Boolean to check if all edge computers have frames to sync
        all_edge_computers_have_frames = True
        
        # Loop until just one edge computer has no more frames to match
        while all_edge_computers_have_frames:
            
            # Initialise the reference edge computer information
            ref_edge_computer = self.edge_computers[0]
            ref_ToAt = ref_edge_computer.extract_ToAt_from_file(self.data_type, ref_edge_computer.get_frame_number(current_frame_numbers[0], self.data_type))
            ref_edge_computer_index = 0
            
            # Find the reference edge computer i.e edge computer with the largest ToAt
            for i in range(1, len(self.edge_computers)):
                curr_edge_computer = self.edge_computers[i]
                curr_ToAt = curr_edge_computer.extract_ToAt_from_file(self.data_type, ref_edge_computer.get_frame_number(current_frame_numbers[i], self.data_type))
                
                if curr_ToAt > ref_ToAt:
                    ref_edge_computer = curr_edge_computer
                    ref_ToAt = curr_ToAt
                    ref_edge_computer_index = i
        
            # Find closely-matching frames for the reference edge computer
            curr_frameset = [0] * len(self.edge_computers)
            curr_frameset[ref_edge_computer_index] = ref_edge_computer.get_frame_numbers(self.data_type)
            
            
            search_terminated = False
            for i in range(len(self.edge_computers)):
                # Skip the reference edge computer
                if i == ref_edge_computer_index:
                    continue
                else:
                    # Get the current edge computer and its ToAt
                    curr_edge_computer = self.edge_computers[i]
                    curr_ToAt = curr_edge_computer.extract_ToAt_from_file(self.data_type, ref_edge_computer.get_frame_number(current_frame_numbers[i], self.data_type))
                    
                    # Find a matching frame within the threshold for the current edge computer
                    continue_search = True
                    found_matching_frame = False
                    while continue_search:
                        
                        # If the current ToAt is within the threshold, store the frame number
                        if abs(curr_ToAt - ref_ToAt) < self.threshold:
                            # Store the frame number in the current frameset
                            curr_frameset[i] = curr_edge_computer.get_frame_number(current_frame_numbers[i], self.data_type)
                            
                            # Increment the current frame number index for this edge computer to exclude this frame from future searches
                            current_frame_numbers[i] += 1
                            
                            # Terminate the search for this edge computer
                            continue_search = False
                            
                            # Found a matching frame, so set the flag
                            found_matching_frame = True
                            
                        else:
                            # If the current ToAt is larger than the reference one, stop searching
                            if curr_ToAt > ref_ToAt:
                                # Terminate the search for this edge computer
                                continue_search = False
                                
                                # Increment the current frame number index for this edge computer
                                current_frame_numbers[i] += 1
                            
                            else:
                                # Check if there are more frames to check for this edge computer
                                if current_frame_numbers[i] < curr_edge_computer.get_total_num_frames(self.data_type) - 1:
                                    # Increment the current frame number index for this edge computer
                                    current_frame_numbers[i] += 1
                                    curr_ToAt = curr_edge_computer.extract_ToAt_from_file(self.data_type, ref_edge_computer.get_frame_number(current_frame_numbers[i], self.data_type))
                                else:
                                    # No more frames to check, stop searching
                                    continue_search = False
                    
                    if not found_matching_frame:
                        # If no matching frame was found, increment the current frame number index for the reference edge computer and terminate the search
                        current_frame_numbers[ref_edge_computer_index] += 1
                        search_terminated = True
                        break
            
            # Check if there is a valid frameset i.e. all edge computers have a frame number in the current frameset
            if not search_terminated:
                # If a valid frameset was found, add it to the list of framesets
                framesets.append(curr_frameset)
                
                # Increment the current frame number index for the reference edge computer
                current_frame_numbers[ref_edge_computer_index] += 1
                
            # Check if any edge computer has no frames to search
            for i in range(len(self.edge_computers)):
                if current_frame_numbers[i] >= self.edge_computers[i].get_total_num_frames(self.data_type):
                    all_edge_computers_have_frames = False
        
        return framesets
    
    
    def get_frameset(self, frameset_index: int) -> list:
        """
        Returns the frameset at the given index.
        
        Parameters
        ----------
        frameset_index : int
            The index of the frameset to return.
        
        Returns
        ----------
        frameset : list
            The frameset at the given index.
        """
        
        if frameset_index < 0 or frameset_index >= len(self.framesets):
            raise IndexError("Frameset index out of range.")
        elif len(self.framesets) == 0:
            raise ValueError("No framesets available.")
        else:
            # Return the frameset at the given index
            return self.framesets[frameset_index]
    
    
    def get_median_frameset(self,) -> list:
        """
        Returns the middle frameset.
        
        Parameters
        ----------
        frameset_index : int
            The index of the frameset to return.
        
        Returns
        ----------
        frameset : list
            The frameset at the given index.
        """
        
        if len(self.framesets) == 0:
            raise ValueError("No framesets available.")
        else:
            frameset_index = len(self.framesets) // 2
            if len(self.framesets) % 2 == 0:
                frameset_index -= 1
        
        return self.framesets[frameset_index]