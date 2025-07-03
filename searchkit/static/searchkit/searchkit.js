django.jQuery(document).ready(function () {
    addFormsetHandlers();

    function updateFormset() {
        const formset = django.jQuery('#searchkit_formset');
        const formData = django.jQuery('#searchkit_formset').closest('form').serialize();
        const baseUrl = formset.data('url');
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
        const formset = django.jQuery('#searchkit_formset');
        const reloadCssClass = formset.data('reload-css-class');
        const totalFormsInput = django.jQuery('input[name$=TOTAL_FORMS]');

        django.jQuery(`.${reloadCssClass}`).each(function () {
            const totalFormsCount = django.jQuery(this).data('total-forms');
            const reloadHandler = django.jQuery(this).data('reload-handler');
            django.jQuery(this).on(reloadHandler, function (e) {
                e.preventDefault();
                if (totalFormsCount) totalFormsInput.val(parseInt(totalFormsCount));
                updateFormset();
            });
        });
    }
});
