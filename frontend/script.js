let session_id = "";

/* 💬 ADD MESSAGE  */
function addMessage(sender, text) {
    let chatbox = document.getElementById("chatbox");

    let msg = document.createElement("div");
    msg.innerHTML = "<b>" + sender + ":</b> " + text;

    chatbox.appendChild(msg);
    chatbox.scrollTop = chatbox.scrollHeight;
}


/* 📞 START CALL */
async function startCall() {
    try {
        let res = await fetch("http://127.0.0.1:8000/ivr/start", {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify({
                caller_number: "Web Simulator"
            })
        });

        let data = await res.json();

        session_id = data.session_id;

        document.getElementById("callStatus").innerText = "Call Connected 📞";

        addMessage("bot", data.prompt || "Welcome");

        speak(data.prompt || "");

    } catch (error) {
        console.error("Start error:", error);
        addMessage("bot", "❌ Failed to start call");
    }
}


/* ❌ END CALL */
function endCall() {
    session_id = "";
    document.getElementById("callStatus").innerText = "Call Ended ❌";
    addMessage("bot", "Call ended.");
}


/* ✍️ TEXT INPUT */
async function sendInput() {

    if (!session_id) {
        alert("Please start call first!");
        return;
    }

    let inputField = document.getElementById("userInput");
    let input = inputField.value;

    if (!input.trim()) {
        alert("Please enter something");
        return;
    }

    addMessage("user", input);

    inputField.value = "";

    try {
        let res = await fetch("http://127.0.0.1:8000/ivr/text", {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify({
                session_id: session_id,
                text: input
            })
        });

        let data = await res.json();

        if (data.response_text) {
            addMessage("bot", data.response_text);
        } else {
            addMessage("bot", "❌ No response");
        }

        if (data.audio_file) {
            let audio = new Audio("http://127.0.0.1:8000/" + data.audio_file);
            audio.play().catch(err => console.error("Audio error:", err));
        }

    } catch (error) {
        console.error("Text error:", error);
        addMessage("bot", "❌ Connection error");
    }
}


/* 🎤 VOICE INPUT */
async function startVoice() {

    if (!session_id) {
        alert("Please start call first!");
        return;
    }

    const micBtn = document.querySelector(".mic-btn");
    if (micBtn) micBtn.style.background = "#ff3d00"; // 🔴 recording

    let stream;

    try {
        stream = await navigator.mediaDevices.getUserMedia({ audio: true });
    } catch (err) {
        alert("Microphone access denied");
        if (micBtn) micBtn.style.background = "#00c853";
        return;
    }

    let mediaRecorder = new MediaRecorder(stream);
    let audioChunks = [];

    mediaRecorder.ondataavailable = event => {
        audioChunks.push(event.data);
    };

    mediaRecorder.onstop = async () => {

        if (micBtn) micBtn.style.background = "#00c853";

        let audioBlob = new Blob(audioChunks, { type: "audio/webm" });

        let formData = new FormData();
        formData.append("audio", audioBlob, "voice.webm");

        addMessage("user", "🎤 Voice input");

        try {
            let res = await fetch(`http://127.0.0.1:8000/ivr/voice?session_id=${session_id}`, {
                method: "POST",
                body: formData
            });

            let data = await res.json();

            if (data.response_text) {
                addMessage("bot", data.response_text);
            } else {
                addMessage("bot", "❌ No response from server");
            }

            if (data.audio_file) {
                let audio = new Audio("http://127.0.0.1:8000/" + data.audio_file);
                audio.play().catch(err => console.error("Audio error:", err));
            }

        } catch (error) {
            console.error("Voice error:", error);
            addMessage("bot", "❌ Connection error");
        }
    };

    mediaRecorder.start();

    setTimeout(() => {
        mediaRecorder.stop();
    }, 6000);
}


/* 🔢 KEYPAD */
function pressKey(key) {

    addMessage("user", `Pressed: ${key}`);

    let mappedText = "";

    if (key === "1") mappedText = "OPD";
    else if (key === "2") mappedText = "Emergency";
    else if (key === "3") mappedText = "Pharmacy";
    else if (key === "4") mappedText = "Directions";
    else if (key === "5") mappedText = "ICU";
    else if (key === "6") mappedText = "Radiology";
    else if (key === "7") mappedText = "Pathology";
    else if (key === "8") mappedText = "Maternity";
    else if (key === "9") mappedText = "General Ward";

    if (mappedText) {
        sendTextToBackend(mappedText);
    }
}


/* 🔁 SEND KEYPAD TEXT */
async function sendTextToBackend(text) {

    if (!session_id) {
        alert("Start call first!");
        return;
    }

    try {
        let res = await fetch("http://127.0.0.1:8000/ivr/text", {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify({
                session_id: session_id,
                text: text
            })
        });

        let data = await res.json();

        addMessage("bot", data.response_text);

        if (data.audio_file) {
            let audio = new Audio("http://127.0.0.1:8000/" + data.audio_file);
            audio.play().catch(err => console.error("Audio error:", err));
        }

    } catch (err) {
        addMessage("bot", "❌ Error");
    }
}


/* 🔊 BROWSER SPEECH */
function speak(text) {
    if (!text) return;

    let speech = new SpeechSynthesisUtterance(text);
    speech.lang = "en-US";
    speechSynthesis.speak(speech);
}