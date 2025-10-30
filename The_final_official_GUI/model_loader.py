import cv2
import numpy as np
from threading import Thread
from queue import Queue
import time


class ModelLoader:
    def __init__(self):
        self.model = None
        self.class_names = {}
        self.detection_queue = Queue(maxsize=1)
        self.result_queue = Queue(maxsize=1)
        self.is_processing = False
        self.processing_thread = None
        self.last_result = None
        self.use_mock = False

        try:
            from ultralytics import YOLO
            self.YOLO = YOLO
        except ImportError as e:
            print(f"YOLO import failed: {e}")
            self.use_mock = True

    def load_model(self, model_path='trained_model/best.pt'):
        if self.use_mock:
            print("Using mock detection")
            self.class_names = {0: 'Object'}
            return True

        try:
            print(f"Loading model from: {model_path}")
            self.model = self.YOLO(model_path)

            warmup_image = np.random.randint(0, 255, (160, 160, 3), dtype=np.uint8)
            _ = self.model(warmup_image, verbose=False, imgsz=160)

            if hasattr(self.model, 'names') and self.model.names:
                self.class_names = self.model.names
            else:
                self.class_names = {
                    0: 'Bin', 1: 'Bottle', 2: 'Keyboard', 3: 'Laptop',
                    4: 'Mouse', 5: 'Mug', 6: 'Notebook', 7: 'Pen',
                    8: 'Phone', 9: 'Stapler'
                }

            print("Model loaded successfully")
            return True

        except Exception as e:
            print(f"Model loading failed: {e}")
            self.use_mock = True
            self.class_names = {0: 'Object'}
            return True

    def predict_single(self, image):
        """Predict and return only the highest confidence detection"""
        if self.use_mock or self.model is None:
            return image, None

        try:
            results = self.model.predict(
                image,
                conf=0.25,
                imgsz=320,
                verbose=False,
                max_det=10,
                agnostic_nms=True
            )

            highest_confidence = 0
            best_detection = None

            if results and len(results) > 0:
                result = results[0]

                if hasattr(result, 'boxes') and result.boxes is not None:
                    # Find detection with highest confidence
                    for box in result.boxes:
                        confidence = float(box.conf[0])
                        if confidence > highest_confidence:
                            highest_confidence = confidence
                            class_id = int(box.cls[0])
                            class_name = self.class_names.get(class_id, f"Class_{class_id}")
                            best_detection = {
                                'class_name': class_name,
                                'confidence': confidence,
                                'class_id': class_id
                            }

                    # Plot only the highest confidence detection
                    if best_detection:
                        # Create a copy of original image
                        annotated_image = image.copy()

                        # Get the highest confidence box
                        for i, box in enumerate(result.boxes):
                            if float(box.conf[0]) == highest_confidence:
                                # Draw only this bounding box
                                x1, y1, x2, y2 = map(int, box.xyxy[0])
                                confidence = float(box.conf[0])
                                class_id = int(box.cls[0])
                                class_name = self.class_names.get(class_id, f"Class_{class_id}")

                                # Draw bounding box
                                color = (0, 255, 0)  # Green
                                cv2.rectangle(annotated_image, (x1, y1), (x2, y2), color, 2)

                                # Draw label
                                label = f"{class_name} {confidence:.2f}"
                                label_size = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.5, 2)[0]
                                cv2.rectangle(annotated_image, (x1, y1 - label_size[1] - 10),
                                              (x1 + label_size[0], y1), color, -1)
                                cv2.putText(annotated_image, label, (x1, y1 - 5),
                                            cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 2)
                                break

                        return annotated_image, best_detection

            return image, best_detection

        except Exception as e:
            print(f"Prediction error: {e}")
            return image, None

    def start_processing(self):
        self.is_processing = True
        self.processing_thread = Thread(target=self._process_queue, daemon=True)
        self.processing_thread.start()

    def stop_processing(self):
        self.is_processing = False
        if self.processing_thread:
            self.processing_thread.join(timeout=0.5)

    def _process_queue(self):
        while self.is_processing:
            try:
                frame = self.detection_queue.get(timeout=0.01)
                if frame is None:
                    break

                if self.use_mock:
                    display_frame = frame.copy()
                    cv2.rectangle(display_frame, (50, 50), (200, 200), (0, 255, 0), 2)
                    cv2.putText(display_frame, "Mock Detection", (60, 40),
                                cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
                    detection = {'class_name': 'Mock', 'confidence': 0.95}
                    self.last_result = (display_frame, detection)
                    if self.result_queue.empty():
                        self.result_queue.put((display_frame, detection))
                else:
                    results = self.model.predict(
                        frame,
                        conf=0.25,
                        imgsz=256,
                        verbose=False,
                        max_det=1,  # Only get top detection
                        agnostic_nms=True
                    )

                    detection = None
                    display_frame = frame.copy()

                    if results and len(results) > 0:
                        result = results[0]
                        if hasattr(result, 'boxes') and result.boxes is not None:
                            for box in result.boxes:
                                confidence = float(box.conf[0])
                                class_id = int(box.cls[0])
                                class_name = self.class_names.get(class_id, f"Class_{class_id}")
                                detection = {
                                    'class_name': class_name,
                                    'confidence': confidence,
                                    'class_id': class_id
                                }
                                break

                    self.last_result = (display_frame, detection)
                    if self.result_queue.empty():
                        self.result_queue.put((display_frame, detection))

            except:
                continue

    def predict_async(self, frame):
        if not self.is_processing:
            return frame, None

        if self.detection_queue.empty():
            try:
                self.detection_queue.put_nowait(frame)
            except:
                pass

        try:
            return self.result_queue.get_nowait()
        except:
            return self.last_result if self.last_result else (frame, None)