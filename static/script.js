document.addEventListener("DOMContentLoaded", () => {
  const loginForm = document.getElementById("login-form");
  if (loginForm) {
    loginForm.addEventListener("submit", async (e) => {
      e.preventDefault();

      const username = document.getElementById("username").value;
      const password = document.getElementById("password").value;

      try {
        const response = await fetch("/login", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ username, password }),
        });

        const data = await response.json();

        if (response.ok) {
          alert(data.message); // Should say "Login successful!"
          window.location.href = "dashboard.html"; // redirect if successful
        } else {
          alert(data.message); // Show "Invalid username or password"
        }
      } catch (error) {
        alert("Server connection failed.");
        console.error("Error:", error);
      }
    });
  }
});
window.addEventListener("load", () => {
  // Keep it for session checking (optional)
  fetch("/session")
    .then(response => response.json())
    .then(data => {
      // Do nothing visually — just verify user is logged in
      console.log("Session status:", data);
    })
    .catch(err => console.error("Session fetch failed:", err));
});

