function get_timeline_survey() {
    /**
     * Returns jsPsych timeline (list of survey trials) for standard McDermott Lab demographic survey.
     */
    var timeline_survey_demographic = {
        type: jsPsychSurveyMultiChoice,
        preamble: [
            "<h4>The following are demographic questions to help us with our study. " +
            "Your payment is NOT dependent on your answers to these questions in any way.</h4>"
        ],
        questions: [
            {
                prompt: "<b>Which country are you from?</b>",
                options: ["USA", "UK", "Canada", "Australia", "New Zealand", "India", "Other", "Prefer not to answer"],
                horizontal: true,
                required: !DEBUG_MODE,
                name: 'country',
            },
            {
                prompt: "<b>What is your native language?</b>",
                options: ["English", "Other"],
                horizontal: true,
                required: !DEBUG_MODE,
                name: 'language',
            },
            {
                prompt: "<b>What is your gender?</b>",
                options: ["Male", "Female", "Other", "Prefer not to answer"],
                horizontal: true,
                required: !DEBUG_MODE,
                name: 'gender',
            },
            // {
            //     prompt: "What is your age?",
            //     options: ["18-24", "25-34", "35-49", "50-64", "65+", "Prefer not to answer"],
            //     horizontal: false,
            //     required: !DEBUG_MODE,
            //     name: 'age',
            // },
        ],
        randomize_question_order: false,
    };
    var timeline_survey_headphones = {
        type: jsPsychSurveyMultiChoice,
        questions: [
            {
                prompt: [
                    "<b>You <i>MUST</i> be wearing headphones for this experiment. " +
                    "Are you using in-ear headphones or over-the-ear headphones?</b>"
                ],
                options: ["In-ear headphones or earbuds", "Over-the-ear headphones"],
                horizontal: true,
                required: !DEBUG_MODE,
                name: 'headphones',
            },
            {
                prompt: "<b>Are you using wired or bluetooth/wireless headphones?</b>",
                options: ["Wired", "Bluetooth/wireless"],
                horizontal: true,
                required: !DEBUG_MODE,
                name: 'connection',
            },
            {
                prompt: "<b>Do you have any hearing loss?</b>",
                options: ["Not aware of any hearing loss", "Yes, I have some hearing loss"],
                horizontal: true,
                required: !DEBUG_MODE,
                name: 'hearing_loss',
            },
            {
                prompt: "<b>Have you ever known how to play a musical instrument?</b>",
                options: ["Yes", "No"],
                horizontal: true,
                required: !DEBUG_MODE,
                name: 'musical_instrument',
            },
            {
                prompt: "<b>If so, how many years did you play?</b>",
                options: ["N/A", "0-5 years", "5-10 years", "10+ years"],
                horizontal: true,
                required: !DEBUG_MODE,
                name: 'musical_training',
            },
        ],
        randomize_question_order: false,
    };
    var timeline_survey_text = {
        type: jsPsychSurveyText,
        questions: [
            {
                prompt: '<b>What is your age?</b> (You may skip this question if you prefer not to answer)',
                name: 'age',
                required: false,
                columns: 8,
            },
            {
                prompt: '<b>What is your Prolific/MTurk ID?</b> (Not required but may help if problems arise)',
                name: 'worker_id',
                required: false,
                columns: 32,
            },
        ],
        randomize_question_order: false,
    };
    var timeline_survey = [
        timeline_survey_demographic,
        timeline_survey_headphones,
        timeline_survey_text,
    ];
    return timeline_survey
}


function get_timeline_calibration() {
    /**
     * Returns jsPsych timeline (audio playback loop) for standard McDermott Lab headphone calibration.
     */
    var calibration_stim = 'https://mcdermottlab.mit.edu/mturk_stimuli/audio_calibration/noise_calib_stim.wav';
    var calibration_instructions = "<h2>Calibration instructions:</h2>" +
        "<p>This listening task requires headphones, so please grab some if you haven't already. Set your computer volume to about 50% of the maximum volume.</p>" +
        "<p>Click the `Play calibration sound` button to hear the calibration sound, and then adjust the volume on your computer until the sound is at a comfortable level.</p>" +
        "<p>Please play the calibration sound as many times as you need.</p>" +
        "<p>Once the volume is at a comfortable level, please refrain from changing the volume for the remainder of the experiment.</p>";
    var timeline_calibration_instructions = {
        type: jsPsychHtmlButtonResponse,
        stimulus: calibration_instructions,
        choices: ["Play calibration sound"],
    };
    var timeline_calibration_loop = {
        timeline: [{
            type: jsPsychAudioButtonResponse,
            stimulus: calibration_stim,
            prompt: calibration_instructions,
            choices: ['Play calibration sound', 'Continue'],
            response_allowed_while_playing: true,
        }],
        loop_function: function (data) {
            if (data.values()[0].response == 0) {
                return true; // Loop if response is not 'continue'
            } else {
                return false; // Break loop and continue otherwise
            }
        },
    };
    var timeline_calibration = [
        timeline_calibration_instructions,
        timeline_calibration_loop,
    ];
    return timeline_calibration
}


