(() => {
    const search = document.querySelector("[data-user-search]");
    const role = document.querySelector("[data-user-role]");
    const rows = [...document.querySelectorAll("[data-user-row]")];
    const count = document.querySelector("[data-user-count]");
    const empty = document.querySelector("[data-user-filter-empty]");
    const clear = document.querySelector("[data-clear-user-filters]");
    const navItems = [...document.querySelectorAll("[data-directory-view]")];
    const accountsPanel = document.querySelector('[data-directory-panel="accounts"]');
    const pendingPanel = document.querySelector('[data-directory-panel="pending"]');

    if (!search || !role || !count || !empty) {
        return;
    }

    const filterUsers = (directoryView = "all") => {
        const searchTerm = search.value.trim().toLowerCase();
        const selectedRole = role.value;
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

        count.textContent = `${visible} ${visible === 1 ? "user" : "users"}`;
        empty.hidden = visible !== 0;
    };

    let activeView = document.body.dataset.directoryView || "all";
    search.addEventListener("input", () => filterUsers(activeView));
    role.addEventListener("change", () => filterUsers(activeView));
    clear?.addEventListener("click", () => {
        search.value = "";
        role.value = "";
        filterUsers(activeView);
    });

    navItems.forEach((item) => {
        item.addEventListener("click", () => {
            activeView = item.dataset.directoryView;
            navItems.forEach((navItem) => navItem.classList.toggle("is-selected", navItem === item));
            if (activeView === "pending") {
                if (accountsPanel) accountsPanel.hidden = true;
                if (pendingPanel) pendingPanel.hidden = false;
                window.history.replaceState({}, "", `/users?view=pending`);
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
