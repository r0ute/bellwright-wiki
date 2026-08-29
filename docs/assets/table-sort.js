document.addEventListener("DOMContentLoaded", () => {
    document.querySelectorAll("table").forEach((table) => {
        const headers = table.querySelectorAll("thead th");
        const tbody = table.querySelector("tbody");

        if (!headers.length || !tbody) return;

        headers.forEach((header, column) => {
            const label = header.textContent.trim();

            header.textContent = `${label} ↕`;
            header.style.cursor = "pointer";

            header.addEventListener("click", () => {
                const ascending = header.dataset.order !== "asc";

                const rows = [...tbody.rows];

                rows.sort((a, b) => {
                    const x = a.cells[column]?.textContent.trim() ?? "";
                    const y = b.cells[column]?.textContent.trim() ?? "";

                    const nx = Number(x);
                    const ny = Number(y);

                    if (
                        x !== "" &&
                        y !== "" &&
                        !Number.isNaN(nx) &&
                        !Number.isNaN(ny)
                    ) {
                        return ascending ? nx - ny : ny - nx;
                    }

                    return ascending
                        ? x.localeCompare(y)
                        : y.localeCompare(x);
                });

                rows.forEach((row) => tbody.appendChild(row));

                headers.forEach((other) => {
                    const text = other.textContent.trim().replace(/[↕↑↓]$/, "").trim();

                    delete other.dataset.order;
                    other.textContent = `${text} ↕`;
                });

                header.dataset.order = ascending ? "asc" : "desc";

                const text = header.textContent.trim().replace(/[↕↑↓]$/, "").trim();
                header.textContent = `${text} ${ascending ? "↑" : "↓"}`;
            });
        });
    });
});