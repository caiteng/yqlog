(() => {
  const mountNode = document.getElementById("albumApp");
  if (!mountNode || !window.Vue) {
    return;
  }

  const { createApp } = window.Vue;
  const config = window.albumConfig || { albumCurrentCount: 0, albumMaxPhotos: 200 };

  createApp({
    delimiters: ["[[", "]]"],
    data() {
      return {
        previews: [],
        submitting: false,
        previewUrl: "",
        albumCurrentCount: config.albumCurrentCount,
        albumMaxPhotos: config.albumMaxPhotos,
      };
    },
    computed: {
      albumFull() {
        return this.albumCurrentCount >= this.albumMaxPhotos;
      },
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
        if (this.albumFull) {
          alert("相册最多 200 张，请先删除照片，再继续上传。");
          return false;
        }
        this.submitting = true;
        return true;
      },
      openPreview(url) {
        this.previewUrl = url;
      },
      closePreview() {
        this.previewUrl = "";
      },
    },
  }).mount("#albumApp");
})();
