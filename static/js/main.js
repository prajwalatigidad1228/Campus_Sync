/**
 * Campus_Sync – Complete Frontend Interaction Engine (Phase 3)
 * Features:
 *  - Theme Engine (Light / Dark with localStorage persistence)
 *  - Hero Slider (3-second auto-rotation with pause-on-hover)
 *  - Mock AI College Copilot (Voice, chips, typing simulator, intelligent campus answers)
 *  - Tab Switching Component
 *  - Mobile Sidebar Drawer Controller
 */

document.addEventListener("DOMContentLoaded", () => {
  initThemeEngine();
  initMobileDrawer();
  initHeroSlider();
  initCopilotEngine();
  initTabsEngine();
  initFlashDismiss();
});

/* ── 1. Theme Engine ─────────────────────────────────────────────────── */
function initThemeEngine() {
  const currentTheme = localStorage.getItem("campussync_theme") || "light";
  applyTheme(currentTheme);

  document.querySelectorAll(".theme-toggle-btn").forEach((btn) => {
    btn.addEventListener("click", () => {
      const activeTheme = document.documentElement.getAttribute("data-theme") || "light";
      const newTheme = activeTheme === "dark" ? "light" : "dark";
      applyTheme(newTheme);
      localStorage.setItem("campussync_theme", newTheme);
    });
  });
}

function applyTheme(theme) {
  document.documentElement.setAttribute("data-theme", theme);
  document.querySelectorAll(".theme-toggle-btn").forEach((btn) => {
    btn.innerHTML = theme === "dark" ? "☀️" : "🌙";
    btn.setAttribute("title", theme === "dark" ? "Switch to Light Mode" : "Switch to Dark Mode");
  });
}

/* ── 2. Mobile Sidebar Drawer ────────────────────────────────────────── */
function initMobileDrawer() {
  const sidebar = document.querySelector(".app-sidebar");
  const backdrop = document.querySelector(".sidebar-backdrop");
  const menuBtn = document.querySelector(".mobile-menu-btn");

  if (!sidebar) return;

  if (menuBtn) {
    menuBtn.addEventListener("click", () => {
      sidebar.classList.toggle("open");
      if (backdrop) backdrop.classList.toggle("open");
    });
  }

  if (backdrop) {
    backdrop.addEventListener("click", () => {
      sidebar.classList.remove("open");
      backdrop.classList.remove("open");
    });
  }
}

/* ── 3. Hero Slider (3-Second Auto-Rotation) ─────────────────────────── */
function initHeroSlider() {
  const slides = document.querySelectorAll(".slider-slide");
  const dots = document.querySelectorAll(".slider-dot");
  if (!slides.length) return;

  let currentIdx = 0;
  let intervalId = null;

  function showSlide(idx) {
    slides.forEach((s, i) => s.classList.toggle("active", i === idx));
    dots.forEach((d, i) => d.classList.toggle("active", i === idx));
    currentIdx = idx;
  }

  function nextSlide() {
    const nextIdx = (currentIdx + 1) % slides.length;
    showSlide(nextIdx);
  }

  function startAutoPlay() {
    if (intervalId) clearInterval(intervalId);
    intervalId = setInterval(nextSlide, 3000);
  }

  function stopAutoPlay() {
    if (intervalId) clearInterval(intervalId);
  }

  dots.forEach((dot, idx) => {
    dot.addEventListener("click", () => {
      showSlide(idx);
      startAutoPlay();
    });
  });

  const sliderWrap = document.querySelector(".hero-slider-wrap");
  if (sliderWrap) {
    sliderWrap.addEventListener("mouseenter", stopAutoPlay);
    sliderWrap.addEventListener("mouseleave", startAutoPlay);
  }

  startAutoPlay();
}

