document.addEventListener('DOMContentLoaded', function() {
    const loginForm = document.getElementById('login-form');
    const loginSection = document.getElementById('login-section');
    const chatSection = document.getElementById('chat-section');
    const chatForm = document.getElementById('chat-form');
    const messagesContainer = document.getElementById('chat-messages');
    const currentEmployeeId = document.getElementById('current-employee-id');
    
    let activeEmployeeId = '';
    let questionCount = 0;
    const MAX_QUESTIONS = 10;

    // Handle login
    loginForm.addEventListener('submit', async function(e) {
        e.preventDefault();
        const employeeId = document.getElementById('employee-id').value;
        
        try {
            // Validate employee ID exists
            const response = await fetch('/chat', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    employee_id: employeeId,
                    query: 'Hello' // Initial greeting
                })
            });

            const data = await response.json();
            
            if (!response.ok) {
                throw new Error(data.error || 'Invalid Employee ID');
            }

            // Reset question count
            questionCount = 0;

            // Store employee ID and switch to chat interface
            activeEmployeeId = employeeId;
            currentEmployeeId.textContent = employeeId;
            
            // Switch sections
            loginSection.style.display = 'none';
            chatSection.style.display = 'flex';

            // Show welcome message
            appendMessage('response', 'Welcome! How can I help you with your salary information today?');
            
            // Load chat history if available
            if (data.history && data.history.length > 0) {
                data.history.forEach(item => {
                    appendMessage('query', item.query, item.timestamp);
                    appendMessage('response', item.response, item.timestamp);
                    questionCount++;
                });
            }

            updateQuestionCounter();
            // Focus on chat input
            document.getElementById('query').focus();

        } catch (error) {
            const loginError = document.getElementById('login-error');
            loginError.textContent = error.message;
            loginError.style.display = 'block';
            setTimeout(() => {
                loginError.style.display = 'none';
            }, 3000);
        }
    });

    // Handle chat messages
    chatForm.addEventListener('submit', async function(e) {
        e.preventDefault();
        
        const query = document.getElementById('query').value;
        if (!query) return;

        // Check question limit
        if (questionCount >= MAX_QUESTIONS) {
            appendMessage('response', 'You have reached the maximum number of questions (10). Please refresh the page to start a new session.');
            return;
        }

        const submitButton = chatForm.querySelector('button');
        
        try {
            // Show user message immediately
            appendMessage('query', query);
            questionCount++;
            updateQuestionCounter();
            
            // Clear input and disable button
            document.getElementById('query').value = '';
            submitButton.disabled = true;

            // Send request
            const response = await fetch('/chat', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    employee_id: activeEmployeeId,
                    query: query
                })
            });

            const data = await response.json();
            
            if (!response.ok) {
                throw new Error(data.error || 'Failed to get response');
            }

            // Show bot response
            appendMessage('response', data.response);

        } catch (error) {
            appendMessage('response', 'Sorry, I encountered an error: ' + error.message);
            questionCount--; // Reduce question count if there was an error
            updateQuestionCounter();
        } finally {
            // Re-enable button if we haven't reached the limit
            submitButton.disabled = questionCount >= MAX_QUESTIONS;
        }
    });

    function updateQuestionCounter() {
        const counterDiv = document.getElementById('question-counter');
        counterDiv.textContent = `Questions: ${questionCount}/${MAX_QUESTIONS}`;
        
        // Update input state
        const queryInput = document.getElementById('query');
        const submitButton = chatForm.querySelector('button');
        
        if (questionCount >= MAX_QUESTIONS) {
            queryInput.disabled = true;
            queryInput.placeholder = 'Maximum questions reached. Please refresh to start new session.';
            submitButton.disabled = true;
        } else {
            queryInput.disabled = false;
            queryInput.placeholder = 'Ask about your salary, deductions, leaves...';
            submitButton.disabled = false;
        }
    }

    function appendMessage(type, content, timestamp = null) {
        const messageDiv = document.createElement('div');
        messageDiv.className = `message ${type}`;
        
        // Add message content
        const contentP = document.createElement('p');
        if (type === 'response') {
            contentP.innerHTML = content; // Allow HTML for bot responses
        } else {
            contentP.textContent = content; // Plain text for user messages
        }
        messageDiv.appendChild(contentP);
        
        // Add timestamp
        if (!timestamp) {
            timestamp = new Date().toISOString();
        }
        const timeDiv = document.createElement('div');
        timeDiv.className = 'timestamp';
        timeDiv.textContent = formatTimestamp(timestamp);
        messageDiv.appendChild(timeDiv);
        
        messagesContainer.appendChild(messageDiv);
        messagesContainer.scrollTop = messagesContainer.scrollHeight;
    }

    function formatTimestamp(timestamp) {
        const date = new Date(timestamp);
        const now = new Date();
        const diffDays = Math.floor((now - date) / (1000 * 60 * 60 * 24));
        
        if (diffDays === 0) {
            return `Today at ${date.toLocaleTimeString()}`;
        } else if (diffDays === 1) {
            return `Yesterday at ${date.toLocaleTimeString()}`;
        } else if (diffDays < 7) {
            return `${diffDays} days ago at ${date.toLocaleTimeString()}`;
        } else {
            return date.toLocaleString();
        }
    }
});
