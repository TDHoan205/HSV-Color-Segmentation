// HSV Color Segmentation - Frontend JavaScript

let currentSessionId = null;
let currentRunId = null;
let singleBusy = false;
let lastAppliedSummary = '';
let workflowNote = '';

function updateWorkflowState() {
    const ready = !!currentSessionId && currentRunId !== null && !singleBusy;
    const state = !currentSessionId ? 'Cần tải ảnh ở mục Tải Ảnh, rồi chọn màu ở Phân Đoạn HSV.'
        : singleBusy ? 'Đang xử lý toàn bộ pipeline; vui lòng chờ.'
        : ready ? `Đã áp dụng · lượt ${currentRunId}. ${lastAppliedSummary}`
        : `Chờ áp dụng: bấm nút áp dụng tại tab này. ${lastAppliedSummary ? 'Ảnh xem trước là kết quả cũ, không khớp thông số hiện tại.' : 'Chưa có kết quả.'}`;
    ['medianState', 'morphState'].forEach(id => {
        const el = document.getElementById(id);
        if (el) el.textContent = state;
    });
    const gt = document.getElementById('groundTruthInput');
    const ev = document.getElementById('evaluationState');
    if (ev) ev.textContent = !ready ? `${state} Cần áp dụng xử lý trước khi đánh giá.`
        : workflowNote || `Lượt ${currentRunId}: ${gt && gt.files.length ? 'Đã chọn GT; bấm Đánh Giá.' : 'Chọn GT đúng ảnh/màu rồi bấm Đánh Giá.'} Mỗi lần xử lý lại phải đánh giá lại.`;
    ['medianApplyBtn', 'morphApplyBtn', 'evaluationProcessBtn'].forEach(id => {
        const el = document.getElementById(id);
        if (el) el.disabled = !currentSessionId || singleBusy;
    });
    const btn = document.getElementById('evaluateBtn');
    if (btn) btn.disabled = !ready || !gt.files.length;
    ['medianBefore', 'medianAfter', 'morphBefore', 'morphAfter'].forEach(id => {
        const el = document.getElementById(id);
        if (el) el.classList.toggle('stale', !ready);
    });
}


