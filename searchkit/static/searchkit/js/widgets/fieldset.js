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
            this.toggle = this.fieldset.querySelector('summary');
            if (this.toggle) this.initCollapsible();
        }

        initCollapsible() {
            // For backward compatibility we backported the fieldset template to
            // use details and summary HTML elements for Django <5.1. We also
            // need some adjustments to the CSS.
            if (window.getComputedStyle(this.toggle).getPropertyValue('background-color') === 'rgba(0, 0, 0, 0)') {
                const bgcolor = window.getComputedStyle(this.h2).getPropertyValue('background-color');
                this.toggle.style.backgroundColor = bgcolor;
                this.toggle.style.padding = '8px';
                this.toggle.style.cursor = 'pointer';
                this.h2.style.display = 'inline';
            }

            // Track the fieldset and its collapse state.
            window.searchkitFieldsets[this.id] = window.searchkitFieldsets[this.id] || false;

            // Uncollapse the fieldset if it was previously opened.
            if (window.searchkitFieldsets[this.id]) {
                this.toggle.click();
            }

            // Set event listener for the toggle element to update the collapse
            // state.
            this.toggle.addEventListener('click', (e) => {
                window.searchkitFieldsets[this.id] = !window.searchkitFieldsets[this.id];
            });
        }
    }


    class LogicFormFieldset extends BaseFieldset {

        constructor (fieldset, index) {
            super(fieldset, index);
            this.logicalOperatorInput = this.fieldset.querySelector('.field-logical_operator select');
            this.negationInput = this.fieldset.querySelector('.field-negation input[type="checkbox"]');
            this.updateHeading();

            // Remove the logical operator field for the first filter rule.
            if (this.index === 0) {
                this.fieldset.querySelector('.field-logical_operator').remove();
                this.logicalOperatorInput = null;
            // Otherwise add an event listener to update the heading text.
            } else {
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
            let header = this.index === 0 ? 'WHERE' : `... ${this.logicalOperatorInput.value.toUpperCase()}`;
            header += this.negationInput.checked ? ' NOT ...' : ' ...';
            this.h2.textContent = header;
        }
    }

    class FilterRuleFieldset extends BaseFieldset {

        constructor (fieldset, index) {
            super(fieldset, index);
            this.fieldLookupSelect = this.fieldset.querySelector('.field-field select');
            this.operatorSelect = this.fieldset.querySelector('.field-operator select');
            this.valueInputs = this.fieldset.querySelectorAll('.field-value input, .field-value select');
            this.updateHeading();

            // Set event listener for the value fields to update the heading text.
            this.valueInputs.forEach((el, index) => {
                el.addEventListener('change', () => {
                    this.updateHeading();
                });
            });
        }

        updateHeading() {
            const lookup = this.fieldLookupSelect.options[this.fieldLookupSelect.selectedIndex].innerHTML;
            const operator_value = this.operatorSelect.value;
            const operator = this.operatorSelect.options[this.operatorSelect.selectedIndex].innerHTML;
            let value = '';
            if (this.valueInputs.length === 1) {
                value = `"${this.valueInputs[0].value}"` || '???';
            } else if (this.valueInputs.length === 2) {
                const value1 = this.valueInputs[0].value || '???';
                const value2 = this.valueInputs[1].value || '???';
                const between = operator_value === 'range' ? '" and "' : ' ';
                value = `"${value1}${between}${value2}"`;
            } else if (this.valueInputs.length === 4) {
                const value1 = this.valueInputs[0].value || '???';
                const value2 = this.valueInputs[1].value || '???';
                const value3 = this.valueInputs[0].value || '???';
                const value4 = this.valueInputs[1].value || '???';
                value = `"${value1} ${value2}" and "${value3} ${value4}"`;
            }
            const header = `\`${lookup}\`  |  ${operator}  |  ${value}`;
            this.h2.textContent = header;
        }
    }

    function initFieldsets() {
        document.querySelectorAll('fieldset.searchkit').forEach((el, index) => {
            if (el.classList.contains('filter-logic')) {
                new LogicFormFieldset(el, index);
            } else if (el.classList.contains('filter-rule')) {
                new FilterRuleFieldset(el, index);
            }
        });
    }

    function initFieldsetsOnReload() {
        const fieldsets = { ...window.searchkitFieldsets };
        initFieldsets();
        // If a filter rule was added we open the last filter-rule fieldset.
        if (Object.keys(window.searchkitFieldsets).length > Object.keys(fieldsets).length) {
            const lastFieldset = [...document.querySelectorAll('fieldset.searchkit.filter-rule')].pop();
            lastFieldset.querySelector('summary').click();
        }
    }

    // Fieldsets are tracked by their ids within a global object.
    window.searchkitFieldsets = {};
    document.addEventListener("DOMContentLoaded", initFieldsets);
    document.addEventListener("searchkit:reloaded", initFieldsetsOnReload);
}
