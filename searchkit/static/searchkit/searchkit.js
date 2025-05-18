django.jQuery(document).ready(function () {
    addFormsetHandlers();

    function updateFormset(index=null) {
        const formset = django.jQuery('#searchkit_formset');
        const ajaxUrl = django.jQuery('#searchkit_add_form a').attr('href');
        const totalFormsInput = django.jQuery("input[id$='TOTAL_FORMS']");

        var formData = django.jQuery('form').serialize();
        if (index !== null) {
            var url = `${ajaxUrl}${index}/?${formData}`;
        } else {
            var url = `${ajaxUrl}?${formData}`;
        }

        django.jQuery.ajax({
            url: url,
            type: 'GET',
            success: function (response) {
                console.log('AJAX GET request successful:', response);
                formset.replaceWith(response);
                addFormsetHandlers();
                // formset = django.jQuery('#searchkit_formset');
            },
            error: function (error) {
                console.error('AJAX GET request failed:', error);
            }
        });
    }

    function addFormsetHandlers() {
        const forms = django.jQuery('.searchkit_form');
        forms.each(function () {
            const form = django.jQuery(this);
            const index = form.attr('data-index');

            // Update the formset when the form is changed
            form.on('change', function () {
                updateFormset(index);
            });
        });

        const addButton = django.jQuery('#searchkit_add_form a');
        addButton.on('click', function (e) {
            e.preventDefault();
            updateFormset();
        });
    }

});
