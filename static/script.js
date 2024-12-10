document.addEventListener('DOMContentLoaded', () => {
    const startBtn = document.getElementById('start-btn');
    const stopBtn = document.getElementById('stop-btn');
    const botStatusElement = document.getElementById('bot-status');
    const statusIndicator = document.getElementById('status-indicator');

    async function updateBotStatus(endpoint) {
        try {
            const response = await fetch(endpoint, { method: 'POST' });
            const data = await response.json();
            
            if (endpoint.includes('start_bot')) {
                botStatusElement.textContent = 'Running';
                statusIndicator.classList.remove('status-stopped');
                statusIndicator.classList.add('status-running');
            } else if (endpoint.includes('stop_bot')) {
                botStatusElement.textContent = 'Stopped';
                statusIndicator.classList.remove('status-running');
                statusIndicator.classList.add('status-stopped');
            }
            
            alert(data.status);
        } catch (error) {
            console.error('Error:', error);
            alert('An error occurred');
        }
    }

    if (startBtn) {
        startBtn.addEventListener('click', () => updateBotStatus('/start_bot'));
    }

    if (stopBtn) {
        stopBtn.addEventListener('click', () => updateBotStatus('/stop_bot'));
    }
});
