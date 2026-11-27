(function () {
    "use strict";

    function init() {
        const media = window.matchMedia("(max-width: 991.98px)");
        const sidebar = document.getElementById("sidebar");
        const overlay = document.getElementById("sidebarOverlay");
        const toggle = document.getElementById("mobileToggleBtn");

        function syncSidebar() {
            const open = Boolean(
                media.matches &&
                sidebar &&
                sidebar.classList.contains("active")
            );

            document.body.classList.toggle(
                "reabi-sidebar-open", open
            );

            if (toggle) {
                toggle.setAttribute("aria-expanded", String(open));
                toggle.setAttribute("aria-controls", "sidebar");
                toggle.setAttribute(
                    "aria-label",
                    open ? "Fechar menu" : "Abrir menu"
                );
            }

            if (sidebar) {
                if (media.matches) {
                    sidebar.setAttribute("aria-hidden", String(!open));
                } else {
                    sidebar.removeAttribute("aria-hidden");
                }
            }
        }

        function closeSidebar() {
            if (!media.matches) return;

            if (sidebar) sidebar.classList.remove("active");
            if (overlay) overlay.classList.remove("active");

            syncSidebar();
        }

        if (sidebar) {
            new MutationObserver(syncSidebar).observe(sidebar, {
                attributes: true,
                attributeFilter: ["class"]
            });
        }

        document.addEventListener("keydown", function (event) {
            if (event.key === "Escape") {
                closeSidebar();
            }
        });

        if (media.addEventListener) {
            media.addEventListener("change", syncSidebar);
        } else {
            media.addListener(syncSidebar);
        }

        window.addEventListener("pageshow", syncSidebar);

        syncSidebar();
    }

    if (document.readyState === "loading") {
        document.addEventListener("DOMContentLoaded", init);
    } else {
        init();
    }
})();
