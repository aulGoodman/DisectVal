"""
Video analysis module for gameplay footage processing.
Analyzes Valorant gameplay to extract events, kills, deaths, and other metrics.
"""

import logging
import os
from dataclasses import dataclass, field
from datetime import timedelta
from enum import Enum
from pathlib import Path
from typing import Any, Generator, List, Optional, Tuple

logger = logging.getLogger(__name__)

try:
    import cv2
    import numpy as np
    CV2_AVAILABLE = True
except ImportError:
    CV2_AVAILABLE = False
    logger.warning("OpenCV not available. Video analysis features will be limited.")


class GameEvent(Enum):
    """Types of in-game events that can be detected."""
    KILL = "kill"
    DEATH = "death"
    ASSIST = "assist"
    ROUND_START = "round_start"
    ROUND_END = "round_end"
    SPIKE_PLANT = "spike_plant"
    SPIKE_DEFUSE = "spike_defuse"
    ABILITY_USED = "ability_used"
    ENEMY_SPOTTED = "enemy_spotted"
    MAP_PING = "map_ping"
    WEAPON_SWITCH = "weapon_switch"
    RELOAD = "reload"


@dataclass
class DetectedEvent:
    """Represents a detected game event with timestamp and details."""
    event_type: GameEvent
    timestamp: float  # Seconds into the video
    confidence: float  # 0.0 to 1.0
    details: dict = field(default_factory=dict)
    frame_number: int = 0
    
    def to_timedelta(self) -> timedelta:
        """Convert timestamp to timedelta."""
        return timedelta(seconds=self.timestamp)


@dataclass
class AnalysisResult:
    """Complete analysis result for a video."""
    video_path: str
    duration: float
    events: List[DetectedEvent]
    kills: int = 0
    deaths: int = 0
    assists: int = 0
    sensitivity_issues: List[str] = field(default_factory=list)
    improvement_suggestions: List[str] = field(default_factory=list)


