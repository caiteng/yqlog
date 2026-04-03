(() => {
  const mountNode = document.getElementById("submitApp");
  if (!mountNode || !window.Vue) {
    return;
  }

  const { createApp } = window.Vue;

  createApp({
    delimiters: ["[[", "]]"],
    data() {
      return {
        form: {
          record_date: "",
          height_cm: "",
          weight_kg: "",
          head_circumference_cm: "",
          note: "",
        },
        previews: [],
        submitting: false,
      };
    },
    methods: {
      onFilesChange(event) {
        const files = Array.from(event.target.files || []).slice(0, 8);
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
  }).mount("#submitApp");
})();
