document.getElementById("chatbot-form").addEventListener("submit", async function (event) {
    event.preventDefault();
    
    const input = document.getElementById("chatbot-input").value;
    const conversation = document.getElementById("chatbot-conversation");

    // Display the user's question
    const userMessage = document.createElement('div');
    userMessage.className = 'chatbot-message';
    userMessage.innerText = input;
    conversation.appendChild(userMessage);

    // Fetch the response from the backend
    const response = await fetch("/ask_chatbot", {
        method: "POST",
        headers: {
            "Content-Type": "application/json",
        },
        body: JSON.stringify({ question: input }),
    });

    const data = await response.json();
    
    // Display the chatbot's response
    const botResponse = document.createElement('div');
    botResponse.className = 'chatbot-response';
    botResponse.innerText = data.answer;
    conversation.appendChild(botResponse);

    // Clear input field
    document.getElementById("chatbot-input").value = '';

    // Scroll to the bottom of the conversation
    conversation.scrollTop = conversation.scrollHeight;
});
