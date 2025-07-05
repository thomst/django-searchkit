document.addEventListener("DOMContentLoaded", function () {
    addFormsetHandlers();

    function updateFormset() {
        const reloadEvent = new Event("searchkit:reloaded");
        const formset = document.getElementById('searchkit_formset');
        const form = formset.closest('form');
        const formData = new URLSearchParams(new FormData(form)).toString();
        const baseUrl = formset.dataset.url;
        const url = `${baseUrl}?${formData}`;

        fetch(url, {
            method: 'GET',
            credentials: 'same-origin',
            headers: {'Accept': 'text/html'},
        })
        .then(response => response.text())
        .then(html => {
            const wrapper = document.createElement('div');
            wrapper.innerHTML = html.trim();
            const newFormset = wrapper.firstChild;
            formset.replaceWith(newFormset);
            // Remove error messages. There not useful on reloading the formset.
            newFormset.querySelectorAll('.errorlist').forEach(el => el.remove());
            window.dispatchEvent(reloadEvent);
            addFormsetHandlers();
        })
        .catch(error => {
            console.error('AJAX GET request failed:', error);
        });
    }

    function addFormsetHandlers() {
        const formset = document.getElementById('searchkit_formset');
        const reloadCssClass = formset.dataset.reloadCssClass;
        const totalFormsInput = formset.closest('form').querySelector('input[name$="TOTAL_FORMS"]');

        document.querySelectorAll(`.${reloadCssClass}`).forEach(function (el) {
            const totalFormsCount = el.dataset.totalForms;
            const reloadHandler = el.dataset.reloadHandler;

            el.addEventListener(reloadHandler, function (e) {
                e.preventDefault();
                if (totalFormsCount) totalFormsInput.value = parseInt(totalFormsCount);
                updateFormset();
            });
        });
    }
});
