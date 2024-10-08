let isWaitingForResponse = false;

document.getElementById("chatbot-form").addEventListener("submit", async function (event) {
    event.preventDefault();
    
    const input = document.getElementById("chatbot-input").value.trim();
    const conversation = document.getElementById("chatbot-conversation");
    const submitButton = document.querySelector("#chatbot-form button[type='submit']");

    // Check if the input is empty
    if (input === "") {
        showError("Please enter your question.");
        return;
    }

    if (isWaitingForResponse) {
        showError("Please wait for the previous response before sending a new question.");
        return;
    }

    // Display the user's question
    const userMessage = document.createElement('div');
    userMessage.className = 'chatbot-message';
    userMessage.innerText = input;
    conversation.appendChild(userMessage);

    // Clear input field and disable submit button
    document.getElementById("chatbot-input").value = '';
    submitButton.disabled = true;
    isWaitingForResponse = true;

    try {
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
    } catch (error) {
        console.error("Error fetching response:", error);
        showError("Sorry, there was an error processing your request. Please try again.");
    } finally {
        // Re-enable submit button and reset waiting flag
        submitButton.disabled = false;
        isWaitingForResponse = false;
    }

    // Scroll to the bottom of the conversation
    conversation.scrollTop = conversation.scrollHeight;
});

function showError(message) {
    const errorElement = document.createElement('div');
    errorElement.className = 'chatbot-error';
    errorElement.innerText = message;
    
    const conversation = document.getElementById("chatbot-conversation");
    conversation.appendChild(errorElement);
    
    // Remove the error message after 3 seconds
    setTimeout(() => {
        errorElement.remove();
    }, 3000);
}