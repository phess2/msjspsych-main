function dictionary_lookup(dictionary_str, button_text, columns=5, column_width="200px") {
    /**
     * Compare text input to dictionary and display table of all matching dictionary values.
     * If text input uniquely matches a dictionary value, enable form submission.
     * 
     * Arguments
     * ---------
     * dictionary_str (string): comma-separated list of allowed responses
     *      (NOTE: allowed responses must not contain commas or quotes)
     * button_text (string): text to display on submission button
     * columns (integer): number of columns for table of matching dictionary values
     * column_width (string): column width for table with units
     */
    var dictionary = dictionary_str.split(`,`);
    var dictionary_subset = [];
    var dictionary_subset_indexes = [];
    var re_strip = /['.,]/g; // Regular expression to exclude unwanted characters from string comparison
    var response_str = document.getElementById(`id_response`).value.toLowerCase().replace(re_strip, "");
    var submit_disabled = true;
    var submit_str = "";
    if (response_str == "?") {
        dictionary_subset = dictionary;
    } else {
        for (var itr = 0; itr < dictionary.length; itr++) {
            var token = dictionary[itr].toLowerCase().replace(re_strip, "");
            if (response_str.length > 0 && token.includes(response_str)) {
                index_of_response_str = token.indexOf(response_str);
                bolded_token = token.replace(response_str, `<strong>${response_str}</strong>`);
                dictionary_subset.push(bolded_token);
                dictionary_subset_indexes.push(itr);
            }
            if (response_str == token) {
                submit_disabled = false; // Allow form submission if there is an exact match
                submit_str = response_str;
            }
        }
        if (dictionary_subset.length == 1) {
            submit_str = dictionary[dictionary_subset_indexes[0]];
            submit_disabled = false; // Allow form submission if there is exactly one partial match
        }
    }
    document.getElementById(`id_submit`).disabled = submit_disabled;
    document.getElementById(`id_submit`).value = button_text + submit_str;
    document.getElementById(`id_submit`).style.fontWeight = "bold";
    // Display subset of matching dictionary responses as a table
    var table = document.getElementById(`id_table`);
    table.innerHTML = "";
    var itr_cell = 0;
    for (var itr_row = 0; itr_row < Math.ceil(dictionary_subset.length / columns); itr_row++) {
        var row = document.createElement("tr");
        for (var itr_col = 0; itr_col < columns; itr_col++) {
            if (itr_cell < dictionary_subset.length) {
                var cell = document.createElement("td");
                cell.innerHTML = dictionary_subset[itr_cell];
                cell.style.width = column_width;
                row.appendChild(cell);
                
            }
            itr_cell += 1;
        }
        table.appendChild(row);
    }
    table.style.borderCollapse = "collapse";
    table.style.margin = "auto";
    table.style.fontSize = "20px";
}


var jsPsychDictionaryText = (function (jspsych) {
    "use strict";

    const info = {
        name: "dictionary-text",
        parameters: {
            /** Question prompt */
            prompt: {
                type: jspsych.ParameterType.HTML_STRING,
                pretty_name: "Prompt",
                default: "",
            },
            /** Placholder for text response */
            placeholder: {
                type: jspsych.ParameterType.HTML_STRING,
                pretty_name: "Placeholder",
                default: "Type here to search allowed responses",
            },
            /** Dictionary of allowed responses */
            dictionary: {
                type: jspsych.ParameterType.STRING,
                pretty_name: "Dictionary",
                default: undefined,
                array: true,
            },
            /** Submit button text */
            button_text: {
                type: jspsych.ParameterType.HTML_STRING,
                pretty_name: "ButtonText",
                default: "Press enter to submit: ",
            },
            /** Number of characters for response text box */
            size: {
                type: jspsych.ParameterType.INT,
                pretty_name: "Size",
                default: 40,
            },
            /** Number of columns for allowed response table */
            columns: {
                type: jspsych.ParameterType.INT,
                pretty_name: "Columns",
                default: 5,
            },
            /** Width of columns for allowed response table */
            column_width: {
                type: jspsych.ParameterType.HTML_STRING,
                pretty_name: "ColumnWidth",
                default: "200px",
            },
        },
    };

    /**
     * ** dictionary-text **
     *
     * Collect text responses that fall within a dictionary of allowed responses.
     * Matching dictionary values are displayed and updated as participant types.
     *
     * @author Mark Saddler
     * @see {@link https://github.mit.edu/msaddler/msjspsych Documentation}
     */
    class jsDictionaryTextPlugin {
        constructor(jsPsych) {
            this.jsPsych = jsPsych;
        }

        trial(display_element, trial) {
            var html = ``;
            html += `<div>`;
            // Add prompt
            html += `<p>${trial.prompt}</p>`;
            // Input text box (with an `oninput` function call to `dictionary_lookup`)
            html += `<input type="text" id="id_response" autocomplete="off" autofocus="true" `;
            html += `data-name="${trial.name}" size="${trial.size}" placeholder="${trial.placeholder}" `;
            html += `oninput="dictionary_lookup`;
            html += `('${trial.dictionary}', '${trial.button_text}', ${trial.columns}, '${trial.column_width}')"`;
            html += `></input>`;
            // Table of allowed responses
            html += `<table id="id_table"></table>`;
            // Input button to submit response
            html += `<input type="button" id="id_submit" class="jspsych-btn" `;
            html += `value="${trial.button_text}" disabled="true" `;
            html += `></input>`;
            html += `</div>`;
            display_element.innerHTML = html;
            display_element.querySelector("#id_response").focus();
            display_element.querySelector("#id_response").addEventListener("keyup", (e) => {
                /**
                 * Click submit button when enter key is detected in text response box.
                 * */
                if (e.key !== "Enter") return;
                document.querySelector("#id_submit").click();
                e.preventDefault();
            });
            display_element.querySelector("#id_submit").addEventListener("click", (e) => {
                /**
                 * Detect when submit button is clicked.
                 */
                e.preventDefault();
                // Measure response time
                var endTime = performance.now();
                var response_time = Math.round(endTime - startTime);
                // Get response string
                var response_str = document.querySelector("#id_response").value;
                var submit_str = document.querySelector("#id_submit").value;
                var response = submit_str.replace(trial.button_text, "");
                // Save data
                var trialdata = {
                    rt: response_time,
                    response: response,
                    response_str: response_str,
                };
                // Next trial
                display_element.innerHTML = "";
                this.jsPsych.finishTrial(trialdata);
            });
            var startTime = performance.now();
        }
    }
    jsDictionaryTextPlugin.info = info;

    return jsDictionaryTextPlugin;
})(jsPsychModule);