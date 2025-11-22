/**
 * Flow State Facilitator - Extension Popup Script
 */

const API_BASE = "http://127.0.0.1:8000/api";

// Update status display
async function updateStatus() {
    try {
        const response = await fetch(`${API_BASE}/status`);
        const data = await response.json();

        const indicator = document.getElementById('statusIndicator');
        const statusText = document.getElementById('statusText');
        const durationText = document.getElementById('durationText');
        const breakLink = document.getElementById('breakFlowLink');

        if (data.in_flow) {
            indicator.className = 'status-indicator active';
            statusText.textContent = 'In Flow State 🔥';

            const minutes = Math.floor(data.current_duration_seconds / 60);
            const seconds = data.current_duration_seconds % 60;
            durationText.textContent = `Duration: ${minutes}m ${seconds}s`;

            breakLink.style.display = 'block';
        } else {
            indicator.className = 'status-indicator inactive';
            statusText.textContent = 'Not in flow';
            durationText.textContent = 'Duration: 0m 0s';
            breakLink.style.display = 'none';
        }

    } catch (error) {
        console.error('Failed to fetch status:', error);
        document.getElementById('statusText').textContent = 'Server offline';
    }
}

// Open dashboard
document.getElementById('dashboardBtn').addEventListener('click', () => {
    chrome.tabs.create({ url: 'http://127.0.0.1:8000' });
});

// Break flow
document.getElementById('breakFlowLink').addEventListener('click', async (e) => {
    e.preventDefault();

    try {
        await fetch(`${API_BASE}/flow/break`, { method: 'POST' });
        updateStatus();
    } catch (error) {
        console.error('Failed to break flow:', error);
    }
});

// Update status on load and every 2 seconds
updateStatus();
setInterval(updateStatus, 2000);
