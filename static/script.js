document.addEventListener("DOMContentLoaded", () => {
  const loginForm = document.getElementById("login-form");
  if (loginForm) {
    loginForm.addEventListener("submit", async (e) => {
      e.preventDefault();

      const username = document.getElementById("username").value;
      const password = document.getElementById("password").value;

      try {
        const response = await fetch("http://127.0.0.1:5001/api/login", {
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
  fetch("/session")
    .then(response => response.json())
    .then(data => {
      if (data.logged_in) {
        document.getElementById("user-display").innerText = `Welcome, ${data.username}!`;
      } else {
        document.getElementById("user-display").innerText = "Please log in.";
      }
    });
});
