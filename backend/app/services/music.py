"""
Music service for playing background audio during study sessions.
Supports various audio types: lofi, nature, classical, ambient, binaural, silence.
"""
import os
import subprocess
import platform
from typing import Optional, Dict
from enum import Enum


class AudioType(str, Enum):
    """Supported audio types"""
    LOFI = "lofi"
    NATURE = "nature"
    CLASSICAL = "classical"
    AMBIENT = "ambient"
    BINAURAL = "binaural"
    SILENCE = "silence"


class MusicService:
    """Service to manage music playback during study sessions"""
    
    def __init__(self):
        self.current_process: Optional[subprocess.Popen] = None
        self.is_playing = False
        self.current_audio_type: Optional[str] = None
        
        # Map audio types to YouTube URLs or local file paths
        # Using YouTube URLs for now - can be replaced with local files or streaming services
        self.audio_sources = {
            AudioType.LOFI: "https://www.youtube.com/watch?v=jfKfPfyJRdk",  # Lo-Fi Hip Hop Radio
            AudioType.NATURE: "https://www.youtube.com/watch?v=1ZYbU82GVz4",  # Nature Sounds
            AudioType.CLASSICAL: "https://www.youtube.com/watch?v=4Tr0otuiQuU",  # Classical Music
            AudioType.AMBIENT: "https://www.youtube.com/watch?v=5qap5aO4i9A",  # Ambient Music
            AudioType.BINAURAL: "https://www.youtube.com/watch?v=4ROlHoHp324",  # Binaural Beats
            AudioType.SILENCE: None,  # No audio
        }
    
    def start_music(self, audio_type: str, duration_minutes: Optional[int] = None) -> Dict[str, any]:
        """
        Start playing music based on audio type
        
        Args:
            audio_type: Type of audio to play (lofi, nature, classical, ambient, binaural, silence)
            duration_minutes: Optional duration in minutes
            
        Returns:
            Dict with status and message
        """
        try:
            # Stop any currently playing music
            if self.is_playing:
                self.stop_music()
            
            # Handle silence
            if audio_type == AudioType.SILENCE.value or not audio_type:
                self.is_playing = False
                self.current_audio_type = None
                return {
                    "status": "success",
                    "message": "Silence mode - no audio will play",
                    "audio_type": audio_type
                }
            
            # Validate audio type
            if audio_type not in [e.value for e in AudioType]:
                return {
                    "status": "error",
                    "message": f"Invalid audio type: {audio_type}",
                    "audio_type": None
                }
            
            # Get audio source - convert string to AudioType enum
            try:
                audio_type_enum = AudioType(audio_type)
                audio_source = self.audio_sources.get(audio_type_enum)
            except ValueError:
                audio_source = None
                
            if not audio_source:
                return {
                    "status": "error",
                    "message": f"No audio source configured for: {audio_type}",
                    "audio_type": None
                }
            
            # Extract YouTube video ID from URL
            youtube_id = self._extract_youtube_id(audio_source)
            if not youtube_id:
                return {
                    "status": "error",
                    "message": f"Invalid YouTube URL: {audio_source}",
                    "audio_type": None
                }
            
            self.is_playing = True
            self.current_audio_type = audio_type
            
            return {
                "status": "success",
                "message": f"Started playing {audio_type} music",
                "audio_type": audio_type,
                "youtube_url": audio_source,
                "youtube_id": youtube_id,
                "duration_minutes": duration_minutes
            }
            
        except Exception as e:
            return {
                "status": "error",
                "message": f"Failed to start music: {str(e)}",
                "audio_type": None
            }
    
    def _extract_youtube_id(self, url: str) -> Optional[str]:
        """
        Extract YouTube video ID from URL
        
        Args:
            url: YouTube URL
            
        Returns:
            Video ID or None
        """
        try:
            if "youtube.com/watch?v=" in url:
                return url.split("watch?v=")[1].split("&")[0]
            elif "youtu.be/" in url:
                return url.split("youtu.be/")[1].split("?")[0]
            return None
        except Exception:
            return None
    
    def pause_music(self) -> Dict[str, any]:
        """
        Pause currently playing music
        
        Returns:
            Dict with status and message
        """
        try:
            self.is_playing = False
            return {
                "status": "success",
                "message": "Music paused",
                "audio_type": self.current_audio_type
            }
        except Exception as e:
            return {
                "status": "error",
                "message": f"Failed to pause music: {str(e)}"
            }
    
    def resume_music(self) -> Dict[str, any]:
        """
        Resume paused music
        
        Returns:
            Dict with status and message
        """
        try:
            if self.current_audio_type:
                self.is_playing = True
                return {
                    "status": "success",
                    "message": "Music resumed",
                    "audio_type": self.current_audio_type
                }
            else:
                return {
                    "status": "error",
                    "message": "No music to resume"
                }
        except Exception as e:
            return {
                "status": "error",
                "message": f"Failed to resume music: {str(e)}"
            }
    
    def stop_music(self) -> Dict[str, any]:
        """
        Stop currently playing music
        
        Returns:
            Dict with status and message
        """
        try:
            if self.current_process:
                self.current_process.terminate()
                self.current_process.wait()
                self.current_process = None
            
            self.is_playing = False
            previous_type = self.current_audio_type
            self.current_audio_type = None
            
            return {
                "status": "success",
                "message": "Music stopped",
                "previous_audio_type": previous_type
            }
        except Exception as e:
            return {
                "status": "error",
                "message": f"Failed to stop music: {str(e)}"
            }
    
    def get_status(self) -> Dict[str, any]:
        """
        Get current music playback status
        
        Returns:
            Dict with current status
        """
        return {
            "is_playing": self.is_playing,
            "audio_type": self.current_audio_type,
            "audio_source": self.audio_sources.get(self.current_audio_type) if self.current_audio_type else None
        }


# Create singleton instance
music_service = MusicService()

