django.jQuery(document).ready(function () {
    addFormsetHandlers();

    function updateFormset() {
        const formset = django.jQuery('#searchkit_formset');
        const formData = django.jQuery('#searchkit_formset').closest('form').serialize();
        const baseUrl = django.jQuery('#searchkit_add_form a').attr('href');
        var url = `${baseUrl}?${formData}`;

        django.jQuery.ajax({
            url: url,
            type: 'GET',
            success: function (response) {
                // console.log('AJAX GET request successful:', response);
                formset.replaceWith(response);
                // We do not want error messages on formset updates. They are
                // not relevant yet.
                django.jQuery('#searchkit_formset').find('.errorlist').remove();
                addFormsetHandlers();
            },
            error: function (error) {
                console.error('AJAX GET request failed:', error);
            }
        });
    }

    function addFormsetHandlers() {
        const totalFormsInput = django.jQuery('input[name$=TOTAL_FORMS]');
        const forms = django.jQuery('.searchkit_form');

        forms.each(function () {
            const form = django.jQuery(this);

            // Update the formset when the form is changed
            form.on('change', function () {
                updateFormset();
            });
        });

        const addButton = django.jQuery('#searchkit_add_form a');
        addButton.on('click', function (e) {
            e.preventDefault();
            totalFormsInput.val(parseInt(totalFormsInput.val()) + 1);
            updateFormset();
        });

        const removeButton = django.jQuery('#searchkit_remove_form a');
        removeButton.on('click', function (e) {
            e.preventDefault();
            totalFormsInput.val(parseInt(totalFormsInput.val()) - 1);
            updateFormset();
        });
    }

});
