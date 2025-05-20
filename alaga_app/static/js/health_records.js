document.addEventListener("DOMContentLoaded", () => {
  // Debug mode - set to true to see console logs
  const DEBUG = true

  function log(...args) {
    if (DEBUG) console.log(...args)
  }

  log("Health Records JS loaded")

  // Safely get DOM element - returns null if element doesn't exist
  function getElement(id) {
    return document.getElementById(id)
  }

  // Safely add event listener - only adds if element exists
  function addEventListenerSafe(element, event, handler) {
    if (element) {
      element.addEventListener(event, handler)
      return true
    }
    return false
  }

  // Set current date
  const currentDateElement = getElement("current-date")
  if (currentDateElement) {
    const currentDate = new Date()
    const dateOptions = { year: "numeric", month: "long", day: "numeric" }
    currentDateElement.textContent = `Today's date: ${currentDate.toLocaleDateString("en-US", dateOptions)}`
  }

  // DOM Elements
  const mainContent = getElement("main-content")
  const historyPage = getElement("history-page")
  const seeHistoryBtn = getElement("seeHistoryBtn")
  const backToMainBtn = getElement("backToMainBtn")
  const editHealthRecordsBtn = getElement("editHealthRecordsBtn")
  const openAddHealthRecordBtn = getElement("openAddHealthRecord")
  const addHealthRecordModal = getElement("addHealthRecordModal")
  const addHealthRecordForm = getElement("addHealthRecordForm")
  const cancelAddHealthRecordBtn = getElement("cancelAddHealthRecord")
  const recordCategory = getElement("recordCategory")
  const vitalSignsOptions = getElement("vitalSignsOptions")
  const biometricsOptions = getElement("biometricsOptions")
  const valueInput = getElement("valueInput")
  const bloodPressureInputs = getElement("bloodPressureInputs")
  const medicalNotesInputs = getElement("medicalNotesInputs")
  const vitalSignType = getElement("vitalSignType")
  const biometricType = getElement("biometricType")
  const editHealthRecordsModal = getElement("editHealthRecordsModal")
  const healthRecordSelect = getElement("healthRecordSelect")
  const editHealthRecordForm = getElement("editFormFields")
  const noRecordSelected = getElement("noRecordSelected")
  const cancelEditHealthRecordBtn = getElement("cancelEditHealthRecord")
  const deleteHealthRecordBtn = getElement("deleteHealthRecordBtn")
  const deleteConfirmationModal = getElement("deleteConfirmationModal")
  const cancelDeleteBtn = getElement("cancelDeleteBtn")
  const confirmDeleteBtn = getElement("confirmDeleteBtn")
  const editModalCloseBtn = getElement("editModalCloseBtn")
  const premiumUpgradeModal = getElement("premiumUpgradeModal")
  const closePremiumModal = getElement("closePremiumModal")
  const upgradePremiumBtn = getElement("upgradePremiumBtn")
  const addVitalSignBtn = getElement("addVitalSignBtn")
  const addBiometricBtn = getElement("addBiometricBtn")
  const addMedicalNoteBtn = getElement("addMedicalNoteBtn")

  // Data storage
  let healthRecords = []
  let selectedRecordId = null

  // Icons for different health record types
  const icons = {
    // Vital Signs
    "blood-pressure": `<i class="fa-solid fa-droplet" style="color: #b10606;"></i>`,

    "body-temperature": `<i class="fa-solid fa-thermometer" style="color: #ef852e;"></i>`,

    "heart-rate": `<i class="fa-solid fa-heart-pulse" style="color: #e85e5e;"></i>`,

    "respiratory-rate": `<i class="fa-solid fa-lungs" style="color: #39c69c;"></i>`,

    "oxygen-saturation": `<i class="fa-solid fa-circle-notch" style="color: #74C0FC;"></i>`,

    weight: `<i class="fa-solid fa-weight-scale" style="color: #d16ba7;"></i>`,

    // Other vital sign
    "other-vital-sign": `<i class="fa-solid fa-stethoscope" style="color: #8491D3;"></i>`,

    //BIOMETRICS
    "blood-glucose": `<i class="fa-solid fa-cube" style="color: #74C0FC;"></i>`,

    cholesterol: `<i class="fa-solid fa-earth-oceania" style="color: #FFD43B;"></i>`,

    "hemoglobin-a1c": `<i class="fas fa-spinner" style="color: #851e23;"></i>`,

    creatinine: `<i class="fas fa-dot-circle" style="color: #e16c2d;"></i>`,

    "liver-enzymes": `<i class="fas fa-map-marker" style="color: #fbc089;"></i>`,

    // Other biometric
    "other-biometric": `<i class="fa-solid fa-vial" style="color: #BC6FB7;"></i>`,

    // Medical Notes
    "medical-notes": `<i class="fa-solid fa-comment-dots" style="color: #e44ed0;"></i>`,
  }

  // Get icon for a record type
  function getIcon(record) {
    if (record.category === "medical-notes") {
      return icons["medical-notes"]
    }

    return icons[record.type] || icons["default"]
  }

  // Format date for display
  function formatDate(dateString) {
    const date = new Date(dateString)
    return date.toLocaleDateString("en-US", { month: "short", day: "numeric" })
  }

  // Format time with AM/PM
  function formatTimeWithAMPM(timeString) {
    if (!timeString) return ""

    const [hours, minutes] = timeString.split(":")
    const hour = Number.parseInt(hours)
    const ampm = hour >= 12 ? "PM" : "AM"
    const hour12 = hour % 12 || 12

    return `${hour12}:${minutes} ${ampm}`
  }

  // Format date and time for "Last taken" display
  function formatLastTaken(dateString, timeString) {
    const date = formatDate(dateString)
    const time = formatTimeWithAMPM(timeString)
    return `${date}, ${time}`
  }

  // Category-specific buttons
  addEventListenerSafe(addVitalSignBtn, "click", () => {
    openAddModal("vital-signs")
  })

  addEventListenerSafe(addBiometricBtn, "click", () => {
    openAddModal("biometrics")
  })

  addEventListenerSafe(addMedicalNoteBtn, "click", () => {
    openAddModal("medical-notes")
  })

  // Open add modal with pre-selected category
  function openAddModal(category = null) {
    log("Opening add modal with category:", category)

    if (!addHealthRecordModal) {
      log("Error: Add health record modal not found")
      return
    }

    // Check if we've reached the limit
    const uniqueVitalSigns = new Set(
      healthRecords.filter((record) => record.category === "vital-signs").map((record) => record.type),
    ).size

    const uniqueBiometrics = new Set(
      healthRecords.filter((record) => record.category === "biometrics").map((record) => record.type),
    ).size

    const medicalNotesCount = healthRecords.filter((record) => record.category === "medical-notes").length

    const totalRecordTypes = uniqueVitalSigns + uniqueBiometrics + (medicalNotesCount > 0 ? 1 : 0)

    if (totalRecordTypes >= 3) {
      showPremiumModal()
      return
    }

    // Reset form
    if (addHealthRecordForm) {
      addHealthRecordForm.reset()
    }

    // Set default date and time
    const now = new Date()
    const formattedDate = now.toISOString().split("T")[0]
    const hours = String(now.getHours()).padStart(2, "0")
    const minutes = String(now.getMinutes()).padStart(2, "0")
    const formattedTime = `${hours}:${minutes}`

    const dateInput = getElement("dateTaken")
    const timeInput = getElement("timeTaken")

    if (dateInput) dateInput.value = formattedDate
    if (timeInput) timeInput.value = formattedTime

    // Pre-select category if provided
    if (category && recordCategory) {
      recordCategory.value = category
      handleCategoryChange()
    }

    // Show modal
    addHealthRecordModal.classList.remove("hidden")
    addHealthRecordModal.classList.add("flex")

    // Add "Other" option to vital signs dropdown if it doesn't exist
    if (vitalSignType && !vitalSignType.querySelector('option[value="other-vital-sign"]')) {
      const otherOption = document.createElement("option")
      otherOption.value = "other-vital-sign"
      otherOption.textContent = "Other"
      vitalSignType.appendChild(otherOption)
    }

    // Add "Other" option to biometrics dropdown if it doesn't exist
    if (biometricType && !biometricType.querySelector('option[value="other-biometric"]')) {
      const otherOption = document.createElement("option")
      otherOption.value = "other-biometric"
      otherOption.textContent = "Other"
      biometricType.appendChild(otherOption)
    }

    // Create other type input field if it doesn't exist
    if (!getElement("otherTypeInput")) {
      const otherTypeDiv = document.createElement("div")
      otherTypeDiv.id = "otherTypeInput"
      otherTypeDiv.className = "mb-4 hidden"
      otherTypeDiv.innerHTML = `
  <label for="otherType" class="block text-gray-700 text-sm font-bold mb-2">
    Specify Type:
  </label>
  <input
    type="text"
    id="otherType"
    name="otherType"
    class="shadow appearance-none border rounded w-full py-2 px-3 text-gray-700 leading-tight focus:outline-none focus:shadow-outline"
    placeholder="Enter the specific type"
  />
`
      // Insert after the biometrics options
      if (biometricsOptions) {
        biometricsOptions.parentNode.insertBefore(otherTypeDiv, biometricsOptions.nextSibling)
      } else if (vitalSignsOptions) {
        vitalSignsOptions.parentNode.insertBefore(otherTypeDiv, vitalSignsOptions.nextSibling)
      }
    }
  }

  // Close add modal
  function closeAddModal() {
    log("Closing add modal")

    if (!addHealthRecordModal) {
      log("Error: Add health record modal not found")
      return
    }

    addHealthRecordModal.classList.add("hidden")
    addHealthRecordModal.classList.remove("flex")

    if (addHealthRecordForm) {
      addHealthRecordForm.reset()
    }
  }

  // Show premium upgrade modal
  function showPremiumModal() {
    log("Showing premium modal")

    if (!premiumUpgradeModal) {
      log("Error: Premium upgrade modal not found")
      alert("You've reached the maximum number of health record types (3). Please upgrade to premium.")
      return
    }

    premiumUpgradeModal.classList.remove("hidden")
    premiumUpgradeModal.classList.add("flex")
  }

  // Close premium modal
  function closePremiumModalFn() {
    log("Closing premium modal")

    if (!premiumUpgradeModal) {
      log("Error: Premium upgrade modal not found")
      return
    }

    premiumUpgradeModal.classList.add("hidden")
    premiumUpgradeModal.classList.remove("flex")
  }

  // Handle category change
  function handleCategoryChange() {
    log("Handling category change")

    if (!recordCategory) {
      log("Error: Record category element not found")
      return
    }

    const category = recordCategory.value

    // Hide all category-specific inputs
    if (vitalSignsOptions) vitalSignsOptions.classList.add("hidden")
    if (biometricsOptions) biometricsOptions.classList.add("hidden")
    if (valueInput) valueInput.classList.add("hidden")
    if (bloodPressureInputs) bloodPressureInputs.classList.add("hidden")
    if (medicalNotesInputs) medicalNotesInputs.classList.add("hidden")

    // Show relevant inputs based on category
    if (category === "vital-signs") {
      if (vitalSignsOptions) vitalSignsOptions.classList.remove("hidden")
      if (valueInput) valueInput.classList.remove("hidden")
      handleVitalSignTypeChange()
    } else if (category === "biometrics") {
      if (biometricsOptions) biometricsOptions.classList.remove("hidden")
      if (valueInput) valueInput.classList.remove("hidden")
    } else if (category === "medical-notes") {
      if (medicalNotesInputs) medicalNotesInputs.classList.remove("hidden")
    }
  }

  // Handle vital sign type change
  function handleVitalSignTypeChange() {
    log("Handling vital sign type change")

    if (!vitalSignType) {
      log("Error: Vital sign type element not found")
      return
    }

    const type = vitalSignType.value
    const recordValueInput = getElement("recordValue")
    const otherTypeInput = getElement("otherTypeInput")

    // Hide blood pressure inputs and other type input by default
    if (bloodPressureInputs) bloodPressureInputs.classList.add("hidden")
    if (otherTypeInput) otherTypeInput.classList.add("hidden")

    // Show blood pressure inputs if blood pressure is selected
    if (type === "blood-pressure") {
      if (bloodPressureInputs) bloodPressureInputs.classList.remove("hidden")
      if (recordValueInput) recordValueInput.classList.add("hidden")
    } else {
      if (recordValueInput) recordValueInput.classList.remove("hidden")

      // Show other type input if other is selected
      if (type === "other-vital-sign" && otherTypeInput) {
        otherTypeInput.classList.remove("hidden")
      }
    }
  }

  function handleBiometricTypeChange() {
    log("Handling biometric type change")

    if (!biometricType) {
      log("Error: Biometric type element not found")
      return
    }

    const type = biometricType.value
    const recordValueInput = getElement("recordValue")
    const otherTypeInput = getElement("otherTypeInput")

    if (recordValueInput) recordValueInput.classList.remove("hidden")

    // Hide other type input by default
    if (otherTypeInput) otherTypeInput.classList.add("hidden")

    // Show other type input if other is selected
    if (type === "other-biometric" && otherTypeInput) {
      otherTypeInput.classList.remove("hidden")
    }
  }

  // Open edit modal
  function openEditModal() {
    log("Opening edit modal")

    if (!editHealthRecordsModal) {
      log("Error: Edit health records modal not found")
      return
    }

    // Populate select with health records
    populateHealthRecordSelect()

    // Show modal
    editHealthRecordsModal.classList.remove("hidden")
    editHealthRecordsModal.classList.add("flex")
  }

  // Close edit modal
  function closeEditModal() {
    log("Closing edit modal")

    if (!editHealthRecordsModal) {
      log("Error: Edit health records modal not found")
      return
    }

    editHealthRecordsModal.classList.add("hidden")
    editHealthRecordsModal.classList.remove("flex")

    if (editHealthRecordForm) editHealthRecordForm.classList.add("hidden")
    if (noRecordSelected) noRecordSelected.classList.remove("hidden")
    if (editModalCloseBtn) editModalCloseBtn.classList.remove("hidden")

    selectedRecordId = null
  }

  // Open delete confirmation modal
  function openDeleteModal() {
    log("Opening delete confirmation modal")

    if (!deleteConfirmationModal) {
      log("Error: Delete confirmation modal not found")
      return
    }

    deleteConfirmationModal.classList.remove("hidden")
    deleteConfirmationModal.classList.add("flex")
  }

  // Close delete confirmation modal
  function closeDeleteModal() {
    log("Closing delete confirmation modal")

    if (!deleteConfirmationModal) {
      log("Error: Delete confirmation modal not found")
      return
    }

    deleteConfirmationModal.classList.add("hidden")
    deleteConfirmationModal.classList.remove("flex")
  }

  // Populate health record select
  function populateHealthRecordSelect() {
    log("Populating health record select")

    if (!healthRecordSelect) {
      log("Error: Health record select element not found")
      return
    }

    // Clear existing options except the first one
    while (healthRecordSelect.options.length > 1) {
      healthRecordSelect.remove(1)
    }

    // Add all health records to select
    healthRecords.forEach((record) => {
      const option = document.createElement("option")
      option.value = record.id

      let label = ""
      if (record.category === "vital-signs" || record.category === "biometrics") {
        const typeLabel = record.type.replace(/-/g, " ")
        label = `${typeLabel.charAt(0).toUpperCase() + typeLabel.slice(1)} (${formatDate(record.date)})`
      } else if (record.category === "medical-notes") {
        label = `${record.subject} (${formatDate(record.date)})`
      }

      option.textContent = label
      healthRecordSelect.appendChild(option)
    })
  }

  // Handle health record selection
  function handleHealthRecordSelection() {
    log("Handling health record selection")

    if (!healthRecordSelect) {
      log("Error: Health record select element not found")
      return
    }

    const recordId = Number.parseInt(healthRecordSelect.value)

    if (recordId) {
      selectedRecordId = recordId
      const record = healthRecords.find((r) => r.id === recordId)

      if (record) {
        // Show form, hide message
        if (editHealthRecordForm) editHealthRecordForm.classList.remove("hidden")
        if (noRecordSelected) noRecordSelected.classList.add("hidden")
        if (editModalCloseBtn) editModalCloseBtn.classList.add("hidden")

        // Populate form fields based on record type
        populateEditForm(record)
      }
    } else {
      // Hide form, show message
      if (editHealthRecordForm) editHealthRecordForm.classList.add("hidden")
      if (noRecordSelected) noRecordSelected.classList.remove("hidden")
      if (editModalCloseBtn) editModalCloseBtn.classList.remove("hidden")
      selectedRecordId = null
    }
  }

  // Populate edit form with record data
  function populateEditForm(record) {
    log("Populating edit form with record:", record)

    if (!editHealthRecordForm) {
      log("Error: Edit form fields container not found")
      return
    }

    // Clear existing fields
    editHealthRecordForm.innerHTML = ""

    // Add common fields
    const dateField = createFormField("date", "Date", record.date, "date")
    const timeField = createFormField("time", "Time", record.time, "time")

    editHealthRecordForm.appendChild(dateField)
    editHealthRecordForm.appendChild(timeField)

    // Add category-specific fields
    if (record.category === "vital-signs" || record.category === "biometrics") {
      const typeLabel = record.type.replace(/-/g, " ")
      const typeLabelCapitalized = typeLabel.charAt(0).toUpperCase() + typeLabel.slice(1)

      // Add type as hidden field
      const typeField = document.createElement("input")
      typeField.type = "hidden"
      typeField.name = "type"
      typeField.value = record.type
      editHealthRecordForm.appendChild(typeField)

      // Add category as hidden field
      const categoryField = document.createElement("input")
      categoryField.type = "hidden"
      categoryField.name = "category"
      categoryField.value = record.category
      editHealthRecordForm.appendChild(categoryField)

      if (record.type === "blood-pressure") {
        // Add blood pressure fields
        const bpContainer = document.createElement("div")
        bpContainer.className = "mb-4"

        const bpLabel = document.createElement("label")
        bpLabel.className = "block text-sm font-medium text-gray-700 mb-2"
        bpLabel.textContent = typeLabelCapitalized

        const bpInputsContainer = document.createElement("div")
        bpInputsContainer.className = "flex space-x-2"

        const systolicContainer = document.createElement("div")
        systolicContainer.className = "w-1/2"

        const systolicLabel = document.createElement("label")
        systolicLabel.className = "block text-xs font-medium text-gray-700"
        systolicLabel.textContent = "Systolic"

        const systolicInput = document.createElement("input")
        systolicInput.type = "number"
        systolicInput.name = "systolic"
        systolicInput.value = record.systolic
        systolicInput.className = "mt-1 block w-full border border-gray-300 rounded-md p-2"

        systolicContainer.appendChild(systolicLabel)
        systolicContainer.appendChild(systolicInput)

        const diastolicContainer = document.createElement("div")
        diastolicContainer.className = "w-1/2"

        const diastolicLabel = document.createElement("label")
        diastolicLabel.className = "block text-xs font-medium text-gray-700"
        diastolicLabel.textContent = "Diastolic"

        const diastolicInput = document.createElement("input")
        diastolicInput.type = "number"
        diastolicInput.name = "diastolic"
        diastolicInput.value = record.diastolic
        diastolicInput.className = "mt-1 block w-full border border-gray-300 rounded-md p-2"

        diastolicContainer.appendChild(diastolicLabel)
        diastolicContainer.appendChild(diastolicInput)

        bpInputsContainer.appendChild(systolicContainer)
        bpInputsContainer.appendChild(diastolicContainer)

        bpContainer.appendChild(bpLabel)
        bpContainer.appendChild(bpInputsContainer)

        editHealthRecordForm.appendChild(bpContainer)
      } else {
        // Add value field
        const valueField = createFormField("value", typeLabelCapitalized, record.value, "text")
        editHealthRecordForm.appendChild(valueField)
      }
    } else if (record.category === "medical-notes") {
      // Add category as hidden field
      const categoryField = document.createElement("input")
      categoryField.type = "hidden"
      categoryField.name = "category"
      categoryField.value = record.category
      editHealthRecordForm.appendChild(categoryField)

      // Add subject field
      const subjectField = createFormField("subject", "Subject", record.subject, "text")
      editHealthRecordForm.appendChild(subjectField)

      // Add body field
      const bodyContainer = document.createElement("div")
      bodyContainer.className = "mb-4"

      const bodyLabel = document.createElement("label")
      bodyLabel.className = "block text-sm font-medium text-gray-700 mb-2"
      bodyLabel.textContent = "Notes"

      const bodyTextarea = document.createElement("textarea")
      bodyTextarea.name = "body"
      bodyTextarea.value = record.body || ""
      bodyTextarea.rows = 3
      bodyTextarea.className = "mt-1 block w-full border border-gray-300 rounded-md p-2"

      bodyContainer.appendChild(bodyLabel)
      bodyContainer.appendChild(bodyTextarea)

      editHealthRecordForm.appendChild(bodyContainer)
    }
  }

  // Create form field
  function createFormField(name, label, value, type = "text") {
    const container = document.createElement("div")
    container.className = "mb-4"

    const labelElement = document.createElement("label")
    labelElement.className = "block text-sm font-medium text-gray-700 mb-2"
    labelElement.textContent = label

    const input = document.createElement("input")
    input.type = type
    input.name = name
    input.value = value
    input.className = "mt-1 block w-full border border-gray-300 rounded-md p-2"

    container.appendChild(labelElement)
    container.appendChild(input)

    return container
  }

  // Load health records from server
  function loadHealthRecords() {
    log("Loading health records from server")
    fetch("/api/health-records")
      .then((response) => {
        if (!response.ok) {
          if (response.status === 400) {
            // No active profile selected, this is expected
            return response.json().then((data) => {
              showNoActiveProfileError(data.error || "No active profile selected. Data will be erased when refreshed.")
              return []
            })
          }
          throw new Error(`Failed to load health records`)
        }
        return response.json()
      })
      .then((data) => {
        log("Received health records from server:", data)
        if (data.error) {
          // Show error message for no active profile
          showNoActiveProfileError(data.error)
          healthRecords = []
        } else {
          // Hide error message if it exists
          hideNoActiveProfileError()
          healthRecords = data.healthRecords || data
        }
        renderHealthRecords()
        renderHealthRecordsHistory()
      })
      .catch((error) => {
        log("Error loading health records:", error)
        healthRecords = []
        renderHealthRecords()
        renderHealthRecordsHistory()
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
    const mainContent = getElement("main-content")
    if (mainContent) {
      mainContent.insertBefore(errorDiv, mainContent.firstChild)
    }

    // Also add to history page
    const historyPage = getElement("history-page")
    if (historyPage) {
      const historyErrorDiv = errorDiv.cloneNode(true)
      historyPage.insertBefore(historyErrorDiv, historyPage.firstChild)
    }
  }

  // Hide error message for no active profile
  function hideNoActiveProfileError() {
    log("Hiding no active profile error")

    // Remove error message from main content
    const mainErrorDiv = getElement("no-active-profile-error")
    if (mainErrorDiv) {
      mainErrorDiv.remove()
    }

    // Remove error message from history page
    const historyPage = getElement("history-page")
    if (historyPage) {
      const historyErrorDiv = historyPage.querySelector("#no-active-profile-error")
      if (historyErrorDiv) {
        historyErrorDiv.remove()
      }
    }
  }

  // Render health records
  function renderHealthRecords() {
    log("Rendering health records")

    // Filter records by category
    const vitalSigns = healthRecords.filter((record) => record.category === "vital-signs")
    const biometrics = healthRecords.filter((record) => record.category === "biometrics")
    const medicalNotes = healthRecords.filter((record) => record.category === "medical-notes")

    // Render each category
    renderCategoryRecords("vital-signs", vitalSigns)
    renderCategoryRecords("biometrics", biometrics)
    renderCategoryRecords("medical-notes", medicalNotes)
  }

  // Render records for a specific category
  function renderCategoryRecords(category, records) {
    log(`Rendering ${category} records:`, records)

    const container = getElement(`${category}-container`)
    const emptyState = getElement(`${category}-empty-state`)

    if (!container) {
      log(`Error: ${category} container not found`)
      return
    }

    if (!emptyState) {
      log(`Error: ${category} empty state not found`)
      // Continue anyway
    }

    // Clear existing records
    if (container) {
      Array.from(container.children).forEach((child) => {
        if (emptyState && child !== emptyState) {
          child.remove()
        } else if (!emptyState) {
          child.remove()
        }
      })
    }

    // Show empty state if no records
    if (records.length === 0) {
      if (emptyState) emptyState.style.display = "block"
      return
    }

    // Hide empty state
    if (emptyState) emptyState.style.display = "none"

    // Group records by type
    const recordsByType = {}

    records.forEach((record) => {
      const key = record.type || "note"
      if (!recordsByType[key]) {
        recordsByType[key] = []
      }
      recordsByType[key].push(record)
    })

    // Render each type
    Object.entries(recordsByType).forEach(([type, typeRecords]) => {
      // Sort records by date (newest first)
      typeRecords.sort((a, b) => new Date(b.date) - new Date(a.date))

      // Get the most recent record
      const latestRecord = typeRecords[0]

      // Create record element
      const recordElement = createRecordElement(latestRecord, category)
      container.appendChild(recordElement)
    })
  }

  // Create record element
  function createRecordElement(record, category) {
    const div = document.createElement("div")
    div.className = "p-4 flex items-center justify-between health-record-card"
    div.dataset.id = record.id

    let content = ""
    const icon = getIcon(record)
    const lastTaken = formatLastTaken(record.date, record.time)

    if (category === "vital-signs") {
      const typeLabel = record.type.replace(/-/g, " ")
      const typeLabelCapitalized = typeLabel.charAt(0).toUpperCase() + typeLabel.slice(1)

      if (record.type === "blood-pressure") {
        content = `
                <div class="flex items-center flex-grow">
                    <div class="mr-3">${icon}</div>
                    <div>
                        <h3 class="font-medium">${typeLabelCapitalized}</h3>
                        <p class="text-gray-500 text-sm">${record.systolic}/${record.diastolic} mmHg</p>
                    </div>
                </div>
                <div class="text-right">
                    <p class="text-gray-400 text-xs">Last taken:</p>
                    <p class="text-gray-500 text-xs">${lastTaken}</p>
                </div>
            `
      } else if (record.type === "respiratory-rate") {
        content = `
                <div class="flex items-center flex-grow">
                    <div class="mr-3">${icon}</div>
                    <div>
                        <h3 class="font-medium">${typeLabelCapitalized}</h3>
                        <p class="text-gray-500 text-sm">${record.value} breathes per min</p>
                    </div>
                </div>
                <div class="text-right">
                    <p class="text-gray-400 text-xs">Last taken:</p>
                    <p class="text-gray-500 text-xs">${lastTaken}</p>
                </div>
            `
      } else if (record.type === "oxygen-saturation") {
        content = `
                <div class="flex items-center flex-grow">
                    <div class="mr-3">${icon}</div>
                    <div>
                        <h3 class="font-medium">${typeLabelCapitalized}</h3>
                        <p class="text-gray-500 text-sm">${record.value} SpO2 %</p>
                    </div>
                </div>
                <div class="text-right">
                    <p class="text-gray-400 text-xs">Last taken:</p>
                    <p class="text-gray-500 text-xs">${lastTaken}</p>
                </div>
            `
      } else if (record.type === "weight") {
        content = `
                <div class="flex items-center flex-grow">
                    <div class="mr-3">${icon}</div>
                    <div>
                        <h3 class="font-medium">${typeLabelCapitalized}</h3>
                        <p class="text-gray-500 text-sm">${record.value} kg</p>
                    </div>
                </div>
                <div class="text-right">
                    <p class="text-gray-400 text-xs">Last taken:</p>
                    <p class="text-gray-500 text-xs">${lastTaken}</p>
                </div>
            `
      } else if (record.type === "body-temperature") {
        content = `
                <div class="flex items-center flex-grow">
                    <div class="mr-3">${icon}</div>
                    <div>
                        <h3 class="font-medium">${typeLabelCapitalized}</h3>
                        <p class="text-gray-500 text-sm">${record.value} °C</p>
                    </div>
                </div>
                <div class="text-right">
                    <p class="text-gray-400 text-xs">Last taken:</p>
                    <p class="text-gray-500 text-xs">${lastTaken}</p>
                </div>
            `
      } else if (record.type === "heart-rate") {
        content = `
                <div class="flex items-center flex-grow">
                    <div class="mr-3">${icon}</div>
                    <div>
                        <h3 class="font-medium">${typeLabelCapitalized}</h3>
                        <p class="text-gray-500 text-sm">${record.value} bpm</p>
                    </div>
                </div>
                <div class="text-right">
                    <p class="text-gray-400 text-xs">Last taken:</p>
                    <p class="text-gray-500 text-xs">${lastTaken}</p>
                </div>
            `
      } else if (record.type === "other-vital-sign") {
        const typeName = record.customType ? record.customType : "Other vital sign"
        content = `
          <div class="flex items-center flex-grow">
              <div class="mr-3">${icon}</div>
              <div>
                  <h3 class="font-medium">${typeName}</h3>
                  <p class="text-gray-500 text-sm">${record.value}</p>
              </div>
          </div>
          <div class="text-right">
              <p class="text-gray-400 text-xs">Last taken:</p>
              <p class="text-gray-500 text-xs">${lastTaken}</p>
          </div>
      `
      } else {
        content = `
                <div class="flex items-center flex-grow">
                    <div class="mr-3">${icon}</div>
                    <div>
                        <h3 class="font-medium">${typeLabelCapitalized}</h3>
                        <p class="text-gray-500 text-sm">${record.value}</p>
                    </div>
                </div>
                <div class="text-right">
                    <p class="text-gray-400 text-xs">Last taken:</p>
                    <p class="text-gray-500 text-xs">${lastTaken}</p>
                </div>
            `
      }
    } else if (category === "biometrics") {
      const typeLabel = record.type.replace(/-/g, " ")
      const typeLabelCapitalized = typeLabel.charAt(0).toUpperCase() + typeLabel.slice(1)

      if (record.type === "blood-glucose") {
        content = `
                <div class="flex items-center flex-grow">
                    <div class="mr-3">${icon}</div>
                    <div>
                        <h3 class="font-medium">${typeLabelCapitalized}</h3>
                        <p class="text-gray-500 text-sm">${record.value} mg/dL</p>
                    </div>
                </div>
                <div class="text-right">
                    <p class="text-gray-400 text-xs">Last taken:</p>
                    <p class="text-gray-500 text-xs">${lastTaken}</p>
                </div>
            `
      } else if (record.type === "cholesterol") {
        content = `
                <div class="flex items-center flex-grow">
                    <div class="mr-3">${icon}</div>
                    <div>
                        <h3 class="font-medium">${typeLabelCapitalized}</h3>
                        <p class="text-gray-500 text-sm">${record.value} mg/dL</p>
                    </div>
                </div>
                <div class="text-right">
                    <p class="text-gray-400 text-xs">Last taken:</p>
                    <p class="text-gray-500 text-xs">${lastTaken}</p>
                </div>
            `
      } else if (record.type === "hemoglobin-a1c") {
        content = `
                <div class="flex items-center flex-grow">
                    <div class="mr-3">${icon}</div>
                    <div>
                        <h3 class="font-medium">${typeLabelCapitalized}</h3>
                        <p class="text-gray-500 text-sm">${record.value} %</p>
                    </div>
                </div>
                <div class="text-right">
                    <p class="text-gray-400 text-xs">Last taken:</p>
                    <p class="text-gray-500 text-xs">${lastTaken}</p>
                </div>
            `
      } else if (record.type === "creatinine") {
        content = `
                <div class="flex items-center flex-grow">
                    <div class="mr-3">${icon}</div>
                    <div>
                        <h3 class="font-medium">${typeLabelCapitalized}</h3>
                        <p class="text-gray-500 text-sm">${record.value} mg/dL</p>
                    </div>
                </div>
                <div class="text-right">
                    <p class="text-gray-400 text-xs">Last taken:</p>
                    <p class="text-gray-500 text-xs">${lastTaken}</p>
                </div>
            `
      } else if (record.type === "liver-enzymes") {
        content = `
                <div class="flex items-center flex-grow">
                    <div class="mr-3">${icon}</div>
                    <div>
                        <h3 class="font-medium">${typeLabelCapitalized}</h3>
                        <p class="text-gray-500 text-sm">${record.value} U/L</p>
                    </div>
                </div>
                <div class="text-right">
                    <p class="text-gray-400 text-xs">Last taken:</p>
                    <p class="text-gray-500 text-xs">${lastTaken}</p>
                </div>
            `
      } else if (record.type === "other-biometric") {
        const typeName = record.customType ? record.customType : "Other biometric"
        content = `
          <div class="flex items-center flex-grow">
              <div class="mr-3">${icon}</div>
              <div>
                  <h3 class="font-medium">${typeName}</h3>
                  <p class="text-gray-500 text-sm">${record.value}</p>
              </div>
          </div>
          <div class="text-right">
              <p class="text-gray-400 text-xs">Last taken:</p>
              <p class="text-gray-500 text-xs">${lastTaken}</p>
          </div>
      `
      } else {
        content = `
                <div class="flex items-center flex-grow">
                    <div class="mr-3">${icon}</div>
                    <div>
                        <h3 class="font-medium">${typeLabelCapitalized}</h3>
                        <p class="text-gray-500 text-sm">${record.value}</p>
                    </div>
                </div>
                <div class="text-right">
                    <p class="text-gray-400 text-xs">Last taken:</p>
                    <p class="text-gray-500 text-xs">${lastTaken}</p>
                </div>
            `
      }
    } else if (category === "medical-notes") {
      content = `
            <div class="flex items-center flex-grow">
                <div class="mr-3">
                    ${icon}
                </div>
                <div>
                    <h3 class="font-medium">${record.subject}</h3>
                    <p class="text-gray-500 text-sm">${record.body ? (record.body.length > 50 ? record.body.substring(0, 50) + "..." : record.body) : ""}</p>
                </div>
            </div>
            <div class="text-right">
                <p class="text-gray-400 text-xs">Last taken:</p>
                <p class="text-gray-500 text-xs">${lastTaken}</p>
            </div>
        `
    }

    div.innerHTML = content

    return div
  }

  // Render health records history
  function renderHealthRecordsHistory() {
    log("Rendering health records history")

    const container = getElement("health-records-history")
    const emptyState = getElement("history-empty-state")

    if (!container) {
      log("Error: Health records history container not found")
      return
    }

    // Clear existing records
    if (container) {
      Array.from(container.children).forEach((child) => {
        if (emptyState && child !== emptyState) {
          child.remove()
        } else if (!emptyState) {
          child.remove()
        }
      })
    }

    // Show empty state if no records
    if (healthRecords.length === 0) {
      if (emptyState) emptyState.style.display = "block"
      return
    }

    // Hide empty state
    if (emptyState) emptyState.style.display = "none"

    // Sort records by date (newest first)
    const sortedRecords = [...healthRecords].sort((a, b) => b.timestamp - a.timestamp)

    // Group records by date
    const recordsByDate = {}

    sortedRecords.forEach((record) => {
      if (!recordsByDate[record.date]) {
        recordsByDate[record.date] = []
      }
      recordsByDate[record.date].push(record)
    })

    // Render each date group
    Object.entries(recordsByDate).forEach(([date, dateRecords]) => {
      // Create date header
      const dateHeader = document.createElement("div")
      dateHeader.className = "p-4 bg-gray-50"

      const dateObj = new Date(date)
      const formattedDate = dateObj.toLocaleDateString("en-US", {
        weekday: "long",
        year: "numeric",
        month: "long",
        day: "numeric",
      })

      dateHeader.innerHTML = `<h3 class="font-medium">${formattedDate}</h3>`
      container.appendChild(dateHeader)

      // Sort records by time
      dateRecords.sort((a, b) => {
        const timeA = a.time.split(":")
        const timeB = b.time.split(":")
        const hourA = Number.parseInt(timeA[0])
        const hourB = Number.parseInt(timeB[0])
        if (hourA !== hourB) return hourB - hourA
        return Number.parseInt(timeA[1]) - Number.parseInt(timeB[1])
      })

      // Render each record
      dateRecords.forEach((record) => {
        const recordElement = createHistoryRecordElement(record)
        container.appendChild(recordElement)
      })
    })
  }

  // Create history record element
  function createHistoryRecordElement(record) {
    const div = document.createElement("div")
    div.className = "p-4 border-t"
    div.dataset.id = record.id

    let content = ""
    const icon = getIcon(record)
    const time = formatTimeWithAMPM(record.time)

    if (record.category === "vital-signs") {
      const typeLabel = record.type.replace(/-/g, " ")
      let typeLabelCapitalized = typeLabel.charAt(0).toUpperCase() + typeLabel.slice(1)
      const categoryLabel = "Vital Sign"
      let valueWithUnit = record.value

      if (record.type === "other-vital-sign") {
        const typeName = record.customType ? record.customType : "Other vital sign"
        valueWithUnit = record.value
        typeLabelCapitalized = typeName
      }

      if (record.type === "blood-pressure") {
        content = `
                <div class="flex justify-between items-start">
                    <div class="flex items-start">
                        <div class="mr-3 mt-1">
                            ${icon}
                        </div>
                        <div>
                            <span class="text-xs text-gray-400">${categoryLabel}</span>
                            <h3 class="font-medium">${typeLabelCapitalized}</h3>
                            <p class="text-gray-500 text-sm">${record.systolic}/${record.diastolic} mmHg</p>
                        </div>
                    </div>
                    <div class="text-right">
                        <p class="text-gray-400 text-xs">Taken at:</p>
                        <p class="text-gray-500 text-xs">${time}</p>
                    </div>
                </div>
            `
      } else {
        // Add units based on record type

        if (record.type === "respiratory-rate") {
          valueWithUnit = `${record.value} breathes per min`
        } else if (record.type === "oxygen-saturation") {
          valueWithUnit = `${record.value} SpO2 %`
        } else if (record.type === "weight") {
          valueWithUnit = `${record.value} kg`
        } else if (record.type === "body-temperature") {
          valueWithUnit = `${record.value} °C`
        } else if (record.type === "heart-rate") {
          valueWithUnit = `${record.value} bpm`
        }

        content = `
                <div class="flex justify-between items-start">
                    <div class="flex items-start">
                        <div class="mr-3 mt-1">
                            ${icon}
                        </div>
                        <div>
                            <span class="text-xs text-gray-400">${categoryLabel}</span>
                            <h3 class="font-medium">${typeLabelCapitalized}</h3>
                            <p class="text-gray-500 text-sm">${valueWithUnit}</p>
                        </div>
                    </div>
                    <div class="text-right">
                        <p class="text-gray-400 text-xs">Taken at:</p>
                        <p class="text-gray-500 text-xs">${time}</p>
                    </div>
                </div>
            `
      }
    } else if (record.category === "biometrics") {
      const typeLabel = record.type.replace(/-/g, " ")
      let typeLabelCapitalized = typeLabel.charAt(0).toUpperCase() + typeLabel.slice(1)
      const categoryLabel = "Biometric"

      // Add units based on record type
      let valueWithUnit = record.value

      if (record.type === "other-biometric") {
        const typeName = record.customType ? record.customType : "Other biometric"
        valueWithUnit = record.value
        typeLabelCapitalized = typeName
      }

      if (record.type === "blood-glucose") {
        valueWithUnit = `${record.value} mg/dL`
      } else if (record.type === "cholesterol") {
        valueWithUnit = `${record.value} mg/dL`
      } else if (record.type === "hemoglobin-a1c") {
        valueWithUnit = `${record.value} %`
      } else if (record.type === "creatinine") {
        valueWithUnit = `${record.value} mg/dL`
      } else if (record.type === "liver-enzymes") {
        valueWithUnit = `${record.value} U/L`
      }

      content = `
            <div class="flex justify-between items-start">
                <div class="flex items-start">
                    <div class="mr-3 mt-1">
                        ${icon}
                    </div>
                    <div>
                        <span class="text-xs text-gray-400">${categoryLabel}</span>
                        <h3 class="font-medium">${typeLabelCapitalized}</h3>
                        <p class="text-gray-500 text-sm">${valueWithUnit}</p>
                    </div>
                </div>
                <div class="text-right">
                    <p class="text-gray-400 text-xs">Taken at:</p>
                    <p class="text-gray-500 text-xs">${time}</p>
                </div>
            </div>
        `
    } else if (record.category === "medical-notes") {
      content = `
            <div class="flex justify-between items-start">
                <div class="flex items-start">
                    <div class="mr-3 mt-1">
                        ${icon}
                    </div>
                    <div>
                        <span class="text-xs text-gray-400">Medical Note</span>
                        <h3 class="font-medium">${record.subject}</h3>
                        <p class="text-gray-500 text-sm">${record.body || ""}</p>
                    </div>
                </div>
                <div class="text-right">
                    <p class="text-gray-400 text-xs">Taken at:</p>
                    <p class="text-gray-500 text-xs">${time}</p>
                </div>
            </div>
        `
    }

    div.innerHTML = content

    return div
  }

  // Add health record to server
  function addHealthRecord(record) {
    log("Adding health record to server:", record)
    fetch("/api/health-records", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify(record),
      credentials: "same-origin",
    })
      .then((response) => {
        if (!response.ok) {
          if (response.status === 403) {
            // Premium limit reached
            showPremiumModal()
            throw new Error("Premium limit reached")
          }
          if (response.status === 400) {
            // No active profile selected, show error but still add the record locally
            return response.json().then((data) => {
              showNoActiveProfileError(data.error || "No active profile selected. Data will be erased when refreshed.")

              // Create a temporary record with a generated ID
              const tempRecord = {
                ...record,
                id: Date.now(),
              }

              // Add to health records array
              healthRecords.push(tempRecord)

              // Re-render the health records
              renderHealthRecords()
              renderHealthRecordsHistory()

              return { id: tempRecord.id }
            })
          }
          return response.json().then((err) => {
            throw new Error(err.error || `HTTP error! Status: ${response.status}`)
          })
        }
        return response.json()
      })
      .then((data) => {
        log("Server response after adding health record:", data)
        // Reload health records from server
        loadHealthRecords()
      })
      .catch((error) => {
        log("Error adding health record:", error)
        // If not a premium error, show general error
        if (!error.message.includes("Premium")) {
          alert("There was an error adding the health record: " + error.message)
        }
      })
  }

  // Update health record on server
  function updateHealthRecord(recordId, updatedFields) {
    log("Updating health record on server:", recordId, updatedFields)
    fetch(`/api/health-records/${recordId}`, {
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
        log("Server response after updating health record:", data)
        // Reload health records from server
        loadHealthRecords()
      })
      .catch((error) => {
        log("Error updating health record:", error)
        alert("There was an error updating the health record: " + error.message)
      })
  }

  // Delete health record from server
  function deleteHealthRecord(recordId) {
    log("Deleting health record from server:", recordId)
    fetch(`/api/health-records/${recordId}`, {
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
        log("Server response after deleting health record:", data)
        // Reload health records from server
        loadHealthRecords()
      })
      .catch((error) => {
        log("Error deleting health record:", error)
        alert("There was an error deleting the health record: " + error.message)
      })
  }

  // Event Listeners

  // Toggle between main content and history page
  addEventListenerSafe(seeHistoryBtn, "click", () => {
    if (mainContent) mainContent.classList.add("hidden")
    if (historyPage) historyPage.classList.remove("hidden")
  })

  addEventListenerSafe(backToMainBtn, "click", () => {
    if (historyPage) historyPage.classList.add("hidden")
    if (mainContent) mainContent.classList.remove("hidden")
  })

  // Open edit modal
  addEventListenerSafe(editHealthRecordsBtn, "click", openEditModal)

  // Open add modal
  addEventListenerSafe(openAddHealthRecordBtn, "click", () => openAddModal())

  // Close add modal
  addEventListenerSafe(cancelAddHealthRecordBtn, "click", closeAddModal)

  // Close add modal when clicking outside
  addEventListenerSafe(addHealthRecordModal, "click", (e) => {
    if (e.target === addHealthRecordModal) {
      closeAddModal()
    }
  })

  // Handle category change
  addEventListenerSafe(recordCategory, "change", handleCategoryChange)

  // Handle vital sign type change
  addEventListenerSafe(vitalSignType, "change", handleVitalSignTypeChange)

  // Handle biometric type change
  addEventListenerSafe(biometricType, "change", handleBiometricTypeChange)

  // Handle health record selection
  addEventListenerSafe(healthRecordSelect, "change", handleHealthRecordSelection)

  // Close edit modal
  addEventListenerSafe(cancelEditHealthRecordBtn, "click", closeEditModal)

  // Close edit modal when clicking outside
  addEventListenerSafe(editHealthRecordsModal, "click", (e) => {
    if (e.target === editHealthRecordsModal) {
      closeEditModal()
    }
  })

  // Close edit modal with close button
  addEventListenerSafe(editModalCloseBtn, "click", closeEditModal)

  // Open delete confirmation modal
  addEventListenerSafe(deleteHealthRecordBtn, "click", (e) => {
    e.preventDefault()
    openDeleteModal()
  })

  // Close delete confirmation modal
  addEventListenerSafe(cancelDeleteBtn, "click", closeDeleteModal)

  // Close delete confirmation modal when clicking outside
  addEventListenerSafe(deleteConfirmationModal, "click", (e) => {
    if (e.target === deleteConfirmationModal) {
      closeDeleteModal()
    }
  })

  // Confirm delete
  addEventListenerSafe(confirmDeleteBtn, "click", () => {
    if (selectedRecordId) {
      // Delete from server
      deleteHealthRecord(selectedRecordId)

      // Close modals
      closeDeleteModal()
      closeEditModal()

      // Clear the selected record ID
      selectedRecordId = null
    }
  })

  // Close premium modal
  addEventListenerSafe(closePremiumModal, "click", closePremiumModalFn)

  // Handle premium upgrade
  addEventListenerSafe(upgradePremiumBtn, "click", () => {
    alert("This would redirect to the premium upgrade page.")
    closePremiumModalFn()
  })

  // Handle add health record form submission
  addEventListenerSafe(addHealthRecordForm, "submit", (e) => {
    e.preventDefault()

    // Reset previous error messages
    const errorMessages = document.querySelectorAll(".error-message")
    errorMessages.forEach((msg) => msg.remove())

    const formData = new FormData(addHealthRecordForm)
    const category = formData.get("category")
    let hasErrors = false

    // Create base record object
    const record = {
      category,
      date: formData.get("date"),
      time: formData.get("time"),
      timestamp: new Date(`${formData.get("date")}T${formData.get("time")}`).getTime(),
    }

    // Add category-specific fields
    if (category === "vital-signs") {
      record.type = formData.get("vitalSignType")

      if (record.type === "blood-pressure") {
        const systolic = formData.get("systolic")
        const diastolic = formData.get("diastolic")

        if (!systolic || !diastolic) {
          if (!systolic) {
            showError("systolic", "Please enter a systolic value")
          }
          if (!diastolic) {
            showError("diastolic", "Please enter a diastolic value")
          }
          hasErrors = true
        } else {
          record.systolic = Number.parseInt(systolic)
          record.diastolic = Number.parseInt(diastolic)
          record.value = `${record.systolic}/${record.diastolic}`
        }
      } else {
        const value = formData.get("value")
        if (!value) {
          showError("recordValue", "Value Required")
          hasErrors = true
        } else {
          record.value = value
        }

        // Handle custom type for "other"
        if (record.type === "other-vital-sign") {
          const customType = formData.get("otherType")
          if (!customType) {
            showError("otherType", "Please specify the type")
            hasErrors = true
          } else {
            record.customType = customType
          }
        }
      }
    } else if (category === "biometrics") {
      record.type = formData.get("biometricType")
      const value = formData.get("value")

      if (!value) {
        showError("recordValue", "Please add a value")
        hasErrors = true
      } else {
        record.value = value
      }

      // Handle custom type for "other"
      if (record.type === "other-biometric") {
        const customType = formData.get("otherType")
        if (!customType) {
          showError("otherType", "Please specify the type")
          hasErrors = true
        } else {
          record.customType = customType
        }
      }
    } else if (category === "medical-notes") {
      const subject = formData.get("subject")
      if (!subject) {
        showError("subject", "Please add a subject")
        hasErrors = true
      } else {
        record.subject = subject
        record.body = formData.get("body")
      }
    }

    // If there are errors, don't submit
    if (hasErrors) {
      return
    }

    // Add record to server
    addHealthRecord(record)

    // Close modal and reset form
    closeAddModal()
  })

  // Show error message for a field
  function showError(fieldId, message) {
    const field = getElement(fieldId)
    if (!field) return

    // Remove any existing error for this field
    const existingError = field.parentNode.querySelector(".error-message")
    if (existingError) existingError.remove()

    // Create error message element
    const errorDiv = document.createElement("div")
    errorDiv.className = "error-message text-red-500 text-sm mt-1"
    errorDiv.textContent = message

    // Insert after the field
    field.parentNode.insertBefore(errorDiv, field.nextSibling)
  }

  // Handle edit health record form submission
  addEventListenerSafe(editHealthRecordForm, "submit", (e) => {
    e.preventDefault()

    if (selectedRecordId) {
      const formData = new FormData(editHealthRecordForm)
      const category = formData.get("category")

      // Create base updated fields object
      const updatedFields = {
        date: formData.get("date"),
        time: formData.get("time"),
        timestamp: new Date(`${formData.get("date")}T${formData.get("time")}`).getTime(),
      }

      // Add category-specific fields
      if (category === "vital-signs" || category === "biometrics") {
        if (formData.get("type") === "blood-pressure") {
          updatedFields.systolic = Number.parseInt(formData.get("systolic"))
          updatedFields.diastolic = Number.parseInt(formData.get("diastolic"))
        } else {
          updatedFields.value = formData.get("value")
        }
      } else if (category === "medical-notes") {
        updatedFields.subject = formData.get("subject")
        updatedFields.body = formData.get("body")
      }

      // Update record on server
      updateHealthRecord(selectedRecordId, updatedFields)

      // Close modal
      closeEditModal()
    }
  })

  // Initialize
  loadHealthRecords()
})
