/**
 * Food Waste Prediction System - Main JavaScript
 * Enhanced Interactivity and User Experience
 */

// Wait for DOM to be fully loaded
document.addEventListener('DOMContentLoaded', function() {
    
    // ==========================================
    // SMOOTH SCROLLING
    // ==========================================
    document.querySelectorAll('a[href^="#"]').forEach(anchor => {
        anchor.addEventListener('click', function (e) {
            e.preventDefault();
            const target = document.querySelector(this.getAttribute('href'));
            if (target) {
                target.scrollIntoView({
                    behavior: 'smooth',
                    block: 'start'
                });
            }
        });
    });

    // ==========================================
    // AUTO-DISMISS ALERTS
    // ==========================================
    const alerts = document.querySelectorAll('.alert');
    alerts.forEach(alert => {
        setTimeout(() => {
            const bsAlert = new bootstrap.Alert(alert);
            bsAlert.close();
        }, 5000); // Auto-dismiss after 5 seconds
    });

    // ==========================================
    // FORM VALIDATION ENHANCEMENT
    // ==========================================
    const forms = document.querySelectorAll('form');
    forms.forEach(form => {
        form.addEventListener('submit', function(e) {
            if (!form.checkValidity()) {
                e.preventDefault();
                e.stopPropagation();
            }
            form.classList.add('was-validated');
        });
    });

    // ==========================================
    // TOOLTIPS INITIALIZATION
    // ==========================================
    const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });

    // ==========================================
    // POPOVERS INITIALIZATION
    // ==========================================
    const popoverTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="popover"]'));
    popoverTriggerList.map(function (popoverTriggerEl) {
        return new bootstrap.Popover(popoverTriggerEl);
    });

    // ==========================================
    // CONFIRM DELETE DIALOGS
    // ==========================================
    const deleteButtons = document.querySelectorAll('[data-confirm-delete]');
    deleteButtons.forEach(button => {
        button.addEventListener('click', function(e) {
            const message = this.getAttribute('data-confirm-delete') || 'Are you sure you want to delete this item?';
            if (!confirm(message)) {
                e.preventDefault();
            }
        });
    });

    // ==========================================
    // NUMBER INPUT VALIDATION
    // ==========================================
    const numberInputs = document.querySelectorAll('input[type="number"]');
    numberInputs.forEach(input => {
        input.addEventListener('input', function() {
            if (this.value < 0) {
                this.value = 0;
            }
        });
    });

    // ==========================================
    // DATE INPUT CONSTRAINTS
    // ==========================================
    const dateInputs = document.querySelectorAll('input[type="date"]');
    const today = new Date().toISOString().split('T')[0];
    
    dateInputs.forEach(input => {
        // Set min date for expiry dates
        if (input.name === 'expiry_date') {
            input.min = today;
        }
        // Set max date for past dates
        if (input.name === 'consumption_date' || input.name === 'waste_date') {
            input.max = today;
        }
    });

    // ==========================================
    // SEARCH FUNCTIONALITY
    // ==========================================
    const searchInputs = document.querySelectorAll('[data-search-table]');
    searchInputs.forEach(searchInput => {
        const tableId = searchInput.getAttribute('data-search-table');
        const table = document.getElementById(tableId);
        
        if (table) {
            searchInput.addEventListener('keyup', function() {
                const searchTerm = this.value.toLowerCase();
                const rows = table.querySelectorAll('tbody tr');
                
                rows.forEach(row => {
                    const text = row.textContent.toLowerCase();
                    row.style.display = text.includes(searchTerm) ? '' : 'none';
                });
            });
        }
    });

    // ==========================================
    // LOADING SPINNER
    // ==========================================
    function showLoadingSpinner() {
        const spinner = document.createElement('div');
        spinner.className = 'spinner-overlay';
        spinner.innerHTML = `
            <div class="spinner-border text-success" role="status">
                <span class="visually-hidden">Loading...</span>
            </div>
        `;
        document.body.appendChild(spinner);
        setTimeout(() => spinner.classList.add('show'), 10);
    }

    function hideLoadingSpinner() {
        const spinner = document.querySelector('.spinner-overlay');
        if (spinner) {
            spinner.classList.remove('show');
            setTimeout(() => spinner.remove(), 300);
        }
    }

    // Show spinner on form submissions
    forms.forEach(form => {
        form.addEventListener('submit', function() {
            if (form.checkValidity()) {
                showLoadingSpinner();
            }
        });
    });

    // ==========================================
    // CARD ANIMATIONS ON SCROLL
    // ==========================================
    const observerOptions = {
        threshold: 0.1,
        rootMargin: '0px 0px -100px 0px'
    };

    const observer = new IntersectionObserver(function(entries) {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                entry.target.classList.add('fade-in');
                observer.unobserve(entry.target);
            }
        });
    }, observerOptions);

    document.querySelectorAll('.card').forEach(card => {
        observer.observe(card);
    });

    // ==========================================
    // QUANTITY CALCULATOR
    // ==========================================
    const quantityInputs = document.querySelectorAll('[data-calculate-remaining]');
    quantityInputs.forEach(input => {
        input.addEventListener('input', function() {
            const maxQty = parseFloat(this.getAttribute('data-max-quantity')) || 0;
            const consumed = parseFloat(this.value) || 0;
            const remaining = maxQty - consumed;
            
            const remainingDisplay = document.getElementById(this.getAttribute('data-remaining-display'));
            if (remainingDisplay) {
                remainingDisplay.textContent = remaining.toFixed(2);
                
                if (remaining < 0) {
                    remainingDisplay.classList.add('text-danger');
                    this.setCustomValidity('Quantity exceeds available amount');
                } else {
                    remainingDisplay.classList.remove('text-danger');
                    this.setCustomValidity('');
                }
            }
        });
    });

    // ==========================================
    // REAL-TIME RISK INDICATOR
    // ==========================================
    function updateRiskIndicators() {
        document.querySelectorAll('[data-risk-score]').forEach(element => {
            const score = parseFloat(element.getAttribute('data-risk-score'));
            let colorClass = 'success';
            let icon = 'check-circle';
            
            if (score >= 70) {
                colorClass = 'danger';
                icon = 'exclamation-triangle';
            } else if (score >= 40) {
                colorClass = 'warning';
                icon = 'exclamation-circle';
            }
            
            element.className = `badge bg-${colorClass}`;
            element.innerHTML = `<i class="fas fa-${icon}"></i> ${Math.round(score)}%`;
        });
    }

    updateRiskIndicators();

    // ==========================================
    // COUNTDOWN TIMER FOR EXPIRY
    // ==========================================
    function updateExpiryCountdowns() {
        document.querySelectorAll('[data-expiry-date]').forEach(element => {
            const expiryDate = new Date(element.getAttribute('data-expiry-date'));
            const now = new Date();
            const diffTime = expiryDate - now;
            const diffDays = Math.ceil(diffTime / (1000 * 60 * 60 * 24));
            
            let html = '';
            let colorClass = 'success';
            
            if (diffDays < 0) {
                html = `<span class="text-danger"><strong>EXPIRED</strong> (${Math.abs(diffDays)} days ago)</span>`;
            } else if (diffDays === 0) {
                html = '<span class="text-danger"><strong>EXPIRES TODAY!</strong></span>';
            } else if (diffDays <= 3) {
                html = `<span class="text-danger"><strong>${diffDays} day${diffDays !== 1 ? 's' : ''} left</strong></span>`;
            } else if (diffDays <= 7) {
                html = `<span class="text-warning">${diffDays} days left</span>`;
            } else {
                html = `<span class="text-success">${diffDays} days left</span>`;
            }
            
            element.innerHTML = html;
        });
    }

    updateExpiryCountdowns();
    setInterval(updateExpiryCountdowns, 60000); // Update every minute

    // ==========================================
    // CHART RESPONSIVENESS
    // ==========================================
    window.addEventListener('resize', function() {
        if (typeof Chart !== 'undefined') {
            Chart.helpers.each(Chart.instances, function(instance) {
                instance.resize();
            });
        }
    });

    // ==========================================
    // COPY TO CLIPBOARD
    // ==========================================
    document.querySelectorAll('[data-copy-text]').forEach(button => {
        button.addEventListener('click', function() {
            const text = this.getAttribute('data-copy-text');
            navigator.clipboard.writeText(text).then(() => {
                const originalText = this.innerHTML;
                this.innerHTML = '<i class="fas fa-check"></i> Copied!';
                setTimeout(() => {
                    this.innerHTML = originalText;
                }, 2000);
            });
        });
    });

    // ==========================================
    // KEYBOARD SHORTCUTS
    // ==========================================
    document.addEventListener('keydown', function(e) {
        // Ctrl/Cmd + K for search
        if ((e.ctrlKey || e.metaKey) && e.key === 'k') {
            e.preventDefault();
            const searchInput = document.querySelector('input[type="search"], input[name="search"]');
            if (searchInput) {
                searchInput.focus();
            }
        }
        
        // Escape to close modals
        if (e.key === 'Escape') {
            const modals = document.querySelectorAll('.modal.show');
            modals.forEach(modal => {
                const bsModal = bootstrap.Modal.getInstance(modal);
                if (bsModal) {
                    bsModal.hide();
                }
            });
        }
    });

    // ==========================================
    // DYNAMIC STATISTICS UPDATE
    // ==========================================
    function animateValue(element, start, end, duration) {
        let startTimestamp = null;
        const step = (timestamp) => {
            if (!startTimestamp) startTimestamp = timestamp;
            const progress = Math.min((timestamp - startTimestamp) / duration, 1);
            element.textContent = Math.floor(progress * (end - start) + start);
            if (progress < 1) {
                window.requestAnimationFrame(step);
            }
        };
        window.requestAnimationFrame(step);
    }

    // Animate statistics on page load
    document.querySelectorAll('[data-animate-value]').forEach(element => {
        const endValue = parseInt(element.textContent);
        element.textContent = '0';
        setTimeout(() => {
            animateValue(element, 0, endValue, 1000);
        }, 200);
    });

    // ==========================================
    // NOTIFICATION SYSTEM
    // ==========================================
    window.showNotification = function(message, type = 'info') {
        const notification = document.createElement('div');
        notification.className = `alert alert-${type} alert-dismissible fade show position-fixed top-0 end-0 m-3`;
        notification.style.zIndex = '9999';
        notification.innerHTML = `
            ${message}
            <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
        `;
        document.body.appendChild(notification);
        
        setTimeout(() => {
            notification.classList.remove('show');
            setTimeout(() => notification.remove(), 300);
        }, 5000);
    };

    // ==========================================
    // BACK TO TOP BUTTON
    // ==========================================
    const backToTopButton = document.createElement('button');
    backToTopButton.innerHTML = '<i class="fas fa-arrow-up"></i>';
    backToTopButton.className = 'btn btn-success position-fixed bottom-0 end-0 m-4';
    backToTopButton.style.cssText = 'display: none; z-index: 1000; border-radius: 50%; width: 50px; height: 50px;';
    document.body.appendChild(backToTopButton);

    window.addEventListener('scroll', function() {
        if (window.pageYOffset > 300) {
            backToTopButton.style.display = 'block';
        } else {
            backToTopButton.style.display = 'none';
        }
    });

    backToTopButton.addEventListener('click', function() {
        window.scrollTo({
            top: 0,
            behavior: 'smooth'
        });
    });

    // ==========================================
    // PRINT FUNCTIONALITY
    // ==========================================
    window.printPage = function() {
        window.print();
    };

    // ==========================================
    // EXPORT TO CSV
    // ==========================================
    window.exportTableToCSV = function(tableId, filename) {
        const table = document.getElementById(tableId);
        if (!table) return;

        let csv = [];
        const rows = table.querySelectorAll('tr');

        rows.forEach(row => {
            const cols = row.querySelectorAll('td, th');
            const csvRow = [];
            cols.forEach(col => {
                csvRow.push('"' + col.textContent.trim().replace(/"/g, '""') + '"');
            });
            csv.push(csvRow.join(','));
        });

        const csvContent = csv.join('\n');
        const blob = new Blob([csvContent], { type: 'text/csv' });
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = filename || 'export.csv';
        a.click();
        window.URL.revokeObjectURL(url);
    };

    // ==========================================
    // INITIALIZE COMPLETE
    // ==========================================
    console.log('%c🌱 Food Waste Prediction System Loaded Successfully!', 
                'color: #198754; font-size: 16px; font-weight: bold;');
});

// ==========================================
// UTILITY FUNCTIONS
// ==========================================

// Format number with commas
function formatNumber(num) {
    return num.toString().replace(/\B(?=(\d{3})+(?!\d))/g, ",");
}

// Calculate percentage
function calculatePercentage(value, total) {
    if (total === 0) return 0;
    return ((value / total) * 100).toFixed(1);
}

// Format date
function formatDate(date) {
    const options = { year: 'numeric', month: 'short', day: 'numeric' };
    return new Date(date).toLocaleDateString('en-US', options);
}

// Get days difference
function getDaysDifference(date1, date2) {
    const diffTime = Math.abs(date2 - date1);
    return Math.ceil(diffTime / (1000 * 60 * 60 * 24));
}