// Ensure DOM is loaded before running script
document.addEventListener('DOMContentLoaded', () => {
    const socket = io(); // Connect to Socket.IO server (Flask)

    const phoneNumberInput = document.getElementById('phoneNumber');
    const callButton = document.getElementById('callButton');
    const endCallButton = document.getElementById('endCallButton');
    const statusDiv = document.getElementById('status');
    const logUl = document.getElementById('log');
    const audioPlayer = document.getElementById('audioPlayer');

    let recognition;
    let isRecognizing = false;
    let currentCallId = null;
    let conversationActive = false;

    // Check for browser support for Web Speech API
    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
    if (!SpeechRecognition) {
        alert("Your browser does not support the Web Speech API. Please use Chrome or Edge.");
        callButton.disabled = true;
    } else {
        recognition = new SpeechRecognition();
        recognition.continuous = false; // Process single utterances
        recognition.interimResults = false; // We want final results
        recognition.lang = 'en-US'; // Set language

        recognition.onstart = () => {
            isRecognizing = true;
            updateStatus('Listening...');
            console.log('Speech recognition started');
        };

        recognition.onresult = (event) => {
            const transcript = event.results[event.results.length - 1][0].transcript.trim();
            console.log('Transcript:', transcript);
            if (transcript && conversationActive) {
                 addLogMessage('User', transcript);
                 updateStatus('Processing your speech...');
                 // Send transcribed text to backend
                 socket.emit('audio_input', { text: transcript, call_id: currentCallId });
            } else if (!conversationActive) {
                 console.log("Recognition result ignored, conversation not active.")
            }
        };

        recognition.onerror = (event) => {
            console.error('Speech recognition error:', event.error);
            updateStatus(`Error: ${event.error}`);
            if(event.error === 'no-speech' && conversationActive) {
                // If no speech was detected, maybe prompt again or wait
                console.log("No speech detected, maybe start listening again?")
                // Optionally restart listening if desired and conversation is active
                // stopRecognition(); // Ensure it's stopped before possibly restarting
                // setTimeout(startRecognition, 500); // Restart listening after a short delay
            } else {
                 isRecognizing = false;
                 conversationActive = false; // Stop interaction on other errors
                 callButton.disabled = false;
                 endCallButton.disabled = true;
            }

        };

        recognition.onend = () => {
            isRecognizing = false;
            console.log('Speech recognition ended');
            // If the conversation is still supposed to be active, restart listening
            if (conversationActive) {
                // Avoid immediate restart if we just got a result and are waiting for AI
                console.log("Recognition ended, will restart if needed after AI response.");
                // updateStatus("Waiting for AI response..."); // Set status here if needed
            } else {
                 updateStatus("Recognition stopped.");
            }
        };
    }

    function startRecognition() {
        if (recognition && !isRecognizing && conversationActive) {
            try {
                recognition.start();
            } catch (e) {
                console.error("Error starting recognition:", e);
                 updateStatus("Error starting listening.");
                 // Maybe try again or disable functionality
            }
        } else if (isRecognizing) {
            console.log("Recognition already active.");
        } else if (!conversationActive) {
             console.log("Cannot start recognition, conversation not active.");
        }
         else {
             console.error("Recognition API not available.");
             updateStatus("Speech recognition not available.");
        }
    }

     function stopRecognition() {
         if (recognition && isRecognizing) {
            recognition.stop();
            isRecognizing = false; // Ensure flag is reset even if onend doesn't fire immediately
            console.log("Recognition stopped manually.");
         }
     }

    function updateStatus(message) {
        statusDiv.textContent = `Status: ${message}`;
    }

    function addLogMessage(speaker, text) {
        const li = document.createElement('li');
        li.classList.add(speaker.toLowerCase());
        li.textContent = `${speaker}: ${text}`;
        logUl.appendChild(li);
        logUl.scrollTop = logUl.scrollHeight; // Scroll to bottom
    }

    function playAudio(audioUrl) {
        console.log("Attempting to play audio:", audioUrl);
        audioPlayer.src = audioUrl;
        // Ensure previous playback is stopped if any
        audioPlayer.pause();
        audioPlayer.currentTime = 0;

        // Play the new audio
        audioPlayer.play()
            .then(() => {
                updateStatus('AI Speaking...');
                console.log("Audio playback started.");
            })
            .catch(error => {
                console.error('Error playing audio:', error);
                updateStatus('Error playing AI response.');
                // If playback failed, maybe try restarting recognition sooner
                if (conversationActive) {
                    startRecognition();
                }
            });
    }

     // Re-enable listening after AI has finished speaking
     audioPlayer.onended = () => {
         console.log("Audio playback finished.");
         updateStatus('Waiting for your response...');
         if (conversationActive) {
             startRecognition(); // Start listening for user response
         }
     };

     audioPlayer.onerror = (e) => {
        console.error("Audio player error:", e);
        updateStatus("Error playing audio.");
        // Even if audio fails, restart recognition if conversation is active
        if (conversationActive) {
            startRecognition();
        }
    };


    // --- SocketIO Event Handlers ---
    socket.on('connect', () => {
        console.log('Connected to server');
        updateStatus('Connected. Ready to start.');
    });

    socket.on('disconnect', () => {
        console.log('Disconnected from server');
        updateStatus('Disconnected from server.');
        stopRecognition();
        conversationActive = false;
        callButton.disabled = false;
        endCallButton.disabled = true;
        currentCallId = null;
    });

    socket.on('call_started', (data) => {
        console.log('Call started event received:', data);
        if(data.status === 'success' && data.call_id) {
            currentCallId = data.call_id;
            conversationActive = true;
            callButton.disabled = true;
            endCallButton.disabled = false;
            phoneNumberInput.disabled = true;
            logUl.innerHTML = ''; // Clear previous log
            addLogMessage('System', `Call simulation started for ${data.number}. Call ID: ${data.call_id}`);
            updateStatus('Call simulation active. Waiting for initial prompt or user speech.');
            // Optional: Play an initial greeting from the AI immediately
            // if(data.initial_message) {
            //     playAudio(data.initial_message_url);
            // } else {
            //     startRecognition(); // Or start listening immediately
            // }
            // Let's start listening immediately for this example
             startRecognition();
        } else {
             updateStatus(`Error starting call: ${data.message}`);
             callButton.disabled = false;
             endCallButton.disabled = true;
        }
    });

    socket.on('agent_response', (data) => {
        console.log('Agent response received:', data);
        if (data.text && data.audio_url && conversationActive) {
             addLogMessage('Agent', data.text);
             stopRecognition(); // Stop listening while AI speaks
             playAudio(data.audio_url); // Play the AI's response audio
             // Recognition will restart automatically via audioPlayer.onended
        } else if (!conversationActive) {
            console.log("Agent response ignored, conversation not active.")
        }
         else {
             console.error("Invalid agent response data:", data);
             updateStatus("Received invalid response from agent.");
             // Decide whether to retry listening or stop
             startRecognition(); // Try listening again
         }
    });

     socket.on('call_ended', (data) => {
         console.log('Call ended event received:', data);
         updateStatus(`Call simulation ended. Reason: ${data.reason || 'User action'}`);
         stopRecognition();
         conversationActive = false;
         currentCallId = null;
         callButton.disabled = false;
         endCallButton.disabled = true;
         phoneNumberInput.disabled = false;
         addLogMessage('System', `Call simulation ended.`);
     });

     socket.on('status_update', (data) => {
         updateStatus(data.message);
     });


    // --- Button Event Listeners ---
    callButton.addEventListener('click', () => {
        const phoneNumber = phoneNumberInput.value.trim();
        if (!phoneNumber) {
            alert('Please enter a phone number.');
            return;
        }
         if (!SpeechRecognition) {
             alert("Speech Recognition API not available in this browser.");
             return;
         }

        updateStatus('Starting call simulation...');
        callButton.disabled = true; // Disable button immediately
        endCallButton.disabled = false;
        socket.emit('start_call', { number: phoneNumber });
    });

     endCallButton.addEventListener('click', () => {
        if (currentCallId) {
            updateStatus('Ending call simulation...');
            socket.emit('end_call', { call_id: currentCallId });
            // UI updates will happen based on the 'call_ended' event from the server
        }
         stopRecognition(); // Ensure recognition stops
         conversationActive = false; // Mark conversation as inactive
         callButton.disabled = false;
         endCallButton.disabled = true;
         phoneNumberInput.disabled = false;
     });

}); // End DOMContentLoaded