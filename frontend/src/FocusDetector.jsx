import React, { useEffect, useRef, useState } from 'react';
import * as faceapi from 'face-api.js';

/**
 * FocusDetector component that uses webcam to detect if user is focused
 * Uses face-api.js for face detection and calculates focus based on:
 * - Face presence and position (centered = focused)
 * - Eye visibility (both eyes visible = focused)
 * - Face size (appropriate distance = focused)
 */
function FocusDetector({ isActive, onFocusChange }) {
  const videoRef = useRef(null);
  const canvasRef = useRef(null);
  const streamRef = useRef(null);
  const detectionIntervalRef = useRef(null);
  const [isDetecting, setIsDetecting] = useState(false);
  const [modelsLoaded, setModelsLoaded] = useState(false);

  // Load face-api.js models
  useEffect(() => {
    const loadModels = async () => {
      try {
        const MODEL_URL = '/models'; // Models should be in public/models folder
        
        // Try to load models, fallback to CDN if not found locally
        try {
          await Promise.all([
            faceapi.nets.tinyFaceDetector.loadFromUri(MODEL_URL),
            faceapi.nets.faceLandmark68Net.loadFromUri(MODEL_URL),
          ]);
        } catch (e) {
          // If local models not found, use CDN
          console.log('Loading models from CDN...');
          await Promise.all([
            faceapi.nets.tinyFaceDetector.loadFromUri('https://cdn.jsdelivr.net/npm/face-api.js@0.22.2/weights'),
            faceapi.nets.faceLandmark68Net.loadFromUri('https://cdn.jsdelivr.net/npm/face-api.js@0.22.2/weights'),
          ]);
        }
        
        setModelsLoaded(true);
        console.log('Face detection models loaded');
      } catch (error) {
        console.error('Error loading face detection models:', error);
        // Continue with basic detection if models fail to load
        setModelsLoaded(false);
      }
    };

    loadModels();
  }, []);

  useEffect(() => {
    if (!isActive) {
      // Stop detection when inactive
      stopDetection();
      return;
    }

    // Start detection when active (wait for models if needed)
    if (modelsLoaded || !modelsLoaded) { // Start even if models not loaded (fallback)
      startDetection();
    }

    return () => {
      stopDetection();
    };
  }, [isActive, modelsLoaded]);

  const startDetection = async () => {
    try {
      // Request webcam access
      const stream = await navigator.mediaDevices.getUserMedia({
        video: {
          width: { ideal: 640 },
          height: { ideal: 480 },
          facingMode: 'user'
        }
      });

      streamRef.current = stream;
      
      if (videoRef.current) {
        videoRef.current.srcObject = stream;
        videoRef.current.play();
        
        // Wait for video to be ready
        videoRef.current.onloadedmetadata = () => {
          setIsDetecting(true);
          startFocusDetection();
        };
      }
    } catch (error) {
      console.error('Error accessing webcam:', error);
      // If webcam access fails, assume not focused
      if (onFocusChange) {
        onFocusChange(false, 0);
      }
    }
  };

  const stopDetection = () => {
    setIsDetecting(false);
    
    // Stop detection interval
    if (detectionIntervalRef.current) {
      clearInterval(detectionIntervalRef.current);
      detectionIntervalRef.current = null;
    }

    // Stop video stream
    if (streamRef.current) {
      streamRef.current.getTracks().forEach(track => track.stop());
      streamRef.current = null;
    }

    if (videoRef.current) {
      videoRef.current.srcObject = null;
    }
  };

  const startFocusDetection = async () => {
    if (!videoRef.current || !canvasRef.current) return;

    const video = videoRef.current;
    const canvas = canvasRef.current;
    const ctx = canvas.getContext('2d');

    // Set canvas size to match video
    canvas.width = video.videoWidth || 640;
    canvas.height = video.videoHeight || 480;

    // Focus detection using face-api.js or fallback
    detectionIntervalRef.current = setInterval(async () => {
      if (!video || video.readyState !== video.HAVE_ENOUGH_DATA) return;

      // Draw current frame to canvas
      ctx.drawImage(video, 0, 0, canvas.width, canvas.height);

      let isFocused = false;
      let focusScore = 0;

      if (modelsLoaded) {
        // Use face-api.js for accurate detection
        const detection = await faceapi
          .detectSingleFace(video, new faceapi.TinyFaceDetectorOptions())
          .withFaceLandmarks();

        if (detection) {
          const { detection: faceDetection, landmarks } = detection;
          
          // Calculate focus based on:
          // 1. Face position (centered = focused)
          // 2. Face size (appropriate distance = focused)
          // 3. Eye visibility (both eyes visible = focused)
          
          const box = faceDetection.box;
          const faceCenterX = box.x + box.width / 2;
          const faceCenterY = box.y + box.height / 2;
          const frameCenterX = canvas.width / 2;
          const frameCenterY = canvas.height / 2;
          
          // Calculate how centered the face is (0-100)
          const xOffset = Math.abs(faceCenterX - frameCenterX) / (canvas.width / 2);
          const yOffset = Math.abs(faceCenterY - frameCenterY) / (canvas.height / 2);
          const centeredScore = (1 - Math.min(1, (xOffset + yOffset) / 2)) * 100;
          
          // Calculate face size score (appropriate size = focused)
          const faceArea = box.width * box.height;
          const frameArea = canvas.width * canvas.height;
          const faceRatio = faceArea / frameArea;
          let sizeScore = 0;
          if (faceRatio > 0.05 && faceRatio < 0.30) {
            sizeScore = 100; // Good size
          } else if (faceRatio > 0.02 && faceRatio < 0.50) {
            sizeScore = 50; // Acceptable size
          }
          
          // Check if eyes are visible (using landmarks)
          const leftEye = landmarks.getLeftEye();
          const rightEye = landmarks.getRightEye();
          const eyesVisible = leftEye.length > 0 && rightEye.length > 0;
          const eyeScore = eyesVisible ? 100 : 0;
          
          // Calculate overall focus score
          focusScore = (centeredScore * 0.4 + sizeScore * 0.3 + eyeScore * 0.3);
          isFocused = focusScore >= 60; // Threshold for "focused"
        } else {
          // No face detected = not focused
          isFocused = false;
          focusScore = 0;
        }
      } else {
        // Fallback: simple detection
        const imageData = ctx.getImageData(0, 0, canvas.width, canvas.height);
        isFocused = detectFocusFallback(imageData, canvas.width, canvas.height);
        focusScore = isFocused ? 70 : 20;
      }

      if (onFocusChange) {
        onFocusChange(isFocused, Math.round(focusScore));
      }
    }, 500); // Check every 500ms
  };

  const detectFocusFallback = (imageData, width, height) => {
    // Simple heuristic-based focus detection fallback
    const data = imageData.data;
    const centerX = width / 2;
    const centerY = height / 2;
    
    // Sample center region for face-like features
    const sampleSize = 100;
    const startX = Math.max(0, centerX - sampleSize / 2);
    const startY = Math.max(0, centerY - sampleSize / 2);
    const endX = Math.min(width, centerX + sampleSize / 2);
    const endY = Math.min(height, centerY + sampleSize / 2);
    
    let skinTonePixels = 0;
    let totalPixels = 0;
    
    // Check center region for skin tone (simple RGB heuristic)
    for (let y = startY; y < endY; y += 5) {
      for (let x = startX; x < endX; x += 5) {
        const index = (y * width + x) * 4;
        const r = data[index];
        const g = data[index + 1];
        const b = data[index + 2];
        
        // Simple skin tone detection
        if (r > 95 && g > 40 && b > 20 && 
            Math.max(r, g, b) - Math.min(r, g, b) > 15 &&
            r > g && r > b) {
          skinTonePixels++;
        }
        totalPixels++;
      }
    }
    
    // If we detect enough skin tone in center, assume focused
    const skinRatio = skinTonePixels / totalPixels;
    return skinRatio > 0.1; // Threshold for "focused"
  };

  // Hidden video and canvas elements
  return (
    <div style={{ display: 'none' }}>
      <video
        ref={videoRef}
        autoPlay
        playsInline
        muted
        style={{ width: '1px', height: '1px' }}
      />
      <canvas ref={canvasRef} style={{ display: 'none' }} />
    </div>
  );
}

export default FocusDetector;

