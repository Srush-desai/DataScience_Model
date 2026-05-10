document.addEventListener("DOMContentLoaded", () => {
    const activePanel = document.querySelector(".active-panel");
    if (activePanel) {
        activePanel.scrollIntoView({ behavior: "smooth", block: "start" });
    }
});
