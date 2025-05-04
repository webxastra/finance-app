/**
 * AI Admin Dashboard JavaScript
 * Handles all dashboard interactions, API calls, and UI updates
 */

// API Endpoints
const API = {
    stats: '/api/ai/stats',
    recentCorrections: '/api/ai/recent-corrections',
    modelInfo: '/api/ai/model-info',
    retrain: '/api/ai/training/retrain-with-corrections',
    reset: '/api/ai/training/reset-model',
    downloadModel: '/api/ai/training/download-model',
    exportCorrections: '/api/ai/training/export-corrections',
    deleteCorrection: '/api/ai/training/delete-correction',
};


// DOM Elements
const elements = {
    // Navigation
    navItems: document.querySelectorAll('.sidebar-nav li'),
    sections: document.querySelectorAll('.dashboard-section'),
    
    // Overview Section
    modelVersion: document.getElementById('model-version'),
    modelAccuracy: document.getElementById('model-accuracy'),
    totalCorrections: document.getElementById('total-corrections'),
    appliedCorrections: document.getElementById('applied-corrections'),
    refreshStatsBtn: document.getElementById('refresh-stats'),
    categoryChart: document.getElementById('category-chart'),
    trainingChart: document.getElementById('training-chart'),
    
    // Model Info Section
    infoVersion: document.getElementById('info-version'),
    infoLastTrained: document.getElementById('info-last-trained'),
    infoAccuracy: document.getElementById('info-accuracy'),
    infoCorrectionsApplied: document.getElementById('info-corrections-applied'),
    infoTrainingEvents: document.getElementById('info-training-events'),
    categoryList: document.getElementById('category-list'),
    
    // Corrections Section
    correctionsTotal: document.getElementById('corrections-total'),
    correctionsApplied: document.getElementById('corrections-applied'),
    correctionsPending: document.getElementById('corrections-pending'),
    correctionsTableBody: document.getElementById('corrections-table-body'),
    refreshCorrectionsBtn: document.getElementById('refresh-corrections'),
    
    // Training Section
    unusedCorrections: document.getElementById('unused-corrections'),
    lastTraining: document.getElementById('last-training'),
    maxCorrections: document.getElementById('max-corrections'),
    startTrainingBtn: document.getElementById('start-training'),
    trainingTimeline: document.getElementById('training-timeline'),
    
    // UI Components
    currentDatetime: document.getElementById('current-datetime'),
    loadingOverlay: document.getElementById('loading-overlay'),
    notificationContainer: document.getElementById('notification-container'),
    
    // Modal
    modalContainer: document.getElementById('modal-container'),
    modalTitle: document.getElementById('modal-title'),
    modalBody: document.getElementById('modal-body'),
    modalClose: document.getElementById('modal-close'),
    modalCancel: document.getElementById('modal-cancel'),
    modalConfirm: document.getElementById('modal-confirm')
};

// Chart instances
let categoryChart = null;
let trainingChart = null;

// Data
let dashboardData = null;
let modelData = null;
let correctionsData = null;

// Initialize the dashboard
function initDashboard() {
    // Set up event listeners
    setupEventListeners();
    
    // Update current date and time
    updateDateTime();
    setInterval(updateDateTime, 60000);
    
    // Load initial data
    loadAllData();
}

