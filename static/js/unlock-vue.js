(() => {
  const mountNode = document.getElementById("unlockApp");
  if (!mountNode || !window.Vue) {
    return;
  }

  const { createApp } = window.Vue;

  createApp({
    delimiters: ["[[", "]]"],
    data() {
      return {
        password: "",
        showPassword: false,
        submitting: false,
      };
    },
    methods: {
      togglePassword() {
        this.showPassword = !this.showPassword;
      },
      onSubmit() {
        this.submitting = true;
      },
    },
  }).mount("#unlockApp");
})();
