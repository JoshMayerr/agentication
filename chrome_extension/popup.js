// DOM Elements
const elements = {
  domainInput: document.getElementById("domainInput"),
  domainError: document.getElementById("domainError"),
  domainList: document.getElementById("domainList"),
  captureStatus: document.getElementById("captureStatus"),
  toggleCapture: document.getElementById("toggleCapture"),
  exportData: document.getElementById("exportData"),
  clearData: document.getElementById("clearData"),
  copyData: document.getElementById("copyData"),
};

// State
let isCapturing = false;
let domains = new Set();

// Utility Functions
function showError(message) {
  elements.domainError.textContent = message;
  elements.domainError.style.display = "block";
  setTimeout(() => {
    elements.domainError.style.display = "none";
  }, 3000);
}

function updateCaptureUI(capturing) {
  isCapturing = capturing;
  elements.captureStatus.textContent = capturing
    ? "Capture Active"
    : "Capture Inactive";
  elements.captureStatus.className = `status ${
    capturing ? "active" : "inactive"
  }`;
  elements.toggleCapture.textContent = capturing
    ? "Stop Capture"
    : "Start Capture";
  elements.exportData.disabled = !capturing;
  elements.clearData.disabled = !capturing;
}

function createDomainElement(domain) {
  const div = document.createElement("div");
  div.className = "domain-item";

  const span = document.createElement("span");
  span.textContent = domain;

  const removeButton = document.createElement("button");
  removeButton.className = "secondary";
  removeButton.textContent = "×";
  removeButton.onclick = () => removeDomain(domain);

  div.appendChild(span);
  div.appendChild(removeButton);
  return div;
}

function updateDomainList() {
  elements.domainList.innerHTML = "";
  domains.forEach((domain) => {
    elements.domainList.appendChild(createDomainElement(domain));
  });
}

// Message handling
async function sendMessage(message) {
  try {
    return await new Promise((resolve, reject) => {
      chrome.runtime.sendMessage(message, (response) => {
        if (chrome.runtime.lastError) {
          reject(chrome.runtime.lastError);
        } else if (!response) {
          reject(new Error("No response received"));
        } else {
          resolve(response);
        }
      });
    });
  } catch (error) {
    console.error("Message send error:", error);
    throw error;
  }
}

// Event Handlers
async function addDomain(event) {
  if (event.key !== "Enter") return;

  const domain = elements.domainInput.value.trim();
  if (!domain) {
    showError("Please enter a domain");
    return;
  }

  try {
    const response = await sendMessage({
      action: "addDomain",
      domain,
    });

    if (response?.success) {
      domains.add(response.domain);
      updateDomainList();
      elements.domainInput.value = "";
    } else {
      showError(response?.error || "Failed to add domain");
    }
  } catch (error) {
    showError("Failed to add domain");
    console.error("Add domain error:", error);
  }
}

async function removeDomain(domain) {
  try {
    const response = await sendMessage({
      action: "removeDomain",
      domain,
    });

    if (response?.success) {
      domains.delete(domain);
      updateDomainList();
    } else {
      showError("Failed to remove domain");
    }
  } catch (error) {
    showError("Failed to remove domain");
    console.error("Remove domain error:", error);
  }
}

async function toggleCapture() {
  if (domains.size === 0) {
    showError("Add at least one domain first");
    return;
  }

  try {
    const response = await sendMessage({
      action: isCapturing ? "stopCapture" : "startCapture",
    });

    if (response?.success) {
      updateCaptureUI(!isCapturing);
    } else {
      showError("Failed to toggle capture");
    }
  } catch (error) {
    showError("Failed to toggle capture");
    console.error("Toggle capture error:", error);
  }
}

async function exportData() {
  try {
    const response = await sendMessage({
      action: "exportData",
    });

    if (response?.success && response?.data) {
      // Format data for export
      const exportData = {
        version: "1.0",
        timestamp: new Date().toISOString(),
        data: response.data,
      };

      // Create and trigger download
      const blob = new Blob([JSON.stringify(exportData, null, 2)], {
        type: "application/json",
      });
      const url = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = `session-capture-${new Date().toISOString()}.json`;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      URL.revokeObjectURL(url);
    } else {
      showError("No data available to export");
    }
  } catch (error) {
    showError("Failed to export data");
    console.error("Export error:", error);
  }
}

async function clearData() {
  if (!confirm("Are you sure you want to clear all captured data?")) {
    return;
  }

  try {
    const response = await sendMessage({
      action: "clearData",
    });

    if (response?.success) {
      showError("Data cleared successfully");
    } else {
      showError("Failed to clear data");
    }
  } catch (error) {
    showError("Failed to clear data");
    console.error("Clear data error:", error);
  }
}

async function copyToClipboard() {
  try {
    const response = await sendMessage({
      action: "exportData",
    });

    if (response?.success && response?.data) {
      await navigator.clipboard.writeText(
        JSON.stringify(response.data, null, 2)
      );
      showError("Copied to clipboard"); // Use as success message
    } else {
      showError("No data to copy");
    }
  } catch (error) {
    showError("Failed to copy data");
    console.error("Copy error:", error);
  }
}

// Initialize popup
async function initialize() {
  try {
    // Load current state
    const state = await sendMessage({ action: "getState" });
    if (state) {
      domains = new Set(state.domains || []);
      updateDomainList();
      updateCaptureUI(state.isCapturing || false);
    }

    // Set up event listeners
    elements.domainInput.addEventListener("keypress", addDomain);
    elements.toggleCapture.addEventListener("click", toggleCapture);
    elements.exportData.addEventListener("click", exportData);
    elements.clearData.addEventListener("click", clearData);
    elements.copyData.addEventListener("click", copyToClipboard);
  } catch (error) {
    showError("Failed to initialize popup");
    console.error("Initialization error:", error);
  }
}

// Start initialization when popup loads
document.addEventListener("DOMContentLoaded", initialize);
