(function () {
    "use strict";

    const mobile = window.matchMedia("(max-width: 991.98px)");

    function prepareTable(table) {
        if (table.dataset.reabiPrepared === "1") return;
        if (table.closest("table") !== null &&
            table.parentElement.closest("table")) return;

        if (table.getAttribute("role") === "presentation") return;

        const head = table.tHead;
        const bodies = Array.from(table.tBodies);
        const rows = bodies.flatMap(body => Array.from(body.rows));

        if (!rows.length) return;

        const headers = head && head.rows.length === 1
            ? Array.from(head.rows[0].cells)
            : [];

        const simple = headers.length > 0 &&
            headers.every(cell =>
                cell.colSpan === 1 && cell.rowSpan === 1
            ) &&
            rows.every(row => {
                const cells = Array.from(row.cells);

                if (cells.length === 1 &&
                    cells[0].colSpan === headers.length) {
                    return true;
                }

                return cells.length === headers.length &&
                    cells.every(cell =>
                        cell.tagName === "TD" &&
                        cell.colSpan === 1 &&
                        cell.rowSpan === 1
                    );
            });

        if (simple) {
            table.classList.add("reabi-card-table");

            rows.forEach(row => {
                Array.from(row.cells).forEach((cell, index) => {
                    if (cell.colSpan > 1) return;

                    const header = headers[index];

                    if (header && !cell.dataset.label) {
                        cell.dataset.label =
                            header.textContent.trim() || "Acoes";
                    }
                });
            });
        } else {
            table.classList.add("reabi-scroll-table");
        }

        // Preservar containers existentes.
        const parent = table.parentElement;

        if (parent && parent.matches(
            ".table-responsive, .table-container, .reabi-table-wrapper"
        )) {
            parent.classList.add("reabi-table-wrapper");
        } else if (parent) {
            const wrapper = document.createElement("div");
            wrapper.className = "reabi-table-wrapper";

            parent.insertBefore(wrapper, table);
            wrapper.appendChild(table);
        }

        table.dataset.reabiPrepared = "1";
    }

    function prepareAll() {
        if (!mobile.matches) return;

        document.querySelectorAll(".main-content table")
            .forEach(prepareTable);
    }

    function init() {
        prepareAll();

        if (mobile.addEventListener) {
            mobile.addEventListener("change", prepareAll);
        } else {
            mobile.addListener(prepareAll);
        }

        window.addEventListener("pageshow", prepareAll);

        const content = document.querySelector(".main-content");

        if (content) {
            let scheduled = false;

            new MutationObserver(function () {
                if (!mobile.matches || scheduled) return;

                scheduled = true;

                requestAnimationFrame(function () {
                    scheduled = false;
                    prepareAll();
                });
            }).observe(content, {
                childList: true,
                subtree: true
            });
        }
    }

    if (document.readyState === "loading") {
        document.addEventListener("DOMContentLoaded", init);
    } else {
        init();
    }
})();
