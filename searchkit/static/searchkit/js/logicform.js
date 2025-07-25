"use strict";

// This script is used to handle the logic form for each filter rule in the
// searchkit.
{
    class LogicForm {

        constructor (fieldset, index) {
            // Setup elements for the logic form.
            this.index = index;
            this.fieldset = fieldset;
            this.h2 = this.fieldset.querySelector('h2');
            this.h2Content = this.h2.textContent;
            this.toggle = this.fieldset.querySelector('summary');
            this.collapsedInput = this.fieldset.querySelector('.field-collapsed input[type="hidden"]');
            this.logicalOperatorInput = this.fieldset.querySelector('.field-logical_operator select');
            this.negationInput = this.fieldset.querySelector('.field-negation input[type="checkbox"]');

            // Remove the logical operator field for the first filter rule.
            if (this.index === 0) {
                this.fieldset.querySelector('.field-logical_operator').remove();
                this.logicalOperatorInput = null;
            }

            // If the value of the collapsedInput is not set, we assume it is
            // collapsed.
            if (this.collapsedInput.value === "") {
                this.collapsedInput.value = "true";
            }

            // Logic form fieldsets are collapsed by default. Uncollapse them if
            // the collapsedInput is set to "false" or unset (empty string).
            if (this.collapsedInput.value === "false") {
                // Uncollapse by triggering a click event on the toggle element.
                this.toggle.click();
            }

            // Set event listener for the toggle element to update the
            // collapsedInput value.
            this.toggle.addEventListener('click', (e) => {
                // Toggle the collapsedInput value.
                this.collapsedInput.value = this.collapsedInput.value === "true" ? "false" : "true";
            });

            // Set event listener for the logical operator input to update the
            // heading text.
            if (this.logicalOperatorInput) {
                this.logicalOperatorInput.addEventListener('change', () => {
                    this.updateHeading();
                });
            }

            // Set event listener for the negation input to update the heading text.
            this.negationInput.addEventListener('change', () => {
                this.updateHeading();
            });
        }
        updateHeading() {
            // Update the header using operator and negation values.
            let operator = this.logicalOperatorInput ? this.logicalOperatorInput.value.toUpperCase() : '';
            operator = operator ? `...${operator}` : '';
            let negation = this.negationInput.checked ? 'NOT' : '';
            negation = operator ? ` ${negation}...` : `${negation}...`;
            this.h2.textContent = `${operator}${negation}`;
        }
    }

    function initLogicForms() {
        document.querySelectorAll('fieldset.searchkit_logicform').forEach((fieldset, index) => {
            const logic_form = new LogicForm(fieldset, index);
            logic_form.updateHeading();
        });
    }

    document.addEventListener("DOMContentLoaded", initLogicForms);
    document.addEventListener("searchkit:reloaded", initLogicForms);
}
