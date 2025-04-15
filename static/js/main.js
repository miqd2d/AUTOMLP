document.addEventListener('DOMContentLoaded', function() {
    // File upload interaction
    const fileInput = document.getElementById('file');
    const fileLabel = document.querySelector('.file-upload-label');
    
    if (fileInput && fileLabel) {
        fileInput.addEventListener('change', function() {
            if (this.files && this.files.length > 0) {
                fileLabel.textContent = this.files[0].name;
                fileLabel.style.color = '#f5f6fa';
            }
        });
    }
    
    // Close flash messages
    document.querySelectorAll('.flash-close').forEach(button => {
        button.addEventListener('click', function() {
            this.parentElement.style.animation = 'slideIn 0.3s ease-out reverse';
            setTimeout(() => {
                this.parentElement.remove();
            }, 300);
        });
    });
    
    // Auto-remove flash messages after 5 seconds
    setTimeout(() => {
        document.querySelectorAll('.flash').forEach(flash => {
            flash.style.animation = 'slideIn 0.3s ease-out reverse';
            setTimeout(() => {
                flash.remove();
            }, 300);
        });
    }, 5000);
});