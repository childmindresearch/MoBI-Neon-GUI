"""Simple GUI for Neon recording."""

import os
import sys
from datetime import datetime

import cv2
from PyQt6.QtCore import QTimer
from PyQt6.QtGui import QImage, QPixmap
from PyQt6.QtWidgets import (
    QApplication,
    QFileDialog,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from neon_gui.neon_recorder import NeonRecorder


class VideoDisplay(QLabel):
    """Widget to display video frames."""
    
    def __init__(self):
        super().__init__()
        self.setMinimumSize(640, 480)
        self.setStyleSheet("border: 1px solid black;")
        self.setText("No video feed")
        self.setScaledContents(True)
        
    def update_frame(self, frame):
        """Update the displayed frame."""
        if frame is None:
            self.setText("No video feed")
            return
            
        # Convert BGR to RGB
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        h, w, ch = rgb_frame.shape
        bytes_per_line = ch * w
        
        # Create QImage and QPixmap
        qt_image = QImage(
            rgb_frame.data, w, h, bytes_per_line, QImage.Format.Format_RGB888
        )
        pixmap = QPixmap.fromImage(qt_image)
        
        # Set the pixmap
        self.setPixmap(pixmap)


class NeonGUI(QMainWindow):
    """Main GUI window."""
    
    def __init__(self):
        super().__init__()
        self.recorder = NeonRecorder()
        self.save_directory = os.path.expanduser("~/Desktop")
        self.setup_ui()
        self.setup_timer()
        
    def setup_ui(self):
        """Set up the user interface."""
        self.setWindowTitle("Neon Scene Camera Recorder")
        self.setGeometry(100, 100, 1000, 700)
        
        # Central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Main layout
        main_layout = QHBoxLayout()
        central_widget.setLayout(main_layout)
        
        # Video display
        self.video_display = VideoDisplay()
        main_layout.addWidget(self.video_display, 2)
        
        # Control panel
        control_panel = self.create_control_panel()
        main_layout.addWidget(control_panel, 1)
        
        # Status bar
        self.statusBar().showMessage("Ready")
        
    def create_control_panel(self):
        """Create the control panel."""
        panel = QWidget()
        layout = QVBoxLayout()
        panel.setLayout(layout)
        
        # Device controls
        device_group = QGroupBox("Device")
        device_layout = QVBoxLayout()
        device_group.setLayout(device_layout)
        
        self.connect_btn = QPushButton("Connect Device")
        self.connect_btn.clicked.connect(self.connect_device)
        device_layout.addWidget(self.connect_btn)
        
        self.disconnect_btn = QPushButton("Disconnect")
        self.disconnect_btn.clicked.connect(self.disconnect_device)
        self.disconnect_btn.setEnabled(False)
        device_layout.addWidget(self.disconnect_btn)
        
        layout.addWidget(device_group)
        
        # Recording controls
        recording_group = QGroupBox("Recording")
        recording_layout = QVBoxLayout()
        recording_group.setLayout(recording_layout)
        
        # Save directory
        dir_layout = QHBoxLayout()
        self.dir_label = QLabel(f"Save to: {self.save_directory}")
        self.dir_label.setWordWrap(True)
        dir_layout.addWidget(self.dir_label)
        
        self.browse_btn = QPushButton("Browse")
        self.browse_btn.clicked.connect(self.browse_directory)
        dir_layout.addWidget(self.browse_btn)
        
        recording_layout.addLayout(dir_layout)
        
        # Recording buttons
        self.start_btn = QPushButton("Start Recording")
        self.start_btn.clicked.connect(self.start_recording)
        self.start_btn.setEnabled(False)
        recording_layout.addWidget(self.start_btn)
        
        self.stop_btn = QPushButton("Stop Recording")
        self.stop_btn.clicked.connect(self.stop_recording)
        self.stop_btn.setEnabled(False)
        recording_layout.addWidget(self.stop_btn)
        
        layout.addWidget(recording_group)
        
        # Log
        log_group = QGroupBox("Log")
        log_layout = QVBoxLayout()
        log_group.setLayout(log_layout)
        
        self.log_text = QTextEdit()
        self.log_text.setMinimumHeight(300)
        self.log_text.setReadOnly(True)
        log_layout.addWidget(self.log_text)
        
        layout.addWidget(log_group)
        
        # Stretch to push everything to top
        layout.addStretch()
        
        return panel
        
    def setup_timer(self):
        """Set up the video update timer."""
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_video)
        
    def log_message(self, message):
        """Add a message to the log."""
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.log_text.append(f"[{timestamp}] {message}")
        
    def connect_device(self):
        """Connect to the Neon device."""
        try:
            self.log_message("Connecting to device...")
            self.statusBar().showMessage("Connecting...")
            
            # Set up LSL stream first
            self.recorder.setup_lsl_stream()
            
            # Connect to device
            self.recorder.connect_device()
            
            # Update UI
            self.connect_btn.setEnabled(False)
            self.disconnect_btn.setEnabled(True)
            self.start_btn.setEnabled(True)
            
            # Start video feed
            self.timer.start(33)  # ~30 FPS
            
            self.log_message("Device connected successfully")
            self.statusBar().showMessage("Connected")
            
        except Exception as e:
            self.log_message(f"Connection failed: {str(e)}")
            self.statusBar().showMessage("Connection failed")
            QMessageBox.critical(self, "Connection Error", str(e))
            
    def disconnect_device(self):
        """Disconnect from the device."""
        try:
            self.timer.stop()
            self.recorder.cleanup()
            
            # Update UI
            self.connect_btn.setEnabled(True)
            self.disconnect_btn.setEnabled(False)
            self.start_btn.setEnabled(False)
            self.stop_btn.setEnabled(False)
            
            self.video_display.setText("No video feed")
            self.log_message("Device disconnected")
            self.statusBar().showMessage("Disconnected")
            
        except Exception as e:
            self.log_message(f"Disconnect error: {str(e)}")
            
    def browse_directory(self):
        """Browse for save directory."""
        directory = QFileDialog.getExistingDirectory(
            self, "Select Save Directory", self.save_directory
        )
        if directory:
            self.save_directory = directory
            self.dir_label.setText(f"Save to: {directory}")
            
    def start_recording(self):
        """Start recording."""
        try:
            # Generate filename
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = os.path.join(
                self.save_directory, f"scene_recording_{timestamp}.mp4"
            )
            
            self.recorder.start_recording(filename)
            
            # Update UI
            self.start_btn.setEnabled(False)
            self.stop_btn.setEnabled(True)
            
            self.log_message(f"Recording started: {filename}")
            self.statusBar().showMessage("Recording...")
            
        except Exception as e:
            self.log_message(f"Recording failed: {str(e)}")
            QMessageBox.critical(self, "Recording Error", str(e))
            
    def stop_recording(self):
        """Stop recording."""
        try:
            self.recorder.stop_recording()
            
            # Update UI
            self.start_btn.setEnabled(True)
            self.stop_btn.setEnabled(False)
            
            self.log_message("Recording stopped")
            self.statusBar().showMessage("Recording saved")
            
        except Exception as e:
            self.log_message(f"Stop recording error: {str(e)}")
            
    def update_video(self):
        """Update the video display."""
        try:
            frame, timestamp = self.recorder.get_frame()
            self.video_display.update_frame(frame)
            
            if frame is None:
                self.log_message("Warning: No frame received")
                
        except Exception as e:
            self.log_message(f"Video update error: {str(e)}")
            
    def closeEvent(self, event):
        """Handle window close event."""
        if self.recorder.recording:
            reply = QMessageBox.question(
                self, 
                "Recording Active", 
                "Recording is active. Stop recording and exit?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )
            if reply == QMessageBox.StandardButton.Yes:
                self.recorder.cleanup()
                event.accept()
            else:
                event.ignore()
        else:
            self.recorder.cleanup()
            event.accept()


def main():
    """Main function."""
    app = QApplication(sys.argv)
    app.setApplicationName("Neon Scene Recorder")
    
    window = NeonGUI()
    window.show()
    
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
