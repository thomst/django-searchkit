{
    // Initialize datetime widgets when searchkit got reloaded.
    window.addEventListener("searchkit:reloaded", (e) => DateTimeShortcuts.init());
}