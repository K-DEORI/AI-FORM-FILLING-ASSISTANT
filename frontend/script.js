document.addEventListener('DOMContentLoaded', function() {
    console.log('✅ Template-aware form filling ready!');
    
    // Elements
    const uploadBtn = document.getElementById('uploadBtn');
    const fileInput = document.getElementById('fileInput');
    const uploadArea = document.getElementById('uploadArea');
    const status = document.getElementById('status');
    const resultsSection = document.getElementById('resultsSection');
    const downloadBtn = document.getElementById('downloadBtn');
    const newFileBtn = document.getElementById('newFileBtn');
    const templateSelect = document.getElementById('templateSelect');
    const dynamicFieldsContainer = document.getElementById('dynamicFieldsContainer');
    const templateFieldsCount = document.getElementById('templateFieldsCount');
    const activeTemplateName = document.getElementById('activeTemplateName');
    const docInfo = document.getElementById('docInfo');
    const output = document.getElementById('output');

    let currentSessionId = '';
    let currentResult = null;
    let currentTemplate = 'standard';

    // Template field definitions
    const TEMPLATE_FIELDS = {
        standard: [
            {key: 'full_name', label: 'Full Name', icon: '👤'},
            {key: 'dob', label: 'Date of Birth', icon: '🎂'},
            {key: 'address', label: 'Address', icon: '🏠', fullWidth: true},
            {key: 'aadhaar', label: 'Aadhaar Number', icon: '🆔'},
            {key: 'pan', label: 'PAN Number', icon: '💳'},
            {key: 'phone', label: 'Phone Number', icon: '📞'}
        ],
        aadhaar: [
            {key: 'full_name', label: 'Full Name', icon: '👤'},
            {key: 'dob', label: 'Date of Birth', icon: '🎂'},
            {key: 'address', label: 'Address', icon: '🏠', fullWidth: true},
            {key: 'aadhaar', label: 'Aadhaar Number', icon: '🆔'}
        ],
        pan: [
            {key: 'full_name', label: 'Full Name', icon: '👤'},
            {key: 'dob', label: 'Date of Birth', icon: '🎂'},
            {key: 'address', label: 'Address', icon: '🏠', fullWidth: true},
            {key: 'pan', label: 'PAN Number', icon: '💳'},
            {key: 'phone', label: 'Phone Number', icon: '📞'}
        ]
    };

    // Event listeners
    uploadBtn.addEventListener('click', () => fileInput.click());
    fileInput.addEventListener('change', handleFileSelect);
    newFileBtn.addEventListener('click', resetForm);
    downloadBtn.addEventListener('click', handleDownload);
    templateSelect.addEventListener('change', handleTemplateChange);

    // Drag & drop
    uploadArea.addEventListener('click', () => fileInput.click());
    ['dragover', 'dragenter'].forEach(event => {
        uploadArea.addEventListener(event, e => {
            e.preventDefault();
            e.stopPropagation();
            uploadArea.classList.add('dragover');
        });
    });
    ['dragleave', 'drop'].forEach(event => {
        uploadArea.addEventListener(event, e => {
            e.preventDefault();
            uploadArea.classList.remove('dragover');
            if (event === 'drop' && e.dataTransfer.files.length) {
                fileInput.files = e.dataTransfer.files;
                handleFileSelect();
            }
        });
    });

    // Initialize
    updateTemplateDisplay();
    renderTemplateFields('standard');

    function handleTemplateChange() {
        currentTemplate = templateSelect.value;
        updateTemplateDisplay();
        renderTemplateFields(currentTemplate);
        if (currentResult) {
            fillFields(currentResult.filled_form);
            showDocInfo(currentResult);
        }
    }

    function updateTemplateDisplay() {
        const option = templateSelect.options[templateSelect.selectedIndex];
        templateFieldsCount.textContent = `(${option.dataset.fields || TEMPLATE_FIELDS[currentTemplate].length} fields)`;
        activeTemplateName.textContent = option.text.split(' (')[0];
    }

    function renderTemplateFields(template) {
        dynamicFieldsContainer.innerHTML = '';
        const fields = TEMPLATE_FIELDS[template] || TEMPLATE_FIELDS.standard;
        
        fields.forEach(field => {
            const div = document.createElement('div');
            div.className = `field-item ${field.fullWidth ? 'full-width' : ''}`;
            div.innerHTML = `
                <label>${field.icon} ${field.label}</label>
                <div class="field-value" data-field="${field.key}">Not processed</div>
            `;
            dynamicFieldsContainer.appendChild(div);
        });
    }

    function handleFileSelect() {
        if (fileInput.files.length > 0) {
            const file = fileInput.files[0];
            console.log('Processing file:', file.name);
            processFile(file);
        }
    }

    async function processFile(file) {
        if (!/\.(jpg|jpeg|png|pdf)$/i.test(file.name)) {
            showStatus('Please upload JPG, PNG, or PDF!', 'error');
            return;
        }

        showStatus('🔍 Processing with OCR...', 'loading');
        uploadBtn.disabled = true;
        uploadBtn.textContent = 'Processing...';

        try {
            const formData = new FormData();
            formData.append('file', file);
            formData.append('template', currentTemplate);

            const response = await fetch('http://127.0.0.1:8000/process', {
                method: 'POST',
                body: formData
            });

            if (!response.ok) {
                throw new Error(`Server error: ${response.status}`);
            }

            const text = await response.text();
            const data = JSON.parse(text);

            if (data.status === 'success') {
                currentResult = data;
                currentSessionId = `doc_${Date.now()}`;
                fillFields(data.filled_form);
                showDocInfo(data);
                resultsSection.style.display = 'block';
                resultsSection.scrollIntoView({ behavior: 'smooth' });
                showStatus(`✅ Success! ${Object.values(data.filled_form).filter(Boolean).length}/${Object.keys(data.filled_form).length-2} fields found`, 'success');
            } else {
                throw new Error(data.message || 'Processing failed');
            }
        } catch (error) {
            console.error('Error:', error);
            const msg = error.message.includes('fetch') ? 'Server not running on port 8000' : error.message;
            showStatus(msg, 'error');
            output.textContent = `Error: ${error.message}\n\nResponse: ${text?.substring(0, 200) || 'No response'}`;
            document.getElementById('debugSection').style.display = 'block';
        } finally {
            uploadBtn.disabled = false;
            uploadBtn.textContent = 'Process Document';
        }
    }

    function fillFields(data) {
        dynamicFieldsContainer.querySelectorAll('.field-value').forEach(field => {
            const key = field.dataset.field;
            const value = data[key] || '';
            field.textContent = value || 'Not found';
            field.parentElement.classList.toggle('field-filled', !!value);
        });
    }

    function showDocInfo(data) {
        docInfo.innerHTML = `
            <div><strong>📄 File:</strong> ${data.filename}</div>
            <div><strong>🌐 Language:</strong> ${data.language?.toUpperCase()}</div>
            <div><strong>📄 Pages:</strong> ${data.page_count || 1}</div>
            <div><strong>📋 Template:</strong> ${data.template?.toUpperCase()}</div>
        `;
    }

    function handleDownload() {
        if (!currentSessionId) {
            showStatus('No results to download!', 'error');
            return;
        }
        window.open(`http://127.0.0.1:8000/download/${currentSessionId}?template=${currentTemplate}`, '_blank');
        showStatus('📥 PDF downloading...', 'success');
    }

    function resetForm() {
        fileInput.value = '';
        resultsSection.style.display = 'none';
        renderTemplateFields(currentTemplate);
        currentResult = null;
        currentSessionId = '';
        showStatus('Ready for new document', 'success');
    }

    function showStatus(msg, type) {
        status.textContent = msg;
        status.className = `status ${type}`;
        status.style.display = 'block';
        if (type !== 'loading') {
            setTimeout(() => {
                if (status.classList.contains(type)) {
                    status.style.display = 'none';
                }
            }, 4000);
        }
    }
});
