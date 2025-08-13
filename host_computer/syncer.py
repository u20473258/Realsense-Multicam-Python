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
        