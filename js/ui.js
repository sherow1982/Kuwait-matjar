const backToTopButton = document.getElementById("back-to-top");

const scrollFunction = () => {
  if (window.pageYOffset > 300) { // إظهار الزر بعد النزول 300 بكسل
    if (!backToTopButton.classList.contains("show")) {
      backToTopButton.classList.add("show");
    }
  } else {
    if (backToTopButton.classList.contains("show")) {
      backToTopButton.classList.remove("show");
    }
  }
};

window.addEventListener("scroll", scrollFunction);

const scrollToTop = () => {
  window.scrollTo({
    top: 0,
    behavior: "smooth"
  });
};

if(backToTopButton) {
    backToTopButton.addEventListener("click", scrollToTop);
}
