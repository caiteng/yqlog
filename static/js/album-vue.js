(() => {
  const mountNode = document.getElementById("albumApp");
  if (!mountNode || !window.Vue) {
    return;
  }

  const { createApp } = window.Vue;

  createApp({
    delimiters: ["[[", "]]"],
    data() {
      return {
        previews: [],
        submitting: false,
      };
    },
    methods: {
      onFilesChange(event) {
        const files = Array.from(event.target.files || []).slice(0, 12);
        this.previews = files
          .filter((file) => file.type.startsWith("image/"))
          .map((file) => ({
            name: file.name,
            url: URL.createObjectURL(file),
          }));
      },
      onSubmit() {
        this.submitting = true;
      },
    },
  }).mount("#albumApp");
})();
