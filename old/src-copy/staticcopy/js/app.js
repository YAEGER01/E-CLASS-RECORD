const loginForm = document.getElementById('loginForm');
    const loginBtn = document.getElementById('loginBtn');
    const successMessage = document.getElementById('successMessage');
    const errorMessage = document.getElementById('errorMessage');
    const togglePass = document.getElementById('togglePass');
    const passwordInput = document.getElementById('password');
    const roleSelect = document.getElementById('role');

    // Demo credentials for the prototype
    const validCredentials = {
      'admin': 'admin123',
      'faculty@isu.edu.ph': 'faculty123',
      'student@isu.edu.ph': 'student123'
    };

    // Toggle password visibility
    togglePass.addEventListener('click', () => {
      const type = passwordInput.type === 'password' ? 'text' : 'password';
      passwordInput.type = type;
      togglePass.textContent = type === 'password' ? '👁️' : '🙈';
    });

    // Helper to set UI states
    function setLoading(isLoading) {
      if (isLoading) {
        loginBtn.textContent = 'Signing In...';
        loginBtn.disabled = true;
        loginBtn.classList.add('loading');
      } else {
        loginBtn.textContent = 'Sign In';
        loginBtn.disabled = false;
        loginBtn.classList.remove('loading');
      }
    }

    function showSuccess(message) {
      successMessage.textContent = message;
      successMessage.style.display = 'block';
      errorMessage.style.display = 'none';
    }

    function showError(message) {
      errorMessage.textContent = message;
      errorMessage.style.display = 'block';
      successMessage.style.display = 'none';
    }

    // Form submission (simulated)
    loginForm.addEventListener('submit', (e) => {
      e.preventDefault();
      const username = document.getElementById('username').value.trim();
      const password = document.getElementById('password').value;
      const role = roleSelect.value;

      // Clear previous messages
      successMessage.style.display = 'none';
      errorMessage.style.display = 'none';

      // Simple validation
      if (!username || !password) {
        showError('Please fill in both fields.');
        return;
      }

      setLoading(true);

      // Simulate API latency
      setTimeout(() => {
        // Role-based acceptance logic for prototype:
        // admin can sign in with admin, faculty with faculty email, student with student email
        const isValid =
          (username === 'admin' && password === validCredentials['admin'] && role === 'admin') ||
          (username === 'faculty@isu.edu.ph' && password === validCredentials['faculty@isu.edu.ph'] && role === 'faculty') ||
          (username === 'student@isu.edu.ph' && password === validCredentials['student@isu.edu.ph'] && role === 'student');

        if (isValid) {
          showSuccess('Login successful. Redirecting to dashboard...');
          loginBtn.style.background = '';
          setTimeout(() => {
            // In a real app, you'd redirect to the dashboard. Here we just reset form.
            alert('Prototype: would redirect to dashboard now.');
            setLoading(false);
            loginForm.reset();
            successMessage.style.display = 'none';
          }, 1200);
        } else {
          showError('Invalid credentials for the selected role.');
          setLoading(false);
        }
      }, 900);
    });

    // Small UX: press Enter inside password toggles login
    passwordInput.addEventListener('keyup', (e) => {
      if (e.key === 'Enter') {
        loginBtn.click();
      }
    });
