async function loadModels() {
    try {
        let res = await fetch("/api/models");
        let models = await res.json();
        let select = document.getElementById("modelSelect");
        select.innerHTML = "";
        models.forEach(m => {
            let opt = document.createElement("option");
            opt.value = m.name;
            opt.textContent = m.name;
            select.appendChild(opt);
        });
    } catch (err) {
        console.error("Error loading models:", err);
    }
}

async function uploadPDF() {
    let file = document.getElementById("pdfFile").files[0];
    if (!file) {
        alert("Please select a PDF file first.");
        return;
    }
    let formData = new FormData();
    formData.append("file", file);

    document.getElementById("uploadStatus").innerText = "Uploading...";
    let res = await fetch("/api/upload", { method: "POST", body: formData });
    let data = await res.json();
    document.getElementById("uploadStatus").innerText = data.message || "Upload complete.";
}

async function askQuestion() {
    let question = document.getElementById("questionInput").value;
    let model = document.getElementById("modelSelect").value;
    let temperature = parseFloat(document.getElementById("temperatureRange").value);

    if (!question) {
        alert("Please enter a question.");
        return;
    }

    document.getElementById("answerBox").innerText = "Thinking...";
    let res = await fetch("/api/ask", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ question, model, temperature })
    });

    let data = await res.json();
    document.getElementById("answerBox").innerText = data.answer || "No answer.";
}

window.onload = loadModels;
