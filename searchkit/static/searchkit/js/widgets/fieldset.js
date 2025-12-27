"use strict";

// This script is used to handle the logic form for each filter rule in the
// searchkit.
{
    class BaseFieldset {

        constructor (fieldset, index) {
            this.index = index;
            this.fieldset = fieldset;
            this.h2 = this.fieldset.querySelector('h2');
            this.id = this.h2.id;
            this.details = this.fieldset.querySelector('details');
            this.summary = this.fieldset.querySelector('summary');
            if (this.collapsible) {
                this.addEventListenerOnCollapse();
            }
        }

        get collapsible() {
            return !!this.details && !!this.summary;
        }

        addEventListenerOnCollapse() {
            // Update the collapse state when fieldset is toggled.
            this.details.addEventListener('toggle', (e) => {
                fieldsetStates[this.id] = this.details.open;
            });
        }
    }


    class LogicFormFieldset extends BaseFieldset {

        constructor (fieldset, index) {
            super(fieldset, index);
            this.logicalOperatorField = this.fieldset.querySelector('.field-logical_operator select');
            this.negationField = this.fieldset.querySelector('.field-negation select');
            this.updateHeading();

            // Set event listener for the negation input to update the heading text.
            this.negationField.addEventListener('change', () => {
                this.updateHeading();
            });
            // Set event listender for logicalOperatorField.
            if (this.logicalOperatorField) {
                this.logicalOperatorField.addEventListener('change', () => {
                    this.updateHeading();
                });
            }
        }

        updateHeading() {
            let header = this.index === 0 ? 'WHERE' : `... ${this.logicalOperatorField.value.toUpperCase()}`;
            header += this.negationField.value === 'True' ? ' NOT ...' : ' ...';
            this.h2.textContent = header;
        }
    }

    class FilterRuleFieldset extends BaseFieldset {

        constructor (fieldset, index) {
            super(fieldset, index);
            this.fieldLookupField = this.fieldset.querySelector('.field-field select');
            this.operatorField = this.fieldset.querySelector('.field-operator select');
            this.valueFields = this.fieldset.querySelectorAll('.field-value input, .field-value select');
            this.updateHeading();

            // Set event listener for the value fields to update the heading text.
            this.valueFields.forEach((el) => {
                el.addEventListener('change', () => {this.updateHeading()});
                // We also need focusout event listeners for the datetime widgets.
                el.addEventListener('focusout', () => {this.updateHeading()});
            });
        }

        updateHeading() {
            const lookup = this.fieldLookupField.options[this.fieldLookupField.selectedIndex].innerHTML;
            const operator_value = this.operatorField.value;
            const operator = this.operatorField.options[this.operatorField.selectedIndex].innerHTML;
            const values = Array.from(this.valueFields).map((el) => {
                if (el.multiple) {
                    const options = Array.from(el.selectedOptions).map(option => option.value);
                    return options.length > 0 ? options.join(', ') : '???';
                } else {
                    return !!el.value ? el.value : '???';
                }
            });

            let value;
            if (values.length === 1) {
                value = values[0];
            } else if (values.length === 2) {
                const between = operator_value === 'range' ? ' -> ' : ' ';
                value = `${values[0]}${between}${values[1]}`;
            } else if (values.length === 4) {
                value = `${values[0]} ${values[1]} -> ${values[2]} ${values[3]}`;
            }
            this.h2.textContent = `${lookup} | ${operator} | ${value}`;
        }
    }

    function initFieldsets(reloaded=false) {
        // Track count of previously initialized fieldsets.
        const count = Object.keys(fieldsetStates).length;
        let fieldsets = [];

        // Initialize all searchkit fieldsets.
        document.querySelectorAll('fieldset.searchkit').forEach((el, index) => {
            // Initialize the fieldset based on its class.
            if (el.classList.contains('filter-logic')) {
                fieldsets.push(new LogicFormFieldset(el, index));
            } else if (el.classList.contains('filter-rule')) {
                fieldsets.push(new FilterRuleFieldset(el, index));
            }
        });

        if (reloaded) {
            // If a filter rule was added we open the last fieldset.
            if (count < fieldsets.length) {
                const lastFieldset = fieldsets[fieldsets.length - 1];
                if (lastFieldset.collapsible) {
                    lastFieldset.details.open = true;
                }
            }

            // Also open all fieldsets that were open before the reload.
            fieldsets.forEach((fieldset) => {
                if (fieldset.collapsible && fieldsetStates[fieldset.id]) {
                    fieldset.details.open = true;
                }
            });
        } else {
            // For a search create request we open the initial filter rule
            // fieldset.
            const initialForms = document.querySelector('input[name$="-INITIAL_FORMS"]');
            const lastFieldset = fieldsets[fieldsets.length - 1];
            if (lastFieldset && lastFieldset.collapsible && initialForms.value === "0") {
                lastFieldset.details.open = true;
            }
        }

        // Track the collapse states of the fieldsets.
        fieldsetStates = {};
        fieldsets.forEach((fieldset) => {
            fieldsetStates[fieldset.id] = fieldset.details.open;
        });
    }

    let fieldsetStates = {};
    document.addEventListener("DOMContentLoaded", function (e) {initFieldsets(false)});
    document.addEventListener("searchkit:reloaded", function (e) {initFieldsets(true)});
}
