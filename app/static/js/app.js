document.addEventListener("DOMContentLoaded", function() {
    let currentPage = 1;
    const perPage = 15;

    const filterForm = document.getElementById("filterForm");
    const recordsTableBody = document.getElementById("recordsTableBody");
    const paginationControls = document.getElementById("paginationControls");
    const filterCustomField = document.getElementById("filterCustomField");
    const filterCustomValue = document.getElementById("filterCustomValue");
    
    const uploadForm = document.getElementById("uploadForm");
    const uploadStatus = document.getElementById("uploadStatus");
    const uploadSubmitBtn = document.getElementById("uploadSubmitBtn");

    // 1. Enable/disable custom value field based on dropdown selection
    if (filterCustomField) {
        filterCustomField.addEventListener("change", function() {
            if (this.value) {
                filterCustomValue.disabled = false;
                filterCustomValue.placeholder = `Search within selected field...`;
                filterCustomValue.required = true;
            } else {
                filterCustomValue.disabled = true;
                filterCustomValue.placeholder = "Select an attribute first...";
                filterCustomValue.value = "";
                filterCustomValue.required = false;
            }
        });
    }

    // 2. Fetch and render records
    function fetchRecords(page = 1) {
        currentPage = page;
        recordsTableBody.innerHTML = `
            <tr>
                <td colspan="8" class="text-center py-5">
                    <div class="spinner-border text-primary" role="status">
                        <span class="visually-hidden">Loading...</span>
                    </div>
                    <p class="text-muted mt-2 mb-0">Querying database records...</p>
                </td>
            </tr>
        `;

        // Gather filters
        const name = document.getElementById("filterName").value.trim();
        const email = document.getElementById("filterEmail").value.trim();
        const phone = document.getElementById("filterPhone").value.trim();
        const company = document.getElementById("filterCompany").value.trim();
        const city = document.getElementById("filterCity").value.trim();
        const customFieldId = filterCustomField.value;
        const customFieldValue = filterCustomValue.value.trim();

        // Construct query string
        const params = new URLSearchParams({
            page: page,
            per_page: perPage,
            name: name,
            email: email,
            phone: phone,
            company: company,
            city: city,
            custom_field_id: customFieldId,
            custom_field_value: customFieldValue
        });

        fetch(`/api/records?${params.toString()}`)
            .then(res => {
                if (!res.ok) throw new Error("Network response was not ok");
                return res.json();
            })
            .then(data => {
                renderTable(data.records);
                renderPagination(data.total, data.page, data.pages);
            })
            .catch(err => {
                console.error(err);
                recordsTableBody.innerHTML = `
                    <tr>
                        <td colspan="8" class="text-center py-5 text-danger">
                            <i class="fa-solid fa-circle-exclamation fs-3 mb-2 d-block"></i>
                            An error occurred while fetching database records. Please try again.
                        </td>
                    </tr>
                `;
            });
    }

    function renderTable(records) {
        if (!records || records.length === 0) {
            recordsTableBody.innerHTML = `
                <tr>
                    <td colspan="8" class="text-center py-5 text-muted">
                        <i class="fa-solid fa-folder-open fs-2 mb-3 d-block text-secondary"></i>
                        No matching records found. Try adjusting your query parameters.
                    </td>
                </tr>
            `;
            return;
        }

        let html = "";
        records.forEach(r => {
            const hasCustom = r.custom_fields && Object.keys(r.custom_fields).length > 0;
            const location = [r.city, r.state, r.country].filter(Boolean).join(", ") || "--";
            
            html += `
                <tr>
                    <td><span class="badge bg-secondary font-outfit">#${r.id}</span></td>
                    <td><strong class="text-dark">${r.name || "--"}</strong></td>
                    <td><span class="text-muted">${r.email || "--"}</span></td>
                    <td><span class="text-muted">${r.phone || "--"}</span></td>
                    <td><span class="text-muted">${r.company || "--"}</span></td>
                    <td><span class="text-muted small">${location}</span></td>
                    <td class="text-center">
                        ${hasCustom ? 
                            `<span class="badge bg-primary-subtle text-primary px-3 py-1 font-outfit">${Object.keys(r.custom_fields).length} attributes</span>` : 
                            `<span class="text-muted small">none</span>`
                        }
                    </td>
                    <td class="text-center">
                        <button class="btn btn-sm btn-outline-primary btn-view-details" data-id="${r.id}">
                            <i class="fa-solid fa-magnifying-glass-plus"></i> View Details
                        </button>
                    </td>
                </tr>
            `;
        });
        recordsTableBody.innerHTML = html;

        // Attach listeners to View Details buttons
        document.querySelectorAll(".btn-view-details").forEach(btn => {
            btn.addEventListener("click", function() {
                const recordId = this.getAttribute("data-id");
                showRecordDetails(recordId);
            });
        });
    }

    function renderPagination(total, page, pages) {
        if (total === 0) {
            paginationControls.innerHTML = "";
            return;
        }

        const startIdx = (page - 1) * perPage + 1;
        const endIdx = Math.min(page * perPage, total);
        
        let html = `
            <div class="text-muted small mb-2 mb-md-0">
                Showing <strong class="text-dark">${startIdx}</strong> to <strong class="text-dark">${endIdx}</strong> of <strong class="text-dark">${total}</strong> records
            </div>
            <nav>
                <ul class="pagination pagination-sm mb-0">
                    <li class="page-item ${page === 1 ? 'disabled' : ''}">
                        <button class="page-link bg-white border-light-subtle text-dark page-btn" data-page="${page - 1}">
                            <i class="fa-solid fa-angle-left"></i>
                        </button>
                    </li>
        `;

        // Render page buttons (sliding window of max 5 pages)
        let startPage = Math.max(1, page - 2);
        let endPage = Math.min(pages, page + 2);

        if (startPage > 1) {
            html += `<li class="page-item"><button class="page-link bg-white border-light-subtle text-dark page-btn" data-page="1">1</button></li>`;
            if (startPage > 2) {
                html += `<li class="page-item disabled"><span class="page-link bg-white border-light-subtle text-muted">...</span></li>`;
            }
        }

        for (let i = startPage; i <= endPage; i++) {
            html += `
                <li class="page-item ${i === page ? 'active' : ''}">
                    <button class="page-link ${i === page ? 'bg-primary border-primary text-white' : 'bg-white border-light-subtle text-dark'} page-btn" data-page="${i}">
                        ${i}
                    </button>
                </li>
            `;
        }

        if (endPage < pages) {
            if (endPage < pages - 1) {
                html += `<li class="page-item disabled"><span class="page-link bg-white border-light-subtle text-muted">...</span></li>`;
            }
            html += `<li class="page-item"><button class="page-link bg-white border-light-subtle text-dark page-btn" data-page="${pages}">${pages}</button></li>`;
        }

        html += `
                    <li class="page-item ${page === pages ? 'disabled' : ''}">
                        <button class="page-link bg-white border-light-subtle text-dark page-btn" data-page="${page + 1}">
                            <i class="fa-solid fa-angle-right"></i>
                        </button>
                    </li>
                </ul>
            </nav>
        `;

        paginationControls.innerHTML = html;

        // Attach listeners to page buttons
        document.querySelectorAll(".page-btn").forEach(btn => {
            btn.addEventListener("click", function() {
                const targetPage = parseInt(this.getAttribute("data-page"));
                fetchRecords(targetPage);
            });
        });
    }

    // 3. Search Form Submission
    if (filterForm) {
        filterForm.addEventListener("submit", function(e) {
            e.preventDefault();
            fetchRecords(1);
        });
    }

    // 4. View Custom Details Modal Resolver
    const detailsModalEl = document.getElementById('detailsModal');
    const detailsModal = detailsModalEl ? new bootstrap.Modal(detailsModalEl) : null;
    const detailsModalBody = document.getElementById("detailsModalBody");
    const detailsModalTitle = document.getElementById("detailsModalTitle");

    const uploadModalEl = document.getElementById('uploadModal');
    const uploadModal = uploadModalEl ? new bootstrap.Modal(uploadModalEl) : null;

    function showRecordDetails(id) {
        if (!detailsModal || !detailsModalTitle || !detailsModalBody) return;
        detailsModalTitle.innerText = `Record Details (ID: #${id})`;
        detailsModalBody.innerHTML = `
            <div class="text-center py-4">
                <div class="spinner-border text-primary" role="status">
                    <span class="visually-hidden">Loading details...</span>
                </div>
            </div>
        `;
        detailsModal.show();

        fetch(`/api/records/${id}/custom`)
            .then(res => {
                if (!res.ok) throw new Error("Could not resolve details");
                return res.json();
            })
            .then(data => {
                if (!data || Object.keys(data).length === 0) {
                    detailsModalBody.innerHTML = `
                        <div class="alert alert-secondary mb-0">
                            <i class="fa-solid fa-info-circle me-2"></i> No custom JSON attributes registered for this record.
                        </div>
                    `;
                    return;
                }

                let html = `<ul class="list-group list-group-flush bg-transparent">`;
                for (const [key, val] of Object.entries(data)) {
                    html += `
                        <li class="list-group-item bg-transparent text-dark border-light-subtle px-0 py-3 d-flex justify-content-between align-items-center">
                            <div class="fw-semibold text-muted">${key}</div>
                            <div class="font-outfit text-primary text-end ms-2">${val}</div>
                        </li>
                    `;
                }
                html += `</ul>`;
                detailsModalBody.innerHTML = html;
            })
            .catch(err => {
                console.error(err);
                detailsModalBody.innerHTML = `
                    <div class="alert alert-danger mb-0">
                        <i class="fa-solid fa-circle-exclamation me-2"></i> Failed to resolve custom JSON details.
                    </div>
                `;
            });
    }

    // 5. File Upload Handler
    if (uploadForm) {
        uploadForm.addEventListener("submit", function(e) {
            e.preventDefault();
            const fileInput = document.getElementById("excelFile");
            if (!fileInput.files || fileInput.files.length === 0) return;

            uploadSubmitBtn.disabled = true;
            uploadSubmitBtn.innerHTML = `<span class="spinner-border spinner-border-sm me-2"></span>Ingesting...`;
            
            uploadStatus.classList.remove("d-none", "alert-success", "alert-danger");
            uploadStatus.classList.add("alert-warning");
            uploadStatus.innerHTML = `<i class="fa-solid fa-spinner fa-spin me-2"></i>Uploading file and booting parsing engine...`;

            const formData = new FormData();
            formData.append("file", fileInput.files[0]);

            fetch("/api/upload", {
                method: "POST",
                body: formData
            })
            .then(res => {
                if (!res.ok) {
                    return res.json().then(data => { throw new Error(data.error || "Upload failed"); });
                }
                return res.json();
            })
            .then(data => {
                uploadStatus.classList.remove("alert-warning");
                uploadStatus.classList.add("alert-success");
                uploadStatus.innerHTML = `<i class="fa-solid fa-circle-check me-2"></i>${data.message}`;
                
                // Reset form
                uploadForm.reset();
                
                // Hide the upload modal
                if (uploadModal) {
                    uploadModal.hide();
                }
                
                // Redirect user to history page to view background progress
                setTimeout(() => {
                    window.location.href = "/history";
                }, 1500);
            })
            .catch(err => {
                console.error(err);
                uploadStatus.classList.remove("alert-warning");
                uploadStatus.classList.add("alert-danger");
                uploadStatus.innerHTML = `<i class="fa-solid fa-circle-xmark me-2"></i>${err.message}`;
                uploadSubmitBtn.disabled = false;
                uploadSubmitBtn.innerText = "Start Ingestion";
            });
        });
    }

    // Load initial records list (only if we are on the dashboard records table page)
    if (recordsTableBody) {
        fetchRecords(1);
    }
});
