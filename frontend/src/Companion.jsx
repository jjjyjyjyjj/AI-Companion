// Companion component for the AI-powered study companion
import React, { useState, useEffect, useRef } from 'react';
import './Companion.css';

// Companion component props
function Companion({ message, focusScore, isFocused, isBreak, isSessionActive }) {
  const [isSpeaking, setIsSpeaking] = useState(false);
  const synthRef = useRef(null); // Reference to the Web Speech API

  useEffect(() => {
    // Initialize the Web Speech API
    synthRef.current = window.speechSynthesis;
    
    // Cleanup the Web Speech API
    return () => {
      if (synthRef.current) {
        synthRef.current.cancel();
      }
    };
  }, []);

  // Speak the message using Web Speech API (text-to-speech)
  useEffect(() => {
    if (message && synthRef.current && message.trim()) {
      const utterance = new SpeechSynthesisUtterance(message);
      utterance.rate = 0.9;
      utterance.pitch = 1.1;
      utterance.volume = 0.8;
      
      utterance.onstart = () => setIsSpeaking(true);
      utterance.onend = () => setIsSpeaking(false);
      utterance.onerror = () => setIsSpeaking(false);
      
      synthRef.current.speak(utterance);
    }
  }, [message]);

  // Get the companion's emotion based on the focus state
  const getCompanionEmotion = () => {
    // Show sleeping state during breaks
    if (isBreak) {
      return 'sleeping';
    }
    
    // If session is inactive (not running), always show neutral
    if (!isSessionActive) {
      return 'neutral';
    }
    
    // If session is active (pomodoro running), show happy when focused, mad when not focused
    if (isFocused === true) {
      return 'happy';
    }
    
    // Session is active but not focused
    return 'mad';
  };

  const emotion = getCompanionEmotion();
  
  // Debug logging
  useEffect(() => {
    console.log('Companion emotion state:', { 
      emotion, 
      isFocused, 
      isBreak, 
      isSessionActive,
      focusScore,
      calculatedEmotion: emotion
    });
  }, [emotion, isFocused, isBreak, isSessionActive, focusScore]);

  return (
    <div className="companion-container-simple">
      <div className="companion-avatar-simple">
        <div className={`companion-face ${emotion}`}>
          <span className="companion-emoji">
            {emotion === 'sleeping' && '😴'}
            {emotion === 'happy' && '😊'}
            {emotion === 'mad' && '😠'}
            {emotion === 'neutral' && '😐'}
          </span>
        </div>
        {isSpeaking && <div className="speaking-indicator">🔊</div>}
      </div>
    </div>
  );
}

export default Companion;