// Initialize on page load
document.addEventListener('DOMContentLoaded', function() {
    setupEventListeners();
    checkServerHealth();
    loadColorPresets();
    setupMorphControls();
    document.getElementById('groundTruthInput').addEventListener('change', () => {
        evaluateSeq += 1;
        markMetricsStale('GT đã đổi, cần đánh giá lại.');
        workflowNote = '';
        updateWorkflowState();
    });
    updateWorkflowState();
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

let uploadSeq = 0;
let evaluateSeq = 0;

function invalidateSingleResult() {
    processSeq += 1;
    evaluateSeq += 1;
    currentRunId = null;
    workflowNote = '';
    markMetricsStale('Tham số đã đổi; hãy xử lý và đánh giá lại.');
    updateWorkflowState();
    const el = document.getElementById('resultStale');
    if (el && document.getElementById('maskRaw').getAttribute('src')) {
        el.textContent = '⚠️ Kết quả cũ; hãy xử lý lại với tham số hiện tại.';
        el.style.display = 'block';
    }
}

function uploadImage() {
    const imageInput = document.getElementById('imageInput');
    const file = imageInput.files[0];
    
    if (!file) return;
    
    if (file.size > 50 * 1024 * 1024) {
        showStatus('❌ File quá lớn (tối đa 50MB)', 'error');
        return;
    }
    
    const seq = ++uploadSeq;
    processSeq += 1;
    evaluateSeq += 1;
    showStatus('📤 Đang tải ảnh...', 'info');
    
    const formData = new FormData();
    formData.append('image', file);
    
    fetch('/api/upload', {
        method: 'POST',
        body: formData
    })
    .then(response => response.json())
    .then(data => {
        if (seq !== uploadSeq) {
            if (data.session_id) fetch('/api/release-session', {method: 'POST', headers: {'Content-Type': 'application/json'}, body: JSON.stringify({session_id: data.session_id})});
            return;
        }
        if (data.error) {
            showStatus(`❌ Lỗi: ${data.error}`, 'error');
        } else {
            resetSession(false);
            currentSessionId = data.session_id;
            updateWorkflowState();
            cmpMarkStale('Ảnh nguồn đã thay đổi');
            
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

// ===== Phase C: Morphology =====
const MORPH_UI_ORDER = [
    { operation: 'close', check: 'use_closing', iter: 'iter_close', label: 'Closing' },
    { operation: 'open', check: 'use_opening', iter: 'iter_open', label: 'Opening' },
    { operation: 'erode', check: 'use_erosion', iter: 'iter_erode', label: 'Erosion' },
    { operation: 'dilate', check: 'use_dilation', iter: 'iter_dilate', label: 'Dilation' },
];
let processSeq = 0;          // chặn response /api/process đến muộn
let appliedMorphKey = null;  // morphology của lần xử lý gần nhất đã áp dụng

function parseStrictInt(text) {
    const raw = String(text).trim();
    return /^-?\d+$/.test(raw) ? parseInt(raw, 10) : raw;   // giá trị sai giữ nguyên để server từ chối
}

function collectMorphology() {
    const ops = [];
    MORPH_UI_ORDER.forEach(o => {
        if (document.getElementById(o.check).checked) {
            ops.push({ operation: o.operation, iterations: parseStrictInt(document.getElementById(o.iter).value) });
        }
    });
    return {
        kernel_size: parseStrictInt(document.getElementById('morph_kernel').value),
        kernel_shape: document.getElementById('morph_shape').value,
        operations: ops,
    };
}

// Khóa so sánh không phụ thuộc thứ tự key (server trả JSON đã sắp xếp key)
function morphCanonicalKey(m) {
    return JSON.stringify({
        k: m.kernel_size,
        s: m.kernel_shape,
        o: m.operations.map(x => [x.operation, x.iterations]),
    });
}

function setMorphologyControls(m) {
    document.getElementById('morph_kernel').value = m.kernel_size;
    document.getElementById('morph_shape').value = m.kernel_shape;
    MORPH_UI_ORDER.forEach(o => {
        const found = m.operations.find(x => x.operation === o.operation);
        document.getElementById(o.check).checked = !!found;
        document.getElementById(o.iter).disabled = !found;
        document.getElementById(o.iter).value = found ? found.iterations : 1;
    });
    morphUpdatePending();
}

function describeMorphology(m) {
    const names = { close: 'Closing', open: 'Opening', erode: 'Erosion', dilate: 'Dilation' };
    const chain = m.operations.length
        ? m.operations.map(o => `${names[o.operation]} ×${o.iterations}`).join(' → ')
        : '(không áp dụng phép nào)';
    return `${chain}; kernel ${m.kernel_size}×${m.kernel_size} ${m.kernel_shape}`;
}

function morphSetMessage(msg) {
    const el = document.getElementById('morphMessage');
    if (!el) return;
    el.textContent = msg ? `❌ ${msg}` : '';
    el.style.display = msg ? 'block' : 'none';
}

function markMetricsStale(reason) {
    workflowNote = reason;
    ['metricsDisplay', 'confusionMatrix', 'visualizationDiv'].forEach(id => {
        const el = document.getElementById(id);
        if (el) el.style.display = 'none';
    });
    ['metricsDisplay', 'confusionMatrix', 'visualizationDiv'].forEach(id => {
        const el = document.getElementById(id);
        if (el && el.style.display !== 'none') el.classList.add('stale');
    });
    const metrics = document.getElementById('metricsDisplay');
    if (metrics && metrics.style.display !== 'none') {
        let note = document.getElementById('metricsStaleNote');
        if (!note) {
            note = document.createElement('div');
            note.id = 'metricsStaleNote';
            note.className = 'morph-pending';
            metrics.parentNode.insertBefore(note, metrics);
        }
        note.textContent = `⚠️ Metrics cũ: ${reason}`;
        note.style.display = 'block';
    }
}

function clearMetricsStale() {
    ['metricsDisplay', 'confusionMatrix', 'visualizationDiv'].forEach(id => {
        const el = document.getElementById(id);
        if (el) el.classList.remove('stale');
    });
    const note = document.getElementById('metricsStaleNote');
    if (note) note.style.display = 'none';
}

function morphUpdatePending() {
    const pending = document.getElementById('morphPending');
    const stale = document.getElementById('resultStale');
    const current = morphCanonicalKey(collectMorphology());
    const differs = appliedMorphKey !== null && current !== appliedMorphKey;
    if (pending) pending.style.display = differs ? 'block' : 'none';
    if (stale) {
        stale.style.display = differs ? 'block' : 'none';
        stale.textContent = '⚠️ Mask Morphology bên dưới không còn khớp tham số hiện tại. Bấm "Áp Dụng Morphology" để cập nhật.';
    }
    ['maskMorph', 'baMorph'].forEach(id => {
        const img = document.getElementById(id);
        if (img) img.classList.toggle('stale', differs);
    });
    const chain = document.getElementById('morphChain');
    if (chain) chain.textContent = describeMorphology(collectMorphology());
    cmpUpdateMorphSummary();
    updateWorkflowState();
}

function onMorphControlChange() {
    invalidateSingleResult();
    MORPH_UI_ORDER.forEach(o => {
        document.getElementById(o.iter).disabled = !document.getElementById(o.check).checked;
    });
    processSeq += 1;   // response đang bay (nếu có) không còn khớp tham số
    morphUpdatePending();
    if (appliedMorphKey !== null) {
        markMetricsStale('tham số Morphology đã đổi, hãy áp dụng rồi đánh giá lại.');
        cmpMarkStale('Tham số Morphology đã đổi');
    }
}

function applyMorphology() {
    processImage();
}

function renderBeforeAfter(data) {
    [['medianBefore', 'raw'], ['medianAfter', 'median'], ['morphBefore', 'median'], ['morphAfter', 'morph']].forEach(([id, stage]) => {
        document.getElementById(id).src = data[`mask_${stage}`];
        document.getElementById(id + 'Info').textContent = `${data.image_dimensions.width}×${data.image_dimensions.height}; pixel trắng: ${data.white_pixels[stage]}`;
    });
    lastAppliedSummary = `Median ${data.applied_config.median_kernel}×${data.applied_config.median_kernel}; ${describeMorphology(data.applied_config.morphology)}`;
    document.getElementById('baMedian').src = data.mask_median;
    document.getElementById('baMorph').src = data.mask_morph;
    const w = data.image_dimensions;
    document.getElementById('baMedianInfo').textContent =
        `${w.width}×${w.height}, pixel trắng: ${data.white_pixels.median}`;
    document.getElementById('baMorphInfo').textContent =
        `${w.width}×${w.height}, pixel trắng: ${data.white_pixels.morph}`;
    const cfg = data.applied_config;
    let text = `Đã áp dụng (${cfg.branch}): median ${cfg.median_kernel}; ${describeMorphology(cfg.morphology)}`;
    if (cfg.warnings && cfg.warnings.length) text += ` | ${cfg.warnings.join('; ')}`;
    document.getElementById('appliedConfigText').textContent = text;
}

function setupMorphControls() {
    ['morph_kernel', 'morph_shape', 'use_closing', 'use_opening', 'use_erosion', 'use_dilation',
     'iter_close', 'iter_open', 'iter_erode', 'iter_dilate', 'median_kernel'].forEach(id => {
        const el = document.getElementById(id);
        if (!el) return;
        el.addEventListener('change', onMorphControlChange);
        el.addEventListener('input', onMorphControlChange);
    });
    onMorphControlChange();
}

function processImage() {
    if (!currentSessionId) {
        showStatus('❌ Vui lòng tải ảnh trước', 'error');
        return;
    }
    
    singleBusy = true;
    evaluateSeq += 1;
    currentRunId = null;
    markMetricsStale('Đang xử lý lại; hãy đánh giá khi hoàn tất.');
    updateWorkflowState();
    showStatus('🔄 Đang xử lý ảnh...', 'info');
    
    const data = {
        session_id: currentSessionId,
        color_id: currentColorId,
        h_min_1: document.getElementById('h_min_1').value,
        h_max_1: document.getElementById('h_max_1').value,
        h_min_2: document.getElementById('h_min_2').value,
        h_max_2: document.getElementById('h_max_2').value,
        s_min: document.getElementById('s_min').value,
        s_max: document.getElementById('s_max').value,
        v_min: document.getElementById('v_min').value,
        v_max: document.getElementById('v_max').value,
        median_kernel: document.getElementById('median_kernel').value,
        morphology: collectMorphology(),
        request_id: ++processSeq,
    };
    const mySeq = data.request_id;
    morphSetMessage('');
    
    fetch('/api/process', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify(data)
    })
    .then(response => response.json())
    .then(data => {
        // response cũ: bỏ. Response lỗi không mang request_id nên chỉ kiểm tra mySeq.
        if (mySeq !== processSeq) return;
        if (!data.error && data.request_id !== mySeq) return;
        if (data.error) {
            morphSetMessage(data.error);
            showStatus(`❌ Lỗi: ${data.error}`, 'error');
        } else {
            // Display masks
            document.getElementById('maskRaw').src = data.mask_raw;
            document.getElementById('maskMedian').src = data.mask_median;
            document.getElementById('maskMorph').src = data.mask_morph;
            renderBeforeAfter(data);
            
            // Display statistics
            const whitePix = data.white_pixels;
            console.log('White pixels - Raw:', whitePix.raw, ', Median:', whitePix.median, ', Morph:', whitePix.morph);
            
            currentRunId = data.run_id;
            appliedMorphKey = morphCanonicalKey(data.applied_config.morphology);
            morphUpdatePending();
            markMetricsStale('Mask đã được xử lý lại; metrics bên dưới thuộc lần xử lý trước, hãy đánh giá lại.');
            cmpMarkStale('Kết quả xử lý ảnh đã thay đổi');
            showStatus('✅ Xử lý ảnh hoàn thành', 'success');
        }
    })
    .catch(e => {
        showStatus(`❌ Lỗi: ${e.message}`, 'error');
    })
    .finally(() => {
        singleBusy = false;
        updateWorkflowState();
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
    
    if (currentRunId === null) {
        showStatus('Hãy xử lý ảnh với tham số hiện tại trước khi đánh giá.', 'error');
        return;
    }
    const seq = ++evaluateSeq;
    const session = currentSessionId;
    const run = currentRunId;
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
            if (seq !== evaluateSeq || session !== currentSessionId || run !== currentRunId || data.run_id !== run) return;
            displayMetrics(data.metrics);
            workflowNote = `Đã đánh giá lượt ${run} bằng GT đã chọn. Đổi ảnh, GT, màu hoặc thông số / xử lý lại thì cần đánh giá lại.`;
            updateWorkflowState();
            clearMetricsStale();
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
    invalidateSingleResult();
    const id = slider.id;
    const displayId = id + '_val';
    
    const displayElement = document.getElementById(displayId);
    if (displayElement) {
        displayElement.textContent = slider.value;
    }
}

// ===== Phase A: Color Palette & HSV Preset =====
let colorPresets = {};      // color_id -> preset (nạp từ /api/color-presets)
let currentColorId = 'red'; // màu đang chọn

function loadColorPresets() {
    return fetch('/api/color-presets')
        .then(r => r.json())
        .then(data => {
            colorPresets = {};
            (data.presets || []).forEach(p => { colorPresets[p.color_id] = p; });
            renderColorPalette();
            applyPreset(currentColorId);
            cmpInitUi();
        })
        .catch(e => showStatus(`⚠️ Không tải được bảng màu: ${e.message}`, 'error'));
}

function renderColorPalette() {
    const container = document.getElementById('colorPalette');
    if (!container) return;
    container.innerHTML = '';
    Object.values(colorPresets).forEach(p => {
        const btn = document.createElement('button');
        btn.type = 'button';
        btn.className = 'color-swatch' + (p.color_id === currentColorId ? ' selected' : '');
        btn.dataset.colorId = p.color_id;
        btn.title = p.name;
        btn.innerHTML = `<span class="swatch-color" style="background:${p.hex}"></span><span class="swatch-name">${p.name}</span>`;
        btn.addEventListener('click', () => selectColor(p.color_id));
        container.appendChild(btn);
    });
}

function setSliderValue(id, value) {
    const slider = document.getElementById(id);
    if (!slider) return;
    slider.value = value;
    const display = document.getElementById(id + '_val');
    if (display) display.textContent = value;
}

function applyPreset(colorId) {
    invalidateSingleResult();
    const p = colorPresets[colorId];
    if (!p) return;
    const hasHue = p.mode === 'hue';
    const [h1, h2] = [p.hue_ranges[0], p.hue_ranges[1] || null];
    // Hue: gán khoảng 1; khoảng 2 chỉ dùng cho màu có 2 khoảng (Đỏ)
    setSliderValue('h_min_1', hasHue ? h1[0] : 0);
    setSliderValue('h_max_1', hasHue ? h1[1] : 179);
    setSliderValue('h_min_2', hasHue && h2 ? h2[0] : 170);
    setSliderValue('h_max_2', hasHue && h2 ? h2[1] : 179);
    setSliderValue('s_min', p.saturation[0]);
    setSliderValue('s_max', p.saturation[1]);
    setSliderValue('v_min', p.value[0]);
    setSliderValue('v_max', p.value[1]);
    setHueControlsEnabled(hasHue, !!h2);

    const nameEl = document.getElementById('currentColorName');
    if (nameEl) nameEl.textContent = p.name;
}

function setHueControlsEnabled(hueEnabled, secondRangeEnabled) {
    ['h_min_1', 'h_max_1'].forEach(id => {
        const el = document.getElementById(id);
        if (el) el.disabled = !hueEnabled;
    });
    ['h_min_2', 'h_max_2'].forEach(id => {
        const el = document.getElementById(id);
        if (el) el.disabled = !(hueEnabled && secondRangeEnabled);
    });
}

function selectColor(colorId) {
    if (!colorPresets[colorId]) return;
    currentColorId = colorId;
    document.querySelectorAll('.color-swatch').forEach(b => {
        b.classList.toggle('selected', b.dataset.colorId === colorId);
    });
    applyPreset(colorId);
}

function resetPresetToColor() {
    applyPreset(currentColorId);
    showStatus(`↺ Đã khôi phục mặc định màu: ${colorPresets[currentColorId] ? colorPresets[currentColorId].name : currentColorId}`, 'info');
}

function releaseServerSession() {
    if (!currentSessionId) return;
    const body = JSON.stringify({ session_id: currentSessionId });
    try {
        navigator.sendBeacon('/api/release-session', new Blob([body], { type: 'application/json' }));
    } catch (e) { /* bỏ qua: TTL phía server sẽ dọn */ }
}

window.addEventListener('pagehide', releaseServerSession);

function exportResults() {
    if (!currentSessionId || currentRunId === null) {
        showStatus('❌ Vui lòng tải ảnh và xử lý trước khi export', 'error');
        return;
    }
    showStatus('📦 Đang export ZIP...', 'info');
    fetch('/api/export-results', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ session_id: currentSessionId, run_id: currentRunId }),
    })
    .then(response => {
        if (!response.ok) {
            return response.json().then(d => { throw new Error(d.error || 'Export thất bại'); });
        }
        return response.blob();
    })
    .then(blob => {
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `run_${currentRunId}_export.zip`;
        a.click();
        window.URL.revokeObjectURL(url);
        showStatus('✅ Export hoàn thành', 'success');
    })
    .catch(e => showStatus(`❌ Lỗi: ${e.message}`, 'error'));
}

function resetSession(cancelUpload = true) {
    if (cancelUpload) uploadSeq += 1;
    evaluateSeq += 1;
    releaseServerSession();
    currentRunId = null;
    currentSessionId = null;
    processSeq += 1;
    appliedMorphKey = null;
    cmpMarkStale('Phiên đã được đặt lại');
    clearMetricsStale();
    ['baMedian', 'baMorph'].forEach(id => { document.getElementById(id).src = ''; });
    document.getElementById('appliedConfigText').textContent = 'Chưa có kết quả xử lý.';
    morphUpdatePending();
    
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
    
    singleBusy = false;
    lastAppliedSummary = '';
    workflowNote = '';
    ['medianBefore', 'medianAfter', 'morphBefore', 'morphAfter'].forEach(id => {
        document.getElementById(id).removeAttribute('src');
        document.getElementById(id + 'Info').textContent = '';
    });
    updateWorkflowState();
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

// ===== Phase B: So sánh ngưỡng HSV =====
const CMP_MIN = 2, CMP_MAX = 6;
let cmpConfigs = [];        // snapshot cấu hình đang soạn (không đụng colorPresets)
let cmpResult = null;       // payload /api/compare-hsv gần nhất còn hợp lệ
let cmpResultSession = null;
let cmpRequestSeq = 0;      // chống kết quả bất đồng bộ đến muộn
let cmpCounter = 0;
let cmpBusy = false;

function cmpEsc(text) {
    const d = document.createElement('div');
    d.textContent = String(text);
    return d.innerHTML;
}

function cmpInitUi() {
    const target = document.getElementById('cmpTargetColor');
    const preset = document.getElementById('cmpPresetSelect');
    if (!target || !preset) return;
    target.innerHTML = '';
    preset.innerHTML = '';
    Object.values(colorPresets).forEach(p => {
        target.add(new Option(p.name, p.color_id));
        preset.add(new Option(p.name, p.color_id));
    });
    target.value = currentColorId;
    preset.value = currentColorId;
    cmpUpdateMorphSummary();
    ['cmpTargetColor', 'cmpStage', 'cmpMedianKernel'].forEach(id => {
        document.getElementById(id).addEventListener('change', () => cmpMarkStale('Tham số chung đã đổi'));
    });
    document.getElementById('cmpImportInput').addEventListener('change', cmpImport);
    if (cmpConfigs.length === 0) {
        cmpAddFromPreset(currentColorId);
        cmpAddFromPreset(currentColorId);
    }
    cmpRenderConfigs();
}

function cmpAddFromPreset(colorId) {
    const p = colorPresets[colorId];
    if (!p || cmpConfigs.length >= CMP_MAX) return false;
    cmpCounter += 1;
    cmpConfigs.push({
        config_id: `cfg${cmpCounter}`,
        name: `${p.name} #${cmpCounter}`,
        source_preset: p.color_id,
        hsv: {
            mode: p.mode,
            hue_ranges: p.hue_ranges.map(r => r.slice()),   // sao chép sâu, không tham chiếu preset
            saturation: p.saturation.slice(),
            value: p.value.slice(),
            hue_applied: p.mode === 'hue',
        },
    });
    return true;
}

function cmpAddConfig() {
    if (!cmpAddFromPreset(document.getElementById('cmpPresetSelect').value)) {
        showStatus(`⚠️ Tối đa ${CMP_MAX} cấu hình`, 'error');
        return;
    }
    cmpRenderConfigs();
    cmpMarkStale('Đã thêm cấu hình');
}

function cmpRemoveConfig(id) {
    if (cmpConfigs.length <= CMP_MIN) {
        showStatus(`⚠️ Cần tối thiểu ${CMP_MIN} cấu hình`, 'error');
        return;
    }
    cmpConfigs = cmpConfigs.filter(c => c.config_id !== id);
    cmpRenderConfigs();
    cmpMarkStale('Đã xóa cấu hình');
}

function cmpNumInput(id, path, value, max, disabled) {
    return `<input type="number" class="cmp-num" min="0" max="${max}" step="1" value="${value}"
        data-cfg="${cmpEsc(id)}" data-path="${path}" ${disabled ? 'disabled' : ''}>`;
}

function cmpRenderConfigs() {
    const list = document.getElementById('cmpConfigList');
    if (!list) return;
    list.innerHTML = '';
    cmpConfigs.forEach(cfg => {
        const h = cfg.hsv;
        const hueOn = h.mode === 'hue';
        const second = hueOn && h.hue_ranges.length > 1;
        const row = document.createElement('div');
        row.className = 'cmp-config';
        row.innerHTML = `
            <div class="cmp-config-head">
                <input type="text" class="cmp-name" maxlength="60" value="${cmpEsc(cfg.name)}" data-cfg="${cmpEsc(cfg.config_id)}" data-path="name">
                <span class="cmp-tag">${cmpEsc(cfg.source_preset || 'custom')} · ${hueOn ? 'hue' : 'sv'}</span>
                <button type="button" class="btn btn-secondary cmp-remove" data-remove="${cmpEsc(cfg.config_id)}">🗑️</button>
            </div>
            <div class="cmp-config-body">
                <span>H1 ${cmpNumInput(cfg.config_id, 'h0_0', h.hue_ranges[0][0], 179, !hueOn)} – ${cmpNumInput(cfg.config_id, 'h0_1', h.hue_ranges[0][1], 179, !hueOn)}</span>
                <span>H2 ${cmpNumInput(cfg.config_id, 'h1_0', second ? h.hue_ranges[1][0] : '', 179, !second)} – ${cmpNumInput(cfg.config_id, 'h1_1', second ? h.hue_ranges[1][1] : '', 179, !second)}</span>
                <span>S ${cmpNumInput(cfg.config_id, 's_0', h.saturation[0], 255, false)} – ${cmpNumInput(cfg.config_id, 's_1', h.saturation[1], 255, false)}</span>
                <span>V ${cmpNumInput(cfg.config_id, 'v_0', h.value[0], 255, false)} – ${cmpNumInput(cfg.config_id, 'v_1', h.value[1], 255, false)}</span>
            </div>`;
        list.appendChild(row);
    });
    list.querySelectorAll('input').forEach(el => el.addEventListener('change', cmpOnConfigEdit));
    list.querySelectorAll('[data-remove]').forEach(b =>
        b.addEventListener('click', () => cmpRemoveConfig(b.dataset.remove)));
    const count = document.getElementById('cmpCount');
    if (count) count.textContent = `${cmpConfigs.length}/${CMP_MAX} cấu hình`;
    const add = document.getElementById('cmpAddBtn');
    if (add) add.disabled = cmpConfigs.length >= CMP_MAX;
}

function cmpOnConfigEdit(e) {
    const el = e.target;
    const cfg = cmpConfigs.find(c => c.config_id === el.dataset.cfg);
    if (!cfg) return;
    const path = el.dataset.path;
    if (path === 'name') {
        cfg.name = el.value;
    } else {
        // Chỉ chấp nhận số nguyên thật; giá trị sai giữ nguyên chuỗi để server từ chối rõ ràng
        const raw = el.value.trim();
        const val = /^-?\d+$/.test(raw) ? parseInt(raw, 10) : raw;
        const [k, i] = path.split(/_/);
        const idx = parseInt(i, 10);
        if (k === 's') cfg.hsv.saturation[idx] = val;
        else if (k === 'v') cfg.hsv.value[idx] = val;
        else {
            const range = parseInt(k.slice(1), 10);
            cfg.hsv.hue_ranges[range][idx] = val;
        }
    }
    cmpMarkStale('Cấu hình đã chỉnh sửa');
}

function cmpShowBanner(id, message, kind) {
    const el = document.getElementById(id);
    if (!el) return;
    if (!message) { el.style.display = 'none'; el.textContent = ''; return; }
    el.className = 'cmp-banner' + (kind ? ' ' + kind : '');
    el.textContent = message;
    el.style.display = 'block';
}

function cmpMarkStale(reason) {
    // Mọi thay đổi đầu vào làm kết quả/đánh giá hiện có không còn khớp cấu hình
    cmpRequestSeq += 1;
    if (!cmpResult) return;
    cmpResult.stale = true;
    cmpShowBanner('cmpStale',
        `⚠️ Kết quả cũ (${reason}). Hãy chạy lại so sánh; không dùng bảng/biểu đồ dưới đây để kết luận.`, 'warn');
    const grid = document.getElementById('cmpGrid');
    if (grid) grid.classList.add('stale');
    const evalCard = document.getElementById('cmpEvalCard');
    if (evalCard) evalCard.classList.add('stale');
    const exp = document.getElementById('cmpExportBtn');
    if (exp) exp.disabled = true;
    const evalBtn = document.getElementById('cmpEvalBtn');
    if (evalBtn) evalBtn.disabled = true;
}

function cmpCollectPipeline() {
    // Dùng chung object morphology với tab Morphology
    return {
        median_kernel: parseInt(document.getElementById('cmpMedianKernel').value, 10),
        morphology: collectMorphology(),
    };
}

function cmpUpdateMorphSummary() {
    const el = document.getElementById('cmpMorphSummary');
    if (el) el.textContent = describeMorphology(collectMorphology());
}

function cmpSetBusy(busy) {
    cmpBusy = busy;
    ['cmpRunBtn', 'cmpAddBtn', 'cmpEvalBtn'].forEach(id => {
        const el = document.getElementById(id);
        if (el) el.disabled = busy || (id === 'cmpEvalBtn' && (!cmpResult || cmpResult.stale));
    });
    const run = document.getElementById('cmpRunBtn');
    if (run) run.textContent = busy ? '⏳ Đang chạy...' : '▶️ Chạy So Sánh';
    if (!busy) cmpRenderConfigs();
}

function cmpRun() {
    if (cmpBusy) return;
    if (!currentSessionId) {
        showStatus('❌ Hãy tải ảnh trước khi so sánh', 'error');
        return;
    }
    const payload = {
        session_id: currentSessionId,
        target_color_id: document.getElementById('cmpTargetColor').value,
        evaluation_stage: document.getElementById('cmpStage').value,
        fixed_pipeline: cmpCollectPipeline(),
        configurations: JSON.parse(JSON.stringify(cmpConfigs)),   // snapshot tại thời điểm bấm chạy
    };
    const seq = ++cmpRequestSeq;
    cmpSetBusy(true);
    cmpShowBanner('cmpBanner', '⏳ Đang chạy so sánh...', 'info');
    fetch('/api/compare-hsv', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload),
    })
    .then(r => r.json().then(d => ({ ok: r.ok, data: d })))
    .then(({ ok, data }) => {
        if (seq !== cmpRequestSeq) return;   // đầu vào đã đổi trong lúc chờ: bỏ kết quả đến muộn
        if (!ok || data.error) {
            cmpShowBanner('cmpBanner', `❌ ${data.error || 'Lỗi so sánh'}`, 'error');
            return;
        }
        cmpResult = data;
        cmpResult.stale = false;
        cmpResultSession = currentSessionId;
        cmpShowBanner('cmpBanner', data.all_ok
            ? '✅ So sánh hoàn tất'
            : '⚠️ Một số cấu hình lỗi; sẽ không xếp hạng hay công bố cấu hình tốt nhất.',
            data.all_ok ? 'success' : 'warn');
        cmpRenderResult();
    })
    .catch(e => {
        if (seq === cmpRequestSeq) cmpShowBanner('cmpBanner', `❌ Lỗi: ${e.message}`, 'error');
    })
    .finally(() => {
        cmpSetBusy(false);
    });
}

function cmpHsvText(h) {
    const hue = h.hue_applied
        ? h.hue_ranges.map(r => `${r[0]}–${r[1]}`).join(' ∪ ')
        : 'không áp dụng (0–179)';
    return `H: ${hue} | S: ${h.saturation[0]}–${h.saturation[1]} | V: ${h.value[0]}–${h.value[1]}`;
}

function cmpRenderResult() {
    const r = cmpResult;
    if (!r) return;
    document.getElementById('cmpResultCard').style.display = 'block';
    document.getElementById('cmpEvalCard').style.display = 'block';
    document.getElementById('cmpEvalCard').classList.remove('stale');
    document.getElementById('cmpGrid').classList.remove('stale');
    cmpShowBanner('cmpStale', '');
    document.getElementById('cmpExportBtn').disabled = false;
    document.getElementById('cmpEvalBtn').disabled = false;
    const grid = document.getElementById('cmpGrid');
    grid.innerHTML = '';
    r.results.forEach(item => {
        const cell = document.createElement('div');
        cell.className = 'cmp-cell';
        const body = item.status === 'ok'
            ? `<img src="${item.masks[r.evaluation_stage]}" alt="mask ${cmpEsc(item.name)}">
               <div class="cmp-meta">Pixel chọn: ${item.selected_pixels} · ${item.elapsed_ms} ms</div>`
            : `<div class="cmp-error">❌ ${cmpEsc(item.error || 'Lỗi không xác định')}</div>`;
        cell.innerHTML = `<h4>${cmpEsc(item.name)}</h4>${body}
            <div class="cmp-hsv">${cmpEsc(cmpHsvText(item.applied_config.hsv))}</div>`;
        grid.appendChild(cell);
    });
    cmpRenderEvaluation(r.evaluations && r.evaluations[r.evaluation_stage]);
}

const CMP_METRICS = [
    ['pixel_accuracy', 'Pixel Acc'], ['iou', 'IoU'], ['precision', 'Precision'],
    ['recall', 'Recall'], ['f1', 'F1'],
];

function cmpFmt(v) {
    return (v === null || v === undefined) ? 'N/A' : Number(v).toFixed(4);
}

function cmpEvaluate() {
    if (!cmpResult || cmpResult.stale) {
        showStatus('⚠️ Kết quả đã cũ, hãy chạy lại so sánh', 'error');
        return;
    }
    const file = document.getElementById('cmpGtInput').files[0];
    if (!file) { showStatus('❌ Chọn file GT (PNG)', 'error'); return; }
    if (!document.getElementById('cmpGtConfirm').checked) {
        showStatus('❌ Cần xác nhận cặp ảnh/GT/màu mục tiêu', 'error');
        return;
    }
    const form = new FormData();
    form.append('session_id', cmpResultSession);
    form.append('comparison_id', cmpResult.comparison_id);
    form.append('evaluation_stage', cmpResult.evaluation_stage);
    form.append('gt_pair_confirmed', 'true');
    form.append('ground_truth', file);
    const seq = cmpRequestSeq;
    const btn = document.getElementById('cmpEvalBtn');
    btn.disabled = true;
    btn.textContent = '⏳ Đang đánh giá...';
    fetch('/api/compare-hsv/evaluate', { method: 'POST', body: form })
    .then(r => r.json().then(d => ({ ok: r.ok, data: d })))
    .then(({ ok, data }) => {
        if (seq !== cmpRequestSeq) return;
        if (!ok || data.error) {
            cmpShowBanner('cmpEvalSummary', `❌ ${data.error || 'Lỗi đánh giá'}`, 'error');
            return;
        }
        cmpResult.evaluations = cmpResult.evaluations || {};
        cmpResult.evaluations[data.evaluation.stage] = data.evaluation;
        cmpRenderEvaluation(data.evaluation);
    })
    .catch(e => cmpShowBanner('cmpEvalSummary', `❌ Lỗi: ${e.message}`, 'error'))
    .finally(() => {
        btn.textContent = '📈 Đánh giá';
        btn.disabled = !cmpResult || !!cmpResult.stale;
    });
}

function cmpRenderEvaluation(ev) {
    const table = document.getElementById('cmpTable');
    const chart = document.getElementById('cmpChart');
    table.innerHTML = '';
    chart.innerHTML = '';
    if (!ev) {
        cmpShowBanner('cmpEvalSummary', 'ℹ️ Chưa đánh giá: metrics là N/A, không có cấu hình tốt nhất.', 'info');
        return;
    }
    const rankMap = {};
    (ev.ranking || []).forEach(x => { rankMap[x.config_id] = x.rank; });
    const best = ev.best_config_ids || [];
    const nameOf = id => (cmpResult.results.find(x => x.config_id === id) || {}).name || id;
    const kind = ev.status === 'ok' ? 'success' : 'warn';
    let summary = ev.reason;
    if (ev.status === 'ok') {
        summary = best.length > 1
            ? `🏆 Đồng hạng nhất: ${best.map(nameOf).join(', ')} (IoU rồi F1)`
            : `🏆 Tốt nhất: ${nameOf(best[0])} (IoU rồi F1)`;
    }
    cmpShowBanner('cmpEvalSummary', summary, kind);

    let html = '<thead><tr><th>Hạng</th><th>Cấu hình</th>'
        + CMP_METRICS.map(m => `<th>${m[1]}</th>`).join('') + '</tr></thead><tbody>';
    cmpResult.results.forEach(item => {
        const m = ev.metrics[item.config_id];
        html += `<tr class="${best.includes(item.config_id) ? 'best' : ''}">
            <td>${rankMap[item.config_id] !== undefined ? rankMap[item.config_id] : 'N/A'}</td>
            <td>${cmpEsc(item.name)}</td>`
            + CMP_METRICS.map(c => `<td>${m ? cmpFmt(m[c[0]]) : 'N/A'}</td>`).join('') + '</tr>';
    });
    table.innerHTML = html + '</tbody>';

    if (!cmpResult.results.some(i => ev.metrics[i.config_id])) return;
    const colors = ['#2a6fdb', '#e8772e', '#2f9e44', '#9c36b5', '#c92a2a', '#0b7285'];
    let svg = '';
    CMP_METRICS.forEach((c, mi) => {
        svg += `<div class="cmp-chart-group"><div class="cmp-chart-title">${c[1]}</div>`;
        cmpResult.results.forEach((item, ci) => {
            const m = ev.metrics[item.config_id];
            const v = m ? Number(m[c[0]]) : null;
            const pct = v === null ? 0 : Math.max(0, Math.min(1, v)) * 100;
            svg += `<div class="cmp-bar-row"><span class="cmp-bar-label">${cmpEsc(item.name)}</span>
                <span class="cmp-bar-track"><span class="cmp-bar" style="width:${pct}%;background:${colors[ci % colors.length]}"></span></span>
                <span class="cmp-bar-val">${v === null ? 'N/A' : v.toFixed(3)}</span></div>`;
        });
        svg += '</div>';
    });
    chart.innerHTML = svg;
}

function cmpExport() {
    if (!cmpResult || cmpResult.stale) {
        showStatus('⚠️ Kết quả đã cũ, hãy chạy lại trước khi xuất', 'error');
        return;
    }
    fetch('/api/compare-hsv/export', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ session_id: cmpResultSession, comparison_id: cmpResult.comparison_id }),
    })
    .then(r => {
        if (!r.ok) return r.json().then(d => { throw new Error(d.error || 'Lỗi export'); });
        return r.blob();
    })
    .then(blob => {
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `${cmpResult.comparison_id}.zip`;
        document.body.appendChild(a);
        a.click();
        a.remove();
        URL.revokeObjectURL(url);
        showStatus('✅ Đã xuất ZIP so sánh', 'success');
    })
    .catch(e => showStatus(`❌ ${e.message}`, 'error'));
}

