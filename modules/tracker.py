from deep_sort_realtime.deepsort_tracker import DeepSort

class ObjectTracker:
    def __init__(self):
        # Initialize DeepSORT
        # max_age: IDs are kept for 30 frames even if lost (Occlusion Handling)
        self.tracker = DeepSort(max_age=30, n_init=2, nms_max_overlap=1.0)

    def update_tracks(self, detections, frame):
        # Update tracker with new detections
        tracks = self.tracker.update_tracks(detections, frame=frame)
        
        confirmed_tracks = []
        for track in tracks:
            if not track.is_confirmed():
                continue
            confirmed_tracks.append(track)
            
        return confirmed_tracks