// Main App component
import React, { useState, useEffect } from 'react';
import './App.css';
import Onboarding from './Onboarding';
import Companion from './Companion';
import Pomodoro from './Pomodoro';
import MusicPlayer from './MusicPlayer';
import wsService from './services/websocket';

// State management
function App() {
  const [isOnboarding, setIsOnboarding] = useState(true);
  const [isConnected, setIsConnected] = useState(false);
  const [sessionData, setSessionData] = useState(null);
  const [focusData, setFocusData] = useState({
    isFocused: false,
    focusScore: 0,
    sessionDuration: 0,
  });
  const [companionMessage, setCompanionMessage] = useState('');
  const [pomodoroState, setPomodoroState] = useState({
    isRunning: false,
    isBreak: false,
    timeRemaining: 25 * 60,
    cycle: 0,
  });
  const [currentTask, setCurrentTask] = useState('');
  const [musicState, setMusicState] = useState({
    youtubeId: null,
    isPlaying: false,
    audioType: null,
  });

  // Local timer countdown effect
  useEffect(() => {
    let interval = null;
    
    if (pomodoroState.isRunning && pomodoroState.timeRemaining > 0) {
      interval = setInterval(() => {
        setPomodoroState(prev => {
          const newTime = prev.timeRemaining - 1;
          
          // When timer reaches 0, switch to break or stop
          if (newTime <= 0) {
            if (!prev.isBreak) {
              // Work session ended, start break
              return {
                ...prev,
                isBreak: true,
                timeRemaining: 5 * 60, // 5 minute break
                cycle: prev.cycle + 1,
              };
            } else {
              // Break ended, stop timer
              return {
                ...prev,
                isRunning: false,
                isBreak: false,
                timeRemaining: 25 * 60,
              };
            }
          }
          
          return {
            ...prev,
            timeRemaining: newTime,
          };
        });
      }, 1000);
    } else if (pomodoroState.timeRemaining === 0 && pomodoroState.isRunning) {
      // Timer reached 0, stop it
      setPomodoroState(prev => ({
        ...prev,
        isRunning: false,
      }));
    }
    
    return () => {
      if (interval) {
        clearInterval(interval);
      }
    };
  }, [pomodoroState.isRunning, pomodoroState.timeRemaining, pomodoroState.isBreak]);

  useEffect(() => {
    // Connect WebSocket only after onboarding
    if (!isOnboarding) {
      wsService.connect();

      // Update connection status
      const handleConnected = () => setIsConnected(true);
      const handleDisconnected = () => setIsConnected(false);
      
      // Handle WebSocket messages
      const handleMessage = (data) => {
        console.log('Received message:', data);
        
        // Handle focus detection updates
        if (data.focus !== undefined) {
          console.log('Focus update received:', data.focus, 'Score:', data.focus_score);
          setFocusData(prev => ({
            ...prev, // Preserve existing state
            isFocused: data.focus,
            focusScore: data.focus_score || prev.focusScore, // Fallback to previous score if not provided
          }));
        }

        // Handle focus score updates (alternative path)
        if (data.focus_score !== undefined) {
          console.log('Focus score update received:', data.focus_score);
          setFocusData(prev => ({
            ...prev,
            focusScore: data.focus_score,
            // If focus_score is high enough, assume focused
            isFocused: data.focus_score >= 60 ? true : (prev.isFocused !== undefined ? prev.isFocused : false),
          }));
        }

        // Handle session duration
        if (data.session_duration !== undefined) {
          setFocusData(prev => ({
            ...prev,
            sessionDuration: data.session_duration,
          }));
        }

        // Handle AI companion messages
        if (data.message) {
          setCompanionMessage(data.message);
        }

        // Handle Pomodoro updates
        if (data.pomodoro) {
          setPomodoroState(prev => ({
            ...prev,
            ...data.pomodoro,
          }));
        }

        // Handle current task updates
        if (data.current_task) {
          setCurrentTask(data.current_task);
        }
      };

      // Register event listeners
      wsService.on('connected', handleConnected);
      wsService.on('disconnected', handleDisconnected);
      wsService.on('message', handleMessage);
      wsService.on('focus_update', handleMessage);
      wsService.on('pomodoro_update', handleMessage);
      wsService.on('ai_message', handleMessage);

      // Cleanup event listeners
      return () => {
        wsService.off('connected', handleConnected);
        wsService.off('disconnected', handleDisconnected);
        wsService.off('message', handleMessage);
        wsService.off('focus_update', handleMessage);
        wsService.off('pomodoro_update', handleMessage);
        wsService.off('ai_message', handleMessage);
      };
    }
  }, [isOnboarding]);

  const handleOnboardingComplete = (data) => {
    setSessionData(data);
    setCurrentTask(data.currentTask || '');
    setIsOnboarding(false);
  };

  // Pomodoro control handlers
  const handleStartPomodoro = async () => {
    console.log('Starting pomodoro session...');
    
    // Start the pomodoro timer locally immediately
    setPomodoroState(prev => {
      const newState = {
        ...prev,
        isRunning: true,
        isBreak: false,
        timeRemaining: 25 * 60, // 25 minutes in seconds
      };
      console.log('Setting pomodoro state:', newState);
      return newState;
    });
    
    // Start the pomodoro timer via WebSocket (if connected)
    if (isConnected) {
      wsService.send({ action: 'start_pomodoro' });
    }
    
    // Start music playback if audio type is available
    if (sessionData && sessionData.audioType) {
      try {
        console.log('Starting music with audio type:', sessionData.audioType);
        const response = await fetch('http://localhost:8000/api/music/start', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({
            audio_type: sessionData.audioType,
            session_id: sessionData.sessionId || null,
            duration_minutes: sessionData.duration || null,
          }),
        });
        
        if (response.ok) {
          const data = await response.json();
          console.log('Music started:', data);
          
          // Start music player with YouTube ID
          if (data.youtube_id) {
            console.log('Setting music state with YouTube ID:', data.youtube_id);
            setMusicState({
              youtubeId: data.youtube_id,
              isPlaying: true,
              audioType: data.audio_type,
            });
          } else {
            console.warn('No YouTube ID in response:', data);
          }
        } else {
          const errorText = await response.text();
          console.error('Failed to start music:', errorText);
        }
      } catch (error) {
        console.error('Error starting music:', error);
      }
    } else {
      console.warn('No session data or audio type available');
    }
  };

  // Stop Pomodoro
  const handleStopPomodoro = async () => {
    setPomodoroState(prev => ({
      ...prev,
      isRunning: false,
    }));
    
    // Pause music when pomodoro stops
    if (musicState.isPlaying) {
      setMusicState(prev => ({ ...prev, isPlaying: false }));
      try {
        await fetch('http://localhost:8000/api/music/pause', {
          method: 'POST',
        });
      } catch (error) {
        console.error('Error pausing music:', error);
      }
    }
    
    if (isConnected) {
      wsService.send({ action: 'stop_pomodoro' });
    }
  };

  // Reset Pomodoro
  const handleResetPomodoro = async () => {
    setPomodoroState(prev => ({
      ...prev,
      isRunning: false,
      isBreak: false,
      timeRemaining: 25 * 60,
    }));
    
    // Stop music when pomodoro resets
    if (musicState.youtubeId) {
      setMusicState(prev => ({ ...prev, isPlaying: false, youtubeId: null }));
      try {
        await fetch('http://localhost:8000/api/music/stop', {
          method: 'POST',
        });
      } catch (error) {
        console.error('Error stopping music:', error);
      }
    }
    
    if (isConnected) {
      wsService.send({ action: 'reset_pomodoro' });
    }
  };
  
  // Handle music player state changes
  const handleMusicStateChange = (state) => {
    console.log('Music player state changed:', state);
    if (state === 'playing') {
      setMusicState(prev => ({ ...prev, isPlaying: true }));
    } else if (state === 'paused') {
      setMusicState(prev => ({ ...prev, isPlaying: false }));
    }
  };

  // Poll attention detection status
  useEffect(() => {
    if (!pomodoroState.isRunning || pomodoroState.isBreak) {
      // Stop attention detection when session is inactive
      fetch('http://localhost:8000/api/attention/stop', {
        method: 'POST',
      }).catch(err => console.error('Error stopping attention detection:', err));
      return;
    }

    // Start attention detection when session is active
    fetch('http://localhost:8000/api/attention/start', {
      method: 'POST',
    }).catch(err => console.error('Error starting attention detection:', err));

    // Poll attention status every 500ms
    const interval = setInterval(async () => {
      try {
        const response = await fetch('http://localhost:8000/api/attention/status');
        if (response.ok) {
          const data = await response.json();
          console.log('Attention status:', data);
          setFocusData(prev => ({
            ...prev,
            isFocused: data.is_attentive || false,
            focusScore: data.attention_percentage || 0,
          }));
        }
      } catch (error) {
        console.error('Error fetching attention status:', error);
      }
    }, 500);

    return () => {
      clearInterval(interval);
      // Stop attention detection on cleanup
      fetch('http://localhost:8000/api/attention/stop', {
        method: 'POST',
      }).catch(err => console.error('Error stopping attention detection:', err));
    };
  }, [pomodoroState.isRunning, pomodoroState.isBreak]);

  // Show onboarding first
  if (isOnboarding) {
    return <Onboarding onComplete={handleOnboardingComplete} />;
  }

  // Render the main app UI
  return (
    <div className="app">
      <div className={`status-indicator ${isConnected ? 'connected' : 'disconnected'}`}>
        <span className="status-dot"></span>
        {isConnected ? 'Connected' : 'Disconnected'}
      </div>

      <header className="app-header">
        <h2 className="current-task-title">{currentTask || 'Ready to start!'}</h2>
      </header>

      <div className="app-content-simple">
        <div className="app-left">
          <Companion 
            message={companionMessage}
            focusScore={focusData.focusScore}
            isFocused={
              // Only pass focus state when session is active
              // When session is inactive, pass undefined to show neutral
              pomodoroState.isRunning && !pomodoroState.isBreak
                ? (focusData.isFocused !== undefined ? focusData.isFocused : false)
                : undefined // undefined = session inactive, show neutral
            }
            isBreak={pomodoroState.isBreak}
            isSessionActive={pomodoroState.isRunning && !pomodoroState.isBreak}
          />
        </div>

        <div className="app-right">
          <Pomodoro
            state={pomodoroState}
            onStart={handleStartPomodoro}
            onStop={handleStopPomodoro}
            onReset={handleResetPomodoro}
          />
        </div>
      </div>
      
      {/* Background music player */}
      {musicState.youtubeId && (
        <MusicPlayer
          youtubeId={musicState.youtubeId}
          isPlaying={musicState.isPlaying && pomodoroState.isRunning}
          onStateChange={handleMusicStateChange}
        />
      )}
      
      
      {/* Debug info - remove in production */}
      {process.env.NODE_ENV === 'development' && (
        <div style={{
          position: 'fixed',
          bottom: '10px',
          left: '10px',
          background: 'rgba(0,0,0,0.7)',
          color: 'white',
          padding: '10px',
          borderRadius: '5px',
          fontSize: '12px',
          zIndex: 9999
        }}>
          <div>WebSocket: {isConnected ? 'Connected' : 'Disconnected'}</div>
          <div>Pomodoro Running: {pomodoroState.isRunning ? 'Yes' : 'No'}</div>
          <div>Pomodoro Break: {pomodoroState.isBreak ? 'Yes' : 'No'}</div>
          <div>Focus Data: {focusData.isFocused !== undefined ? (focusData.isFocused ? 'Focused' : 'Not Focused') : 'Unknown'}</div>
          <div>Focus Score: {focusData.focusScore}%</div>
          <div>Is Focused (final): {isConnected && focusData.isFocused !== undefined ? (focusData.isFocused ? 'Yes' : 'No') : (pomodoroState.isRunning && !pomodoroState.isBreak ? 'Yes (fallback)' : 'No')}</div>
          {musicState.youtubeId && (
            <>
              <div>Music: {musicState.isPlaying ? 'Playing' : 'Paused'}</div>
              <div>YouTube ID: {musicState.youtubeId}</div>
            </>
          )}
        </div>
      )}
    </div>
  );
}

export default App;



