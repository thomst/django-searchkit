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
            this.logicalOperatorField = this.fieldset.querySelector('.field-logical_operator select');
            this.negationSelect = this.fieldset.querySelector('.field-negation select');
            this.updateHeading();

            // Remove the logical operator field for the first filter rule.
            if (this.index === 0) {
                this.fieldset.querySelector('.field-logical_operator').remove();
                this.logicalOperatorField = null;
            // Otherwise add an event listener to update the heading text.
            } else {
                this.logicalOperatorField.addEventListener('change', () => {
                    this.updateHeading();
                });
            }

            // Set event listener for the negation input to update the heading text.
            this.negationSelect.addEventListener('change', () => {
                this.updateHeading();
            });
        }

        updateHeading() {
            let header = this.index === 0 ? 'WHERE' : `... ${this.logicalOperatorField.value.toUpperCase()}`;
            header += this.negationSelect.value === 'True' ? ' NOT ...' : ' ...';
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
