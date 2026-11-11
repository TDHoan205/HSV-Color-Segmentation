// HSV Color Segmentation - Frontend JavaScript

let currentSessionId = null;

// Initialize on page load
document.addEventListener('DOMContentLoaded', function() {
    setupEventListeners();
    checkServerHealth();
});

function setupEventListeners() {
    // Upload area
    const uploadArea = document.getElementById('uploadArea');
    const imageInput = document.getElementById('imageInput');
    
    uploadArea.addEventListener('click', () => imageInput.click());
    uploadArea.addEventListener('dragover', (e) => {
        e.preventDefault();
        uploadArea.style.background = '#d6f0f7';
    });
    uploadArea.addEventListener('dragleave', () => {
        uploadArea.style.background = '';
    });
    uploadArea.addEventListener('drop', (e) => {
        e.preventDefault();
        if (e.dataTransfer.files.length > 0) {
            imageInput.files = e.dataTransfer.files;
            uploadImage();
        }
    });
    
    imageInput.addEventListener('change', uploadImage);
    
    // Slider updates
    const sliders = document.querySelectorAll('.slider');
    sliders.forEach(slider => {
        slider.addEventListener('input', updateSliderDisplay);
    });
}

function checkServerHealth() {
    fetch('/api/health')
        .then(r => r.json())
        .then(data => {
            console.log('✅ Server is running');
        })
        .catch(e => {
            showStatus('⚠️ Kết nối server thất bại', 'error');
        });
}

function switchTab(tabName) {
    // Hide all tabs
    document.querySelectorAll('.tab-content').forEach(tab => {
        tab.classList.remove('active');
    });
    
    // Deactivate all nav items
    document.querySelectorAll('.nav-item').forEach(item => {
        item.classList.remove('active');
    });
    
    // Show selected tab
    document.getElementById(tabName).classList.add('active');
    
    // Activate nav item
    event.target.closest('.nav-item').classList.add('active');
}

function uploadImage() {
    const imageInput = document.getElementById('imageInput');
    const file = imageInput.files[0];
    
    if (!file) return;
    
    if (file.size > 50 * 1024 * 1024) {
        showStatus('❌ File quá lớn (tối đa 50MB)', 'error');
        return;
    }
    
    showStatus('📤 Đang tải ảnh...', 'info');
    
    const formData = new FormData();
    formData.append('image', file);
    
    fetch('/api/upload', {
        method: 'POST',
        body: formData
    })
    .then(response => response.json())
    .then(data => {
        if (data.error) {
            showStatus(`❌ Lỗi: ${data.error}`, 'error');
        } else {
            currentSessionId = data.session_id;
            
            // Show preview
            const uploadedImageDiv = document.getElementById('uploadedImage');
            const previewImage = document.getElementById('previewImage');
            previewImage.src = data.image_base64;
            uploadedImageDiv.style.display = 'block';
            document.getElementById('uploadArea').style.display = 'none';
            
            showStatus(`✅ Tải ảnh thành công: ${data.width}x${data.height}px`, 'success');
        }
    })
    .catch(e => {
        showStatus(`❌ Lỗi: ${e.message}`, 'error');
    });
}

function processImage() {
    if (!currentSessionId) {
        showStatus('❌ Vui lòng tải ảnh trước', 'error');
        return;
    }
    
    showStatus('🔄 Đang xử lý ảnh...', 'info');
    
    const data = {
        session_id: currentSessionId,
        h_min_1: document.getElementById('h_min_1').value,
        h_max_1: document.getElementById('h_max_1').value,
        h_min_2: document.getElementById('h_min_2').value,
        h_max_2: document.getElementById('h_max_2').value,
        s_min: document.getElementById('s_min').value,
        s_max: document.getElementById('s_max').value,
        v_min: document.getElementById('v_min').value,
        v_max: document.getElementById('v_max').value,
        median_kernel: document.getElementById('median_kernel').value,
        morph_kernel: document.getElementById('morph_kernel').value,
        use_closing: document.getElementById('use_closing').checked,
        use_opening: document.getElementById('use_opening').checked,
    };
    
    fetch('/api/process', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify(data)
    })
    .then(response => response.json())
    .then(data => {
        if (data.error) {
            showStatus(`❌ Lỗi: ${data.error}`, 'error');
        } else {
            // Display masks
            document.getElementById('maskRaw').src = data.mask_raw;
            document.getElementById('maskMedian').src = data.mask_median;
            document.getElementById('maskMorph').src = data.mask_morph;
            
            // Display statistics
            const whitePix = data.white_pixels;
            console.log('White pixels - Raw:', whitePix.raw, ', Median:', whitePix.median, ', Morph:', whitePix.morph);
            
            showStatus('✅ Xử lý ảnh hoàn thành', 'success');
        }
    })
    .catch(e => {
        showStatus(`❌ Lỗi: ${e.message}`, 'error');
    });
}

