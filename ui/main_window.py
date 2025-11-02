import sys
import os
import cv2
import time
from PySide6.QtWidgets import (QMainWindow, QVBoxLayout, QHBoxLayout, QPushButton,
                               QLabel, QWidget, QTextEdit, QFrame, QFileDialog,
                               QMessageBox, QProgressBar)
from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QPixmap, QImage, QDragEnterEvent, QDropEvent, QFont

# Import from the same directory structure
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from model_loader import ModelLoader
from camera_handler import CameraThread
from file_processor import FileProcessor

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.model_loader = ModelLoader()
        self.camera_thread = CameraThread()
        self.file_processor = FileProcessor(self.model_loader)

        self.current_fps = 0
        self.is_camera_on = False
        self.last_detection_log = 0
        self.last_display_time = 0
        self.processing_files = False
        self.current_display_image = None
        self.last_camera_frame = None

        self.init_ui()
        self.connect_signals()
        self.load_model()

    def init_ui(self):
        """UI with right-side logger and camera below"""
        self.setWindowTitle("Office Object Detector")
        self.setGeometry(50, 30, 1400, 800)

        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        # Main horizontal layout
        main_layout = QHBoxLayout()
        main_layout.setContentsMargins(8, 8, 8, 8)
        main_layout.setSpacing(8)

        # Left side - Camera and controls
        left_widget = QWidget()
        left_layout = QVBoxLayout(left_widget)
        left_layout.setContentsMargins(0, 0, 0, 0)
        left_layout.setSpacing(8)

        # Controls header
        header_frame = QFrame()
        header_frame.setMaximumHeight(50)
        header_layout = QHBoxLayout(header_frame)
        header_layout.setContentsMargins(5, 5, 5, 5)

        # Camera controls
        self.start_btn = QPushButton("Start Camera")
        self.start_btn.setFixedSize(120, 35)
        self.start_btn.setStyleSheet(self.get_button_style("green"))
        self.start_btn.clicked.connect(self.start_camera)

        self.stop_btn = QPushButton("Stop Camera")
        self.stop_btn.setFixedSize(120, 35)
        self.stop_btn.setStyleSheet(self.get_button_style("red"))
        self.stop_btn.clicked.connect(self.stop_camera)
        self.stop_btn.setEnabled(False)

        # Snapshot button
        self.snapshot_btn = QPushButton("Take Snapshot")
        self.snapshot_btn.setFixedSize(120, 35)
        self.snapshot_btn.setStyleSheet(self.get_button_style("purple"))
        self.snapshot_btn.clicked.connect(self.take_snapshot)
        self.snapshot_btn.setEnabled(False)

        # File controls
        self.upload_btn = QPushButton("Upload Image")
        self.upload_btn.setFixedSize(120, 35)
        self.upload_btn.setStyleSheet(self.get_button_style("blue"))
        self.upload_btn.clicked.connect(self.upload_image)

        self.folder_btn = QPushButton("Upload Folder")
        self.folder_btn.setFixedSize(120, 35)
        self.folder_btn.setStyleSheet(self.get_button_style("orange"))
        self.folder_btn.clicked.connect(self.upload_folder)

        # Detection info box
        self.detection_info = QLabel("No detection")
        self.detection_info.setFixedSize(200, 35)
        self.detection_info.setStyleSheet("""
            QLabel {
                color: #7f8c8d;
                font-weight: bold;
                font-size: 12px;
                background-color: #2c3e50;
                border: 2px solid #7f8c8d;
                border-radius: 5px;
                padding: 5px;
                text-align: center;
            }
        """)
        self.detection_info.setAlignment(Qt.AlignCenter)

        header_layout.addWidget(self.start_btn)
        header_layout.addWidget(self.stop_btn)
        header_layout.addWidget(self.snapshot_btn)
        header_layout.addStretch()
        header_layout.addWidget(self.upload_btn)
        header_layout.addWidget(self.folder_btn)
        header_layout.addStretch()
        header_layout.addWidget(self.detection_info)

        # Camera display area
        camera_container = QWidget()
        camera_layout = QVBoxLayout(camera_container)
        camera_layout.setContentsMargins(0, 0, 0, 0)

        # Camera label
        self.camera_label = QLabel()
        self.camera_label.setAlignment(Qt.AlignCenter)
        self.camera_label.setMinimumSize(900, 500)
        self.camera_label.setStyleSheet("""
            QLabel {
                border: 2px dashed #7f8c8d;
                background-color: #2c3e50;
                color: white;
                font-size: 16px;
                border-radius: 8px;
            }
        """)
        self.camera_label.setText("Camera Feed\nClick 'Start Camera' or upload images")

        # Loading overlay
        self.loading_overlay = QWidget(self.camera_label)
        self.loading_overlay.setGeometry(0, 0, 400, 120)
        self.loading_overlay.setStyleSheet("""
            QWidget {
                background-color: rgba(0, 0, 0, 0.85);
                border: 2px solid #3498db;
                border-radius: 15px;
            }
        """)
        self.loading_overlay.hide()

        loading_layout = QVBoxLayout(self.loading_overlay)
        loading_layout.setAlignment(Qt.AlignCenter)
        loading_layout.setSpacing(10)

        self.loading_spinner = QProgressBar()
        self.loading_spinner.setFixedSize(300, 20)
        self.loading_spinner.setRange(0, 0)
        self.loading_spinner.setStyleSheet("""
            QProgressBar {
                border: 2px solid #34495e;
                border-radius: 10px;
                background-color: #2c3e50;
                text-align: center;
            }
            QProgressBar::chunk {
                background-color: #27ae60;
                border-radius: 8px;
            }
        """)

        self.loading_text = QLabel("Processing...")
        self.loading_text.setStyleSheet("""
            QLabel {
                color: #ecf0f1;
                font-weight: bold;
                font-size: 14px;
                background-color: transparent;
            }
        """)
        self.loading_text.setAlignment(Qt.AlignCenter)

        loading_layout.addWidget(self.loading_spinner)
        loading_layout.addWidget(self.loading_text)

        camera_layout.addWidget(self.camera_label)

        # Add to left layout
        left_layout.addWidget(header_frame)
        left_layout.addWidget(camera_container, 1)

        # RIGHT SIDE - Logger
        right_widget = QWidget()
        right_layout = QVBoxLayout(right_widget)
        right_layout.setContentsMargins(0, 0, 0, 0)
        right_layout.setSpacing(8)

        # Logger title
        logger_title = QLabel("Detection Logger")
        logger_title.setStyleSheet("""
            QLabel {
                color: #3498db;
                font-weight: bold;
                font-size: 16px;
                background-color: #2c3e50;
                border: 2px solid #3498db;
                border-radius: 5px;
                padding: 8px;
                text-align: center;
            }
        """)
        logger_title.setAlignment(Qt.AlignCenter)
        logger_title.setMaximumHeight(40)

        # Logger console with larger font
        self.console = QTextEdit()
        self.console.setStyleSheet("""
            QTextEdit {
                background-color: #1a1a1a;
                color: #e0e0e0;
                font-family: 'Consolas', monospace;
                font-size: 12px;
                border: 2px solid #34495e;
                border-radius: 8px;
                padding: 10px;
                selection-background-color: #3498db;
            }
        """)

        # Set larger font
        font = QFont("Consolas", 10)
        self.console.setFont(font)

        self.console.setPlainText("System initialized and ready.\nClick 'Start Camera' to begin detection.\n\n")

        right_layout.addWidget(logger_title)
        right_layout.addWidget(self.console, 1)

        # Add left and right widgets to main layout
        main_layout.addWidget(left_widget, 2)  # Camera area - 2 parts
        main_layout.addWidget(right_widget, 1)  # Logger area - 1 part

        central_widget.setLayout(main_layout)

    def get_button_style(self, color):
        """Button styles while hover"""
        colors = {
            "green": {
                "normal": "#27ae60",
                "hover": "#2ecc71",
                "pressed": "#229954"
            },
            "red": {
                "normal": "#e74c3c",
                "hover": "#ec7063",
                "pressed": "#cb4335"
            },
            "blue": {
                "normal": "#3498db",
                "hover": "#5dade2",
                "pressed": "#2e86c1"
            },
            "orange": {
                "normal": "#e67e22",
                "hover": "#eb984e",
                "pressed": "#ca6f1e"
            },
            "purple": {
                "normal": "#9b59b6",
                "hover": "#8e44ad",
                "pressed": "#7d3c98"
            }
        }

        color_set = colors[color]

        return f"""
            QPushButton {{
                background-color: {color_set['normal']};
                color: white;
                font-weight: bold;
                border: none;
                border-radius: 5px;
                font-size: 12px;
            }}
            QPushButton:hover {{
                background-color: {color_set['hover']};
            }}
            QPushButton:pressed {{
                background-color: {color_set['pressed']};
            }}
            QPushButton:disabled {{
                background-color: #95a5a6;
                color: #7f8c8d;
            }}
        """

    def connect_signals(self):
        """Connect all signals"""
        self.camera_thread.frame_ready.connect(self.process_camera_frame)
        self.camera_thread.camera_error.connect(self.handle_camera_error)
        self.file_processor.progress_update.connect(self.update_progress)
        self.file_processor.finished_processing.connect(self.processing_finished)
        # Connect the new image processed signal
        if hasattr(self.file_processor, 'image_processed'):
            self.file_processor.image_processed.connect(self.display_processed_image)

    def handle_camera_error(self, error_message):
        """Handle camera errors"""
        self.log_message("Camera Error: " + error_message)
        self.stop_camera()

        msg = QMessageBox()
        msg.setIcon(QMessageBox.Warning)
        msg.setWindowTitle("Camera Error")
        msg.setText("Camera Access Problem")
        msg.setInformativeText(error_message)
        msg.exec()

    def update_detection_info(self, detection):
        """Update detection info box with class, confidence and performance"""
        if detection:
            class_name = detection['class_name']
            confidence = detection['confidence']

            # Determine performance level
            if confidence >= 0.8:
                performance = "Excellent"
                color = "#27ae60"
            elif confidence >= 0.5:
                performance = "Good"
                color = "#f39c12"
            else:
                performance = "Poor"
                color = "#e74c3c"

            info_text = f"{class_name}: {confidence:.2f} ({performance})"

            self.detection_info.setText(info_text)
            self.detection_info.setStyleSheet(f"""
                QLabel {{
                    color: {color};
                    font-weight: bold;
                    font-size: 12px;
                    background-color: #2c3e50;
                    border: 2px solid {color};
                    border-radius: 5px;
                    padding: 5px;
                    text-align: center;
                }}
            """)
        else:
            self.detection_info.setText("No detection")
            self.detection_info.setStyleSheet("""
                QLabel {
                    color: #7f8c8d;
                    font-weight: bold;
                    font-size: 12px;
                    background-color: #2c3e50;
                    border: 2px solid #7f8c8d;
                    border-radius: 5px;
                    padding: 5px;
                    text-align: center;
                }
            """)

    def show_loading(self, message="Processing..."):
        """Show centered loading indicator"""
        self.processing_files = True

        camera_rect = self.camera_label.rect()
        overlay_width = 400
        overlay_height = 120
        x = (camera_rect.width() - overlay_width) // 2
        y = (camera_rect.height() - overlay_height) // 2

        self.loading_overlay.setGeometry(x, y, overlay_width, overlay_height)
        self.loading_text.setText(message)
        self.loading_overlay.show()
        self.loading_overlay.raise_()

        self.upload_btn.setEnabled(False)
        self.folder_btn.setEnabled(False)
        self.start_btn.setEnabled(False)
        self.snapshot_btn.setEnabled(False)

        self.camera_label.clear()
        self.camera_label.setText("")

    def hide_loading(self):
        """Hide loading indicator"""
        self.processing_files = False
        self.loading_overlay.hide()

        self.upload_btn.setEnabled(True)
        self.folder_btn.setEnabled(True)
        self.start_btn.setEnabled(not self.is_camera_on)
        self.snapshot_btn.setEnabled(self.is_camera_on)

    def display_detected_image(self, image):
        """Display the detected image on the camera label"""
        try:
            rgb_image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
            h, w, ch = rgb_image.shape
            bytes_per_line = ch * w

            qt_image = QImage(rgb_image.data, w, h, bytes_per_line, QImage.Format_RGB888)
            pixmap = QPixmap.fromImage(qt_image)

            scaled_pixmap = pixmap.scaled(
                self.camera_label.width(),
                self.camera_label.height(),
                Qt.KeepAspectRatio,
                Qt.SmoothTransformation
            )

            self.camera_label.setPixmap(scaled_pixmap)
            self.current_display_image = image

        except Exception as e:
            print(f"Error displaying detected image: {e}")
            self.camera_label.setText("Error displaying image")

    def display_processed_image(self, image, detection, filename):
        """Display processed image from folder upload and log it"""
        self.display_detected_image(image)

        if detection:
            self.update_detection_info(detection)
            self.log_message(
                f"Folder Image: {filename} - {detection['class_name']} detected with confidence {detection['confidence']:.2f}")
        else:
            self.update_detection_info(None)
            self.log_message(f"Folder Image: {filename} - No objects detected")

    def take_snapshot(self):
        """Take a snapshot of the current camera frame and process it"""
        if not self.is_camera_on or self.processing_files:
            return

        self.log_message("Taking snapshot...")

        if hasattr(self, 'last_camera_frame') and self.last_camera_frame is not None:
            snapshot_frame = self.last_camera_frame.copy()

            self.show_loading("Analyzing snapshot...")
            self.stop_camera()

            QTimer.singleShot(100, lambda: self.process_snapshot(snapshot_frame))
        else:
            self.log_message("No camera frame available for snapshot")

    def process_snapshot(self, snapshot_frame):
        """Process the taken snapshot with object detection - save only if objects detected"""
        try:
            snapshot_frame = cv2.flip(snapshot_frame, 1)

            # Get only the highest confidence detection
            processed_image, detection = self.model_loader.predict_single(snapshot_frame)

            # Display the processed snapshot
            self.display_detected_image(processed_image)

            # Update detection info
            self.update_detection_info(detection)

            # Log the detection
            if detection:
                self.log_message(
                    f"Snapshot: {detection['class_name']} detected with confidence {detection['confidence']:.2f}")
            else:
                self.log_message("Snapshot: No objects detected")

            # Save the snapshot ONLY if object is detected
            if detection:
                os.makedirs('output', exist_ok=True)
                timestamp = time.strftime("%Y%m%d_%H%M%S")
                snapshot_path = f"snapshots/snapshot_{timestamp}.jpg"
                cv2.imwrite(snapshot_path, processed_image)
                self.log_message(f"Saved to: {snapshot_path}")
            else:
                self.log_message("Image not saved (no detections)")

        except Exception as e:
            self.log_message(f"Error processing snapshot: {str(e)}")
        finally:
            self.hide_loading()

    def auto_stop_camera_for_upload(self):
        """Automatically stop camera when uploading files"""
        if self.is_camera_on:
            self.log_message("Auto-stopping camera for file upload...")
            self.stop_camera()
            return True
        return False

    def load_model(self):
        """Load YOLO11s model"""
        self.log_message("Loading YOLOv11 model...")
        if self.model_loader.load_model('trained_model/best.pt'):
            self.model_loader.start_processing()
            self.log_message("Model loaded successfully!")
        else:
            self.log_message("Failed to load model")

    def start_camera(self):
        """Start camera"""
        if self.processing_files:
            self.log_message("Please wait for current processing to finish")
            return

        self.log_message("Starting camera...")
        time.sleep(0.3)

        if self.camera_thread.start_camera(port=0):
            self.is_camera_on = True
            self.start_btn.setEnabled(False)
            self.stop_btn.setEnabled(True)
            self.snapshot_btn.setEnabled(True)
            self.camera_label.clear()
            self.camera_label.setText("")
            self.update_detection_info(None)
            self.log_message("Camera started successfully!")
        else:
            self.log_message("Camera not available")

    def stop_camera(self):
        """Stop camera"""
        self.is_camera_on = False
        self.camera_thread.stop_camera()
        self.start_btn.setEnabled(True)
        self.stop_btn.setEnabled(False)
        self.snapshot_btn.setEnabled(False)

        if self.current_display_image is not None:
            self.display_detected_image(self.current_display_image)
        else:
            self.camera_label.clear()
            self.camera_label.setText("Camera Feed\nClick 'Start Camera' or upload images")

        self.update_detection_info(None)
        self.log_message("Camera stopped")

    def process_camera_frame(self, frame):
        """Simple approach that maintains boxes with minimal flicker"""
        if not self.is_camera_on or self.processing_files:
            return

        self.last_camera_frame = frame.copy()

        if not hasattr(self, 'frame_counter'):
            self.frame_counter = 0
            self.last_detection_frame = None

        self.frame_counter += 1
        current_time = time.time()
        frame = cv2.flip(frame, 1)

        if self.frame_counter % 3 == 0:  # Process frame
            processed_frame, detection = self.model_loader.predict_single(frame)
            self.last_detection_frame = processed_frame.copy()

            if detection and current_time - self.last_detection_log > 2.0:
                self.log_message(f"Live: {detection['class_name']} - {detection['confidence']:.2f}")
                self.last_detection_log = current_time
        else:
            # On skipped frames, use the last processed frame with boxes
            if self.last_detection_frame is not None:
                processed_frame = self.last_detection_frame
                detection = None  # Don't update detection info on skipped frames
            else:
                processed_frame = frame
                detection = None

        # Always display some version of the frame
        self.display_detected_image(processed_frame)
        self.last_display_time = current_time

        # Only update detection info on processed frames to avoid flickering text
        if self.frame_counter % 3 == 0:
            self.update_detection_info(detection)
    def display_frame_only(self, frame):
        """Quick display without processing"""
        try:
            frame = cv2.flip(frame, 1)
            rgb_image = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            h, w, ch = rgb_image.shape
            bytes_per_line = ch * w
            qt_image = QImage(rgb_image.data, w, h, bytes_per_line, QImage.Format_RGB888)
            pixmap = QPixmap.fromImage(qt_image)
            scaled_pixmap = pixmap.scaled(
                self.camera_label.width(),
                self.camera_label.height(),
                Qt.KeepAspectRatio,
                Qt.SmoothTransformation
            )
            self.camera_label.setPixmap(scaled_pixmap)
        except Exception as e:
            print(f"Display error: {e}")

    def upload_image(self):
        """Upload single image - auto stops camera"""
        if self.processing_files:
            self.log_message("Please wait for current processing to finish")
            return

        if self.auto_stop_camera_for_upload():
            time.sleep(0.2)

        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Select Image",
            "",
            "Image Files (*.jpg *.jpeg *.png *.bmp *.tiff *.webp)"
        )

        if file_path:
            self.show_loading("Processing: " + os.path.basename(file_path))
            QTimer.singleShot(100, lambda: self.process_single_image(file_path))

    def upload_folder(self):
        """Upload folder - auto stops camera"""
        if self.processing_files:
            self.log_message("Please wait for current processing to finish")
            return

        if self.auto_stop_camera_for_upload():
            time.sleep(0.2)

        folder_path = QFileDialog.getExistingDirectory(
            self,
            "Select Folder with Images"
        )

        if folder_path:
            self.show_loading("Scanning folder for images...")
            self.log_message("Processing folder: " + folder_path)
            QTimer.singleShot(100, lambda: self.start_folder_processing(folder_path))

    def start_folder_processing(self, folder_path):
        """Start folder processing with loading indicator"""
        self.file_processor.add_folder(folder_path)
        self.file_processor.start()

    def process_single_image(self, file_path):
        """Process single uploaded image and display it - save only if detected"""
        try:
            filename = os.path.basename(file_path)
            self.log_message("Processing: " + filename)

            image = cv2.imread(file_path)
            if image is not None:
                # Get only the highest confidence detection
                processed_image, detection = self.model_loader.predict_single(image)

                # Display the detected image
                self.display_detected_image(processed_image)

                # Update detection info
                self.update_detection_info(detection)

                # Log the result
                if detection:
                    self.log_message(
                        f"Image: {filename} - {detection['class_name']} detected with confidence {detection['confidence']:.2f}")
                else:
                    self.log_message(f"Image: {filename} - No objects detected")

                # Save ONLY if object is detected
                if detection:
                    os.makedirs('output', exist_ok=True)
                    output_path = f"output/detected_{filename}"
                    cv2.imwrite(output_path, processed_image)
                    self.log_message(f"Saved: {output_path}")
                else:
                    self.log_message("Image not saved (no detections)")
            else:
                self.log_message("Failed to load image: " + filename)
                self.camera_label.setText("Failed to load image\nTry another image")
        finally:
            self.hide_loading()

    def update_progress(self, message):
        """Update progress in console"""
        self.log_message(message)
        if "Processing" in message or "Found" in message:
            self.loading_text.setText(message)

    def processing_finished(self):
        """Called when file processing is complete"""
        self.log_message("All files processed successfully!")
        self.hide_loading()

    def log_message(self, message):
        """Add message to console with timestamp"""
        timestamp = time.strftime("%H:%M:%S")
        log_entry = f"[{timestamp}] {message}"
        self.console.append(log_entry)

        # Auto-scroll to bottom and ensure visibility
        self.console.verticalScrollBar().setValue(
            self.console.verticalScrollBar().maximum()
        )

    def resizeEvent(self, event):
        """Handle window resize"""
        super().resizeEvent(event)
        if self.loading_overlay.isVisible():
            camera_rect = self.camera_label.rect()
            overlay_width = 400
            overlay_height = 120
            x = (camera_rect.width() - overlay_width) // 2
            y = (camera_rect.height() - overlay_height) // 2
            self.loading_overlay.setGeometry(x, y, overlay_width, overlay_height)

        if self.current_display_image is not None:
            self.display_detected_image(self.current_display_image)

    def closeEvent(self, event):
        """Clean up on close"""
        self.stop_camera()
        self.model_loader.stop_processing()
        if self.file_processor.isRunning():
            self.file_processor.wait(2000)
        event.accept()