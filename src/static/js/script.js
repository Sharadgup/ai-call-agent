document.addEventListener('DOMContentLoaded', function() {
    const phoneNumberInput = document.getElementById('phoneNumber');
    const callButton = document.getElementById('callButton');
    const statusDiv = document.getElementById('status');
    const callSidSpan = document.getElementById('callSid');
    const dbIdSpan = document.getElementById('dbId');
    const twilioStatusSpan = document.getElementById('twilioStatus');
    const recordingUrlSpan = document.getElementById('recordingUrl');
    const callDetailsDiv = document.getElementById('callDetails');

    callButton.addEventListener('click', function() {
        const phoneNumber = phoneNumberInput.value.trim();

        if (!phoneNumber) {
            displayStatus('Please enter a phone number.', 'error');
            return;
        }

        // Basic validation (you might need more robust validation)
        if (!/^\+?[1-9]\d{1,14}$/.test(phoneNumber)) {
             displayStatus('Please enter a valid phone number (e.g., +11234567890).', 'error');
             return;
        }


        callButton.disabled = true;
        displayStatus('Initiating call...', 'info');
        resetCallDetails();


        fetch('/initiate_call', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ number: phoneNumber }),
        })
        .then(response => response.json())
        .then(data => {
            if (data.status === 'success') {
                displayStatus(data.message, 'success');
                updateCallDetails(data);
                // Optional: Implement WebSocket here to receive real-time status updates from Flask
                // and update the callDetails spans dynamically
            } else {
                displayStatus(`Call failed: ${data.message}`, 'error');
                callButton.disabled = false;
            }
        })
        .catch((error) => {
            console.error('Error:', error);
            displayStatus(`An error occurred: ${error}`, 'error');
            callButton.disabled = false;
        });
    });

    function displayStatus(message, type) {
        statusDiv.textContent = message;
        statusDiv.className = 'status-message ' + type; // Clears previous classes
    }

    function updateCallDetails(data) {
        callSidSpan.textContent = data.call_sid || '-';
        dbIdSpan.textContent = data.db_id || '-';
        // Twilio status and recording URL will be updated by potential
        // real-time updates (e.g., via WebSockets) triggered by Twilio webhooks
        twilioStatusSpan.textContent = data.twilio_status || 'Initiated'; // Show initial status
        recordingUrlSpan.textContent = data.recording_url || '-';
        // Hide/Show call details section if needed
        callDetailsDiv.style.display = 'block'; // Assuming it starts hidden
    }

     function resetCallDetails() {
        callSidSpan.textContent = '-';
        dbIdSpan.textContent = '-';
        twilioStatusSpan.textContent = '-';
        recordingUrlSpan.textContent = '-';
        // Hide call details until a call is initiated
        // callDetailsDiv.style.display = 'none';
    }

    // Initial state
     resetCallDetails(); // Reset on page load
});