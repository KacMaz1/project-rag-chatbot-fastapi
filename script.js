const form = document.getElementById("chat-form");
const input = document.getElementById("message-input");
const chatBox = document.getElementById("chat-box");

const threadId = "frontend_user_1";

function addMessage(text, sender) {
    const messageDiv = document.createElement("div");

    messageDiv.classList.add("message");
    messageDiv.classList.add(sender);
    messageDiv.textContent = text;

    chatBox.appendChild(messageDiv);
    chatBox.scrollTop = chatBox.scrollHeight;

    return messageDiv;
}

form.addEventListener("submit", async function (event) {
    event.preventDefault();

    const userMessage = input.value.trim();

    if (!userMessage) {
        return;
    }

    addMessage(userMessage, "user");
    input.value = "";

    const waitingMessage = addMessage("Bot mysli...", "bot");

    try {
        const response = await fetch("http://127.0.0.1:8000/chat", {
            method: "POST",
            headers: {
                "Content-Type": "application/json",
            },
            body: JSON.stringify({
                user_message: userMessage,
                thread_id: threadId,
            }),
        });

        if (!response.ok) {
            throw new Error("API zwrocilo blad");
        }

        const data = await response.json();
        waitingMessage.textContent = data.response;
    } catch (error) {
        waitingMessage.textContent = "Nie udalo sie polaczyc z API.";
        console.error(error);
    }
});