// Set up event listeners
function setupEventListeners() {
    // Download model
    const downloadBtn = document.getElementById('download-model-btn');
    if (downloadBtn) {
        downloadBtn.addEventListener('click', function() {
            window.open(API.downloadModel, '_blank');
        });
    }
    // Export corrections
    const exportBtn = document.getElementById('export-corrections-btn');
    if (exportBtn) {
        exportBtn.addEventListener('click', function() {
            window.open(API.exportCorrections + '?format=csv', '_blank');
        });
    }
    // Reset model
    const resetBtn = document.getElementById('reset-model-btn');
    if (resetBtn) {
        resetBtn.addEventListener('click', function() {
            showModal('Reset Model',
                '<p>Are you sure you want to reset the AI model? This will clear all corrections and restore the default model.</p>',
                function() { resetModel(); }
            );
        });
    }
    // Delete correction (delegated)
    const correctionsTable = document.getElementById('corrections-table-body');
    if (correctionsTable) {
        correctionsTable.addEventListener('click', function(e) {
            if (e.target && e.target.classList.contains('delete-correction-btn')) {
                const id = e.target.getAttribute('data-id');
                showModal('Delete Correction',
                    '<p>Are you sure you want to delete this correction?</p>',
                    function() { deleteCorrection(id); }
                );
            }
        });
    }

    // Navigation
    elements.navItems.forEach(item => {
        item.addEventListener('click', () => {
            navigateToSection(item.getAttribute('data-section'));
        });
    });
    
    // Refresh buttons
    elements.refreshStatsBtn.addEventListener('click', () => {
        loadStatsData();
    });
    
    elements.refreshCorrectionsBtn.addEventListener('click', () => {
        loadCorrectionsData();
    });
    
    // Training
    elements.startTrainingBtn.addEventListener('click', () => {
        showRetrainConfirmation();
    });
}

// Navigation
function navigateToSection(sectionId) {
    // Update navigation
    elements.navItems.forEach(item => {
        item.classList.remove('active');
        if (item.getAttribute('data-section') === sectionId) {
            item.classList.add('active');
        }
    });
    
    // Show selected section
    elements.sections.forEach(section => {
        section.classList.remove('active');
        if (section.id === sectionId) {
            section.classList.add('active');
        }
    });
}

// Date and time
function updateDateTime() {
    const now = new Date();
    elements.currentDatetime.textContent = now.toLocaleString();
}

// Load all data
function loadAllData() {
    showLoading('Loading dashboard data...');
    
    // Load stats
    loadStatsData()
        .then(() => loadModelInfo())
        .then(() => loadCorrectionsData())
        .finally(() => hideLoading());
}

// Load stats data
async function loadStatsData() {
    try {
        showLoading('Loading AI stats...');
        const response = await fetch(API.stats);
        
        if (!response.ok) {
            throw new Error(`Failed to load stats: ${response.status}`);
        }
        
        const data = await response.json();
        
        if (!data.success) {
            throw new Error(data.message || 'Failed to load stats');
        }
        
        dashboardData = data.stats;
        updateStatsUI();
        
        return dashboardData;
    } catch (error) {
        showNotification('error', `Error: ${error.message}`);
        console.error('Error loading stats:', error);
    } finally {
        hideLoading();
    }
}

// Load model info
async function loadModelInfo() {
    try {
        showLoading('Loading model information...');
        const response = await fetch(API.modelInfo);
        
        if (!response.ok) {
            throw new Error(`Failed to load model info: ${response.status}`);
        }
        
        const data = await response.json();
        
        if (!data.success) {
            throw new Error(data.message || 'Failed to load model info');
        }
        
        modelData = data.model;
        updateModelInfoUI();
        
        return modelData;
    } catch (error) {
        showNotification('error', `Error: ${error.message}`);
        console.error('Error loading model info:', error);
    } finally {
        hideLoading();
    }
}

// Load corrections data
async function loadCorrectionsData() {
    try {
        showLoading('Loading corrections data...');
        const response = await fetch(API.recentCorrections);
        
        if (!response.ok) {
            throw new Error(`Failed to load corrections: ${response.status}`);
        }
        
        const data = await response.json();
        
        if (!data.success) {
            throw new Error(data.message || 'Failed to load corrections');
        }
        
        correctionsData = data.corrections;
        updateCorrectionsUI();
        
        return correctionsData;
    } catch (error) {
        showNotification('error', `Error: ${error.message}`);
        console.error('Error loading corrections:', error);
    } finally {
        hideLoading();
    }
}

// Update stats UI
function updateStatsUI() {
    if (!dashboardData) return;
    
    // Update overview cards
    elements.modelVersion.textContent = dashboardData.model.version || 'N/A';
    
    const accuracy = dashboardData.model.accuracy;
    elements.modelAccuracy.textContent = accuracy 
        ? `${(accuracy * 100).toFixed(1)}%` 
        : 'N/A';
    
    elements.totalCorrections.textContent = dashboardData.corrections.total || 0;
    elements.appliedCorrections.textContent = dashboardData.corrections.applied || 0;
    
    // Update category chart
    updateCategoryChart();
    
    // Update training chart
    updateTrainingChart();
}

