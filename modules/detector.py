from ultralytics import YOLO
import cv2

class ObjectDetector:
    def __init__(self, model_path):
        # Load YOLOv8 Model
        self.model = YOLO(model_path)

    def detect(self, frame, conf_threshold):
        # Perform Inference
        results = self.model(frame, conf=conf_threshold, classes=[0], verbose=False) # Class 0 = Person
        
        detections = []
        # Extract bounding boxes
        for result in results:
            for box in result.boxes:
                x1, y1, x2, y2 = map(int, box.xyxy[0])
                w, h = x2 - x1, y2 - y1
                conf = float(box.conf[0])
                
                # Format: [left, top, w, h], confidence, class_class
                detections.append(([x1, y1, w, h], conf, 'person'))
                
        return detections