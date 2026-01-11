# backend/google_assistant_service.py

import google.auth.transport.grpc
import google.auth.transport.requests
import google.oauth2.credentials
from google.assistant.embedded.v1alpha2 import (
    embedded_assistant_pb2,
    embedded_assistant_pb2_grpc
)
import json
import os

class GoogleAssistantService:
    """Control Google Home via Assistant SDK"""
    
    def __init__(self):
        # Load credentials
        creds_path = 'google_assistant_credentials.json'
        
        if not os.path.exists(creds_path):
            raise ValueError("Google Assistant credentials not found!")
        
        with open(creds_path, 'r') as f:
            credentials_data = json.load(f)
        
        self.credentials = google.oauth2.credentials.Credentials(
            token=credentials_data['access_token'],
            refresh_token=credentials_data.get('refresh_token'),
            token_uri='https://oauth2.googleapis.com/token',
            client_id=credentials_data['client_id'],
            client_secret=credentials_data['client_secret']
        )
        
        # Create gRPC channel
        http_request = google.auth.transport.requests.Request()
        self.credentials.refresh(http_request)
        
        grpc_channel = google.auth.transport.grpc.secure_authorized_channel(
            self.credentials,
            http_request,
            'embeddedassistant.googleapis.com'
        )
        
        self.assistant = embedded_assistant_pb2_grpc.EmbeddedAssistantStub(grpc_channel)
    
    def send_text_command(self, command: str):
        """
        Send text command to Google Assistant
        
        Args:
            command: Command like "play lo-fi music on Spotify"
        """
        try:
            # Create text query
            config = embedded_assistant_pb2.AssistConfig(
                text_query=command,
                audio_out_config=embedded_assistant_pb2.AudioOutConfig(
                    encoding='LINEAR16',
                    sample_rate_hertz=16000,
                    volume_percentage=100,
                )
            )
            
            request = embedded_assistant_pb2.AssistRequest(config=config)
            
            # Send request
            for response in self.assistant.Assist([request]):
                if response.speech_results:
                    return response.speech_results[0].transcript
            
            return "Command sent"
        
        except Exception as e:
            print(f"Assistant error: {e}")
            return None
    
    # Convenience methods for music control
    
    def play_spotify(self, genre: str, duration: int = None):
        """
        Play music from Spotify
        
        Args:
            genre: Music type (lofi, jazz, ambient, etc.)
            duration: Optional duration in minutes
        """
        genres_map = {
            'lofi': 'lo-fi hip hop',
            'jazz': 'jazz study music',
            'ambient': 'ambient study music',
            'classical': 'classical study music',
            'nature': 'nature sounds',
            'brown_noise': 'brown noise',
            'rain': 'rain sounds'
        }
        
        query = genres_map.get(genre, genre)
        
        if duration:
            command = f"play {query} on Spotify for {duration} minutes"
        else:
            command = f"play {query} on Spotify"
        
        return self.send_text_command(command)
    
    def stop_music(self):
        """Stop playback"""
        return self.send_text_command("stop")
    
    def pause_music(self):
        """Pause playback"""
        return self.send_text_command("pause")
    
    def resume_music(self):
        """Resume playback"""
        return self.send_text_command("resume")
    
    def set_volume(self, level: int):
        """
        Set volume (0-100)
        """
        return self.send_text_command(f"set volume to {level}%")
    
    def play_on_device(self, device_name: str, query: str):
        """
        Play on specific device
        
        Args:
            device_name: Name of your Google Home (e.g., "Living Room")
            query: What to play
        """
        return self.send_text_command(f"play {query} on {device_name}")

# Create singleton
google_assistant = GoogleAssistantService()