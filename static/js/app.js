// Import necessary variables and functions
const showLoading = (btn) => {
  btn.disabled = true
  btn.textContent = "Loading..."
  return () => {
    btn.disabled = false
    btn.textContent = "Browse"
  }
}

const showNotification = (message, type) => {
  const notification = document.createElement("div")
  notification.className = `fixed bottom-0 right-0 mb-4 mr-4 bg-${type}-100 border border-${type}-400 text-${type}-700 px-4 py-3 rounded relative`
  notification.innerHTML = `<strong class="font-bold">${type.charAt(0).toUpperCase() + type.slice(1)}</strong> <span class="block sm:inline">${message}</span>`
  document.body.appendChild(notification)

  setTimeout(() => {
    document.body.removeChild(notification)
  }, 3000)
}

const Plotly = window.Plotly

class AutoVizApp {
  constructor() {
    this.currentData = null
    this.currentHeaders = null
    this.currentChart = null

    this.initializeEventListeners()
  }

  initializeEventListeners() {
    // File upload
    const fileInput = document.getElementById("file-input")
    const uploadArea = document.getElementById("upload-area")
    const browseBtn = document.getElementById("browse-btn")

    browseBtn.addEventListener("click", () => fileInput.click())
    fileInput.addEventListener("change", (e) => this.handleFileUpload(e.target.files[0]))

    // Drag and drop
    uploadArea.addEventListener("dragover", (e) => {
      e.preventDefault()
      uploadArea.classList.add("border-blue-500", "bg-blue-50")
    })

    uploadArea.addEventListener("dragleave", () => {
      uploadArea.classList.remove("border-blue-500", "bg-blue-50")
    })

    uploadArea.addEventListener("drop", (e) => {
      e.preventDefault()
      uploadArea.classList.remove("border-blue-500", "bg-blue-50")
      this.handleFileUpload(e.dataTransfer.files[0])
    })

    // Remove file
    document.getElementById("remove-file").addEventListener("click", () => {
      this.resetApp()
    })

    // Chart generation
    document.getElementById("generate-chart").addEventListener("click", () => {
      this.generateChart()
    })

    // Export buttons
    document.getElementById("export-png").addEventListener("click", () => {
      this.exportChart("png")
    })

    document.getElementById("export-csv").addEventListener("click", () => {
      this.exportData("csv")
    })

    document.getElementById("export-json").addEventListener("click", () => {
      this.exportData("json")
    })
  }

  async handleFileUpload(file) {
    if (!file) return

    const formData = new FormData()
    formData.append("file", file)

    const uploadBtn = document.getElementById("browse-btn")
    const hideLoading = showLoading(uploadBtn)

    try {
      const response = await fetch("/upload", {
        method: "POST",
        body: formData,
      })

      const result = await response.json()

      if (result.success) {
        this.currentData = result.data
        this.currentHeaders = result.headers

        this.showFileInfo(file, result.total_rows)
        this.populateColumnSelectors(result.headers, result.column_info)
        this.showDataStats(result)
        this.showDataPreview(result.data, result.headers)

        showNotification("File uploaded successfully!", "success")
      } else {
        showNotification(result.error, "error")
      }
    } catch (error) {
      showNotification("Upload failed: " + error.message, "error")
    } finally {
      hideLoading()
    }
  }

  showFileInfo(file, totalRows) {
    document.getElementById("file-name").textContent = file.name
    document.getElementById("file-size").textContent = `${(file.size / 1024).toFixed(1)} KB • ${totalRows} rows`
    document.getElementById("file-info").classList.remove("hidden")
    document.getElementById("chart-config").classList.remove("hidden")
    document.getElementById("export-options").classList.remove("hidden")
  }

  populateColumnSelectors(headers, columnInfo) {
    const xAxisSelect = document.getElementById("x-axis")
    const yAxisSelect = document.getElementById("y-axis")

    // Clear existing options
    xAxisSelect.innerHTML = '<option value="">Select column...</option>'
    yAxisSelect.innerHTML = '<option value="">Select column...</option>'

    // Populate options
    headers.forEach((header) => {
      const xOption = new Option(header, header)
      const yOption = new Option(header, header)

      xAxisSelect.appendChild(xOption)
      yAxisSelect.appendChild(yOption)
    })

    // Auto-select first two columns
    if (headers.length >= 2) {
      xAxisSelect.value = headers[0]
      yAxisSelect.value = headers[1]
    }
  }