function get_timeline_headphone_check() {
    /**
     * Returns jsPsych timeline (audio response trials) for standard McDermott Lab headphone check.
     */
    var headphone_check_min_correct = 5;
    var headphone_check_timeline_variables = [
        { stimulus: 'https://mcdermottlab.mit.edu/mturk_stimuli/audio_calibration/antiphase_HC_ISO.wav', hc_answer: 2 },
        { stimulus: 'https://mcdermottlab.mit.edu/mturk_stimuli/audio_calibration/antiphase_HC_IOS.wav', hc_answer: 3 },
        { stimulus: 'https://mcdermottlab.mit.edu/mturk_stimuli/audio_calibration/antiphase_HC_SOI.wav', hc_answer: 1 },
        { stimulus: 'https://mcdermottlab.mit.edu/mturk_stimuli/audio_calibration/antiphase_HC_SIO.wav', hc_answer: 1 },
        { stimulus: 'https://mcdermottlab.mit.edu/mturk_stimuli/audio_calibration/antiphase_HC_OSI.wav', hc_answer: 2 },
        { stimulus: 'https://mcdermottlab.mit.edu/mturk_stimuli/audio_calibration/antiphase_HC_OIS.wav', hc_answer: 3 },
    ];
    var headphone_check_instructions = [
        "<h2>Loudness task:</h2>" +
        "<p>You will now perform a quick <i>loudness</i> task.</p>" +
        "<p>A series of three sounds will play when you press `Next`.</p>" +
        "<p>Simply judge <b>which sound which was the quietest</b> -- either the 1st, 2nd, or 3rd.</p>" +
        "<p>Are you ready?</p>"
    ];
    var timeline_headphone_check_instructions = {
        type: jsPsychInstructions,
        pages: headphone_check_instructions,
        show_clickable_nav: true,
    };
    var timeline_headphone_check_loop = {
        timeline: [{
            type: jsPsychAudioButtonResponse,
            stimulus: jsPsych.timelineVariable('stimulus'),
            choices: ['1', '2', '3'],
            prompt: "<p>Which sound is the <b>quietest</b>?</p>",
            response_ends_trial: true,
            response_allowed_while_playing: DEBUG_MODE,
            data: {
                stim_type: 'hc',
                hc_answer: jsPsych.timelineVariable('hc_answer'),
            },
            on_finish: function (data) {
                var hc_answer = jsPsych.timelineVariable('hc_answer');
                var hc_correct = (data.response + 1) == hc_answer;
                jsPsych.data.get().addToLast({ hc_correct: hc_correct ? 1 : 0 });
            },
        }],
        timeline_variables: headphone_check_timeline_variables,
        randomize_order: !DEBUG_MODE,
    };
    var timeline_headphone_check_end = {
        type: jsPsychHtmlButtonResponse,
        stimulus: "<p>You have completed the loudness task.</p>",
        choices: ["Next"],
        response_ends_trial: true,
        on_finish: function () {
            var hc_correct_count = jsPsych.data.get().filter({ hc_correct: 1 }).count()
            var hc_passed = hc_correct_count >= headphone_check_min_correct;
            jsPsych.data.addProperties({ hc_passed: hc_passed });
            debug_print("hc_passed = " + hc_passed);
        },
    };
    var timeline_headphone_check_failed = {
        timeline: [{
            type: jsPsychHtmlKeyboardResponse,
            stimulus: [
                "<p>I am afraid you may not proceed further in the experiment.</p>" +
                "<p>Please return your submission on Prolific now by selecting the " +
                "`Stop without completing` button, to avoid receiving a rejection.</p>",
            ],
            choices: 'NO_KEYS',
        }],
        conditional_function: function () {
            var hc_passed = jsPsych.data.get().last().values()[0].hc_passed;
            return !hc_passed
        },
    };
    var timeline_headphone_check = [
        timeline_headphone_check_instructions,
        timeline_headphone_check_loop,
        timeline_headphone_check_end,
        timeline_headphone_check_failed,
    ];
    return timeline_headphone_check
}


function get_timeline_preexisting_filename(url_filename) {
    /**
     * Returns jsPsych timeline that terminates experiment if `filename_exists(url_filename)` returns True.
     * This timeline can be used to exclude participants who have previously completed experiment.
     */
    var timeline_preexisting_filename = {
        timeline: [{
            type: jsPsychHtmlKeyboardResponse,
            stimulus: [
                "<p><b>It appears you may have already completed this experiment before.</b></p>" +
                "<p>Please return your submission on Prolific now by selecting the " +
                "`Stop without completing` button, to avoid receiving a rejection.</p>",
            ],
            choices: 'NO_KEYS',
        }],
        conditional_function: function () {
            return filename_exists(url_filename)
        },
    };
    return [timeline_preexisting_filename];
}


function arange(start, stop, step) {
    var list = [];
    for (var i = start; i < stop; i += step) {
        list.push(i);
    }
    return list
}


function filename_exists(url_filename) {
    /**
     * Helper function returns True if `url_filename` already exists.
     * This can be useful for ensuring non-repeat participants.
     */
    var http = new XMLHttpRequest();
    http.open('HEAD', url_filename, false);
    http.send();
    var exists = http.status != 404;
    debug_print(`Checking existence of ${url_filename}: ${exists}`);
    return exists;
}


function write_data_to_server(url_write_data_php, filename, filedata) {
    /**
     * This function sends a data packet to the specified URL as a POST request.
     * The specified URL is for a PHP script that writes the POST request's
     * contents (`filename` and `filedata`) to a file on the server.
     */
    jQuery.ajax({
        type: 'post',
        cache: false,
        url: url_write_data_php,
        data: {
            filename: filename,
            filedata: filedata,
        },
    });
    debug_print(`Attempted to write data to: ${output_filename}`);
}


var DEBUG_MODE;


function debug_print(x) {
    if (DEBUG_MODE) {
        console.log(x);
    }
}
