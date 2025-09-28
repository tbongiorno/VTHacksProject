// Function to switch tabs
function showTab(tabId) {
    const tabs = document.querySelectorAll('.tab-content');
    tabs.forEach(tab => tab.classList.remove('active'));

    const selectedTab = document.getElementById(tabId);
    if (selectedTab) {
        selectedTab.classList.add('active');
    }
}

// Default settings if none exist
let settingsData = {
    categories: {
        Rent: 50,
        Savings: 30,
        Investment: 20
    },
    limits: {}
};

// Load settings from server or localStorage
async function loadSettings() {
    try {
        const response = await fetch('/settings');
        if (!response.ok) throw new Error('Network error');
        const data = await response.json();

        if (data && (Object.keys(data.categories || {}).length > 0 || Object.keys(data.limits || {}).length > 0)) {
            settingsData = data;
        }
    } catch (error) {
        console.error('Error loading settings:', error);
    }

    const localSaved = localStorage.getItem("userSettings");
    if (localSaved) {
        try {
            const localData = JSON.parse(localSaved);
            if (localData && (Object.keys(localData.categories || {}).length > 0 || Object.keys(localData.limits || {}).length > 0)) {
                settingsData = localData;
            }
        } catch {
            // Ignore parsing errors
        }
    }

    saveSettings();
    populateForm(settingsData); // refresh the form view with new limits

}

// Save settings to server and localStorage
async function saveSettings() {
    try {
        const response = await fetch('/settings', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(settingsData),
        });

        const result = await response.json();
        console.log(result.message);
    } catch (error) {
        console.error('Error saving settings:', error);
    }

    localStorage.setItem("userSettings", JSON.stringify(settingsData));
}

// Get total percentage (categories + limits)
function getTotalPercentage() {
    let total = 0;
    for (const val of Object.values(settingsData.categories)) {
        total += val;
    }
    for (const obj of Object.values(settingsData.limits)) {
        total += obj.percent;
    }
    return total;
}

// Populate settings form
function populateForm(data) {
    const settingsContainer = document.getElementById("settings-container");
    settingsContainer.innerHTML = "";

    for (const [category, percent] of Object.entries(data.categories || {})) {
        settingsContainer.innerHTML += `
            <div class="setting-item">
                <label>${category} (%):</label>
                <input type="number" name="${category}" value="${percent}" min="0" max="100"><br><br>
            </div>
        `;
    }

    for (const [category, obj] of Object.entries(data.limits || {})) {
        settingsContainer.innerHTML += `
            <div class="setting-item">
                <label>${category} (% until $ limit):</label>
                <input type="number" name="${category}-percent" value="${obj.percent}" min="0" max="100"> %
                <input type="number" name="${category}-limit" value="${obj.limit}" min="0"> $<br><br>
            </div>
        `;
    }
}

// Get all current splits (for paycheck calculation)
function getCategorySplits() {
    const savedSettings = localStorage.getItem("userSettings");

    if (savedSettings) {
        try {
            const parsed = JSON.parse(savedSettings);
            const percentCats = parsed.categories || {};
            const limitCats = parsed.limits || {};
            const combined = { ...percentCats };
            for (const [key, val] of Object.entries(limitCats)) {
                combined[key] = val.percent;
            }
            return combined;
        } catch {
            // fallback to default
        }
    }

    return {
        Rent: 50,
        Savings: 30,
        Investment: 20
    };
}

