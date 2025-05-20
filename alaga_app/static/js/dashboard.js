document.addEventListener("DOMContentLoaded", () => {
  // Format the current date
  const currentDate = new Date()
  const dateOptions = { year: "numeric", month: "long", day: "numeric" }
  const todaysDateElement = document.getElementById("todaysDate")
  if (todaysDateElement && !todaysDateElement.textContent.includes(currentDate.getFullYear())) {
    todaysDateElement.textContent = `Today's date: ${currentDate.toLocaleDateString("en-US", dateOptions)}`
  }

  // Add event listeners for todo checkboxes
  const checkboxes = document.querySelectorAll('input[type="checkbox"]')

  checkboxes.forEach((checkbox) => {
    checkbox.addEventListener("change", function () {
      const todoId = this.id.replace("task", "")
      const completed = this.checked

      // Update todo status via API
      fetch(`/api/todos/${todoId}`, {
        method: "PUT",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ completed: completed }),
      })
        .then((response) => {
          if (!response.ok) {
            throw new Error("Failed to update todo status")
          }
          return response.json()
        })
        .catch((error) => {
          console.error("Error updating todo status:", error)
          // Revert checkbox state on error
          this.checked = !completed
        })
    })
  })

  // Function to format time (24h to 12h)
  function formatTime(time) {
    if (!time) return ""

    const [hours, minutes] = time.split(":")
    const date = new Date()
    date.setHours(Number.parseInt(hours))
    date.setMinutes(Number.parseInt(minutes))

    return date.toLocaleTimeString("en-US", {
      hour: "numeric",
      minute: "numeric",
      hour12: true,
    })
  }

  // Format all time displays
  document.querySelectorAll(".time-display").forEach((el) => {
    const time = el.textContent.trim()
    if (time) {
      el.textContent = formatTime(time)
    }
  })
})