class VideoAnalyzer:
    """
    Analyzes Valorant gameplay footage.
    Extracts events, tracks metrics, and generates insights.
    """
    
    # Video file extensions to process
    VIDEO_EXTENSIONS = {'.mp4', '.avi', '.mkv', '.mov', '.wmv', '.flv', '.webm'}
    
    def __init__(self):
        """Initialize the video analyzer."""
        self._current_video: Optional[str] = None
        self._cap: Optional[Any] = None  # cv2.VideoCapture
        
    def find_videos(self, directories: List[str]) -> Generator[Path, None, None]:
        """
        Find all video files in the given directories.
        
        Args:
            directories: List of directory paths to search
            
        Yields:
            Path objects for each video file found
        """
        for dir_path in directories:
            path = Path(dir_path)
            if not path.exists():
                logger.warning(f"Directory not found: {dir_path}")
                continue
            
            for file_path in path.rglob('*'):
                if file_path.suffix.lower() in self.VIDEO_EXTENSIONS:
                    yield file_path
    
    def analyze_video(self, video_path: str) -> Optional[AnalysisResult]:
        """
        Analyze a single video file.
        
        Args:
            video_path: Path to the video file
            
        Returns:
            AnalysisResult with detected events and metrics
        """
        if not CV2_AVAILABLE:
            logger.error("OpenCV required for video analysis")
            return None
        
        path = Path(video_path)
        if not path.exists():
            logger.error(f"Video file not found: {video_path}")
            return None
        
        self._current_video = video_path
        events: List[DetectedEvent] = []
        
        try:
            self._cap = cv2.VideoCapture(video_path)
            
            if not self._cap.isOpened():
                logger.error(f"Could not open video: {video_path}")
                return None
            
            # Get video properties
            fps = self._cap.get(cv2.CAP_PROP_FPS)
            frame_count = int(self._cap.get(cv2.CAP_PROP_FRAME_COUNT))
            duration = frame_count / fps if fps > 0 else 0
            
            logger.info(f"Analyzing video: {path.name} ({duration:.1f}s, {frame_count} frames)")
            
            # Process frames
            frame_number = 0
            sample_rate = max(1, int(fps / 2))  # Sample 2 frames per second
            
            while True:
                ret, frame = self._cap.read()
                if not ret:
                    break
                
                # Process every nth frame for efficiency
                if frame_number % sample_rate == 0:
                    timestamp = frame_number / fps
                    detected = self._analyze_frame(frame, timestamp, frame_number)
                    events.extend(detected)
                
                frame_number += 1
            
            # Generate analysis result
            result = AnalysisResult(
                video_path=video_path,
                duration=duration,
                events=events,
                kills=sum(1 for e in events if e.event_type == GameEvent.KILL),
                deaths=sum(1 for e in events if e.event_type == GameEvent.DEATH),
                assists=sum(1 for e in events if e.event_type == GameEvent.ASSIST),
            )
            
            # Generate suggestions
            result.sensitivity_issues = self._analyze_sensitivity(events)
            result.improvement_suggestions = self._generate_suggestions(result)
            
            return result
            
        except Exception as e:
            logger.error(f"Error analyzing video: {e}")
            return None
        
        finally:
            if self._cap is not None:
                self._cap.release()
                self._cap = None
    
    def _analyze_frame(
        self, 
        frame: np.ndarray, 
        timestamp: float, 
        frame_number: int
    ) -> List[DetectedEvent]:
        """
        Analyze a single frame for game events.
        
        Args:
            frame: The video frame as numpy array
            timestamp: Current timestamp in seconds
            frame_number: Current frame number
            
        Returns:
            List of detected events in this frame
        """
        events = []
        
        # Detect kill feed events (top-right area typically)
        kill_event = self._detect_kill_feed(frame, timestamp, frame_number)
        if kill_event:
            events.append(kill_event)
        
        # Detect round state changes
        round_event = self._detect_round_state(frame, timestamp, frame_number)
        if round_event:
            events.append(round_event)
        
        # Detect minimap events
        minimap_events = self._detect_minimap_events(frame, timestamp, frame_number)
        events.extend(minimap_events)
        
        return events
    
    def _detect_kill_feed(
        self, 
        frame: np.ndarray, 
        timestamp: float,
        frame_number: int
    ) -> Optional[DetectedEvent]:
        """Detect kill/death events from the kill feed area."""
        # Get frame dimensions
        height, width = frame.shape[:2]
        
        # Kill feed is typically in the top-right corner
        # Extract that region
        kill_feed_region = frame[0:int(height*0.15), int(width*0.6):width]
        
        # Convert to HSV for color detection
        hsv = cv2.cvtColor(kill_feed_region, cv2.COLOR_BGR2HSV)
        
        # Detect red color (enemy kill indicator)
        red_lower = np.array([0, 100, 100])
        red_upper = np.array([10, 255, 255])
        red_mask = cv2.inRange(hsv, red_lower, red_upper)
        
        # Detect green color (friendly/your kill indicator)
        green_lower = np.array([35, 100, 100])
        green_upper = np.array([85, 255, 255])
        green_mask = cv2.inRange(hsv, green_lower, green_upper)
        
        red_pixels = cv2.countNonZero(red_mask)
        green_pixels = cv2.countNonZero(green_mask)
        
        # Threshold for detection (adjust based on resolution)
        threshold = 500
        
        if green_pixels > threshold:
            return DetectedEvent(
                event_type=GameEvent.KILL,
                timestamp=timestamp,
                confidence=min(1.0, green_pixels / 2000),
                frame_number=frame_number,
                details={"detected_from": "kill_feed_green"}
            )
        
        if red_pixels > threshold:
            return DetectedEvent(
                event_type=GameEvent.DEATH,
                timestamp=timestamp,
                confidence=min(1.0, red_pixels / 2000),
                frame_number=frame_number,
                details={"detected_from": "kill_feed_red"}
            )
        
        return None
    
    def _detect_round_state(
        self,
        frame: np.ndarray,
        timestamp: float,
        frame_number: int
    ) -> Optional[DetectedEvent]:
        """Detect round start/end from UI elements."""
        height, width = frame.shape[:2]
        
        # Round timer is typically at the top center
        timer_region = frame[0:int(height*0.08), int(width*0.4):int(width*0.6)]
        
        # Convert to grayscale and check for specific patterns
        gray = cv2.cvtColor(timer_region, cv2.COLOR_BGR2GRAY)
        
        # Check for bright UI elements indicating round state
        bright_pixels = np.sum(gray > 200)
        total_pixels = gray.size
        
        if bright_pixels / total_pixels > 0.1:
            # Could indicate round transition
            return DetectedEvent(
                event_type=GameEvent.ROUND_START,
                timestamp=timestamp,
                confidence=0.6,
                frame_number=frame_number,
                details={"detected_from": "timer_region"}
            )
        
        return None
    
    def _detect_minimap_events(
        self,
        frame: np.ndarray,
        timestamp: float,
        frame_number: int
    ) -> List[DetectedEvent]:
        """Detect events from the minimap area."""
        events = []
        height, width = frame.shape[:2]
        
        # Minimap is typically in the top-left corner
        minimap_region = frame[int(height*0.02):int(height*0.25), int(width*0.02):int(width*0.2)]
        
        # Convert to HSV for color detection
        hsv = cv2.cvtColor(minimap_region, cv2.COLOR_BGR2HSV)
        
        # Detect red markers (enemies)
        red_lower = np.array([0, 100, 100])
        red_upper = np.array([10, 255, 255])
        red_mask = cv2.inRange(hsv, red_lower, red_upper)
        
        red_pixels = cv2.countNonZero(red_mask)
        
        if red_pixels > 100:
            events.append(DetectedEvent(
                event_type=GameEvent.ENEMY_SPOTTED,
                timestamp=timestamp,
                confidence=min(1.0, red_pixels / 500),
                frame_number=frame_number,
                details={"detected_from": "minimap", "pixel_count": red_pixels}
            ))
        
        # Detect pings (yellow/orange markers)
        yellow_lower = np.array([20, 100, 100])
        yellow_upper = np.array([30, 255, 255])
        yellow_mask = cv2.inRange(hsv, yellow_lower, yellow_upper)
        
        yellow_pixels = cv2.countNonZero(yellow_mask)
        
        if yellow_pixels > 50:
            events.append(DetectedEvent(
                event_type=GameEvent.MAP_PING,
                timestamp=timestamp,
                confidence=min(1.0, yellow_pixels / 200),
                frame_number=frame_number,
                details={"detected_from": "minimap", "pixel_count": yellow_pixels}
            ))
        
        return events
    
    def _analyze_sensitivity(self, events: List[DetectedEvent]) -> List[str]:
        """
        Analyze events to detect potential sensitivity issues.
        
        Based on death patterns and aim behavior.
        """
        issues = []
        
        # Count rapid consecutive deaths
        deaths = [e for e in events if e.event_type == GameEvent.DEATH]
        if len(deaths) >= 2:
            for i in range(1, len(deaths)):
                time_diff = deaths[i].timestamp - deaths[i-1].timestamp
                if time_diff < 30:  # Deaths within 30 seconds
                    issues.append(
                        "Multiple deaths in quick succession detected. "
                        "This may indicate over-peeking or sensitivity issues."
                    )
                    break
        
        # Check kill/death ratio from events
        kills = len([e for e in events if e.event_type == GameEvent.KILL])
        death_count = len(deaths)
        
        if death_count > kills * 2 and death_count > 5:
            issues.append(
                "High death count relative to kills. Consider reviewing your "
                "crosshair placement and pre-aim positions."
            )
        
        return issues
    
    def _generate_suggestions(self, result: AnalysisResult) -> List[str]:
        """Generate improvement suggestions based on analysis."""
        suggestions = []
        
        # K/D based suggestions
        if result.deaths > 0:
            kd = result.kills / result.deaths
            if kd < 0.8:
                suggestions.append(
                    "Your K/D appears low. Consider:\n"
                    "- Practicing crosshair placement in aim trainers\n"
                    "- Playing more passively and holding angles\n"
                    "- Using utility to gain advantages before peeking"
                )
        
        # Check for missed minimap information
        enemy_spotted = len([e for e in result.events if e.event_type == GameEvent.ENEMY_SPOTTED])
        map_pings = len([e for e in result.events if e.event_type == GameEvent.MAP_PING])
        
        if enemy_spotted > 5 and result.deaths > enemy_spotted:
            suggestions.append(
                "Enemies appear on minimap frequently but deaths are high. "
                "Try to pay more attention to minimap callouts."
            )
        
        if map_pings > 0:
            suggestions.append(
                f"Detected {map_pings} map pings during gameplay. "
                "Make sure to acknowledge and react to team communication."
            )
        
        # Sensitivity suggestions
        if result.sensitivity_issues:
            suggestions.append(
                "Sensitivity check: If aim feels inconsistent, ensure:\n"
                "- Windows 'Enhance pointer precision' is OFF\n"
                "- Consider using Raw Accel or Intercept Mouse for custom curves\n"
                "- Match your sensitivity across all games"
            )
        
        return suggestions
    
    def extract_clip(
        self, 
        video_path: str, 
        start_time: float, 
        end_time: float, 
        output_path: str
    ) -> bool:
        """
        Extract a clip from a video.
        
        Args:
            video_path: Source video path
            start_time: Start time in seconds
            end_time: End time in seconds
            output_path: Output clip path
            
        Returns:
            True if clip was extracted successfully
        """
        if not CV2_AVAILABLE:
            return False
        
        try:
            cap = cv2.VideoCapture(video_path)
            if not cap.isOpened():
                return False
            
            fps = cap.get(cv2.CAP_PROP_FPS)
            width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
            height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
            
            fourcc = cv2.VideoWriter_fourcc(*'mp4v')
            out = cv2.VideoWriter(output_path, fourcc, fps, (width, height))
            
            start_frame = int(start_time * fps)
            end_frame = int(end_time * fps)
            
            cap.set(cv2.CAP_PROP_POS_FRAMES, start_frame)
            
            current_frame = start_frame
            while current_frame < end_frame:
                ret, frame = cap.read()
                if not ret:
                    break
                out.write(frame)
                current_frame += 1
            
            cap.release()
            out.release()
            return True
            
        except Exception as e:
            logger.error(f"Error extracting clip: {e}")
            return False


