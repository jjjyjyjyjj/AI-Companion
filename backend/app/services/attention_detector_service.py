"""
Attention Detector Service
Extracts the core detection logic from attention_detector.py for use in the backend API
"""
import cv2
import numpy as np
import threading
import time
from typing import Optional, Tuple


class AttentionDetectorService:
    """Service for detecting user attention using OpenCV"""
    
    def __init__(self):
        self.cap = None
        self.running = False
        self.detection_thread = None
        self.current_status = "Unknown"
        self.current_percentage = 0
        self.is_attentive = False
        self.last_update_time = 0
        
        # OpenCV classifiers
        self.face_cascade = cv2.CascadeClassifier(
            cv2.data.haarcascades + 'haarcascade_frontalface_default.xml'
        )
        self.eye_cascade = cv2.CascadeClassifier(
            cv2.data.haarcascades + 'haarcascade_eye.xml'
        )
    
    def start_detection(self) -> bool:
        """Start attention detection"""
        if self.running:
            return True
        
        try:
            # Initialize webcam
            self.cap = cv2.VideoCapture(0)
            if not self.cap.isOpened():
                print("Error: Could not open webcam")
                return False
            
            # Set camera resolution
            self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
            self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
            
            self.running = True
            self.current_status = "Starting"
            self.current_percentage = 0
            self.is_attentive = False
            
            # Start detection thread
            self.detection_thread = threading.Thread(target=self._detection_loop, daemon=True)
            self.detection_thread.start()
            
            return True
        except Exception as e:
            print(f"Error starting detection: {e}")
            self.running = False
            return False
    
    def stop_detection(self):
        """Stop attention detection"""
        self.running = False
        
        if self.cap:
            self.cap.release()
            self.cap = None
        
        self.current_status = "Stopped"
        self.current_percentage = 0
        self.is_attentive = False
    
    def _detection_loop(self):
        """Main detection loop running in background thread"""
        while self.running:
            if self.cap is None or not self.cap.isOpened():
                time.sleep(0.1)
                continue
            
            ret, frame = self.cap.read()
            if not ret:
                time.sleep(0.1)
                continue
            
            # Detect attention
            is_attentive, score, _ = self.detect_attention(frame)
            
            # Update state
            self.is_attentive = is_attentive
            self.current_percentage = min(100, max(0, int(score)))
            self.current_status = "Paying Attention" if is_attentive else "Not Paying Attention"
            self.last_update_time = time.time()
            
            time.sleep(0.1)  # ~10 FPS
    
    def detect_attention(self, frame) -> Tuple[bool, float, np.ndarray]:
        """
        Detect if person is paying attention
        
        Returns:
            Tuple of (is_attentive, attention_score, processed_frame)
        """
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        
        # Detect faces
        faces = self.face_cascade.detectMultiScale(gray, 1.3, 5)
        
        if len(faces) == 0:
            return False, 0, frame  # No face detected
        
        # Get the largest face (assuming it's the main person)
        largest_face = max(faces, key=lambda rect: rect[2] * rect[3])
        x, y, w, h = largest_face
        
        # Region of Interest for eyes
        roi_gray = gray[y:y+h, x:x+w]
        
        # Detect eyes
        eyes = self.eye_cascade.detectMultiScale(roi_gray, 1.1, 3)
        
        # Calculate attention metrics
        eye_count = len(eyes)
        
        # Face position and size (center and size relative to frame)
        frame_height, frame_width = frame.shape[:2]
        face_center_x = x + w // 2
        face_center_y = y + h // 2
        
        # Check if face is centered (within 30% of center)
        center_threshold = 0.3
        x_center_offset = abs(face_center_x - frame_width // 2) / (frame_width // 2)
        y_center_offset = abs(face_center_y - frame_height // 2) / (frame_height // 2)
        
        # Face size (should be reasonable, not too small or too large)
        face_area = w * h
        frame_area = frame_width * frame_height
        face_ratio = face_area / frame_area
        
        # Calculate attention based on multiple factors
        factors = {
            'face_detected': 30,  # Base score for having a face
            'face_centered_x': 0,
            'face_centered_y': 0,
            'eyes_detected': 0,
            'face_size': 0
        }
        
        # Face centered score (x-axis)
        if x_center_offset < center_threshold:
            factors['face_centered_x'] = 25
        elif x_center_offset < 0.5:
            factors['face_centered_x'] = 15
        
        # Face centered score (y-axis)
        if y_center_offset < center_threshold:
            factors['face_centered_y'] = 20
        elif y_center_offset < 0.5:
            factors['face_centered_y'] = 10
        
        # Eyes detected score
        if eye_count >= 2:
            factors['eyes_detected'] = 25
        elif eye_count == 1:
            factors['eyes_detected'] = 10
        
        # Face size score (optimal size is around 10-30% of frame)
        if 0.05 < face_ratio < 0.40:
            factors['face_size'] = 10
        elif 0.02 < face_ratio < 0.50:
            factors['face_size'] = 5
        
        attention_score = sum(factors.values())
        
        # Determine if paying attention (threshold: 60%)
        is_attentive = attention_score >= 60
        
        return is_attentive, attention_score, frame
    
    def get_status(self) -> dict:
        """Get current attention detection status"""
        return {
            "is_attentive": self.is_attentive,
            "attention_percentage": self.current_percentage,
            "status": self.current_status,
            "running": self.running,
            "last_update": self.last_update_time
        }


# Create singleton instance
attention_detector_service = AttentionDetectorService()