/* ── 4. Mock AI College Copilot Engine ───────────────────────────────── */
function initCopilotEngine() {
  const input = document.querySelector(".chat-text-input");
  const askBtn = document.querySelector(".ask-btn");
  const micBtn = document.querySelector(".mic-btn");
  const clearBtn = document.querySelector(".clear-chat-btn");
  const messagesBox = document.querySelector(".copilot-messages");
  const chips = document.querySelectorAll(".suggestion-chip");

  if (!messagesBox) return;

  function formatTime() {
    const now = new Date();
    return now.toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" });
  }

  function appendMessage(sender, text, source) {
    const row = document.createElement("div");
    row.className = `chat-bubble-row ${sender}`;

    const avatar = document.createElement("div");
    avatar.className = "chat-bubble-avatar";
    avatar.innerHTML = sender === "user" ? "👤" : "🤖";

    const contentWrap = document.createElement("div");
    contentWrap.className = "chat-bubble-content";

    const bubble = document.createElement("div");
    bubble.className = "chat-bubble";
    // Render text with basic markdown bold support
    bubble.innerHTML = text.replace(/\*\*(.*?)\*\*/g, "<strong>$1</strong>").replace(/\n/g, "<br>");

    const time = document.createElement("span");
    time.className = "chat-timestamp";
    time.textContent = formatTime();

    contentWrap.appendChild(bubble);

    if (source) {
      const srcEl = document.createElement("div");
      srcEl.style.marginTop = "0.35rem";
      srcEl.innerHTML = `<span class="badge-pill badge-pill--blue" style="font-size: 0.72rem; font-weight: 600;">📚 Source: ${source}</span>`;
      contentWrap.appendChild(srcEl);
    }

    contentWrap.appendChild(time);

    row.appendChild(avatar);
    row.appendChild(contentWrap);

    messagesBox.appendChild(row);
    messagesBox.scrollTop = messagesBox.scrollHeight;
  }

  function showTyping() {
    const row = document.createElement("div");
    row.className = "chat-bubble-row assistant typing-row";

    const avatar = document.createElement("div");
    avatar.className = "chat-bubble-avatar";
    avatar.innerHTML = "🤖";

    const bubble = document.createElement("div");
    bubble.className = "chat-bubble typing-indicator";
    bubble.innerHTML = `
      <div class="typing-dot"></div>
      <div class="typing-dot"></div>
      <div class="typing-dot"></div>
    `;

    row.appendChild(avatar);
    row.appendChild(bubble);
    messagesBox.appendChild(row);
    messagesBox.scrollTop = messagesBox.scrollHeight;
    return row;
  }

  async function handleSend(text) {
    const query = (text || (input ? input.value : "")).trim();
    if (!query) return;

    appendMessage("user", query);
    if (input) input.value = "";

    const typingEl = showTyping();

    try {
      const response = await fetch("/api/copilot/chat", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ message: query }),
      });

      if (typingEl && typingEl.parentNode) {
        typingEl.parentNode.removeChild(typingEl);
      }

      if (!response.ok) {
        appendMessage("assistant", "An error occurred connecting to the Copilot service. Please try again.");
        return;
      }

      const data = await response.json();
      appendMessage("assistant", data.response || "No response received.", data.source);
    } catch (err) {
      if (typingEl && typingEl.parentNode) {
        typingEl.parentNode.removeChild(typingEl);
      }
      appendMessage("assistant", "Could not reach the Copilot server. Please check your network connection.");
    }
  }

  if (askBtn) {
    askBtn.addEventListener("click", () => handleSend());
  }

  if (input) {
    input.addEventListener("keydown", (e) => {
      if (e.key === "Enter" && !e.shiftKey) {
        e.preventDefault();
        handleSend();
      }
    });
  }

  chips.forEach((chip) => {
    chip.addEventListener("click", () => {
      const text = chip.textContent.replace(/^["'\s]+|["'\s]+$/g, "");
      handleSend(text);
    });
  });

  if (micBtn) {
    micBtn.addEventListener("click", () => {
      micBtn.classList.add("recording");
      const sampleQueries = [
        "What is the minimum attendance requirement?",
        "What are my exam results?",
        "Do I have any pending assignments?",
        "When is my next exam scheduled?"
      ];
      const randomQ = sampleQueries[Math.floor(Math.random() * sampleQueries.length)];

      if (input) input.placeholder = "Listening... Speak now";

      setTimeout(() => {
        micBtn.classList.remove("recording");
        if (input) {
          input.placeholder = "Ask anything about courses, exams, campus...";
          input.value = randomQ;
        }
        handleSend(randomQ);
      }, 1200);
    });
  }

  if (clearBtn) {
    clearBtn.addEventListener("click", async () => {
      try {
        await fetch("/api/copilot/clear", { method: "POST" });
      } catch (e) {}

      messagesBox.innerHTML = `
        <div class="chat-bubble-row assistant">
          <div class="chat-bubble-avatar">🤖</div>
          <div class="chat-bubble-content">
            <div class="chat-bubble">
              Chat cleared. Hello! I am your AI College Copilot. Ask me any question about your courses, timetable, attendance, exams, campus events, or institute regulations.
            </div>
            <span class="chat-timestamp">${formatTime()}</span>
          </div>
        </div>
      `;
    });
  }

}

/* ── 5. Tab Switching Engine ─────────────────────────────────────────── */
function initTabsEngine() {
  document.querySelectorAll(".tabs-nav").forEach((tabsNav) => {
    const buttons = tabsNav.querySelectorAll(".tab-btn");
    const container = tabsNav.closest(".module-container") || tabsNav.parentElement;
    if (!container) return;

    buttons.forEach((btn) => {
      btn.addEventListener("click", () => {
        const targetTab = btn.getAttribute("data-tab");
        buttons.forEach((b) => b.classList.remove("active"));
        btn.classList.add("active");

        container.querySelectorAll(".tab-pane").forEach((pane) => {
          pane.classList.toggle("active", pane.id === targetTab);
        });
      });
    });
  });
}

/* ── 6. Flash Message Auto-Dismiss ───────────────────────────────────── */
function initFlashDismiss() {
  document.querySelectorAll(".flash").forEach((el) => {
    setTimeout(() => {
      el.style.transition = "opacity 0.4s ease, transform 0.4s ease";
      el.style.opacity = "0";
      el.style.transform = "translateY(-6px)";
      setTimeout(() => el.remove(), 400);
    }, 4500);
  });
}
