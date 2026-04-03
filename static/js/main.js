(function () {
  const photoInput = document.getElementById('photoInput');
  const photoPreview = document.getElementById('photoPreview');
  const growthForm = document.getElementById('growthForm');

  if (photoInput && photoPreview) {
    photoInput.addEventListener('change', () => {
      photoPreview.innerHTML = '';
      const files = Array.from(photoInput.files || []).slice(0, 8);
      files.forEach((file) => {
        if (!file.type.startsWith('image/')) return;
        const img = document.createElement('img');
        img.src = URL.createObjectURL(file);
        img.alt = `预览-${file.name}`;
        photoPreview.appendChild(img);
      });
    });
  }

  if (growthForm) {
    growthForm.addEventListener('submit', () => {
      const submitButton = growthForm.querySelector('button[type="submit"]');
      if (submitButton) {
        submitButton.disabled = true;
        submitButton.textContent = '提交中...';
      }
    });
  }
})();
