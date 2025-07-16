"""Core Neon recording functionality."""

import cv2
from pupil_labs.realtime_api.simple import discover_one_device
from pylsl import StreamInfo, StreamOutlet


class NeonRecorder:
    """Handles Neon device connection and recording."""
    
    def __init__(self):
        self.device = None
        self.outlet = None
        self.video_writer = None
        self.recording = False
        self.first_frame_captured = False
        self.last_frame_time = None
        
    def setup_lsl_stream(self):
        """Set up LSL marker stream."""
        info = StreamInfo("SceneCameraMarker", "Markers", 1, 0, "string", "scene123")
        self.outlet = StreamOutlet(info)
        
    def connect_device(self, timeout=10):
        """Connect to Neon device."""
        print("Looking for Neon device...")
        self.device = discover_one_device(max_search_duration_seconds=timeout)
        if self.device is None:
            raise RuntimeError("No device found")
        print(f"Connected to device: {self.device}")
        return True
        
    def start_recording(self, filename="scene_recording.mp4"):
        """Start recording video."""
        if self.device is None:
            raise RuntimeError("No device connected")
            
        # Get initial frame for resolution
        frame, _ = self.device.receive_scene_video_frame()
        if frame is None:
            raise RuntimeError("Failed to receive initial frame")
            
        # Set up video writer
        height, width = frame.shape[:2]
        fourcc = cv2.VideoWriter_fourcc(*'mp4v')
        self.video_writer = cv2.VideoWriter(filename, fourcc, 30.0, (width, height))
        
        self.recording = True
        self.first_frame_captured = False
        
    def stop_recording(self):
        """Stop recording video."""
        if (
            self.recording
            and self.first_frame_captured
            and self.last_frame_time is not None
        ):
            self.outlet.push_sample(["scene_end"], timestamp=self.last_frame_time)
            print("Recording stopped - end marker sent")
            
        self.recording = False
        self.first_frame_captured = False
        
        if self.video_writer is not None:
            self.video_writer.release()
            self.video_writer = None
            
    def get_frame(self):
        """Get current frame from device."""
        if self.device is None:
            return None, None
            
        frame, timestamp = self.device.receive_scene_video_frame()
        
        # Handle recording
        if self.recording and frame is not None and self.video_writer is not None:
            # Send start marker before first frame
            if not self.first_frame_captured:
                self.outlet.push_sample(["scene_start"], timestamp=timestamp)
                print("Recording started - start marker sent")
                self.first_frame_captured = True
                
            self.video_writer.write(frame)
            self.last_frame_time = timestamp
            
        return frame, timestamp
        
    def cleanup(self):
        """Clean up resources."""
        if self.recording:
            self.stop_recording()