class PassiveTrainer:
    """
    Manages passive training from gameplay footage.
    Processes videos in the background to train the AI model.
    """
    
    def __init__(self, training_dirs: Optional[List[str]] = None):
        """
        Initialize the passive trainer.
        
        Args:
            training_dirs: Directories containing gameplay footage
        """
        self.training_dirs = training_dirs or []
        self.analyzer = VideoAnalyzer()
        self._processed_videos: set = set()
        self._is_training = False
    
    def add_training_directory(self, directory: str) -> bool:
        """Add a directory for training data."""
        path = Path(directory)
        if path.exists() and path.is_dir():
            if directory not in self.training_dirs:
                self.training_dirs.append(directory)
            return True
        return False
    
    def get_unprocessed_videos(self) -> List[Path]:
        """Get list of videos that haven't been processed yet."""
        unprocessed = []
        for video in self.analyzer.find_videos(self.training_dirs):
            if str(video) not in self._processed_videos:
                unprocessed.append(video)
        return unprocessed
    
    def process_next_video(self) -> Optional[AnalysisResult]:
        """Process the next unprocessed video."""
        unprocessed = self.get_unprocessed_videos()
        if not unprocessed:
            return None
        
        video_path = unprocessed[0]
        result = self.analyzer.analyze_video(str(video_path))
        
        if result:
            self._processed_videos.add(str(video_path))
        
        return result
    
    def get_training_stats(self) -> dict:
        """Get statistics about training progress."""
        all_videos = list(self.analyzer.find_videos(self.training_dirs))
        return {
            "total_videos": len(all_videos),
            "processed": len(self._processed_videos),
            "remaining": len(all_videos) - len(self._processed_videos),
            "training_directories": len(self.training_dirs),
        }
