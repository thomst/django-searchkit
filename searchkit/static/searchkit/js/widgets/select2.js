"use strict";

// Initialize the select2 autocomplete widgets. Requires jquery.

{

    function initSelect2 () {
        $('.searchkit-select2').each((i, el) => { $(el).select2() });
    }

    document.addEventListener("DOMContentLoaded", function () { initSelect2() });
    document.addEventListener("searchkit:reloaded", (e) => initSelect2());

}
