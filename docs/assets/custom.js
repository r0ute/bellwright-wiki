// table sorting
document.querySelectorAll("table").forEach((table) => {
    const headers = table.querySelectorAll("thead th");
    const tbody = table.querySelector("tbody");

    if (!headers.length || !tbody) return;

    headers.forEach((header, column) => {
        header.classList.add("sortable");

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
                delete other.dataset.order;
            });

            header.dataset.order = ascending ? "asc" : "desc";
        });
    });
});

// logo
document.querySelector(".logo")?.addEventListener("click", (event) => {
    const logo = event.currentTarget;

    logo.classList.remove("ringing");
    void logo.offsetWidth;
    logo.classList.add("ringing");
});