// Update model info UI
function updateModelInfoUI() {
    if (!modelData) return;
    
    // Update model details
    elements.infoVersion.textContent = modelData.version || 'N/A';
    elements.infoLastTrained.textContent = formatDate(modelData.last_trained) || 'Never';
    
    const accuracy = modelData.accuracy;
    elements.infoAccuracy.textContent = accuracy 
        ? `${(accuracy * 100).toFixed(1)}%` 
        : 'N/A';
    
    elements.infoCorrectionsApplied.textContent = modelData.corrections_applied || 0;
    elements.infoTrainingEvents.textContent = modelData.total_retraining_events || 0;
    
    // Update category list
    updateCategoryList();
}

// Update corrections UI
function updateCorrectionsUI() {
    if (!correctionsData || !dashboardData) return;
    
    // Update stats
    elements.correctionsTotal.textContent = dashboardData.corrections.total || 0;
    elements.correctionsApplied.textContent = dashboardData.corrections.applied || 0;
    elements.correctionsPending.textContent = dashboardData.corrections.unused || 0;
    
    // Update training section stats
    elements.unusedCorrections.textContent = dashboardData.corrections.unused || 0;
    elements.lastTraining.textContent = formatDate(dashboardData.training.last_training) || 'Never';
    
    // Update corrections table
    updateCorrectionsTable();
    
    // Update training timeline
    updateTrainingTimeline();
}

// Update category chart
function updateCategoryChart() {
    if (!dashboardData) return;
    
    const categoryData = dashboardData.corrections.by_category || {};
    const categories = Object.keys(categoryData);
    const counts = categories.map(c => categoryData[c]);
    
    // Prepare chart data
    const data = {
        labels: categories.length > 0 ? categories : ['No data'],
        datasets: [{
            label: 'Corrections by Category',
            data: counts.length > 0 ? counts : [0],
            backgroundColor: [
                'rgba(74, 108, 247, 0.7)',
                'rgba(110, 74, 247, 0.7)',
                'rgba(247, 74, 181, 0.7)',
                'rgba(247, 181, 74, 0.7)',
                'rgba(74, 247, 110, 0.7)',
                'rgba(74, 181, 247, 0.7)'
            ],
            borderColor: 'rgba(255, 255, 255, 0.7)',
            borderWidth: 1
        }]
    };
    
    // Create or update chart
    if (!categoryChart) {
        const ctx = elements.categoryChart.getContext('2d');
        categoryChart = new Chart(ctx, {
            type: 'pie',
            data: data,
            options: {
                responsive: true,
                plugins: {
                    legend: {
                        position: 'right',
                    }
                }
            }
        });
    } else {
        categoryChart.data = data;
        categoryChart.update();
    }
}

// Update training chart
function updateTrainingChart() {
    if (!dashboardData) return;
    
    // Get training history (mock data for now)
    const events = dashboardData.training.total_events || 0;
    const corrections = dashboardData.training.corrections_applied || 0;
    const averagePerEvent = events > 0 ? Math.round(corrections / events) : 0;
    
    // Prepare chart data
    const data = {
        labels: ['Total Events', 'Total Corrections', 'Avg. per Event'],
        datasets: [{
            label: 'Training Statistics',
            data: [events, corrections, averagePerEvent],
            backgroundColor: [
                'rgba(74, 108, 247, 0.7)',
                'rgba(40, 167, 69, 0.7)',
                'rgba(255, 193, 7, 0.7)'
            ],
            borderColor: [
                'rgba(74, 108, 247, 1)',
                'rgba(40, 167, 69, 1)',
                'rgba(255, 193, 7, 1)'
            ],
            borderWidth: 1
        }]
    };
    
    // Create or update chart
    if (!trainingChart) {
        const ctx = elements.trainingChart.getContext('2d');
        trainingChart = new Chart(ctx, {
            type: 'bar',
            data: data,
            options: {
                responsive: true,
                scales: {
                    y: {
                        beginAtZero: true
                    }
                }
            }
        });
    } else {
        trainingChart.data = data;
        trainingChart.update();
    }
}