  showDataStats(result) {
    document.getElementById("total-rows").textContent = result.total_rows
    document.getElementById("total-columns").textContent = result.headers.length

    const numericCols = Object.values(result.column_info).filter((col) => col.type === "numeric").length
    const categoricalCols = Object.values(result.column_info).filter((col) => col.type === "categorical").length

    document.getElementById("numeric-columns").textContent = numericCols
    document.getElementById("categorical-columns").textContent = categoricalCols
    document.getElementById("data-stats").classList.remove("hidden")
  }

  showDataPreview(data, headers) {
    const tableHeader = document.getElementById("table-header")
    const tableBody = document.getElementById("table-body")

    // Create header
    tableHeader.innerHTML =
      "<tr>" +
      headers.map((h) => `<th class="px-4 py-2 text-left font-medium text-gray-700 border-b">${h}</th>`).join("") +
      "</tr>"

    // Create rows (first 10)
    tableBody.innerHTML = data
      .slice(0, 10)
      .map(
        (row) =>
          '<tr class="hover:bg-gray-50">' +
          headers.map((h) => `<td class="px-4 py-2 border-b text-gray-600">${row[h] || ""}</td>`).join("") +
          "</tr>",
      )
      .join("")

    document.getElementById("data-preview").classList.remove("hidden")
    document.getElementById("welcome-screen").classList.add("hidden")
  }

  async generateChart() {
    const config = {
      chart_type: document.getElementById("chart-type").value,
      x_axis: document.getElementById("x-axis").value,
      y_axis: document.getElementById("y-axis").value,
      color_scheme: document.getElementById("color-scheme").value,
      title: document.getElementById("chart-title").value,
    }

    if (!config.x_axis) {
      showNotification("Please select X-axis column", "error")
      return
    }

    const generateBtn = document.getElementById("generate-chart")
    const hideLoading = showLoading(generateBtn)

    try {
      const response = await fetch("/generate_chart", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify(config),
      })

      const result = await response.json()

      if (result.success) {
        this.currentChart = JSON.parse(result.chart)

        Plotly.newPlot("plotly-chart", this.currentChart.data, this.currentChart.layout, {
          responsive: true,
          displayModeBar: true,
          modeBarButtonsToRemove: ["pan2d", "lasso2d", "select2d"],
          displaylogo: false,
        })

        document.getElementById("chart-container").classList.remove("hidden")
        document.getElementById("welcome-screen").classList.add("hidden")

        showNotification("Chart generated successfully!", "success")
      } else {
        showNotification(result.error, "error")
      }
    } catch (error) {
      showNotification("Chart generation failed: " + error.message, "error")
    } finally {
      hideLoading()
    }
  }

  exportChart(format) {
    if (!this.currentChart) {
      showNotification("No chart to export", "error")
      return
    }

    if (format === "png") {
      Plotly.downloadImage("plotly-chart", {
        format: "png",
        width: 1200,
        height: 800,
        filename: document.getElementById("chart-title").value || "chart",
      })
      showNotification("Chart exported as PNG", "success")
    }
  }

  async exportData(format) {
    if (!this.currentData) {
      showNotification("No data to export", "error")
      return
    }

    try {
      const response = await fetch(`/export_data/${format}`)

      if (response.ok) {
        const blob = await response.blob()
        const url = window.URL.createObjectURL(blob)
        const a = document.createElement("a")
        a.href = url
        a.download = `autoviz_data.${format}`
        document.body.appendChild(a)
        a.click()
        document.body.removeChild(a)
        window.URL.revokeObjectURL(url)

        showNotification(`Data exported as ${format.toUpperCase()}`, "success")
      } else {
        showNotification("Export failed", "error")
      }
    } catch (error) {
      showNotification("Export failed: " + error.message, "error")
    }
  }

  resetApp() {
    this.currentData = null
    this.currentHeaders = null
    this.currentChart = null

    document.getElementById("file-info").classList.add("hidden")
    document.getElementById("chart-config").classList.add("hidden")
    document.getElementById("export-options").classList.add("hidden")
    document.getElementById("data-stats").classList.add("hidden")
    document.getElementById("data-preview").classList.add("hidden")
    document.getElementById("chart-container").classList.add("hidden")
    document.getElementById("welcome-screen").classList.remove("hidden")

    document.getElementById("file-input").value = ""
  }
}

// Initialize app when DOM is loaded
document.addEventListener("DOMContentLoaded", () => {
  new AutoVizApp()
})