function cmpImport() {
    const input = document.getElementById('cmpImportInput');
    const file = input.files[0];
    if (!file) return;
    if (!currentSessionId) {
        showStatus('❌ Hãy tải ảnh trước khi nhập cấu hình', 'error');
        input.value = '';
        return;
    }
    const form = new FormData();
    form.append('session_id', currentSessionId);
    form.append('config_file', file);
    const seq = ++cmpRequestSeq;
    cmpSetBusy(true);
    fetch('/api/compare-hsv/import-config', { method: 'POST', body: form })
    .then(r => r.json().then(d => ({ ok: r.ok, data: d })))
    .then(({ ok, data }) => {
        if (seq !== cmpRequestSeq) return;
        if (!ok || data.error) {
            cmpShowBanner('cmpBanner', `❌ ${data.error || 'Lỗi nhập cấu hình'}`, 'error');
            return;
        }
        // Khôi phục cấu hình/pipeline vào form từ kết quả đã được server kiểm tra
        cmpConfigs = data.results.map(it => JSON.parse(JSON.stringify(it.applied_config)));
        document.getElementById('cmpTargetColor').value = data.target_color_id;
        document.getElementById('cmpStage').value = data.evaluation_stage;
        const p = data.fixed_pipeline;
        document.getElementById('cmpMedianKernel').value = p.median_kernel;
        setMorphologyControls(p.morphology || {
            kernel_size: p.morph_kernel, kernel_shape: p.kernel_shape,
            operations: p.operations.map(o => ({ operation: o.op, iterations: o.iterations })),
        });
        cmpUpdateMorphSummary();
        cmpRenderConfigs();
        cmpResult = data;
        cmpResult.stale = false;
        cmpResultSession = currentSessionId;
        const imp = data.import || {};
        const msg = imp.image_hash_match
            ? '✅ Đã nhập và chạy lại; hash ảnh khớp. Metrics trong file chỉ là dữ liệu lịch sử, không phải kết quả mới.'
            : `⚠️ ${imp.warning || 'Hash ảnh không khớp'}`;
        cmpRenderResult();
        cmpShowBanner('cmpBanner', msg, imp.image_hash_match ? 'success' : 'warn');
    })
    .catch(e => {
        if (seq === cmpRequestSeq) cmpShowBanner('cmpBanner', `❌ Lỗi: ${e.message}`, 'error');
    })
    .finally(() => {
        input.value = '';
        cmpSetBusy(false);
    });
}

// Handle Enter key in sliders to trigger processing
document.addEventListener('keypress', (e) => {
    if (e.key === 'Enter' && document.activeElement.classList.contains('slider')) {
        processImage();
    }
});