// Update category list
function updateCategoryList() {
    if (!modelData || !modelData.categories) {
        elements.categoryList.innerHTML = '<span class="loading">No categories available</span>';
        return;
    }
    
    // Create category tags
    const categoriesHtml = modelData.categories.map(category => 
        `<span class="category-tag">${category}</span>`
    ).join('');
    
    elements.categoryList.innerHTML = categoriesHtml;
}

// Update corrections table
function updateCorrectionsTable() {
    // Add delete button to each row
    if (!correctionsData) return;
    elements.correctionsTableBody.innerHTML = '';
    if (correctionsData.length === 0) {
        elements.correctionsTableBody.innerHTML = '<tr><td colspan="6">No corrections found.</td></tr>';
        return;
    }
    correctionsData.forEach(correction => {
        const row = document.createElement('tr');
        row.innerHTML = `
            <td>${correction.id}</td>
            <td>${truncateText(correction.description, 40)}</td>
            <td>${correction.predicted_category || '-'}</td>
            <td>${correction.correct_category || '-'}</td>
            <td>${formatDate(correction.created_at)}</td>
            <td>${correction.is_applied ? 'Applied' : 'Pending'}
                <button class="delete-correction-btn" data-id="${correction.id}" title="Delete Correction" style="margin-left:7px;color:#f44336;background:none;border:none;cursor:pointer;"><i class="fas fa-trash"></i></button>
            </td>
        `;
        elements.correctionsTableBody.appendChild(row);
    });
}

// Update training timeline
function updateTrainingTimeline() {
    if (!dashboardData || !dashboardData.training || !dashboardData.training.retraining_events) {
        elements.trainingTimeline.innerHTML = `
            <div class="timeline-loading">No training history available</div>
        `;
        return;
    }
    
    const events = dashboardData.training.retraining_events || [];
    
    if (events.length === 0) {
        elements.trainingTimeline.innerHTML = `
            <div class="timeline-loading">No training events recorded yet</div>
        `;
        return;
    }
    
    // Create timeline events
    const timelineHtml = events.map((event, index) => `
        <div class="timeline-event">
            <div class="timeline-date">${formatDate(event.timestamp)}</div>
            <div class="timeline-title">Model v${event.version} Training</div>
            <div class="timeline-details">
                Applied ${event.corrections_applied} corrections
                ${event.accuracy ? `• Accuracy: ${(event.accuracy * 100).toFixed(1)}%` : ''}
            </div>
        </div>
    `).join('');
    
    elements.trainingTimeline.innerHTML = timelineHtml;
}

// Show retrain confirmation
function showRetrainConfirmation() {
    const maxCorrections = elements.maxCorrections.value;
    
    showModal(
        'Retrain AI Model',
        `
        <p>Are you sure you want to retrain the AI model?</p>
        <p>This will use up to <strong>${maxCorrections}</strong> unused corrections for training.</p>
        <p>The process may take a few moments to complete.</p>
        `,
        () => retrainModel(maxCorrections)
    );
}

// Reset model
async function resetModel() {
    showLoading('Resetting model...');
    try {
        const resp = await fetch(API.reset, { method: 'POST', headers: { 'Content-Type': 'application/json' } });
        const data = await resp.json();
        if (data.success) {
            showNotification('success', 'Model reset successfully.');
            await loadAllData();
        } else {
            showNotification('error', data.message || 'Failed to reset model.');
        }
    } catch (e) {
        showNotification('error', 'Error resetting model: ' + e.message);
    } finally {
        hideLoading();
    }
}

// Delete correction
async function deleteCorrection(id) {
    showLoading('Deleting correction...');
    try {
        const resp = await fetch(`${API.deleteCorrection}/${id}`, { method: 'DELETE' });
        const data = await resp.json();
        if (data.success) {
            showNotification('success', 'Correction deleted.');
            await loadCorrectionsData();
        } else {
            showNotification('error', data.message || 'Failed to delete correction.');
        }
    } catch (e) {
        showNotification('error', 'Error deleting correction: ' + e.message);
    } finally {
        hideLoading();
    }
}

