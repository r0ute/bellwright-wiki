document.querySelectorAll("table").forEach((table) => {
    const headers = table.querySelectorAll("thead th");

    headers.forEach((header, column) => {
        header.style.cursor = "pointer";

        header.addEventListener("click", () => {
            const rows = [...table.querySelector("tbody").rows];
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

            rows.forEach((row) => table.querySelector("tbody").appendChild(row));

            headers.forEach((h) => delete h.dataset.order);
            header.dataset.order = ascending ? "asc" : "desc";
        });
    });
});