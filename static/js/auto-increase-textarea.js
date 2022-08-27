$(document).ready(function () {
  document.getElementById("text_area_input").addEventListener(
    "keyup",
    function () {
      this.style.overflow = "auto";
      this.style.height = 0;
      this.style.height = this.scrollHeight + 2 + "px";
    },
    false
  );
	document.getElementById("text_area_input").addEventListener(
    "paste",
    function () {
      this.style.overflow = "auto";
      this.style.height = 0;
      this.style.height = this.scrollHeight + 2 + "px";
    },
    false
  );
	document.getElementById("text_area_input").addEventListener(
    "cut",
    function () {
      this.style.overflow = "auto";
      this.style.height = 0;
      this.style.height = this.scrollHeight + 2 + "px";
    },
    false
  );
});
