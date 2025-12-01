import cv2
import numpy as np
import math
from collections import deque

class AnalyticsEngine:
    def __init__(self, width, height):
        self.track_history = {}  # Stores path of each ID
        self.width = width
        self.height = height
        # Heatmap Canvas (Float32 for accumulation)
        self.heatmap_accumulator = np.zeros((height, width), dtype=np.float32)
        
        # State
        self.is_panic = False
        self.avg_velocity = 0.0
        self.occupancy = 0

    def process_behavior(self, tracks, panic_threshold):
        current_speeds = []
        self.occupancy = len(tracks)

        for track in tracks:
            track_id = track.track_id
            ltrb = track.to_ltrb() # Left, Top, Right, Bottom
            
            # Calculate Centroid
            cx = int((ltrb[0] + ltrb[2]) / 2)
            cy = int((ltrb[1] + ltrb[3]) / 2)

            # 1. Manage Velocity History
            if track_id not in self.track_history:
                self.track_history[track_id] = deque(maxlen=10)
            
            self.track_history[track_id].append((cx, cy))

            # 2. Calculate Velocity (Displacement per frame)
            if len(self.track_history[track_id]) > 2:
                prev_x, prev_y = self.track_history[track_id][-2]
                # Euclidean distance
                speed = math.hypot(cx - prev_x, cy - prev_y)
                current_speeds.append(speed)

            # 3. Update Heatmap (Add intensity at centroid)
            try:
                # Create a Gaussian splash at the centroid position
                y_grid, x_grid = np.ogrid[0:self.height, 0:self.width]
                mask = (x_grid - cx)**2 + (y_grid - cy)**2 <= 15**2
                self.heatmap_accumulator[mask] += 0.5 # Add heat
            except:
                pass

        # 4. Determine Panic State
        if len(current_speeds) > 0:
            self.avg_velocity = np.mean(current_speeds)
            if self.avg_velocity > panic_threshold:
                self.is_panic = True
            else:
                self.is_panic = False
        else:
            self.avg_velocity = 0.0
            self.is_panic = False

        return self.is_panic, self.avg_velocity

    def get_heatmap_overlay(self, frame):
        # Normalize heatmap to 0-255
        heatmap_norm = cv2.normalize(self.heatmap_accumulator, None, 0, 255, cv2.NORM_MINMAX)
        heatmap_img = np.uint8(heatmap_norm)
        
        # Apply Color Map (Blue to Red)
        heatmap_color = cv2.applyColorMap(heatmap_img, cv2.COLORMAP_JET)
        
        # Overlay on original frame
        return cv2.addWeighted(frame, 0.6, heatmap_color, 0.4, 0)