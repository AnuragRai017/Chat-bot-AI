document.addEventListener('DOMContentLoaded', function() {
    const chatForm = document.getElementById('chat-form');
    const messagesContainer = document.getElementById('chat-messages');

    chatForm.addEventListener('submit', async function(e) {
        e.preventDefault();

        const employeeId = document.getElementById('employee-id').value;
        const query = document.getElementById('query').value;

        if (!employeeId || !query) {
            showError('Please fill in all fields');
            return;
        }

        try {
            // Show loading state
            const submitButton = chatForm.querySelector('button');
            submitButton.disabled = true;
            submitButton.textContent = 'Processing...';

            // Make API request
            const response = await fetch('/chat', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    employee_id: employeeId,
                    query: query
                })
            });

            const data = await response.json();

            if (!response.ok) {
                throw new Error(data.error || 'Failed to get response');
            }

            // Add messages to chat
            appendMessage('query', `Employee ID: ${employeeId}\nQuery: ${query}`);
            appendMessage('response', data.response);

            // Clear form
            document.getElementById('query').value = '';

        } catch (error) {
            showError(error.message);
        } finally {
            // Reset button state
            submitButton.disabled = false;
            submitButton.textContent = 'Send';
        }
    });

    function appendMessage(type, content) {
        const messageDiv = document.createElement('div');
        messageDiv.className = `message ${type}`;
        messageDiv.textContent = content;
        messagesContainer.appendChild(messageDiv);
        messagesContainer.scrollTop = messagesContainer.scrollHeight;
    }

    function showError(message) {
        const errorDiv = document.getElementById('error-message');
        errorDiv.textContent = message;
        errorDiv.style.display = 'block';
        setTimeout(() => {
            errorDiv.style.display = 'none';
        }, 3000);
    }
});
