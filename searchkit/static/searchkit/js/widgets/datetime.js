"use strict";

// Initialize datetime widgets when searchkit got reloaded.

{

    document.addEventListener("searchkit:reloaded", (e) => DateTimeShortcuts.init());

}