function evaluateResults() {
    if (!currentSessionId) {
        showStatus('❌ Vui lòng tải ảnh và xử lý trước', 'error');
        return;
    }
    
    const gtInput = document.getElementById('groundTruthInput');
    if (!gtInput.files.length) {
        showStatus('❌ Vui lòng chọn Ground Truth Mask', 'error');
        return;
    }
    
    showStatus('🔍 Đang đánh giá...', 'info');
    
    const formData = new FormData();
    formData.append('session_id', currentSessionId);
    formData.append('ground_truth', gtInput.files[0]);
    
    fetch('/api/evaluate', {
        method: 'POST',
        body: formData
    })
    .then(response => response.json())
    .then(data => {
        if (data.error) {
            showStatus(`❌ Lỗi: ${data.error}`, 'error');
        } else {
            displayMetrics(data.metrics);
            document.getElementById('visualization').src = data.visualization;
            document.getElementById('visualizationDiv').style.display = 'block';
            showStatus('✅ Đánh giá hoàn thành', 'success');
        }
    })
    .catch(e => {
        showStatus(`❌ Lỗi: ${e.message}`, 'error');
    });
}

function displayMetrics(metrics) {
    // Display individual metrics
    document.getElementById('metricAccuracy').textContent = (metrics.pixel_accuracy * 100).toFixed(2) + '%';
    document.getElementById('metricIoU').textContent = (metrics.iou * 100).toFixed(2) + '%';
    document.getElementById('metricPrecision').textContent = (metrics.precision * 100).toFixed(2) + '%';
    document.getElementById('metricRecall').textContent = (metrics.recall * 100).toFixed(2) + '%';
    document.getElementById('metricF1').textContent = metrics.f1.toFixed(4);
    document.getElementById('metricSpecificity').textContent = (metrics.specificity * 100).toFixed(2) + '%';
    
    // Display confusion matrix
    document.getElementById('tp').textContent = metrics.TP;
    document.getElementById('tn').textContent = metrics.TN;
    document.getElementById('fp').textContent = metrics.FP;
    document.getElementById('fn').textContent = metrics.FN;
    
    // Show containers
    document.getElementById('metricsDisplay').style.display = 'block';
    document.getElementById('confusionMatrix').style.display = 'block';
}

function downloadMask(maskType) {
    if (!currentSessionId) {
        showStatus('❌ Vui lòng tải ảnh trước', 'error');
        return;
    }
    
    showStatus('📥 Đang tải xuống...', 'info');
    
    const data = {
        session_id: currentSessionId,
        mask_type: maskType,
    };
    
    fetch('/api/download-mask', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify(data)
    })
    .then(response => {
        if (!response.ok) throw new Error('Download failed');
        return response.blob();
    })
    .then(blob => {
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `mask_${maskType}.png`;
        a.click();
        window.URL.revokeObjectURL(url);
        showStatus('✅ Tải xuống hoàn thành', 'success');
    })
    .catch(e => {
        showStatus(`❌ Lỗi: ${e.message}`, 'error');
    });
}

function updateSliderDisplay(event) {
    const slider = event.target;
    const id = slider.id;
    const displayId = id + '_val';
    
    const displayElement = document.getElementById(displayId);
    if (displayElement) {
        displayElement.textContent = slider.value;
    }
}

function resetSession() {
    currentSessionId = null;
    
    // Reset UI
    document.getElementById('uploadArea').style.display = 'block';
    document.getElementById('uploadedImage').style.display = 'none';
    document.getElementById('imageInput').value = '';
    
    // Clear results
    document.getElementById('maskRaw').src = '';
    document.getElementById('maskMedian').src = '';
    document.getElementById('maskMorph').src = '';
    document.getElementById('visualization').src = '';
    document.getElementById('metricsDisplay').style.display = 'none';
    document.getElementById('confusionMatrix').style.display = 'none';
    document.getElementById('visualizationDiv').style.display = 'none';
    document.getElementById('groundTruthInput').value = '';
    
    showStatus('✅ Đã đặt lại', 'info');
}

function showStatus(message, type = 'info') {
    const container = document.getElementById('statusContainer');
    
    const statusItem = document.createElement('div');
    statusItem.className = `status-item ${type}`;
    statusItem.textContent = message;
    
    container.appendChild(statusItem);
    
    // Remove after 5 seconds
    setTimeout(() => {
        statusItem.style.opacity = '0';
        setTimeout(() => {
            container.removeChild(statusItem);
        }, 300);
    }, 5000);
}

// Handle Enter key in sliders to trigger processing
document.addEventListener('keypress', (e) => {
    if (e.key === 'Enter' && document.activeElement.classList.contains('slider')) {
        processImage();
    }
});
