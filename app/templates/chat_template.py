CHAT_TEMPLATE = '''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
    <title>AI Chat</title>
    <link href="https://fonts.googleapis.com/icon?family=Material+Icons" rel="stylesheet">
    <style>
        :root {
            --primary-color: #007AFF;
            --secondary-color: #5856D6;
            --background-color: #F2F2F7;
            --bubble-user: #007AFF;
            --bubble-ai: #E9E9EB;
            --text-user: #FFFFFF;
            --text-ai: #000000;
            --input-background: #FFFFFF;
            --border-radius: 18px;
            --spacing: 12px;
        }

        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
            -webkit-tap-highlight-color: transparent;
        }

        body {
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
            background-color: var(--background-color);
            color: #000000;
            line-height: 1.4;
            -webkit-font-smoothing: antialiased;
            height: 100vh;
            display: flex;
            flex-direction: column;
        }

        .chat-container {
            max-width: 100%;
            height: 100vh;
            display: flex;
            flex-direction: column;
            background-color: var(--background-color);
        }

        .header {
            background-color: rgba(255, 255, 255, 0.8);
            backdrop-filter: blur(10px);
            -webkit-backdrop-filter: blur(10px);
            padding: var(--spacing);
            text-align: center;
            border-bottom: 1px solid rgba(0, 0, 0, 0.1);
            position: sticky;
            top: 0;
            z-index: 100;
        }

        .header h1 {
            font-size: 1.2rem;
            font-weight: 600;
            color: #000000;
        }

        .messages {
            flex: 1;
            overflow-y: auto;
            padding: var(--spacing);
            display: flex;
            flex-direction: column;
            gap: var(--spacing);
            -webkit-overflow-scrolling: touch;
        }

        .message {
            max-width: 85%;
            padding: 12px 16px;
            border-radius: var(--border-radius);
            position: relative;
            animation: fadeIn 0.3s ease-out;
            word-wrap: break-word;
        }

        @keyframes fadeIn {
            from { opacity: 0; transform: translateY(10px); }
            to { opacity: 1; transform: translateY(0); }
        }

        .message.user {
            background-color: var(--bubble-user);
            color: var(--text-user);
            align-self: flex-end;
            border-bottom-right-radius: 4px;
        }

        .message.ai {
            background-color: var(--bubble-ai);
            color: var(--text-ai);
            align-self: flex-start;
            border-bottom-left-radius: 4px;
        }

        .message-time {
            font-size: 0.7rem;
            opacity: 0.7;
            margin-top: 4px;
            text-align: right;
        }

        .input-area {
            background-color: rgba(255, 255, 255, 0.8);
            backdrop-filter: blur(10px);
            -webkit-backdrop-filter: blur(10px);
            padding: var(--spacing);
            border-top: 1px solid rgba(0, 0, 0, 0.1);
            position: sticky;
            bottom: 0;
            z-index: 100;
        }

        .input-container {
            display: flex;
            gap: 8px;
            align-items: flex-end;
        }

        .message-input {
            flex: 1;
            border: none;
            background-color: var(--input-background);
            padding: 12px 16px;
            border-radius: 20px;
            font-size: 1rem;
            resize: none;
            max-height: 120px;
            min-height: 44px;
            box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
            transition: all 0.2s ease;
        }

        .message-input:focus {
            outline: none;
            box-shadow: 0 2px 6px rgba(0, 0, 0, 0.15);
        }

        .send-button {
            background-color: var(--primary-color);
            color: white;
            border: none;
            width: 44px;
            height: 44px;
            border-radius: 22px;
            display: flex;
            align-items: center;
            justify-content: center;
            cursor: pointer;
            transition: all 0.2s ease;
            box-shadow: 0 1px 3px rgba(0, 0, 0, 0.2);
        }

        .send-button:hover {
            background-color: #0066CC;
            transform: scale(1.05);
        }

        .send-button:active {
            transform: scale(0.95);
        }

        .send-button:disabled {
            background-color: #B0B0B0;
            cursor: not-allowed;
        }

        .loading {
            display: none;
            align-items: center;
            gap: 8px;
            padding: 12px 16px;
            background-color: var(--bubble-ai);
            border-radius: var(--border-radius);
            align-self: flex-start;
            margin-bottom: var(--spacing);
        }

        .loading.active {
            display: flex;
        }

        .loading-dots {
            display: flex;
            gap: 4px;
        }

        .dot {
            width: 8px;
            height: 8px;
            background-color: #666;
            border-radius: 50%;
            animation: bounce 1.4s infinite ease-in-out;
        }

        .dot:nth-child(1) { animation-delay: -0.32s; }
        .dot:nth-child(2) { animation-delay: -0.16s; }

        @keyframes bounce {
            0%, 80%, 100% { transform: scale(0); }
            40% { transform: scale(1); }
        }

        @media (max-width: 768px) {
            .message {
                max-width: 90%;
            }
            
            .header h1 {
                font-size: 1.1rem;
            }
        }

        @media (max-width: 480px) {
            :root {
                --spacing: 8px;
            }
            
            .message {
                max-width: 95%;
                padding: 10px 14px;
            }
            
            .message-input {
                font-size: 0.95rem;
                padding: 10px 14px;
            }
        }

        /* iOS-specific styles */
        @supports (-webkit-touch-callout: none) {
            .chat-container {
                height: -webkit-fill-available;
            }
            
            .input-area {
                padding-bottom: calc(var(--spacing) + env(safe-area-inset-bottom));
            }
            
            .header {
                padding-top: calc(var(--spacing) + env(safe-area-inset-top));
            }
        }
    </style>
</head>
<body>
    <div class="chat-container">
        <div class="header">
            <h1>AI Chat Assistant</h1>
        </div>
        
        <div class="messages" id="messages">
            <!-- Messages will be added here -->
        </div>
        
        <div class="loading" id="loading">
            <div class="loading-dots">
                <div class="dot"></div>
                <div class="dot"></div>
                <div class="dot"></div>
            </div>
        </div>
        
        <div class="input-area">
            <div class="input-container">
                <textarea 
                    class="message-input" 
                    id="messageInput" 
                    placeholder="Type a message..." 
                    rows="1"
                    maxlength="1000"
                ></textarea>
                <button class="send-button" id="sendButton" disabled>
                    <span class="material-icons">send</span>
                </button>
            </div>
        </div>
    </div>

    <script>
        // Generate a unique session ID
        const sessionId = 'session_' + Math.random().toString(36).substr(2, 9);
        
        // DOM Elements
        const messagesContainer = document.getElementById('messages');
        const messageInput = document.getElementById('messageInput');
        const sendButton = document.getElementById('sendButton');
        const loadingIndicator = document.getElementById('loading');
        
        // Auto-resize textarea
        messageInput.addEventListener('input', function() {
            this.style.height = 'auto';
            this.style.height = (this.scrollHeight) + 'px';
            sendButton.disabled = !this.value.trim();
        });
        
        // Load chat history
        async function loadChatHistory() {
            try {
                const response = await fetch('/chat_history');
                const data = await response.json();
                
                data.messages.forEach(msg => {
                    addMessageToUI(msg.text, msg.sender_type, msg.timestamp);
                });
                
                scrollToBottom();
            } catch (error) {
                console.error('Error loading chat history:', error);
            }
        }
        
        // Add message to UI
        function addMessageToUI(text, senderType, timestamp) {
            const messageDiv = document.createElement('div');
            messageDiv.className = `message ${senderType}`;
            
            const messageText = document.createElement('div');
            messageText.className = 'message-text';
            messageText.textContent = text;
            
            const messageTime = document.createElement('div');
            messageTime.className = 'message-time';
            messageTime.textContent = new Date(timestamp).toLocaleTimeString();
            
            messageDiv.appendChild(messageText);
            messageDiv.appendChild(messageTime);
            messagesContainer.appendChild(messageDiv);
            
            scrollToBottom();
        }
        
        // Send message
        async function sendMessage() {
            const message = messageInput.value.trim();
            if (!message) return;
            
            // Add user message to UI
            addMessageToUI(message, 'user', new Date().toISOString());
            
            // Clear input
            messageInput.value = '';
            messageInput.style.height = 'auto';
            sendButton.disabled = true;
            
            // Show loading indicator
            loadingIndicator.classList.add('active');
            
            try {
                const response = await fetch('/chat', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify({
                        message: message,
                        session_id: sessionId
                    })
                });
                
                const data = await response.json();
                
                // Add AI response to UI
                addMessageToUI(data.response, 'ai', new Date().toISOString());
            } catch (error) {
                console.error('Error sending message:', error);
                addMessageToUI('Sorry, I encountered an error. Please try again.', 'ai', new Date().toISOString());
            } finally {
                loadingIndicator.classList.remove('active');
            }
        }
        
        // Event listeners
        sendButton.addEventListener('click', sendMessage);
        
        messageInput.addEventListener('keypress', function(e) {
            if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                sendMessage();
            }
        });
        
        // Scroll to bottom
        function scrollToBottom() {
            messagesContainer.scrollTop = messagesContainer.scrollHeight;
        }
        
        // Initial load
        loadChatHistory();
        
        // Handle visibility change
        document.addEventListener('visibilitychange', function() {
            if (document.visibilityState === 'visible') {
                loadChatHistory();
            }
        });
    </script>
</body>
</html>
''' 