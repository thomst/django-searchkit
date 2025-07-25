"use strict";

{

    // This script is used to reload the formset when the searchkit is reloaded.

    class SearchkitFormset {

        constructor () {
            this.formset = document.getElementById('searchkit_formset');
            this.form = this.formset.closest('form');
            this.baseUrl = this.formset.dataset.url;
            this.reloadCssClass = this.formset.dataset.reloadCssClass;
            this.totalFormsInput = this.form.querySelector('input[name$="TOTAL_FORMS"]');

            // Set event listener for reloading the formset.
            this.form.querySelectorAll(`.${this.reloadCssClass}`).forEach((el) => {
                const totalFormsCount = el.dataset.totalForms;
                const reloadHandler = el.dataset.reloadHandler;

                el.addEventListener(reloadHandler, (e) => {
                    e.preventDefault();
                    if (totalFormsCount) this.totalFormsInput.value = parseInt(totalFormsCount);
                    this.reload();
                });
            });
        }

        reload () {
            const formData = new URLSearchParams(new FormData(this.form)).toString();
            const url = `${this.baseUrl}?${formData}`;

            fetch(url, {
                method: 'GET',
                credentials: 'same-origin',
                headers: {'Accept': 'text/html'},
            })
            .then(response => response.text())
            .then(html => {
                // Get dom element from html string.
                const wrapper = document.createElement('div');
                wrapper.innerHTML = html;
                const formset = wrapper.firstChild;
                // Remove error messages. They are not useful yet since we did
                // no form submission.
                formset.querySelectorAll('.errorlist').forEach(el => el.remove());
                // Replace the formset dom element.
                this.formset.replaceWith(formset);
                // Reinitialize the formset object itself.
                window.SearchkitFormset = new SearchkitFormset()
                // Trigger reloaded event.
                document.dispatchEvent(new Event("searchkit:reloaded"));
            })
            .catch(error => {
                console.error('AJAX GET request failed:', error);
            });
        }
    }

    document.addEventListener("DOMContentLoaded", function () {
        window.SearchkitFormset = new SearchkitFormset()
    });
}
