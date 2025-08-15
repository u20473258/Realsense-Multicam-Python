import os
import pandas as pd
import cv2
import cv2.aruco as aruco
import numpy as np

from edge_computer import EdgeComputer
from syncer import Syncer

class Calibrator:
    """
    Class of calibrator objects. Each calibrator will find the tranformation matrices for each edge given 
    edge computer.
    """
    
    def __init__(self, edge_computers: list, folder_path: str, board_params: dict):
        """
        Constructor.
        
        Parameters
        ----------
        edge_computers : list
            The list of edge computers whose images will be synced.
        folder_path : str
            The folder path containing data to be calibrated.
        board_params : dict
            The parameters of the ChArUco board to be used for calibration:
            - aruco_dictionary: The dictionary of ArUco markers used in the ChArUco board.
            - vertical_squares: The number of vertical squares in the ChArUco board.
            - horizontal_squares: The number of horizontal squares in the ChArUco board.
            - square_size: The size of each square in the ChArUco board.
            - marker_length: The length of the markers in the ChArUco board.
        
        Returns
        ----------
        calibrator : Calibrator
            A Calibrator object.
        """
        
        self.edge_computers = edge_computers
        self.folder_path = folder_path
        self.board_params = board_params
        
        # Create a folder for the synced data
        self.calibration_folder = os.path.join(folder_path, f"calibration_data")
        os.makedirs(self.calibration_folder, exist_ok=True)
        
        # Create a Syncer object to synchronize the data
        self.syncer = Syncer(edge_computers, folder_path, "colour", threshold=30)
        
        # Calibrate the cameras
        self.transformations = self.calibrate()
        
        
    def create_board(self, board_params):
        """
        Creates a calibration board for the cameras.
        
        Returns
        ----------
        board : object
            The calibration board object.
        """
        
        ARUCO_DICTIONARY = board_params['aruco_dictionary']
        SQUARES_HORIZONTALLY = board_params['horizontal_squares']
        SQUARES_VERTICALLY = board_params['vertical_squares']
        SQUARE_LENGTH = board_params['square_size']
        MARKER_LENGTH = board_params['marker_length']
        
        # Create an ArUco dictionary
        charuco_dict = aruco.getPredefinedDictionary(ARUCO_DICTIONARY)
        
        # Create a ChArUco board
        board = aruco.CharucoBoard((SQUARES_HORIZONTALLY, SQUARES_VERTICALLY), SQUARE_LENGTH, MARKER_LENGTH, charuco_dict)
        
        return charuco_dict, board
    
    
    def get_camera_intrinsics(self,):
        """
        Gets the intrinsics of each edge computer's camera and stores it in a numpy array
        in a specific format:
        
        [[fx, 0, ppx], [0, fy, ppy], [0, 0, 1]]
        
        Parameters
        ----------
        frameset : list
            The frameset containing the images to be used for calibration.
        
        Returns
        ----------
        camera_matrix : list
            A list of the camera intrinsics for each edge computer.
        dist_coeffs : np.ndarray
            The distortion coefficients for each edge computer.
        """
        
        # Get the distortion coefficients for each edge computer (All cameras are assumed to have 
        # the same distortion coefficients)
        distCoeffs = np.zeros((5, 1), dtype=np.float32)
        
        # Get the intrinsics for each edge computer
        intrinsics = [edge_computer.load_cam_intrinsics() for edge_computer in self.edge_computers]
        
        # Store the intrinsics in a numpy array
        camera_matrix = [np.zeros((len(self.edge_computers), 3, 3), dtype=np.float32)] * len(self.edge_computers)
        for i, intrinsics in enumerate(intrinsics):
            camera_matrix[i][0, 0] = intrinsics[0]
            camera_matrix[i][1, 1] = intrinsics[1]
            camera_matrix[i][0, 2] = intrinsics[2]
            camera_matrix[i][1, 2] = intrinsics[3]
            
        return camera_matrix, [distCoeffs] * len(self.edge_computers)
        
       
    def calibrate(self,) -> list:
        """
        Uses the pose of each camera with respect to the position of the ChArUco board to find the 
        transformation matrices between the cameras and the ChArUco board.
        
        Parameters
        ----------
        
        Returns
        ----------
        transformations : list
            A list of the transformations for each edge camera.
        """
        
        # Create a list to store the transformations
        transformations = []
        
        # Create calibration dictionary and board
        charuco_dict, board = self.create_board(self.board_params)
        
        # Get camera intrinsics
        camera_matrix, dist_coeffs = self.get_camera_intrinsics()
        
        # Get the framesets from the Syncer object
        framesets = self.syncer.get_median_frameset()
        
        # Find transformations (that transform the camera view to the board's view)
        for i, edge_computer in enumerate(self.edge_computers):
            # Load images
            image = edge_computer.load_image(framesets[i], greyscale=True)
            
            # Detect ArUco markers in the image
            corners, ids, rejectedImgPoints = aruco.detectMarkers(image, charuco_dict)

        
            if ids is not None:
                aruco.drawDetectedMarkers(image, corners, ids)
                
                # Interpolate ChArUco corners
                retval, charuco_corners, charuco_ids = cv2.aruco.interpolateCornersCharuco(
                    markerCorners=corners,
                    markerIds=ids,
                    image=image,
                    board=board
                )
                        
                if retval > 0:
                    aruco.drawDetectedCornersCharuco(image, charuco_corners, charuco_ids)
                
                    # Get the camera pose
                    valid, rvec, tvec = aruco.estimatePoseCharucoBoard(
                    charuco_corners, charuco_ids, board, camera_matrix[i], dist_coeffs[i], np.empty(1), np.empty(1), False
                    )
                
                    if valid:
                        image = cv2.drawFrameAxes(image, camera_matrix[i], dist_coeffs[i], rvec, tvec, 0.05)
                        
                        R, _ = cv2.Rodrigues(rvec)
                        T = np.eye(4)
                        T[:3, :3] = R
                        T[:3, 3] = tvec.flatten()
                        
                        transformations.append(np.linalg.inv(T))
            
        return transformations