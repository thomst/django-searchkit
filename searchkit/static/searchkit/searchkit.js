django.jQuery(document).ready(function () {
    addFormsetHandlers();

    function updateFormset(add_form=false) {
        const formset = django.jQuery('#searchkit_formset');
        const baseUrl = django.jQuery('#searchkit_add_form a').attr('href').replace('/add/', '');
        var formData = django.jQuery('form').serialize();

        if (add_form) {
            var url = `${baseUrl}/add/?${formData}`;
        } else {
            var url = `${baseUrl}/update/?${formData}`;
        }

        django.jQuery.ajax({
            url: url,
            type: 'GET',
            success: function (response) {
                console.log('AJAX GET request successful:', response);
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
        const forms = django.jQuery('.searchkit_form');
        forms.each(function () {
            const form = django.jQuery(this);

            // Update the formset when the form is changed
            form.on('change', function () {
                updateFormset(false);
            });
        });

        const addButton = django.jQuery('#searchkit_add_form a');
        addButton.on('click', function (e) {
            e.preventDefault();
            updateFormset(true);
        });
    }

});
