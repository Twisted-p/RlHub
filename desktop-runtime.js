// Loaded by the desktop host before the shared application script.
window.RL_HUB_STANDALONE = true;
document.body.classList.add("desktop-app");
const connectButton = document.querySelector('[data-connect-action="link"]');
if (connectButton) connectButton.textContent = "Koble spiller";
document.querySelectorAll("a[href]").forEach((link) => {
  const url = new URL(link.getAttribute("href"), window.location.href);
  if (url.origin === window.location.origin) {
    link.removeAttribute("target");
  }
});
