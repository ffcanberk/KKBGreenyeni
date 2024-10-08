let isWaitingForResponse = false;

document.addEventListener('DOMContentLoaded', function() {
    const chatbotForm = document.getElementById("chatbot-form");
    const chatbotInput = document.getElementById("chatbot-input");
    const conversation = document.getElementById("chatbot-conversation");
    const submitButton = chatbotForm.querySelector("button[type='submit']");

    // Load conversation history when the page loads
    loadConversationHistory();

    chatbotForm.addEventListener("submit", async function (event) {
        event.preventDefault();
        
        const input = chatbotInput.value.trim();

        if (input === "") {
            showError("Lütfen sorunuzu girin.");
            return;
        }

        if (isWaitingForResponse) {
            showError("Lütfen önceki yanıtı bekleyin.");
            return;
        }

        addMessageToConversation('user', input);

        chatbotInput.value = '';
        submitButton.disabled = true;
        isWaitingForResponse = true;

        try {
            const response = await fetch("/ask_chatbot", {
                method: "POST",
                headers: {
                    "Content-Type": "application/json",
                },
                body: JSON.stringify({ question: input }),
            });

            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }

            const data = await response.json();
            
            // Clear the conversation and display the full history
            conversation.innerHTML = '';
            data.conversation_history.forEach(msg => {
                addMessageToConversation(msg.role, msg.content);
            });
        } catch (error) {
            console.error("Yanıt alınırken hata oluştu:", error);
            showError("Üzgünüz, isteğiniz işlenirken bir hata oluştu. Lütfen tekrar deneyin.");
        } finally {
            submitButton.disabled = false;
            isWaitingForResponse = false;
        }

        conversation.scrollTop = conversation.scrollHeight;
    });

    async function loadConversationHistory() {
        try {
            const response = await fetch("/get_conversation_history");
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            const history = await response.json();
            conversation.innerHTML = '';
            history.forEach(msg => {
                addMessageToConversation(msg.role, msg.content);
            });
            conversation.scrollTop = conversation.scrollHeight;
        } catch (error) {
            console.error("Geçmiş yüklenirken hata oluştu:", error);
            showError("Geçmiş yüklenirken bir hata oluştu. Lütfen sayfayı yenileyin.");
        }
    }

    function addMessageToConversation(role, content) {
        const messageElement = document.createElement('div');
        messageElement.className = role === 'user' ? 'chatbot-message' : 'chatbot-response';
        messageElement.innerText = content;
        conversation.appendChild(messageElement);
    }

    function showError(message) {
        const errorElement = document.createElement('div');
        errorElement.className = 'chatbot-error';
        errorElement.innerText = message;
        
        conversation.appendChild(errorElement);
        
        setTimeout(() => {
            errorElement.remove();
        }, 3000);
    }
});

// Form submission prevention (as there's no backend for form processing in the provided code)
document.addEventListener('DOMContentLoaded', function() {
    const submitBtn = document.querySelector('.submit-btn');
    if (submitBtn) {
        submitBtn.addEventListener('click', function(event) {
            event.preventDefault();
            alert('Form gönderme işlevi henüz uygulanmadı.');
        });
    }
});