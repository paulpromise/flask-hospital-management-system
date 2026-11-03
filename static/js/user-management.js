(() => {
    const search = document.querySelector("[data-directory-search]");
    const role = document.querySelector("[data-user-role]");
    const rows = [...document.querySelectorAll("[data-user-row]")];
    const count = document.querySelector("[data-user-count]");
    const empty = document.querySelector("[data-user-filter-empty]");
    const searchButton = document.querySelector("[data-directory-search-button]");
    const clear = document.querySelector("[data-directory-clear]");
    const pendingRows = [...document.querySelectorAll("[data-pending-row]")];
    const navItems = [...document.querySelectorAll(".directory-nav [data-directory-view]")];
    const accountsPanel = document.querySelector('[data-directory-panel="accounts"]');
    const pendingPanel = document.querySelector('[data-directory-panel="pending"]');

    if (!search) {
        return;
    }

    const filterUsers = (directoryView = "all") => {
        const searchTerm = search.value.trim().toLowerCase();
        const selectedRole = role?.value || "";
        let visible = 0;

        rows.forEach((row) => {
            const matchesSearch = row.dataset.userSearchValue.toLowerCase().includes(searchTerm);
            const matchesRole = !selectedRole || row.dataset.userRoleValue === selectedRole;
            const matchesView = directoryView === "all" || directoryView === row.dataset.userStatusValue;
            const show = matchesSearch && matchesRole && matchesView;

            row.hidden = !show;
            if (show) {
                visible += 1;
            }
        });

        pendingRows.forEach((row) => {
            row.hidden = directoryView !== "pending" ||
                !row.dataset.pendingSearchValue.toLowerCase().includes(searchTerm);
        });
        if (count && empty) {
            count.textContent = `${visible} ${visible === 1 ? "user" : "users"}`;
            empty.hidden = visible !== 0;
        }
    };

    let activeView = document.body.dataset.directoryView || "all";
    searchButton?.addEventListener("click", () => {
        const query = encodeURIComponent(search.value.trim());
        window.location.href = `/users?view=${activeView}${query ? `&q=${query}` : ""}`;
    });
    search.addEventListener("keydown", (event) => {
        if (event.key === "Enter") {
            event.preventDefault();
            searchButton?.click();
        }
    });
    role?.addEventListener("change", () => filterUsers(activeView));
    clear?.addEventListener("click", () => {
        window.location.href = `/users?view=${activeView}`;
    });

    navItems.forEach((item) => {
        item.addEventListener("click", (event) => {
            event.preventDefault();
            activeView = item.dataset.directoryView;
            navItems.forEach((navItem) => navItem.classList.toggle("is-selected", navItem === item));
            if (activeView === "pending") {
                if (accountsPanel) accountsPanel.hidden = true;
                if (pendingPanel) pendingPanel.hidden = false;
                window.history.replaceState({}, "", `/users?view=pending`);
                filterUsers(activeView);
                return;
            }
            if (accountsPanel) accountsPanel.hidden = false;
            if (pendingPanel) pendingPanel.hidden = true;
            window.history.replaceState({}, "", `/users?view=${activeView}`);
            filterUsers(activeView);
        });
    });

    if (activeView !== "pending") {
        filterUsers(activeView);
    }
})();