// Retrain model
async function retrainModel(maxCorrections) {
    try {
        showLoading('Retraining model...');
        
        const response = await fetch(API.retrain, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                max_corrections: parseInt(maxCorrections)
            })
        });
        
        if (!response.ok) {
            throw new Error(`Retraining failed: ${response.status}`);
        }
        
        const data = await response.json();
        
        if (!data.success) {
            throw new Error(data.message || 'Retraining failed');
        }
        
        // Show success and reload data
        showNotification('success', `Retraining successful! Applied ${data.corrections_applied} corrections.`);
        
        // Reload all data
        await Promise.all([
            loadStatsData(),
            loadModelInfo(),
            loadCorrectionsData()
        ]);
        
        // Force update UI components
        updateStatsUI();
        updateModelInfoUI();
        updateCorrectionsUI();
        
    } catch (error) {
        showNotification('error', `Error: ${error.message}`);
        console.error('Error retraining model:', error);
    } finally {
        hideLoading();
    }
}

// Make retrainModel globally accessible
window.retrainModel = retrainModel;
window.resetModel = resetModel;
window.deleteCorrection = deleteCorrection;

// UI Helpers

// Format date
function formatDate(dateString) {
    if (!dateString) return '';
    
    const date = new Date(dateString);
    if (isNaN(date.getTime())) return dateString;
    
    return date.toLocaleString();
}

// Truncate text
function truncateText(text, maxLength) {
    if (!text) return '';
    if (text.length <= maxLength) return text;
    
    return text.substring(0, maxLength) + '...';
}

// Show loading overlay
function showLoading(message = 'Loading...') {
    elements.loadingOverlay.querySelector('.loading-message').textContent = message;
    elements.loadingOverlay.classList.remove('hidden');
}

// Hide loading overlay
function hideLoading() {
    elements.loadingOverlay.classList.add('hidden');
}

// Show notification
function showNotification(type, message) {
    const id = 'notification-' + Date.now();
    const html = `
        <div id="${id}" class="notification notification-${type}">
            <span class="notification-icon">
                <i class="fas fa-${type === 'success' ? 'check-circle' : type === 'error' ? 'exclamation-circle' : 'info-circle'}"></i>
            </span>
            <span class="notification-message">${message}</span>
            <button class="notification-close">&times;</button>
        </div>
    `;
    
    elements.notificationContainer.insertAdjacentHTML('beforeend', html);
    
    // Add close event
    const notification = document.getElementById(id);
    notification.querySelector('.notification-close').addEventListener('click', () => {
        notification.remove();
    });
    
    // Auto remove after 5 seconds
    setTimeout(() => {
        if (notification && notification.parentNode) {
            notification.remove();
        }
    }, 5000);
}

// Show modal
function showModal(title, body, confirmCallback) {
    const newModal = document.getElementById('new-modal');
    const newModalTitle = document.getElementById('new-modal-title');
    const newModalBody = document.getElementById('new-modal-body');
    const newModalConfirm = document.getElementById('new-modal-confirm');
    const newModalCancel = document.getElementById('new-modal-cancel');
    const newModalClose = document.getElementById('new-modal-close');

    newModalTitle.textContent = title;
    newModalBody.innerHTML = body;

    // Remove old event listeners by cloning
    const freshConfirm = newModalConfirm.cloneNode(true);
    const freshCancel = newModalCancel.cloneNode(true);
    const freshClose = newModalClose.cloneNode(true);

    newModalConfirm.parentNode.replaceChild(freshConfirm, newModalConfirm);
    newModalCancel.parentNode.replaceChild(freshCancel, newModalCancel);
    newModalClose.parentNode.replaceChild(freshClose, newModalClose);

    // Add listeners
    freshCancel.addEventListener('click', closeModal);
    freshClose.addEventListener('click', closeModal);

    if (typeof confirmCallback === 'function') {
        freshConfirm.addEventListener('click', function() {
            closeModal();
            confirmCallback();
        });
    } else {
        freshConfirm.addEventListener('click', closeModal);
    }

    newModal.style.display = 'block';
    console.log('Modal displayed');
}

function closeModal() {
    const newModal = document.getElementById('new-modal');
    newModal.style.display = 'none';
}


// Initialize when DOM is ready
document.addEventListener('DOMContentLoaded', initDashboard); 