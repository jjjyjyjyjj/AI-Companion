import React, { useEffect, useRef, useState } from 'react';

/**
 * MusicPlayer component that plays YouTube videos in the background
 * Uses YouTube IFrame API for playback control
 */
function MusicPlayer({ youtubeId, isPlaying, onStateChange }) {
  const playerRef = useRef(null);
  const [player, setPlayer] = useState(null);
  const [isReady, setIsReady] = useState(false);
  const [apiLoading, setApiLoading] = useState(false);

  // Load YouTube IFrame API script
  useEffect(() => {
    if (window.YT && window.YT.Player) {
      console.log('YouTube API already loaded');
      setIsReady(true);
      return;
    }

    if (window.onYouTubeIframeAPIReady) {
      console.log('YouTube API already loading, waiting...');
      // API is already loading, wait for it
      const checkReady = setInterval(() => {
        if (window.YT && window.YT.Player) {
          console.log('YouTube API ready!');
          setIsReady(true);
          clearInterval(checkReady);
        }
      }, 100);
      return () => clearInterval(checkReady);
    }

    if (apiLoading) return;

    console.log('Loading YouTube IFrame API...');
    setApiLoading(true);

    // Load the API
    const tag = document.createElement('script');
    tag.src = 'https://www.youtube.com/iframe_api';
    const firstScriptTag = document.getElementsByTagName('script')[0];
    firstScriptTag.parentNode.insertBefore(tag, firstScriptTag);

    window.onYouTubeIframeAPIReady = () => {
      console.log('YouTube IFrame API ready callback fired');
      setIsReady(true);
    };
  }, [apiLoading]);

  // Initialize player when API is ready
  useEffect(() => {
    if (!isReady || !youtubeId) {
      if (!isReady) console.log('Waiting for YouTube API to be ready...');
      if (!youtubeId) console.log('Waiting for YouTube ID...');
      return;
    }

    console.log('Initializing YouTube player with ID:', youtubeId);

    if (player) {
      // If player exists, load new video
      console.log('Loading new video in existing player:', youtubeId);
      try {
        player.loadVideoById(youtubeId);
        if (isPlaying) {
          setTimeout(() => {
            player.playVideo();
          }, 500);
        }
      } catch (error) {
        console.error('Error loading video:', error);
      }
      return;
    }

    if (!playerRef.current) {
      console.error('Player ref not available');
      return;
    }

    console.log('Creating new YouTube player instance');

    // Create new player instance
    try {
      const newPlayer = new window.YT.Player(playerRef.current, {
        height: '1', // Very small but not 0 (some browsers block 0x0)
        width: '1',
        videoId: youtubeId,
        playerVars: {
          autoplay: isPlaying ? 1 : 0,
          controls: 0,
          disablekb: 1,
          enablejsapi: 1,
          fs: 0,
          iv_load_policy: 3,
          modestbranding: 1,
          playsinline: 1,
          rel: 0,
          showinfo: 0,
          loop: 1, // Loop the video
          playlist: youtubeId, // Required for loop to work
          mute: 0, // Make sure it's not muted
        },
        events: {
          onReady: (event) => {
            console.log('YouTube player ready!');
            try {
              event.target.setVolume(70); // Set volume to 70%
              if (isPlaying) {
                // Try to play immediately
                const playPromise = event.target.playVideo();
                if (playPromise !== undefined) {
                  playPromise.catch(error => {
                    console.error('Autoplay was prevented:', error);
                    // Try again after a short delay
                    setTimeout(() => {
                      try {
                        event.target.playVideo();
                        console.log('Retrying play after autoplay prevention');
                      } catch (e) {
                        console.error('Error retrying play:', e);
                      }
                    }, 1000);
                  });
                }
                console.log('Attempting to play video...');
              }
              if (onStateChange) {
                onStateChange('ready');
              }
            } catch (error) {
              console.error('Error in onReady:', error);
            }
          },
          onStateChange: (event) => {
            console.log('YouTube player state changed:', event.data);
            if (onStateChange) {
              // YT.PlayerState.PLAYING = 1
              // YT.PlayerState.PAUSED = 2
              // YT.PlayerState.ENDED = 0
              // YT.PlayerState.BUFFERING = 3
              // YT.PlayerState.CUED = 5
              if (event.data === window.YT.PlayerState.PLAYING) {
                console.log('Video is playing!');
                onStateChange('playing');
              } else if (event.data === window.YT.PlayerState.PAUSED) {
                console.log('Video is paused');
                onStateChange('paused');
              } else if (event.data === window.YT.PlayerState.ENDED) {
                console.log('Video ended');
                onStateChange('ended');
              } else if (event.data === window.YT.PlayerState.BUFFERING) {
                console.log('Video is buffering');
              }
            }
          },
          onError: (event) => {
            console.error('YouTube player error:', event.data);
            if (onStateChange) {
              onStateChange('error');
            }
          },
        },
      });

      setPlayer(newPlayer);
    } catch (error) {
      console.error('Error creating YouTube player:', error);
    }
  }, [isReady, youtubeId, isPlaying]);

  // Control playback based on isPlaying prop
  useEffect(() => {
    if (!player) {
      console.log('Player not ready yet, cannot control playback');
      return;
    }

    try {
      const playerState = player.getPlayerState();
      console.log('Current player state:', playerState, 'isPlaying prop:', isPlaying);

      if (isPlaying) {
        if (playerState !== window.YT.PlayerState.PLAYING) {
          console.log('Playing video...');
          const playPromise = player.playVideo();
          if (playPromise !== undefined) {
            playPromise.catch(error => {
              console.error('Play was prevented:', error);
              // Retry after a delay
              setTimeout(() => {
                try {
                  player.playVideo();
                } catch (e) {
                  console.error('Error retrying play:', e);
                }
              }, 500);
            });
          }
        }
      } else {
        if (playerState === window.YT.PlayerState.PLAYING) {
          console.log('Pausing video...');
          player.pauseVideo();
        }
      }
    } catch (error) {
      console.error('Error controlling playback:', error);
    }
  }, [isPlaying, player]);

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      if (player) {
        try {
          player.destroy();
        } catch (e) {
          console.error('Error destroying player:', e);
        }
      }
    };
  }, [player]);

  // Very small but visible container (browsers may block completely hidden players)
  return (
    <div style={{ 
      position: 'fixed',
      bottom: '-1px',
      right: '-1px',
      width: '1px',
      height: '1px',
      overflow: 'hidden',
      zIndex: -1,
      pointerEvents: 'none'
    }}>
      <div ref={playerRef}></div>
    </div>
  );
}

export default MusicPlayer;

