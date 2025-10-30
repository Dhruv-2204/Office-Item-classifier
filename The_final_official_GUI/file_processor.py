import os
import cv2
from pathlib import Path
from PySide6.QtCore import QThread, Signal


class FileProcessor(QThread):
    progress_update = Signal(str)
    finished_processing = Signal()
    image_processed = Signal(object, object, str)  # image, detection, filename

    def __init__(self, model_loader):
        super().__init__()
        self.model_loader = model_loader
        self.files_to_process = []
        self.output_dir = "output"
        self.last_processed_image = None
        self.last_detection = None

    def add_files(self, file_paths):
        self.files_to_process.extend(file_paths)

    def add_folder(self, folder_path):
        supported_formats = ('.jpg', '.jpeg', '.png', '.bmp', '.tiff', '.webp')

        for file_path in Path(folder_path).rglob('*'):
            if file_path.suffix.lower() in supported_formats:
                self.files_to_process.append(str(file_path))

        self.progress_update.emit(f"Found {len(self.files_to_process)} images")

    def run(self):
        os.makedirs(self.output_dir, exist_ok=True)
        total_files = len(self.files_to_process)

        for i, file_path in enumerate(self.files_to_process):
            try:
                filename = os.path.basename(file_path)
                self.progress_update.emit(f"Processing {i + 1}/{total_files}: {filename}")

                image = cv2.imread(file_path)
                if image is None:
                    self.progress_update.emit(f"Skipped (invalid): {filename}")
                    continue

                # Get only the highest confidence detection
                processed_image, detection = self.model_loader.predict_single(image)

                # Store the last processed image and detection
                self.last_processed_image = processed_image
                self.last_detection = detection

                # Emit signal to display the image
                self.image_processed.emit(processed_image, detection, filename)

                # Save ONLY if object is detected
                if detection:
                    output_path = os.path.join(self.output_dir, f"detected_{filename}")
                    cv2.imwrite(output_path, processed_image)
                    self.progress_update.emit(
                        f"Detected: {filename} - {detection['class_name']} ({detection['confidence']:.2f})")
                else:
                    self.progress_update.emit(f"No detection: {filename}")

            except Exception as e:
                self.progress_update.emit(f"Error: {os.path.basename(file_path)} - {str(e)}")

        self.files_to_process.clear()
        self.finished_processing.emit()