document.addEventListener("DOMContentLoaded", () => {
  // Set current date
  const currentDate = new Date()
  const dateOptions = { year: "numeric", month: "long", day: "numeric" }
  document.getElementById("current-date").textContent =
    `Today's date: ${currentDate.toLocaleDateString("en-US", dateOptions)}`

  // Modal functionality
  const addModal = document.getElementById("addMedicationModal")
  const editModal = document.getElementById("editMedicationsModal")
  const deleteModal = document.getElementById("deleteConfirmationModal")
  const openAddModalBtn = document.getElementById("openAddMedication")
  const cancelAddBtn = document.getElementById("cancelAddMedication")
  const addForm = document.getElementById("addMedicationForm")
  const editForm = document.getElementById("editMedicationForm")
  const medicationSelect = document.getElementById("medicationSelect")
  const noMedicationSelected = document.getElementById("noMedicationSelected")
  const editModalCloseBtn = document.getElementById("editModalCloseBtn")
  const editMedicationsBtn = document.getElementById("editMedicationsBtn")
  const cancelEditBtn = document.getElementById("cancelEditMedication")
  const deleteMedicationBtn = document.getElementById("deleteMedicationBtn")
  const cancelDeleteBtn = document.getElementById("cancelDeleteBtn")
  const confirmDeleteBtn = document.getElementById("confirmDeleteBtn")
  const seeHistoryBtn = document.getElementById("seeHistoryBtn")
  const backToMainBtn = document.getElementById("backToMainBtn")
  const mainContent = document.getElementById("main-content")
  const historyPage = document.getElementById("history-page")

  // Medications and history data
  let medications = []
  let medicationHistory = []
  let selectedMedicationId = null

  const premiumModal = document.getElementById("premiumUpgradeModal")
  const closePremiumBtn = document.getElementById("closePremiumModal")
  const upgradePremiumBtn = document.getElementById("upgradePremiumBtn")

  // Close premium modal
  function closePremiumModal() {
    premiumModal.classList.add("hidden")
    premiumModal.classList.remove("flex")
  }

  closePremiumBtn.addEventListener("click", closePremiumModal)
  
  // fix - added a condition kung ga exist ang btn 
  if (upgradePremiumBtn) {
    upgradePremiumBtn.addEventListener("click", () => {
      alert("This would redirect to the premium upgrade page.")
      closePremiumModal()
    })
  }

  // Close modal when clicking outside
  premiumModal.addEventListener("click", (e) => {
    if (e.target === premiumModal) {
      closePremiumModal()
    }
  })

  // Open add modal - fix - added error handlng condition
  openAddModalBtn.addEventListener("click", () => {
    // Check medication count from the server
    fetch("/api/medications")
      .then((response) => response.json())
      .then((data) => {
        if (data.error) {
          console.error("Error:", data.error)
          // fall back if there's an error
          if (medications.length >= 3) {
            premiumModal.classList.remove("hidden")
            premiumModal.classList.add("flex")
          } else {
            addModal.classList.remove("hidden")
            addModal.classList.add("flex")
          }
          return
        }

        if (data.medications && data.medications.length >= 3) {
          premiumModal.classList.remove("hidden")
          premiumModal.classList.add("flex")
        } else {
          addModal.classList.remove("hidden")
          addModal.classList.add("flex")
        }
      })
      .catch((error) => {
        console.error("Error checking medication count:", error)
        //  fix -- catch error
        if (medications.length >= 3) {
          premiumModal.classList.remove("hidden")
          premiumModal.classList.add("flex")
        } else {
          addModal.classList.remove("hidden")
          addModal.classList.add("flex")
        }
      })
  })

  // Close add modal
  function closeAddModal() {
    addModal.classList.add("hidden")
    addModal.classList.remove("flex")
    addForm.reset()
  }

  cancelAddBtn.addEventListener("click", closeAddModal)

  // Close modal when clicking outside
  addModal.addEventListener("click", (e) => {
    if (e.target === addModal) {
      closeAddModal()
    }
  })

  // Open edit modal
  editMedicationsBtn.addEventListener("click", () => {
    populateMedicationSelect()
    editModal.classList.remove("hidden")
    editModal.classList.add("flex")
  })

  // Close edit modal
  function closeEditModal() {
    editModal.classList.add("hidden")
    editModal.classList.remove("flex")
    editForm.classList.add("hidden")
    noMedicationSelected.classList.remove("hidden")
    selectedMedicationId = null
  }

  editModalCloseBtn.addEventListener("click", closeEditModal)
  cancelEditBtn.addEventListener("click", closeEditModal)

  // Close modal when clicking outside
  editModal.addEventListener("click", (e) => {
    if (e.target === editModal) {
      closeEditModal()
    }
  })

  // Open delete confirmation modal
  deleteMedicationBtn.addEventListener("click", (e) => {
    e.preventDefault()
    deleteModal.classList.remove("hidden")
    deleteModal.classList.add("flex")
  })

  // Close delete confirmation modal
  function closeDeleteModal() {
    deleteModal.classList.add("hidden")
    deleteModal.classList.remove("flex")
  }

  cancelDeleteBtn.addEventListener("click", closeDeleteModal)

  // Close modal when clicking outside
  deleteModal.addEventListener("click", (e) => {
    if (e.target === deleteModal) {
      closeDeleteModal()
    }
  })

  // Confirm delete - fix - added error handling like the ones above
  confirmDeleteBtn.addEventListener("click", () => {
    if (selectedMedicationId) {
      // Delete medication from server
      fetch(`/api/medications/${selectedMedicationId}`, {
        method: "DELETE",
        headers: {
          "Content-Type": "application/json",
        },
      })
        .then((response) => {
          if (!response.ok) {
            throw new Error("Failed to delete medication")
          }
          return response.json()
        })
        .then((data) => {
          // Remove from local array
          medications = medications.filter((med) => med.id != selectedMedicationId)

          // Close modals
          closeDeleteModal()
          closeEditModal()

          // Clear the selected medication ID
          selectedMedicationId = null

          // Re-render medications
          renderMedications()

          // Also update the medication select dropdown
          populateMedicationSelect()
        })
        .catch((error) => {
          console.error("Error deleting medication:", error)
          alert("Failed to delete medication. Please try again.")
          
          // even if server fails, add fallbacks:
          medications = medications.filter((med) => med.id != selectedMedicationId)
          closeDeleteModal()
          closeEditModal()
          selectedMedicationId = null
          renderMedications()
          populateMedicationSelect()
        })
    }
  })

  // Switch between main and history pages
  seeHistoryBtn.addEventListener("click", () => {
    mainContent.classList.add("hidden")
    historyPage.classList.remove("hidden")
    loadMedicationHistory()
  })

  backToMainBtn.addEventListener("click", () => {
    historyPage.classList.add("hidden")
    mainContent.classList.remove("hidden")
  })

  // Populate medication select dropdown
  function populateMedicationSelect() {
    // Clear existing options except the first one
    while (medicationSelect.options.length > 1) {
      medicationSelect.remove(1)
    }

    // Add medications to select
    medications.forEach((med) => {
      const option = document.createElement("option")
      option.value = med.id
      option.textContent = `${med.name} (${formatTime(med.time)})`
      medicationSelect.appendChild(option)
    })
  }

  // Handle medication selection
  medicationSelect.addEventListener("change", function () {
    const selectedId = this.value

    if (selectedId) {
      selectedMedicationId = selectedId
      const medication = medications.find((med) => med.id == selectedId)

      if (medication) {
        // Fill form with medication data
        editForm.elements.name.value = medication.name
        editForm.elements.dosage.value = medication.dosage || ""
        editForm.elements.instructions.value = medication.instructions || ""
        editForm.elements.dosageType.value = medication.dosageType
        editForm.elements.startDate.value = medication.startDate
        editForm.elements.endDate.value = medication.endDate
        editForm.elements.time.value = medication.time

        // Show form, hide message
        editForm.classList.remove("hidden")
        noMedicationSelected.classList.add("hidden")
        editModalCloseBtn.classList.add("hidden")
      }
    } else {
      // Hide form, show message
      editForm.classList.add("hidden")
      noMedicationSelected.classList.remove("hidden")
      editModalCloseBtn.classList.remove("hidden")
      selectedMedicationId = null
    }
  })

  // Handle form submission for adding medication - fix-- added error handling again
  addForm.addEventListener("submit", (e) => {
    e.preventDefault()

    const formData = new FormData(addForm)
    const medication = {
      name: formData.get("name"),
      dosage: formData.get("dosage") || "",
      instructions: formData.get("instructions") || "",
      dosageType: formData.get("dosageType"),
      startDate: formData.get("startDate"),
      endDate: formData.get("endDate"),
      time: formData.get("time"),
    }

    // Send to server
    fetch("/api/medications", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify(medication),
    })
      .then((response) => {
        if (!response.ok) {
          return response.json().then((data) => {
            throw new Error(data.error || "Failed to add medication")
          })
        }
        return response.json()
      })
      .then((data) => {
        medications.push(data.medication)
        renderMedications()
        closeAddModal()
        addForm.reset()
      })
      .catch((error) => {
        console.error("Error adding medication:", error)
        alert(error.message || "Failed to add medication. Please try again.")
        
        // fallback
        const tempMedication = {
          ...medication,
          id: Date.now().toString() // Temporary ID
        }
        medications.push(tempMedication)
        renderMedications()
        closeAddModal()
        addForm.reset()
      })
  })

  // Handle form submission for editing medication - fix - added error handling
  editForm.addEventListener("submit", (e) => {
    e.preventDefault()

    if (selectedMedicationId) {
      const formData = new FormData(editForm)
      const updatedMedication = {
        name: formData.get("name"),
        dosage: formData.get("dosage") || "",
        instructions: formData.get("instructions") || "",
        dosageType: formData.get("dosageType"),
        startDate: formData.get("startDate"),
        endDate: formData.get("endDate"),
        time: formData.get("time"),
      }

      // Send to server
      fetch(`/api/medications/${selectedMedicationId}`, {
        method: "PUT",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify(updatedMedication),
      })
        .then((response) => {
          if (!response.ok) {
            throw new Error("Failed to update medication")
          }
          return response.json()
        })
        .then((data) => {
          // Update local array
          medications = medications.map((med) => {
            if (med.id == selectedMedicationId) {
              return data.medication
            }
            return med
          })

          renderMedications()
          closeEditModal()
        })
        .catch((error) => {
          console.error("Error updating medication:", error)
          alert("Failed to update medication. Please try again.")
          
          //= fallback - still update if server fails
          const tempUpdatedMedication = {
            ...updatedMedication,
            id: selectedMedicationId
          }
          medications = medications.map((med) => {
            if (med.id == selectedMedicationId) {
              return tempUpdatedMedication
            }
            return med
          })
          renderMedications()
          closeEditModal()
        })
    }
  })

  // Load medications from server - fix added error handling
  function loadMedications() {
    fetch("/api/medications")
      .then((response) => {
        if (!response.ok) {
          if (response.status === 400) {
            // No active profile selected, this is expected
            return { medications: [] }
          }
          throw new Error("Failed to load medications")
        }
        return response.json()
      })
      .then((data) => {
        if (data.medications) {
          medications = data.medications
          renderMedications()
        }
      })
      .catch((error) => {
        console.error("Error loading medications:", error)
        // If we can't load from server, initialize using empty array
        medications = []
        renderMedications()
      })
  }

  // Load medication history from server -- fix again
  function loadMedicationHistory() {
    fetch("/api/medication-history")
      .then((response) => {
        if (!response.ok) {
          if (response.status === 400) {
            // No active profile selected, this is expected
            return { history: [] }
          }
          throw new Error("Failed to load medication history")
        }
        return response.json()
      })
      .then((data) => {
        if (data.history) {
          medicationHistory = data.history
          renderMedicationHistory()
        }
      })
      .catch((error) => {
        console.error("Error loading medication history:", error)
        // If we can't load from server, initialize with empty array
        medicationHistory = []
        renderMedicationHistory()
      })
  }

  // Render medications
  function renderMedications() {
    const todayContainer = document.getElementById("today-medications")
    const tomorrowContainer = document.getElementById("tomorrow-medications")
    const upcomingContainer = document.getElementById("upcoming-medications")
    const todayEmptyState = document.getElementById("today-empty-state")
    const tomorrowEmptyState = document.getElementById("tomorrow-empty-state")
    const upcomingEmptyState = document.getElementById("upcoming-empty-state")

    // Check if elements exist before proceeding
    if (!todayContainer || !tomorrowContainer || !upcomingContainer || 
        !todayEmptyState || !tomorrowEmptyState || !upcomingEmptyState) {
      console.error("Required DOM elements not found")
      return
    }

    // Clear existing medications (except empty state)
    Array.from(todayContainer.children).forEach((child) => {
      if (child !== todayEmptyState) {
        child.remove()
      }
    })

    Array.from(tomorrowContainer.children).forEach((child) => {
      if (child !== tomorrowEmptyState) {
        child.remove()
      }
    })

    Array.from(upcomingContainer.children).forEach((child) => {
      if (child !== upcomingEmptyState) {
        child.remove()
      }
    })

    // Reset visibility of empty states
    todayEmptyState.style.display = "block"
    tomorrowEmptyState.style.display = "block"
    upcomingEmptyState.style.display = "block"

    if (medications.length > 0) {
      // Get dates
      const today = new Date()
      today.setHours(0, 0, 0, 0)

      const tomorrow = new Date(today)
      tomorrow.setDate(tomorrow.getDate() + 1)

      const dayAfterTomorrow = new Date(today)
      dayAfterTomorrow.setDate(dayAfterTomorrow.getDate() + 2)

      let hasToday = false
      let hasTomorrow = false
      let hasUpcoming = false

      // Group medications by name for upcoming section
      const upcomingMedicationsByName = {}

      // Add medications
      medications.forEach((med) => {
        const startDate = new Date(med.startDate)
        startDate.setHours(0, 0, 0, 0)
        const endDate = new Date(med.endDate)
        endDate.setHours(0, 0, 0, 0)

        // Generate dates (daily by default)
        const dates = generateDates(startDate, endDate)

        // Check if medication should be shown today
        if (dates.some((date) => isSameDay(date, today))) {
          hasToday = true
          const todayMed = createMedicationElement(med, "today")
          todayContainer.appendChild(todayMed)
          todayEmptyState.style.display = "none"
        }

        // Check if medication should be shown tomorrow
        if (dates.some((date) => isSameDay(date, tomorrow))) {
          hasTomorrow = true
          const tomorrowMed = createMedicationElement(med, "tomorrow")
          tomorrowContainer.appendChild(tomorrowMed)
          tomorrowEmptyState.style.display = "none"
        }

        // Check if medication should be shown in upcoming days
        const upcomingDates = dates.filter((date) => date >= dayAfterTomorrow)

        if (upcomingDates.length > 0) {
          hasUpcoming = true

          // Store medication with its upcoming dates
          if (!upcomingMedicationsByName[med.id]) {
            upcomingMedicationsByName[med.id] = {
              medication: med,
              dates: upcomingDates,
            }
          }

          upcomingEmptyState.style.display = "none"
        }
      })

      // Create one card per medication for upcoming section
      Object.values(upcomingMedicationsByName).forEach(({ medication, dates }) => {
        // Sort dates chronologically
        dates.sort((a, b) => a - b)

        // Get first and last date in the range
        const firstDate = dates[0]
        const lastDate = dates[dates.length - 1]

        // Create a single card with date range
        const upcomingMed = createMedicationElement(medication, "upcoming", firstDate, lastDate)
        upcomingContainer.appendChild(upcomingMed)
      })
    }
  }

  function renderMedicationHistory() {
    const historyContainer = document.getElementById("medication-history")
    const historyEmptyState = document.getElementById("history-empty-state")

    // Check if elements exist before proceeding
    if (!historyContainer || !historyEmptyState) {
      console.error("Required DOM elements for history not found")
      return
    }

    // Clear existing history items (except empty state)
    Array.from(historyContainer.children).forEach((child) => {
      if (child !== historyEmptyState) {
        child.remove()
      }
    })

    // Filter out any entries with null status (only show taken or skipped)
    const validHistory = medicationHistory.filter((item) => item.status === "taken" || item.status === "skipped")

    if (validHistory.length > 0) {
      historyEmptyState.style.display = "none"

      // Sort history by date (newest first)
      validHistory.sort((a, b) => new Date(b.date) - new Date(a.date))

      // Group history items by date
      const historyByDate = {}

      validHistory.forEach((item) => {
        if (!historyByDate[item.date]) {
          historyByDate[item.date] = []
        }
        historyByDate[item.date].push(item)
      })

      // Create history items grouped by date
      Object.keys(historyByDate)
        .sort((a, b) => new Date(b) - new Date(a))
        .forEach((date) => {
          // Add date header
          const dateHeader = document.createElement("div")
          dateHeader.className = "p-3 bg-gray-50 font-medium"
          dateHeader.textContent = formatDate(new Date(date))
          historyContainer.appendChild(dateHeader)

          // Add items for this date
          historyByDate[date].forEach((item) => {
            const historyItem = document.createElement("div")
            historyItem.className = "p-4 flex items-center justify-between border-b"

            const statusClass = item.status === "taken" ? "text-green-500" : "text-red-500"
            const statusText = item.status === "taken" ? "Taken" : "Skipped"

            // Find the medication to get its dosage type
            const medication = medications.find((med) => med.id == item.medicationId)
            const dosageType = medication ? medication.dosageType : "other"

            // Get the appropriate icon based on dosage type
            const icon = getMedicationIcon(dosageType)

            historyItem.innerHTML = `
              <div class="flex items-center">
                ${icon}
                <div class="ml-4">
                  <h4 class="font-medium">${item.name}</h4>
                  <p class="text-sm text-gray-500">${item.dosage || ""}</p>
                </div>
              </div>
              <div class="text-right">
                <p class="text-sm text-gray-500">${formatTime(item.time)}</p>
                <p class="text-sm font-medium ${statusClass}">${statusText}</p>
              </div>
            `

            historyContainer.appendChild(historyItem)
          })
        })
    } else {
      historyEmptyState.style.display = "block"
    }
  }

  // Generate dates (daily by default)
  function generateDates(startDate, endDate) {
    const dates = []
    const currentDate = new Date(startDate)

    while (currentDate <= endDate) {
      dates.push(new Date(currentDate))
      // Default to daily
      currentDate.setDate(currentDate.getDate() + 1)
    }

    return dates
  }

  // Check if two dates are the same day
  function isSameDay(date1, date2) {
    return (
      date1.getFullYear() === date2.getFullYear() &&
      date1.getMonth() === date2.getMonth() &&
      date1.getDate() === date2.getDate()
    )
  }

  // Get medication icon based on dosage type ------------ ICONS
  function getMedicationIcon(dosageType) {
    switch (dosageType) {
      case "tablet":
        return `<i class="fa-solid fa-tablets" style="color: #fc9682;"></i>`
      case "capsule":
        return `<i class="fa-solid fa-capsules" style="color: #2457a8;"></i>`
      case "powder":
        return `<i class="fa-solid fa-mortar-pestle" style="color: #da78ed;"></i>`
      case "solution":
        return `<i class="fa-solid fa-spoon" style="color: #9090a7;"></i>`
      case "injection":
        return `<i class="fa-solid fa-syringe" style="color: #1f858e;"></i>`
      default: // other
        return `<i class="fa-solid fa-prescription-bottle-medical" style="color: #63E6BE;"></i>`
    }
  }

  // Create medication element
  function createMedicationElement(medication, section, date, endDate = null) {
    const div = document.createElement("div")
    div.className = "p-4 flex items-center justify-between medication-card"
    div.dataset.id = medication.id

    // Get the appropriate icon based on dosage type
    const icon = getMedicationIcon(medication.dosageType)

    const time = formatTime(medication.time)

    // Create inner HTML based on section
    if (section === "today") {
      // Check if there's a history entry for today
      const today = new Date().toISOString().split("T")[0]
      const historyEntry = medicationHistory.find((item) => item.medicationId == medication.id && item.date === today)

      // Set initial button states based on current status
      const skipBtnClass =
        historyEntry && historyEntry.status === "skipped"
          ? "h-8 w-8 rounded-full bg-red-500 text-white flex items-center justify-center mr-2 skipped-btn"
          : "h-8 w-8 rounded-full bg-gray-100 text-gray-400 flex items-center justify-center mr-2 skipped-btn"

      const takenBtnClass =
        historyEntry && historyEntry.status === "taken"
          ? "h-8 w-8 rounded-full bg-green-500 text-white flex items-center justify-center taken-btn"
          : "h-8 w-8 rounded-full bg-gray-100 text-gray-400 flex items-center justify-center taken-btn"

      // Set status label
      let statusLabel = ""
      if (historyEntry) {
        statusLabel =
          historyEntry.status === "taken"
            ? '<span class="mr-2 text-green-500 font-medium">Taken</span>'
            : '<span class="mr-2 text-red-500 font-medium">Skip</span>'
      } else {
        statusLabel = '<span class="mr-2 text-gray-400 font-medium"></span>'
      }

      div.innerHTML = `
          <div class="flex items-center">
            ${icon}
            <div class="ml-4">
              <h4 class="font-medium">${medication.name}</h4>
              <p class="text-sm text-gray-500">${medication.dosage}</p>
              ${medication.instructions ? `<p class="text-sm text-gray-500">IN: ${medication.instructions}</p>` : ""}
            </div>
          </div>
          <div class="flex items-center">
            <span class="mr-4">${time}</span>
            ${statusLabel}
            <button class="${skipBtnClass}" title="Mark as skipped" data-medication-id="${medication.id}">
              <svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
              </svg>
            </button>
            <button class="${takenBtnClass}" title="Mark as taken" data-medication-id="${medication.id}">
              <svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7" />
              </svg>
            </button>
          </div>
        `

      // Add event listeners for today's medications
      setTimeout(() => {
        const skippedBtn = div.querySelector(".skipped-btn")
        const takenBtn = div.querySelector(".taken-btn")
        const statusLabelSpan = div.querySelector("span.mr-2")

        if (skippedBtn && takenBtn) {
          skippedBtn.addEventListener("click", () =>
            handleMedicationStatus(medication, skippedBtn, takenBtn, statusLabelSpan, "skipped"),
          )
          takenBtn.addEventListener("click", () =>
            handleMedicationStatus(medication, takenBtn, skippedBtn, statusLabelSpan, "taken"),
          )
        }
      }, 0)
    } else if (section === "upcoming" && date) {
      // For upcoming medications, show date range if endDate is provided
      let dateDisplay = formatDate(date)

      if (endDate && !isSameDay(date, endDate)) {
        dateDisplay = `${formatDate(date)} - ${formatDate(endDate)}`
      }

      div.innerHTML = `
      <div class="flex items-center">
        ${icon}
        <div class="ml-4">
          <h4 class="font-medium">${medication.name}</h4>
          <p class="text-sm text-gray-500">${medication.dosage}</p>
          ${medication.instructions ? `<p class="text-sm text-gray-500">IN: ${medication.instructions}</p>` : ""}
        </div>
      </div>
      <div class="flex items-center">
        <span class="mr-4">${time} <span class="text-gray-500 text-sm">${dateDisplay}</span></span>
      </div>
    `
    } else {
      // For tomorrow medications
      div.innerHTML = `
          <div class="flex items-center">
            ${icon}
            <div class="ml-4">
              <h4 class="font-medium">${medication.name}</h4>
              <p class="text-sm text-gray-500">${medication.dosage}</p>
              ${medication.instructions ? `<p class="text-sm text-gray-500">IN: ${medication.instructions}</p>` : ""}
            </div>
          </div>
          <div class="flex items-center">
            <span class="mr-4">${time}</span>
          </div>
        `
    }

    return div
  }

  // Handle medication status changes (taken or skipped) - fix - added error handling
  function handleMedicationStatus(medication, activeBtn, otherBtn, statusLabel, status) {
    const today = new Date().toISOString().split("T")[0]

    // Find existing history entry
    const existingEntryIndex = medicationHistory.findIndex(
      (item) => item.medicationId == medication.id && item.date === today,
    )

    // Check if the button is already active (toggling off)
    if (
      (status === "taken" && activeBtn.classList.contains("bg-green-500")) ||
      (status === "skipped" && activeBtn.classList.contains("bg-red-500"))
    ) {
      // Reset active button
      if (status === "taken") {
        activeBtn.classList.remove("bg-green-500", "text-white")
        activeBtn.classList.add("bg-gray-100", "text-gray-400")
      } else {
        activeBtn.classList.remove("bg-red-500", "text-white")
        activeBtn.classList.add("bg-gray-100", "text-gray-400")
      }

      // Update status label
      statusLabel.textContent = " "
      statusLabel.classList.remove("text-green-500", "text-red-500")
      statusLabel.classList.add("text-gray-400")

      // Update local data - remove the entry
      if (existingEntryIndex !== -1) {
        medicationHistory.splice(existingEntryIndex, 1)
      }

      // Send delete request to server
      deleteMedicationHistory(medication.id, today)
    } else {
      // Activate this button
      if (status === "taken") {
        activeBtn.classList.remove("bg-gray-100", "text-gray-400")
        activeBtn.classList.add("bg-green-500", "text-white")

        // Update status label
        statusLabel.textContent = "Taken"
        statusLabel.classList.remove("text-gray-400", "text-red-500")
        statusLabel.classList.add("text-green-500")

        // Reset other button
        otherBtn.classList.remove("bg-red-500", "text-white")
        otherBtn.classList.add("bg-gray-100", "text-gray-400")
      } else {
        activeBtn.classList.remove("bg-gray-100", "text-gray-400")
        activeBtn.classList.add("bg-red-500", "text-white")

        // Update status label
        statusLabel.textContent = "Skipped"
        statusLabel.classList.remove("text-gray-400", "text-green-500")
        statusLabel.classList.add("text-red-500")

        // Reset other button
        otherBtn.classList.remove("bg-green-500", "text-white")
        otherBtn.classList.add("bg-gray-100", "text-gray-400")
      }

      // Update local data
      if (existingEntryIndex !== -1) {
        medicationHistory[existingEntryIndex].status = status
      } else {
        medicationHistory.push({
          id: Date.now().toString(), // Temporary ID
          medicationId: medication.id,
          name: medication.name,
          dosage: medication.dosage,
          date: today,
          time: medication.time,
          status: status,
        })
      }

      // Send to server
      updateMedicationStatus(medication.id, status)
    }
  }

  // Delete medication history entry - fix - added error handling
  function deleteMedicationHistory(medicationId, date) {
    // First find the history entry ID if it exists
    fetch("/api/medication-history")
      .then((response) => response.json())
      .then((data) => {
        if (data.history) {
          const historyEntry = data.history.find((item) => item.medicationId == medicationId && item.date === date)

          if (historyEntry) {
            // If we found the entry, delete it
            fetch(`/api/medication-history/${historyEntry.id}`, {
              method: "DELETE",
              headers: {
                "Content-Type": "application/json",
              },
            })
              .then((response) => {
                if (!response.ok) {
                  throw new Error("Failed to delete medication history")
                }
                return response.json()
              })
              .then(() => {
                // If we're viewing the history page, update it
                if (!historyPage.classList.contains("hidden")) {
                  loadMedicationHistory()
                }
              })
              .catch((error) => {
                console.error("Error deleting medication history:", error)
                // still update even if the server fails - condition
                if (!historyPage.classList.contains("hidden")) {
                  renderMedicationHistory()
                }
              })
          }
        }
      })
      .catch((error) => {
        console.error("Error finding medication history to delete:", error)
        // still update 
        if (!historyPage.classList.contains("hidden")) {
          renderMedicationHistory()
        }
      })
  }

  // Update medication status and add to history - fix - added error handling
  function updateMedicationStatus(id, status) {
    // Send to server
    fetch("/api/medication-history", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        medicationId: id,
        status: status,
        date: new Date().toISOString().split("T")[0], // Ensure we're using today's date
      }),
    })
      .then((response) => {
        if (!response.ok) {
          throw new Error("Failed to update medication status")
        }
        return response.json()
      })
      .then((data) => {
        // If we're viewing the history page, update it to reflect changes
        if (!historyPage.classList.contains("hidden")) {
          loadMedicationHistory()
        }
      })
      .catch((error) => {
        console.error("Error updating medication status:", error)
        // If there was an error, still update instead of loading
        if (!historyPage.classList.contains("hidden")) {
          renderMedicationHistory()
        }
      })
  }

  // Format time (24h to 12h)
  function formatTime(time) {
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

  // Format date (Apr 30)
  function formatDate(date) {
    return date.toLocaleDateString("en-US", {
      month: "short",
      day: "numeric",
    })
  }


  //fix - still render even if syncing errors
  function syncMedicationStatus() {
    // First load the latest medication history
    fetch("/api/medication-history")
      .then((response) => {
        if (!response.ok) {
          if (response.status === 400) {
            // No active profile selected, this is expected
            return { history: [] }
          }
          throw new Error("Failed to load medication history")
        }
        return response.json()
      })
      .then((data) => {
        if (data.history) {
          medicationHistory = data.history
          // After updating the history data, re-render medications to update button states
          renderMedications()
        }
      })
      .catch((error) => { // added a condition
        console.error("Error syncing medication status:", error)
        renderMedications()
      })
  }
  
  // Initialize the app - load data when page loads and when active profile changes
  loadMedications()
  loadMedicationHistory()
  syncMedicationStatus()

  // Add event listener for page visibility changes to refresh data when user returns to the page
  document.addEventListener("visibilitychange", () => {
    if (document.visibilityState === "visible") {
      loadMedications()
      loadMedicationHistory()
      syncMedicationStatus()
    }
  })
  
  window.addEventListener("focus", () => {
    syncMedicationStatus()
  })
})