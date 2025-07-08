"use strict";

// Initialize the select2 autocomplete widgets. Requires jquery.

{

    function initSelect2 () {
        django.jQuery('.admin-autocomplete').each((i, el) => {
            django.jQuery(el).select2()
        });
    }
    document.addEventListener("searchkit:reloaded", (e) => initSelect2());

}
