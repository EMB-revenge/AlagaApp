document.addEventListener("DOMContentLoaded", () => {
  // Debug mode - set to true to see console logs
  const DEBUG = true

  function log(...args) {
    if (DEBUG) console.log(...args)
  }

  log("Todo JS loaded")

  // Set current date
  const currentDate = new Date()
  const dateOptions = { year: "numeric", month: "long", day: "numeric" }
  const todaysDateElement = document.getElementById("todaysDate")
  if (todaysDateElement) {
    todaysDateElement.textContent = `Today's date: ${currentDate.toLocaleDateString("en-US", dateOptions)}`
  }

  // Modal elements
  const addModal = document.getElementById("addTodoModal")
  const editModal = document.getElementById("editTasksModal")
  const deleteModal = document.getElementById("deleteConfirmationModal")
  const premiumModal = document.getElementById("premiumUpgradeModal")

  // Buttons
  const openAddModalBtn = document.getElementById("openAddTodo")
  const cancelAddBtn = document.getElementById("cancelAddTodo")
  const editTasksBtn = document.getElementById("editTasksBtn")
  const cancelEditBtn = document.getElementById("cancelEditTask")
  const deleteTaskBtn = document.getElementById("deleteTaskBtn")
  const cancelDeleteBtn = document.getElementById("cancelDeleteBtn")
  const confirmDeleteBtn = document.getElementById("confirmDeleteBtn")
  const closePremiumBtn = document.getElementById("closePremiumModal")
  const upgradePremiumBtn = document.getElementById("upgradePremiumBtn")
  const editModalCloseBtn = document.getElementById("editModalCloseBtn")

  // Forms and selects
  const addForm = document.getElementById("addTodoForm")
  const editForm = document.getElementById("editTaskForm")
  const taskSelect = document.getElementById("taskSelect")
  const noTaskSelected = document.getElementById("noTaskSelected")

  // Tasks data
  let todayTasks = []
  let tomorrowTasks = []
  let upcomingTasks = []
  let selectedTaskId = null

  // Close premium modal
  function closePremiumModal() {
    log("Closing premium modal")
    if (premiumModal) {
      premiumModal.classList.add("hidden")
      premiumModal.classList.remove("flex")
    } else {
      log("Error: Premium modal element not found")
    }
  }

  // Add event listener for premium modal close button
  if (closePremiumBtn) {
    log("Adding event listener to premium modal close button")
    closePremiumBtn.addEventListener("click", (e) => {
      e.preventDefault()
      log("Premium modal close button clicked")
      closePremiumModal()
    })
  } else {
    log("Warning: Premium modal close button not found")
  }

  // Add event listener for premium upgrade button
  if (upgradePremiumBtn) {
    upgradePremiumBtn.addEventListener("click", (e) => {
      e.preventDefault()
      alert("This would redirect to the premium upgrade page.")
      closePremiumModal()
    })
  }

  // Close modal when clicking outside
  if (premiumModal) {
    premiumModal.addEventListener("click", (e) => {
      if (e.target === premiumModal) {
        closePremiumModal()
      }
    })
  }

  // Count total tasks
  function countTotalTasks() {
    return todayTasks.length + tomorrowTasks.length + upcomingTasks.length
  }

  // Check if task limit reached
  function isTaskLimitReached() {
    return countTotalTasks() >= 5
  }

  // Open add modal
  if (openAddModalBtn) {
    openAddModalBtn.addEventListener("click", () => {
      // Check task count
      if (isTaskLimitReached()) {
        if (premiumModal) {
          premiumModal.classList.remove("hidden")
          premiumModal.classList.add("flex")
          log("Showing premium modal")
        } else {
          log("Error: Premium modal element not found")
          alert("You've reached the maximum number of tasks (5). Please upgrade to premium.")
        }
      } else {
        addModal.classList.remove("hidden")
        addModal.classList.add("flex")

        // Set default date to today
        const today = new Date()
        const formattedDate = today.toISOString().split("T")[0]
        const newTodoDateElement = document.getElementById("newTodoDate")
        if (newTodoDateElement) {
          newTodoDateElement.value = formattedDate
        }
      }
    })
  }

  // Close add modal
  function closeAddModal() {
    if (addModal) {
      addModal.classList.add("hidden")
      addModal.classList.remove("flex")
    }
    if (addForm) {
      addForm.reset()
    }
  }

  if (cancelAddBtn) {
    cancelAddBtn.addEventListener("click", closeAddModal)
  }

  // Close modal when clicking outside
  if (addModal) {
    addModal.addEventListener("click", (e) => {
      if (e.target === addModal) {
        closeAddModal()
      }
    })
  }

  // Open edit modal
  if (editTasksBtn) {
    editTasksBtn.addEventListener("click", () => {
      populateTaskSelect()
      editModal.classList.remove("hidden")
      editModal.classList.add("flex")
    })
  }

  // Close edit modal
  function closeEditModal() {
    if (editModal) {
      editModal.classList.add("hidden")
      editModal.classList.remove("flex")
    }
    if (editForm) {
      editForm.classList.add("hidden")
    }
    if (noTaskSelected) {
      noTaskSelected.classList.remove("hidden")
    }
    selectedTaskId = null
  }

  if (editModalCloseBtn) {
    editModalCloseBtn.addEventListener("click", closeEditModal)
  }

  if (cancelEditBtn) {
    cancelEditBtn.addEventListener("click", closeEditModal)
  }

  // Close modal when clicking outside
  if (editModal) {
    editModal.addEventListener("click", (e) => {
      if (e.target === editModal) {
        closeEditModal()
      }
    })
  }

  // Open delete confirmation modal
  if (deleteTaskBtn) {
    deleteTaskBtn.addEventListener("click", (e) => {
      e.preventDefault()
      deleteModal.classList.remove("hidden")
      deleteModal.classList.add("flex")
    })
  }

  // Close delete confirmation modal
  function closeDeleteModal() {
    if (deleteModal) {
      deleteModal.classList.add("hidden")
      deleteModal.classList.remove("flex")
    }
  }

  if (cancelDeleteBtn) {
    cancelDeleteBtn.addEventListener("click", closeDeleteModal)
  }

  // Close modal when clicking outside
  if (deleteModal) {
    deleteModal.addEventListener("click", (e) => {
      if (e.target === deleteModal) {
        closeDeleteModal()
      }
    })
  }

  // Populate task select dropdown
  function populateTaskSelect() {
    if (!taskSelect) {
      log("Error: Task select element not found")
      return
    }

    // Clear existing options except the first one
    while (taskSelect.options.length > 1) {
      taskSelect.remove(1)
    }

    // Add all tasks to select
    const allTasks = [...todayTasks, ...tomorrowTasks, ...upcomingTasks]
    allTasks.forEach((task) => {
      const option = document.createElement("option")
      option.value = task.id
      option.textContent = `${task.text} (${formatShortDate(new Date(task.date))})`
      taskSelect.appendChild(option)
    })
  }

  // Handle task selection
  if (taskSelect) {
    taskSelect.addEventListener("change", function () {
      const selectedId = this.value

      if (selectedId) {
        selectedTaskId = Number.parseInt(selectedId)
        const allTasks = [...todayTasks, ...tomorrowTasks, ...upcomingTasks]
        const task = allTasks.find((t) => t.id == selectedId)

        if (task) {
          // Fill form with task data
          editForm.elements.text.value = task.text
          // Convert date format from ISO to YYYY-MM-DD for input field
          const dateObj = new Date(task.date)
          const formattedDate = dateObj.toISOString().split("T")[0]
          editForm.elements.date.value = formattedDate

          // Show form, hide message
          editForm.classList.remove("hidden")
          noTaskSelected.classList.add("hidden")
          editModalCloseBtn.classList.add("hidden")
        }
      } else {
        // Hide form, show message
        editForm.classList.add("hidden")
        noTaskSelected.classList.remove("hidden")
        editModalCloseBtn.classList.remove("hidden")
        selectedTaskId = null
      }
    })
  }

  // Confirm delete
  if (confirmDeleteBtn) {
    confirmDeleteBtn.addEventListener("click", () => {
      if (selectedTaskId) {
        // Delete from server
        deleteTodoFromServer(selectedTaskId)

        // Close modals
        closeDeleteModal()
        closeEditModal()

        // Clear the selected task ID
        selectedTaskId = null
      }
    })
  }

  // Handle form submission for adding task
  if (addForm) {
    addForm.addEventListener("submit", (e) => {
      e.preventDefault()

      const formData = new FormData(addForm)
      const task = {
        text: formData.get("text"),
        date: formData.get("date"),
        completed: false,
      }

      // Add task to server
      addTodoToServer(task)

      // Close modal and reset form
      closeAddModal()
    })
  }

  // Handle form submission for editing task
  if (editForm) {
    editForm.addEventListener("submit", (e) => {
      e.preventDefault()

      if (selectedTaskId) {
        const formData = new FormData(editForm)
        const updatedTask = {
          text: formData.get("text"),
          date: formData.get("date"),
          completed: false, // Reset completion status when edited
        }

        // Update task on server
        updateTodoOnServer(selectedTaskId, updatedTask)

        // Close modal
        closeEditModal()
      }
    })
  }

  // Check if two dates are the same day
  function isSameDay(date1, date2) {
    return (
      date1.getFullYear() === date2.getFullYear() &&
      date1.getMonth() === date2.getMonth() &&
      date1.getDate() === date2.getDate()
    )
  }

  // Format date for display in upcoming tasks (e.g., "May 1")
  function formatShortDate(date) {
    return date.toLocaleDateString("en-US", { month: "short", day: "numeric" })
  }

  // Render all tasks
  function renderTasks() {
    renderTaskList("today", todayTasks)
    renderTaskList("tomorrow", tomorrowTasks)
    renderTaskList("upcoming", upcomingTasks)
  }

  // Render a specific task list
  function renderTaskList(type, tasks) {
    const container = document.getElementById(`${type}-tasks`)
    if (!container) return

    const emptyState = document.getElementById(`${type}-empty-state`)
    if (!emptyState) return

    // Clear existing tasks (except empty state)
    Array.from(container.children).forEach((child) => {
      if (child !== emptyState) {
        child.remove()
      }
    })

    // Reset visibility of empty state
    emptyState.style.display = "block"

    if (tasks.length > 0) {
      emptyState.style.display = "none"

      tasks.forEach((task) => {
        const taskElement = createTaskElement(task, type)
        container.appendChild(taskElement)
      })
    }
  }

  // Create task element
  function createTaskElement(task, section) {
    const div = document.createElement("div")
    div.className = "p-4 flex items-center justify-between task-card"
    div.dataset.id = task.id

    // Create inner HTML based on section
    if (section === "upcoming") {
      div.innerHTML = `
      <div class="flex items-center">
        <input type="checkbox" id="task-${task.id}" 
          class="w-6 h-6 appearance-none border-2 border-gray-300 rounded-full 
          checked:bg-[#8491D3] checked:border-transparent focus:outline-none relative">
        <label for="task-${task.id}" class="ml-3 text-gray-800">
          <span class="task-text">${task.text}</span>
          <span class="text-xs text-gray-500 ml-2">(${formatShortDate(new Date(task.date))})</span>
        </label>
      </div>
    `
    } else {
      div.innerHTML = `
      <div class="flex items-center">
        <input type="checkbox" id="task-${task.id}" 
          class="w-6 h-6 appearance-none border-2 border-gray-300 rounded-full 
          checked:bg-[#8491D3] checked:border-transparent focus:outline-none relative">
        <label for="task-${task.id}" class="ml-3 text-gray-800">
          <span class="task-text">${task.text}</span>
        </label>
      </div>
    `
    }

    // Add event listener for checkbox
    setTimeout(() => {
      const checkbox = div.querySelector('input[type="checkbox"]')
      if (checkbox) {
        // Explicitly set the checked property based on task.completed
        checkbox.checked = task.completed

        checkbox.addEventListener("change", () => {
          const taskId = div.dataset.id
          const allTasks = [...todayTasks, ...tomorrowTasks, ...upcomingTasks]
          const task = allTasks.find((t) => t.id == taskId)

          if (task) {
            // Update the task's completed status
            task.completed = checkbox.checked

            // Update on server
            updateTodoOnServer(taskId, { completed: checkbox.checked })
          }
        })
      }
    }, 0)

    return div
  }

  // API Functions

  // Load todos from server
  function loadTodosFromServer() {
    log("Loading todos from server")
    fetch("/api/todos")
      .then((response) => {
        if (!response.ok) {
          if (response.status === 400) {
            // No active profile selected, this is expected
            return response.json().then((data) => {
              showNoActiveProfileError(data.error || "No active profile selected. Data will be erased when refreshed.")
              return { today: [], tomorrow: [], upcoming: [] }
            })
          }
          throw new Error(`HTTP error! Status: ${response.status}`)
        }
        return response.json()
      })
      .then((data) => {
        log("Received todos from server:", data)
        if (data.error) {
          // Show error message for no active profile
          showNoActiveProfileError(data.error)
          todayTasks = []
          tomorrowTasks = []
          upcomingTasks = []
        } else {
          // Hide error message if it exists
          hideNoActiveProfileError()
          todayTasks = data.today || []
          tomorrowTasks = data.tomorrow || []
          upcomingTasks = data.upcoming || []
        }
        renderTasks()
      })
      .catch((error) => {
        log("Error loading todos:", error)
        // Initialize with empty arrays if there's an error
        todayTasks = []
        tomorrowTasks = []
        upcomingTasks = []
        renderTasks()
      })
  }

  // Show error message for no active profile
  function showNoActiveProfileError(errorMessage) {
    log("Showing no active profile error:", errorMessage)

    // Check if error message already exists
    if (document.getElementById("no-active-profile-error")) {
      return
    }

    // Create error message element
    const errorDiv = document.createElement("div")
    errorDiv.id = "no-active-profile-error"
    errorDiv.className = "p-4 mb-4 text-sm text-red-700 bg-red-100 rounded-lg"
    errorDiv.innerHTML = `
  <div class="flex items-center">
    <i class="fa-solid fa-circle-exclamation mr-2"></i>
    <span>${errorMessage}</span>
  </div>
`

    // Insert at the top of the main content
    const mainContent = document.querySelector(".container")
    if (mainContent) {
      mainContent.insertBefore(errorDiv, mainContent.firstChild)
    }
  }

  // Hide error message for no active profile
  function hideNoActiveProfileError() {
    log("Hiding no active profile error")

    // Remove error message
    const errorDiv = document.getElementById("no-active-profile-error")
    if (errorDiv) {
      errorDiv.remove()
    }
  }

  // Add todo to server
  function addTodoToServer(todo) {
    log("Adding todo to server:", todo)
    fetch("/api/todos", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify(todo),
      credentials: "same-origin",
    })
    .then((response) => {
      if (!response.ok) {
        if (response.status === 403) {
          // Premium limit reached
          if (premiumModal) {
            premiumModal.classList.remove("hidden")
            premiumModal.classList.add("flex")
            log("Showing premium modal due to 403 response")
          } else {
            log("Error: Premium modal element not found")
            alert("You've reached the maximum number of tasks (5). Please upgrade to premium.")
          }
          throw new Error("Premium limit reached")
        }
        if (response.status === 400) {
          // No active profile selected, show error but still add the todo locally
          return response.json().then((data) => {
            showNoActiveProfileError(data.error || "No active profile selected. Data will be erased when refreshed.")
            
            // Create a temporary todo with a generated ID
            const tempTodo = {
              ...todo,
              id: Date.now(),
              completed: false,
            }

            // Add to appropriate list based on date
            const today = new Date().toISOString().split("T")[0]
            const tomorrow = new Date(Date.now() + 86400000).toISOString().split("T")[0]

            if (todo.date === today) {
              todayTasks.push(tempTodo)
            } else if (todo.date === tomorrow) {
              tomorrowTasks.push(tempTodo)
            } else {
              upcomingTasks.push(tempTodo)
            }

            renderTasks()
            return { todo: tempTodo }
          })
        }
        return response.json().then((err) => {
          throw new Error(err.error || `HTTP error! Status: ${response.status}`)
        })
      }
      return response.json()
    })
    .then((data) => {
      log("Server response after adding todo:", data)
      // Reload todos from server
      loadTodosFromServer()
    })
    .catch((error) => {
      log("Error adding todo:", error)
      // If not a premium error, show general error
      if (!error.message.includes("Premium")) {
        alert("There was an error adding the todo: " + error.message)
      }
    })
  }

  // Update todo on server
  function updateTodoOnServer(todoId, updatedFields) {
    log("Updating todo on server:", todoId, updatedFields)
    fetch(`/api/todos/${todoId}`, {
      method: "PUT",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify(updatedFields),
      credentials: "same-origin",
    })
      .then((response) => {
        if (!response.ok) {
          return response.json().then((err) => {
            throw new Error(err.error || `HTTP error! Status: ${response.status}`)
          })
        }
        return response.json()
      })
      .then((data) => {
        log("Server response after updating todo:", data)
        // Reload todos from server
        loadTodosFromServer()
      })
      .catch((error) => {
        log("Error updating todo:", error)
        alert("There was an error updating the todo: " + error.message)
      })
  }

  // Delete todo from server
  function deleteTodoFromServer(todoId) {
    log("Deleting todo from server:", todoId)
    fetch(`/api/todos/${todoId}`, {
      method: "DELETE",
      credentials: "same-origin",
    })
      .then((response) => {
        if (!response.ok) {
          return response.json().then((err) => {
            throw new Error(err.error || `HTTP error! Status: ${response.status}`)
          })
        }
        return response.json()
      })
      .then((data) => {
        log("Server response after deleting todo:", data)
        // Reload todos from server
        loadTodosFromServer()
      })
      .catch((error) => {
        log("Error deleting todo:", error)
        alert("There was an error deleting the todo: " + error.message)
      })
  }

  // Initialize the app
  loadTodosFromServer()
})
