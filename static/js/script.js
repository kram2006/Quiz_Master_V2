// Prevent back button during quiz
function preventBackDuringQuiz() {
    if (document.getElementById('quiz-form')) {
      history.pushState(null, null, location.href);
      window.onpopstate = function() {
        history.go(1);
        alert("Warning: You cannot navigate away from this quiz without submitting your answers.");
      };
    }
  }
  
  // Initialize on page load
  document.addEventListener('DOMContentLoaded', function() {
    preventBackDuringQuiz();
  
    // Find all quiz cards and add hover effect
    const quizCards = document.querySelectorAll('.quiz-card');
    if (quizCards) {
      quizCards.forEach(card => {
        card.addEventListener('mouseenter', function() {
          this.classList.add('shadow-lg');
        });
        card.addEventListener('mouseleave', function() {
          this.classList.remove('shadow-lg');
        });
      });
    }
  });
  
  
  // Function to initialize all UI enhancements
  document.addEventListener('DOMContentLoaded', function() {
      // Highlight current page in navigation
      highlightCurrentPage();
  
      // Add icons to various UI elements
      addIconsToNavigation();
      addIconsToFeatureCards();
      addIconsToButtons();
  
      // Run other initialization functions
      animateCards();
      setupFormAnimations();
      highlightCorrectAnswers();
      animateSubmitButton();
      initQuizTimer(); //This function is replaced
      animateProgressBars();
  
      // Add animation to jumbotron
      const jumbotron = document.querySelector('.jumbotron');
      if (jumbotron) {
          jumbotron.classList.add('animate__animated', 'animate__fadeIn');
      }
  
      // Animate stat values if they exist
      animateStatValues();
  
      // Add floating effect to cards
      addFloatingEffect();
  });
  
  // Highlight current page in navigation
  function highlightCurrentPage() {
      const currentLocation = window.location.pathname;
      const navLinks = document.querySelectorAll('.navbar-nav .nav-link');
  
      navLinks.forEach(link => {
          const href = link.getAttribute('href');
          if (href && currentLocation.includes(href) && href !== '/') {
              link.classList.add('active');
          }
      });
  }
  
  // Add icons to navigation links
  function addIconsToNavigation() {
      const navMapping = {
          'Home': '<i class="fas fa-home me-2"></i>',
          'Dashboard': '<i class="fas fa-tachometer-alt me-2"></i>',
          'Subjects': '<i class="fas fa-book me-2"></i>',
          'Chapters': '<i class="fas fa-bookmark me-2"></i>',
          'Quizzes': '<i class="fas fa-question-circle me-2"></i>',
          'Users': '<i class="fas fa-users me-2"></i>',
          'My History': '<i class="fas fa-history me-2"></i>',
          'Login': '<i class="fas fa-sign-in-alt me-2"></i>',
          'Register': '<i class="fas fa-user-plus me-2"></i>',
          'Logout': '<i class="fas fa-sign-out-alt me-2"></i>'
      };
  
      const navLinks = document.querySelectorAll('.navbar-nav .nav-link');
      navLinks.forEach(link => {
          const text = link.textContent.trim();
          if (navMapping[text]) {
              link.innerHTML = navMapping[text] + text;
          }
      });
  
      // Also add icon to navbar brand
      const brand = document.querySelector('.navbar-brand');
      if (brand) {
          brand.innerHTML = '<i class="fas fa-graduation-cap me-2"></i>' + brand.textContent;
      }
  }
  
  // Add icons to feature cards on homepage
  function addIconsToFeatureCards() {
      const featureCards = document.querySelectorAll('.card .card-title');
      const icons = {
          'Multiple Subjects': '<i class="fas fa-books me-2"></i>',
          'Track Your Progress': '<i class="fas fa-chart-line me-2"></i>',
          'Challenge Yourself': '<i class="fas fa-trophy me-2"></i>'
      };
  
      featureCards.forEach(title => {
          const text = title.textContent.trim();
          if (icons[text]) {
              title.innerHTML = icons[text] + text;
          }
      });
  }
  
  // Add icons to buttons
  function addIconsToButtons() {
      const buttonMapping = {
          'Submit': '<i class="fas fa-paper-plane me-2"></i>',
          'Save': '<i class="fas fa-save me-2"></i>',
          'Delete': '<i class="fas fa-trash-alt me-2"></i>',
          'Edit': '<i class="fas fa-edit me-2"></i>',
          'Add': '<i class="fas fa-plus me-2"></i>',
          'View': '<i class="fas fa-eye me-2"></i>',
          'Back': '<i class="fas fa-arrow-left me-2"></i>',
          'Login': '<i class="fas fa-sign-in-alt me-2"></i>',
          'Register': '<i class="fas fa-user-plus me-2"></i>'
      };
  
      const buttons = document.querySelectorAll('.btn');
      buttons.forEach(button => {
          const text = button.textContent.trim();
  
          for (const [key, icon] of Object.entries(buttonMapping)) {
              if (text.includes(key)) {
                  button.innerHTML = icon + text;
                  break;
              }
          }
      });
  }
  
  // Animate cards with staggered effect
  function animateCards() {
      const cards = document.querySelectorAll('.card');
      if (cards.length > 0) {
          cards.forEach((card, index) => {
              setTimeout(() => {
                  card.classList.add('animate__animated', 'animate__fadeInUp');
              }, index * 100);
          });
      }
  }
  
  // Set up form animations
  function setupFormAnimations() {
      const formControls = document.querySelectorAll('.form-control');
      formControls.forEach(control => {
          control.addEventListener('focus', function() {
              this.parentElement.classList.add('animate__animated', 'animate__pulse');
          });
  
          control.addEventListener('blur', function() {
              this.parentElement.classList.remove('animate__animated', 'animate__pulse');
          });
      });
  }
  
  // Highlight correct answers in quiz results
  function highlightCorrectAnswers() {
      const correctOptions = document.querySelectorAll('.correct-option');
      const userOptions = document.querySelectorAll('.user-option');
  
      correctOptions.forEach(option => {
          option.innerHTML = '<i class="fas fa-check-circle text-success me-2"></i>' + option.innerHTML;
      });
  
      userOptions.forEach(option => {
          if (option.classList.contains('correct')) {
              option.innerHTML = '<i class="fas fa-check-circle text-success me-2"></i>' + option.innerHTML;
          } else {
              option.innerHTML = '<i class="fas fa-times-circle text-danger me-2"></i>' + option.innerHTML;
          }
      });
  }
  
  // Animate submit button
  function animateSubmitButton() {
      const submitBtn = document.querySelector('button[type="submit"]');
      if (submitBtn) {
          submitBtn.addEventListener('mouseenter', function() {
              this.classList.add('pulse');
          });
  
          submitBtn.addEventListener('mouseleave', function() {
              this.classList.remove('pulse');
          });
      }
  }
  
  // Initialize quiz timer if available
  let timerInterval; // Declare timerInterval in the outer scope
  
  function initQuizTimer() {
      const timerElement = document.getElementById('timer');
      if (timerElement) {
          // Parse initial time from timer element (e.g. "10:00")
          let initialTime = timerElement.textContent.split(':');
          let minutes = parseInt(initialTime[0]) || 0;
          let seconds = parseInt(initialTime[1]) || 0;
          let timeLimit = (minutes * 60) + seconds;
  
          // Update the timer every second
          timerInterval = setInterval(function() {
              timeLimit--;
  
              // Display the time in MM:SS format
              let mins = Math.floor(timeLimit / 60);
              let secs = timeLimit % 60;
              timerElement.textContent = mins + ':' + (secs < 10 ? '0' : '') + secs;
  
              // Visual indication when time is running out
              if (timeLimit <= 60) { // Last minute
                  timerElement.parentElement.classList.add('bg-danger');
                  timerElement.parentElement.classList.remove('bg-primary');
              }
  
              // Automatically submit the form when time runs out
              if (timeLimit <= 0) {
                  clearInterval(timerInterval);
                  alert('Time is up! Your quiz will be submitted automatically.');
                  const quizForm = document.getElementById('quiz-form');
                  if(quizForm) quizForm.submit();
              }
          }, 1000);
      }
  }
  
  // Animate progress bars
  function animateProgressBars() {
      const progressBars = document.querySelectorAll('.progress-bar');
      if (progressBars.length > 0) {
          progressBars.forEach(bar => {
              const value = bar.getAttribute('aria-valuenow');
              bar.style.width = '0%';
              setTimeout(() => {
                  bar.style.width = value + '%';
              }, 300);
          });
      }
  }
  
  // Animate stat values with counting effect
  function animateStatValues() {
      const statValues = document.querySelectorAll('.stat-value');
      if (statValues.length > 0) {
          statValues.forEach(stat => {
              const finalValue = parseInt(stat.textContent);
              let startValue = 0;
              const duration = 1500;
              const frameRate = 30;
              const increment = finalValue / (duration / frameRate);
  
              const counter = setInterval(() => {
                  startValue += increment;
                  if (startValue >= finalValue) {
                      stat.textContent = finalValue;
                      clearInterval(counter);
                  } else {
                      stat.textContent = Math.floor(startValue);
                  }
              }, frameRate);
          });
      }
  }
  
  // Add subtle floating effect to cards
  function addFloatingEffect() {
      const cards = document.querySelectorAll('.card');
      if (cards.length > 0) {
          cards.forEach(card => {
              card.addEventListener('mouseenter', function() {
                  this.style.transform = 'translateY(-10px)';
                  this.style.boxShadow = '0 20px 30px rgba(0, 0, 0, 0.12)';
              });
  
              card.addEventListener('mouseleave', function() {
                  this.style.transform = '';
                  this.style.boxShadow = '';
              });
          });
      }
  }
  
  // Quiz timer functionality
  function startTimer(minutes) {
      const timerElement = document.getElementById('timer');
      if (!timerElement) return; // Exit if timer element doesn't exist
  
      let totalSeconds = minutes * 60;
  
      timerInterval = setInterval(function() {
          totalSeconds--;
  
          if (totalSeconds <= 0) {
              clearInterval(timerInterval);
              const quizForm = document.getElementById('quiz-form');
              if (quizForm) quizForm.submit();
              return;
          }
  
          const minutesRemaining = Math.floor(totalSeconds / 60);
          const secondsRemaining = totalSeconds % 60;
  
          timerElement.textContent = `${minutesRemaining}:${secondsRemaining < 10 ? '0' : ''}${secondsRemaining}`;
  
          // Change color when time is running out
          if (totalSeconds < 60) {
              timerElement.classList.remove('bg-warning');
              timerElement.classList.add('bg-danger');
          }
      }, 1000);
  }
  
  
  // Handle beforeunload event to prevent users from navigating away
  window.addEventListener('beforeunload', function(e) {
      // Only add the warning if we're on a quiz page with an active timer
      const quizForm = document.getElementById('quiz-form');
      if (quizForm && timerInterval) {
          // Submit the form instead of showing a warning
          quizForm.submit();
  
          // Cancel the event
          e.preventDefault();
          // Chrome requires returnValue to be set
          e.returnValue = '';
      }
  });