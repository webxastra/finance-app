// Adds logic to handle the AI Module toggle on login

document.addEventListener('DOMContentLoaded', function() {
    const aiToggle = document.getElementById('ai-module-toggle');
    const loginForm = document.querySelector('.login-form form');
    if (!aiToggle || !loginForm) return;

    loginForm.addEventListener('submit', function(e) {
        // If AI Module is selected, add a hidden input to indicate this
        if (aiToggle.checked) {
            let aiInput = document.getElementById('ai-module-input');
            if (!aiInput) {
                aiInput = document.createElement('input');
                aiInput.type = 'hidden';
                aiInput.name = 'ai_module';
                aiInput.id = 'ai-module-input';
                loginForm.appendChild(aiInput);
            }
            aiInput.value = '1';
        }
    });
});
