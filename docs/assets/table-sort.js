document.querySelectorAll("table").forEach((table) => {
    const headers = table.querySelectorAll("thead th");
    const tbody = table.querySelector("tbody");

    headers.forEach((header, column) => {
        header.style.cursor = "pointer";

        header.addEventListener("click", () => {
            const rows = [...tbody.rows];
            const ascending = header.dataset.order !== "asc";

            rows.sort((a, b) => {
                const x = a.cells[column].textContent.trim();
                const y = b.cells[column].textContent.trim();

                const nx = Number(x);
                const ny = Number(y);

                if (!Number.isNaN(nx) && !Number.isNaN(ny)) {
                    return ascending ? nx - ny : ny - nx;
                }

                return ascending
                    ? x.localeCompare(y)
                    : y.localeCompare(x);
            });

            rows.forEach((row) => tbody.appendChild(row));

            // Remove sorting state from all headers.
            headers.forEach((h) => {
                delete h.dataset.order;
                h.textContent = h.textContent.replace(/ [▲▼]$/, "");
            });

            // Add arrow to the selected column.
            header.dataset.order = ascending ? "asc" : "desc";
            header.textContent += ascending ? " ▲" : " ▼";
        });
    });
});