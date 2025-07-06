#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
GratefulGPT Flask Server - Web interface for the AI Deadhead
"""

import os
from flask import Flask, request, jsonify, render_template_string
import torch
from transformers import AutoTokenizer, AutoModelForCausalLM

app = Flask(__name__)

# Global variables for model and tokenizer
model = None
tokenizer = None

def load_model():
    """Load the trained GratefulGPT model"""
    global model, tokenizer
    
    model_path = "jaysooner/gratefulgpt"
    
    print("🎸 Loading GratefulGPT AI Deadhead from Hugging Face...")
    
    tokenizer = AutoTokenizer.from_pretrained(model_path)
    if tokenizer.pad_token is None:
        tokenizer.pad_token = tokenizer.eos_token
    model = AutoModelForCausalLM.from_pretrained(
        model_path,
        torch_dtype=torch.float16,
        device_map="auto"
    )
    
    print("⚡ GratefulGPT loaded and ready to spread good vibes!")

def generate_response(prompt, max_length=200, temperature=0.7):
    """Generate response from GratefulGPT"""
    global model, tokenizer
    
    try:
        # Format the prompt
        formatted_prompt = f"Human: {prompt}\nAssistant:"
        
        # Tokenize input and move to model device
        inputs = tokenizer(formatted_prompt, return_tensors="pt", padding=True, truncation=True)
        if torch.cuda.is_available():
            inputs = {k: v.to('cuda') for k, v in inputs.items()}
        
        # Generate response with safer parameters
        with torch.no_grad():
            outputs = model.generate(
                **inputs,
                max_new_tokens=max_length,
                temperature=max(0.1, min(temperature, 1.0)),
                do_sample=True,
                top_p=0.9,
                pad_token_id=tokenizer.pad_token_id,
                eos_token_id=tokenizer.eos_token_id
            )
        
        # Decode response
        response = tokenizer.decode(outputs[0], skip_special_tokens=True)
        
        # Extract just the assistant's response
        if "Assistant:" in response:
            response = response.split("Assistant:")[-1].strip()
        
        return response
    except Exception as e:
        print(f"Generation error: {e}")
        return "Sorry, I'm having trouble generating a response right now. 🌀"

# HTML template for the web interface
HTML_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <title>🎸 GratefulGPT - AI Deadhead 🌹</title>
    <style>
        body {
            font-family: 'Courier New', monospace;
            background: linear-gradient(45deg, #ff6b6b, #4ecdc4, #45b7d1, #96ceb4);
            background-size: 400% 400%;
            animation: gradient 15s ease infinite;
            margin: 0;
            padding: 20px;
            color: #333;
        }
        
        @keyframes gradient {
            0% { background-position: 0% 50%; }
            50% { background-position: 100% 50%; }
            100% { background-position: 0% 50%; }
        }
        
        .container {
            max-width: 800px;
            margin: 0 auto;
            background: rgba(255, 255, 255, 0.9);
            border-radius: 15px;
            padding: 30px;
            box-shadow: 0 8px 32px rgba(0, 0, 0, 0.1);
        }
        
        h1 {
            text-align: center;
            color: #2c3e50;
            margin-bottom: 30px;
            font-size: 2.5em;
        }
        
        .chat-container {
            border: 2px solid #3498db;
            border-radius: 10px;
            padding: 20px;
            margin-bottom: 20px;
            height: 400px;
            overflow-y: auto;
            background: #f8f9fa;
        }
        
        .message {
            margin-bottom: 15px;
            padding: 10px;
            border-radius: 8px;
        }
        
        .user-message {
            background: #e3f2fd;
            border-left: 4px solid #2196f3;
        }
        
        .bot-message {
            background: #e8f5e8;
            border-left: 4px solid #4caf50;
        }
        
        .input-container {
            display: flex;
            gap: 10px;
        }
        
        #userInput {
            flex: 1;
            padding: 15px;
            border: 2px solid #3498db;
            border-radius: 8px;
            font-size: 16px;
        }
        
        #sendBtn {
            padding: 15px 30px;
            background: #3498db;
            color: white;
            border: none;
            border-radius: 8px;
            cursor: pointer;
            font-size: 16px;
            transition: background 0.3s;
        }
        
        #sendBtn:hover {
            background: #2980b9;
        }
        
        .loading {
            text-align: center;
            color: #7f8c8d;
            font-style: italic;
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>🎸 GratefulGPT - AI Deadhead 🌹</h1>
        <p style="text-align: center; font-style: italic; color: #7f8c8d;">
            Channeling the cosmic vibes of Kesey, Cassady, Hunter & Barlow ⚡
        </p>
        
        <div id="chatContainer" class="chat-container">
            <div class="message bot-message">
                <strong>GratefulGPT:</strong> Hey there, friend! I'm your AI deadhead, ready to share some cosmic wisdom and good vibes. What's on your mind? 🚌✨
            </div>
        </div>
        
        <div class="input-container">
            <input type="text" id="userInput" placeholder="Ask the AI deadhead anything..." onkeypress="handleKeyPress(event)">
            <button id="sendBtn" onclick="sendMessage()">Send ⚡</button>
        </div>
    </div>

    <script>
        function handleKeyPress(event) {
            if (event.key === 'Enter') {
                sendMessage();
            }
        }

        async function sendMessage() {
            const input = document.getElementById('userInput');
            const chatContainer = document.getElementById('chatContainer');
            const message = input.value.trim();
            
            if (!message) return;
            
            // Add user message
            const userDiv = document.createElement('div');
            userDiv.className = 'message user-message';
            userDiv.innerHTML = `<strong>You:</strong> ${message}`;
            chatContainer.appendChild(userDiv);
            
            // Clear input
            input.value = '';
            
            // Add loading message
            const loadingDiv = document.createElement('div');
            loadingDiv.className = 'message bot-message loading';
            loadingDiv.innerHTML = '<strong>GratefulGPT:</strong> <em>Channeling cosmic vibes...</em> 🔮';
            chatContainer.appendChild(loadingDiv);
            
            // Scroll to bottom
            chatContainer.scrollTop = chatContainer.scrollHeight;
            
            try {
                const response = await fetch('/chat', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify({ message: message })
                });
                
                const data = await response.json();
                
                // Remove loading message
                chatContainer.removeChild(loadingDiv);
                
                // Add bot response
                const botDiv = document.createElement('div');
                botDiv.className = 'message bot-message';
                botDiv.innerHTML = `<strong>GratefulGPT:</strong> ${data.response}`;
                chatContainer.appendChild(botDiv);
                
            } catch (error) {
                // Remove loading message
                chatContainer.removeChild(loadingDiv);
                
                // Add error message
                const errorDiv = document.createElement('div');
                errorDiv.className = 'message bot-message';
                errorDiv.innerHTML = '<strong>GratefulGPT:</strong> <em>Whoa, cosmic interference! Try again, friend. 🌀</em>';
                chatContainer.appendChild(errorDiv);
            }
            
            // Scroll to bottom
            chatContainer.scrollTop = chatContainer.scrollHeight;
        }
    </script>
</body>
</html>
"""

@app.route('/')
def home():
    """Serve the main chat interface"""
    return render_template_string(HTML_TEMPLATE)

@app.route('/chat', methods=['POST'])
def chat():
    """Handle chat requests"""
    try:
        data = request.get_json()
        user_message = data.get('message', '')
        
        if not user_message:
            return jsonify({'error': 'No message provided'}), 400
        
        # Generate response
        response = generate_response(user_message)
        
        return jsonify({'response': response})
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/health')
def health():
    """Health check endpoint"""
    return jsonify({'status': 'alive', 'model_loaded': model is not None})

if __name__ == '__main__':
    # Load the model when starting the server
    load_model()
    
    print("🚌 Starting GratefulGPT server...")
    print("🌐 Open your browser to http://localhost:5000")
    print("⚡ Ready to spread cosmic vibes!")
    
    app.run(host='0.0.0.0', port=5000, debug=False)