// Main logic
document.addEventListener("DOMContentLoaded", function () {
    const paycheckForm = document.getElementById("paycheck-form");
    const splitResult = document.getElementById("split-result");

    paycheckForm.addEventListener("submit", function (e) {
        e.preventDefault();

        const paycheckInput = document.getElementById("paycheck");
        const paycheckAmount = parseFloat(paycheckInput.value);

        if (isNaN(paycheckAmount) || paycheckAmount <= 0) {
            splitResult.innerHTML = `<p style="color:red;">Please enter a valid paycheck amount.</p>`;
            return;
        }

        const categories = getCategorySplits();
        let resultHTML = "<h3>Paycheck Split:</h3><ul>";

        for (const category in categories) {
            const percent = categories[category];
            let amount = (percent / 100) * paycheckAmount;
            let limitNote = "";

            // Check for limit category
            if (settingsData.limits[category]) {
                const currentLimit = settingsData.limits[category].limit;

                // Subtract from remaining limit
                settingsData.limits[category].limit -= amount;

                if (settingsData.limits[category].limit <= 0) {
                    delete settingsData.limits[category];
                }

                // Show new remaining limit
                limitNote = ` <span style="color:gray;">(Remaining Limit: $${settingsData.limits[category].limit.toFixed(2)})</span>`;
            }

            resultHTML += `<li><strong>${category}:</strong> $${amount.toFixed(2)}${limitNote}</li>`;
        }

        resultHTML += "</ul>";
        splitResult.innerHTML = resultHTML;

            // ✅ Save updated limits to localStorage/server
        saveSettings();
    });

    // SETTINGS FORM
    const settingsForm = document.getElementById("settings-form");
    const saveMessage = document.getElementById("save-message");

    settingsForm.addEventListener("submit", function (e) {
        e.preventDefault();

        const inputs = settingsForm.querySelectorAll("input[type='number']");
        let valid = true;

        // Clear current data
        settingsData.categories = {};
        settingsData.limits = {};

        inputs.forEach(input => {
            const name = input.name;
            const value = parseFloat(input.value);

            if (name.includes("-percent")) {
                const catName = name.replace("-percent", "");
                if (!settingsData.limits[catName]) settingsData.limits[catName] = { percent: 0, limit: 0 };
                if (isNaN(value) || value < 0 || value > 100) valid = false;
                else settingsData.limits[catName].percent = value;
            } else if (name.includes("-limit")) {
                const catName = name.replace("-limit", "");
                if (!settingsData.limits[catName]) settingsData.limits[catName] = { percent: 0, limit: 0 };
                settingsData.limits[catName].limit = isNaN(value) ? 0 : value;
            } else {
                if (isNaN(value) || value < 0 || value > 100) valid = false;
                else settingsData.categories[name] = value;
            }
        });

        if (!valid) {
            saveMessage.textContent = "⚠️ Please enter valid values between 0 and 100.";
            saveMessage.style.color = "red";
            return;
        }

        const total = getTotalPercentage();
        if (total !== 100) {
            saveMessage.textContent = "⚠️ Percentages must add up to 100%.";
            saveMessage.style.color = "red";
            return;
        }

        saveSettings();
        saveMessage.textContent = "✅ Settings saved!";
        saveMessage.style.color = "green";
    });

    // ADD CATEGORY FORM
    const addCategoryForm = document.getElementById("add-category-form");
    const addMessage = document.getElementById("add-message");
    const toggle = document.getElementById('category-toggle');
    const hiddenInput = document.getElementById('category-type');
    const limitInputContainer = document.getElementById('limit-input-container');

    const nameInput = document.getElementById("new-category-name");
    const valueInput = document.getElementById("new-category-value");  // Fixed ID
    const limitInput = document.getElementById("category-limit");

    toggle.setAttribute('aria-checked', true);
    limitInputContainer.style.display = "none";

    toggle.addEventListener('click', () => {
        toggle.classList.toggle('active');
        const isPercent = !toggle.classList.contains('active');
        hiddenInput.value = isPercent ? 'percent' : 'limit';
        toggle.setAttribute('aria-checked', isPercent);
        limitInputContainer.style.display = isPercent ? 'none' : 'block';
    });

    addCategoryForm.addEventListener("submit", function (e) {
        e.preventDefault();

        const name = nameInput.value.trim();
        const type = hiddenInput.value;
        const value = parseFloat(valueInput.value);
        const limit = parseFloat(limitInput.value);

        if (!name) {
            addMessage.textContent = "Please enter a category name.";
            addMessage.style.color = "red";
            return;
        }

        if (isNaN(value) || value <= 0) {
            addMessage.textContent = "Please enter a valid positive percentage.";
            addMessage.style.color = "red";
            return;
        }

        if (type === "limit" && (isNaN(limit) || limit <= 0)) {
            addMessage.textContent = "Please enter a valid positive dollar limit.";
            addMessage.style.color = "red";
            return;
        }

        if (settingsData.categories[name] !== undefined || settingsData.limits[name] !== undefined) {
            addMessage.textContent = "Category name already exists.";
            addMessage.style.color = "red";
            return;
        }

        const currentTotal = getTotalPercentage();
        if (currentTotal + value > 100) {
            addMessage.textContent = "⚠️ Adding this category would exceed 100%.";
            addMessage.style.color = "red";
            return;
        }

        if (type === "percent") {
            settingsData.categories[name] = value;
        } else {
            settingsData.limits[name] = { percent: value, limit: limit };
        }

        localStorage.setItem("userSettings", JSON.stringify(settingsData));
        populateForm(settingsData);

        addMessage.textContent = `✅ Added "${name}" (${type === "percent" ? value + "%" : value + "% until $" + limit})`;
        addMessage.style.color = "green";

        // Reset inputs
        nameInput.value = "";
        valueInput.value = "";
        limitInput.value = "";
        hiddenInput.value = "percent";
        toggle.classList.remove("active");
        toggle.setAttribute('aria-checked', true);
        limitInputContainer.style.display = "none";
    });

    loadSettings();
});

const chatBox = document.getElementById('chat-box');
const userInput = document.getElementById('user-input');
const sendBtn = document.getElementById('send-btn');

// Replace with your actual Gemini AI API endpoint
const GEMINI_API_URL = 'https://your-server.com/gemini-chat';

function addMessage(message, sender) {
  const msgDiv = document.createElement('div');
  msgDiv.classList.add('message', sender === 'user' ? 'user-message' : 'ai-message');
  msgDiv.textContent = message;
  chatBox.appendChild(msgDiv);
  chatBox.scrollTop = chatBox.scrollHeight;
}

async function sendMessage() {
  const message = userInput.value.trim();
  if (!message) return;

  addMessage(message, 'user');
  userInput.value = '';

  try {
    const response = await fetch(GEMINI_API_URL, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({ message })
    });

    const data = await response.json();
    addMessage(data.reply, 'ai');
  } catch (error) {
    addMessage("Error talking to Gemini AI.", 'ai');
    console.error(error);
  }
}

sendBtn.addEventListener('click', sendMessage);
userInput.addEventListener('keydown', (e) => {
  if (e.key === 'Enter') sendMessage();
});