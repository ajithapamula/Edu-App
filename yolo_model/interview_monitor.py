import cv2
import numpy as np
from ultralytics import YOLO
import onnxruntime as ort
import torch
import time
from typing import Tuple, Optional
from torchvision import transforms
from ultralytics.utils import LOGGER

# Suppress YOLO logs
LOGGER.disabled = True

# Define constants
FRAME_WIDTH, FRAME_HEIGHT = 640, 480
NO_FACE_TIMEOUT = 15  # seconds for detecting user absence
SIDEWAYS_THRESHOLD = 15  # seconds for detecting sideways head orientation
FEAR_CONFIDENCE = 0.7
CHECK_INTERVAL = 10  # seconds for checking conditions

class FaceDetector:
    def __init__(self, model_path: str = r'yolo_model\yolov11n.pt', emotion_model_path: str = r'yolo_model\emotion-ferplus-12-int8.onnx'):
        self.device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
        
        # Load YOLOv11n for face and phone detection
        self.yolo_model = YOLO(model_path, task='detect')
        
        # Load emotion model for fear detection
        self.emotion_session = ort.InferenceSession(emotion_model_path, providers=['CUDAExecutionProvider', 'CPUExecutionProvider'])
        
        # Preprocessing for FER+ model (64x64 grayscale, normalized to [-1, 1])
        self.transform = transforms.Compose([
            transforms.ToPILImage(),
            transforms.Resize((64, 64)),
            transforms.Grayscale(num_output_channels=1),
            transforms.ToTensor(),
            transforms.Normalize(mean=[0.5], std=[0.5])
        ])
        
        # State tracking
        self.no_face_timer = 0
        self.last_face_time = time.time()
        self.sideways_timer = 0
        self.last_sideways_time = 0
        self.last_check_time = 0

    def preprocess_frame(self, frame: np.ndarray) -> np.ndarray:
        """Preprocess frame for FER+ emotion model."""
        input_tensor = self.transform(frame).numpy()
        return input_tensor  # Shape: [1, 64, 64]

    def detect_objects(self, frame: np.ndarray) -> Tuple[Optional[Tuple[int, int, int, int]], bool]:
        """Detect faces and phones using YOLOv11n."""
        results = self.yolo_model.predict(frame, imgsz=(FRAME_WIDTH, FRAME_HEIGHT), conf=0.5, device=self.device, verbose=False)
        boxes = results[0].boxes.xyxy.cpu().numpy()
        classes = results[0].boxes.cls.cpu().numpy()
        
        face_box = None
        phone_detected = False
        
        for box, cls in zip(boxes, classes):
            if cls == 0:  # Person (face)
                face_box = box
            elif cls == 67:  # Cell phone
                phone_detected = True
        
        return face_box, phone_detected

    def infer_emotion(self, face_roi: np.ndarray) -> bool:
        """Infer fear emotion using FER+ ONNX model."""
        input_tensor = self.preprocess_frame(face_roi)
        input_tensor = np.expand_dims(input_tensor, axis=0)  # Shape: [1, 1, 64, 64]
        outputs = self.emotion_session.run(None, {'Input3': input_tensor})[0]
        outputs = torch.from_numpy(outputs).to(self.device)
        fear_prob = outputs[0, 6]  # Fear is index 6 in FER+
        return fear_prob > FEAR_CONFIDENCE

    def detect_sideways(self, frame: np.ndarray, face_box: Tuple[int, int, int, int]) -> bool:
        """Detect if head is completely turned sideways."""
        x1, y1, x2, y2 = map(int, face_box)
        face_width = x2 - x1
        face_height = y2 - y1
        return face_width < 0.5 * face_height

    def process_frame(self, frame: np.ndarray):
        """Process frame every 10 seconds and output only on serious triggers."""
        current_time = time.time()
        
        # Check every 10 seconds
        if current_time - self.last_check_time < CHECK_INTERVAL:
            return
        
        self.last_check_time = current_time
        
        face_box, phone_detected = self.detect_objects(frame)
        
        # User presence
        if face_box is None:
            if current_time - self.last_face_time > NO_FACE_TIMEOUT:
                print("User not present")
                self.no_face_timer = current_time
            return
        
        self.last_face_time = current_time
        
        # Phone detection
        if phone_detected:
            print("Phone detected")
        
        x1, y1, x2, y2 = map(int, face_box)
        face_roi = frame[y1:y2, x1:x2]
        
        if face_roi.size == 0:
            return
            
        # Fear detection
        if self.infer_emotion(face_roi):
            print("User appears to be fearful")
        
        # Sideways detection
        if self.detect_sideways(frame, face_box):
            if self.last_sideways_time and current_time - self.last_sideways_time > SIDEWAYS_THRESHOLD:
                print("User is looking completely sideways")
            elif not self.last_sideways_time:
                self.last_sideways_time = current_time
        else:
            self.last_sideways_time = 0

if __name__ == "__main__":
    detector = FaceDetector()
    
    cap = cv2.VideoCapture(0)
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, FRAME_WIDTH)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, FRAME_HEIGHT)
    
    while True:
        ret, frame = cap.read()
        if not ret:
            print("Failed to capture frame")
            break
            
        detector.process_frame(frame)
        
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break
    
    cap.release()
    cv2.destroyAllWindows()