
    document.addEventListener('DOMContentLoaded', function() {
      function setupProfileSlider(sliderId) {
        const slider = document.getElementById(sliderId);
        if (!slider) return;
        const leftImage = slider.querySelector('.image-left');
        const rightImage = slider.querySelector('.image-right');

        function updateSplit(clientX) {
          const rect = slider.getBoundingClientRect();
          let offsetX = clientX - rect.left;
          offsetX = Math.max(0, Math.min(offsetX, rect.width)); // clamp
          const percent = (offsetX / rect.width) * 100;
          leftImage.style.clipPath = `polygon(0 0, ${percent}% 0, ${percent}% 100%, 0% 100%)`;
          rightImage.style.clipPath = `polygon(${percent}% 0, 100% 0, 100% 100%, ${percent}% 100%)`;
        }

        slider.addEventListener('mousemove', function(e) {
          updateSplit(e.clientX);
        });

        // Touch support
        slider.addEventListener('touchmove', function(e) {
          if (e.touches && e.touches.length > 0) {
            updateSplit(e.touches[0].clientX);
          }
        });

        slider.addEventListener('mouseleave', function() {
          leftImage.style.clipPath = 'polygon(0 0, 50% 0, 50% 100%, 0% 100%)';
          rightImage.style.clipPath = 'polygon(50% 0, 100% 0, 100% 100%, 50% 100%)';
        });

        slider.addEventListener('touchend', function() {
          leftImage.style.clipPath = 'polygon(0 0, 50% 0, 50% 100%, 0% 100%)';
          rightImage.style.clipPath = 'polygon(50% 0, 100% 0, 100% 100%, 50% 100%)';
        });
      }
      setupProfileSlider('profileSlider');
      setupProfileSlider('profileSlider_2');
    });
