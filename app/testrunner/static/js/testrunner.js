$(document).ready(function() {

    // first check if production test has been loaded on this machine
    $.ajax({
        type: 'POST',
        url: $('span.check-install-url').html(),
        dataType: 'json',                          // expecting json back from server
        success: function (responsedata) {
            if (responsedata['install'] == false) {
                $('span.install-error').html(responsedata['message']);
            }
        },
        error: function (responsedata) {
            $('span.install-error').html('Problem checking production test code install');
        }
    });

    // On document ready fill in all step numbers and hide table rows so test steps revealed one at a time
    var step = 1;
    $('tr.test-plan-row').each(function(){
        if ($(this).find('span.step-number').length)
        {
            $(this).find('span.step-number').html(step);
            $(this).attr("data-step", step);
            if (step > 1) {
                $(this).hide();
            }
            step = step + 1;
        }
    });

    // function to reveal each row after a serial number entered or selection made
    const show_next_test_plan_row = (step) => {
        var last_step_to_show = 1;

        $('tr.test-plan-row').each(function() {
            if ($(this).is(":visible") && $(this).find("input:radio:checked").val())
            {
                // for radio button rows
                last_step_to_show = $(this).data("step");
            }
            else if ($(this).data("step") - 1 == last_step_to_show)
            {
                $(this).fadeIn(500);
                $('html, body').animate({scrollTop: $(document).height()}, 'slow');
            }
        });
    }

    // function to build start_time string
    const get_time = () => {
        var d = new Date();
        return d.getFullYear() + "-" + ("0" + (d.getMonth() + 1)).slice(-2)  + "-" + ("0" + d.getDate()).slice(-2)
                + "H" + ("0" + d.getHours()).slice(-2) + ":" + ("0" + d.getMinutes()).slice(-2) + ":" +
                ("0" + d.getSeconds()).slice(-2);
    }

    // calculate test duration in seconds
    const test_duration = (st, et) => {
        var st_arr = timestamp_to_ints(st);
        var et_arr = timestamp_to_ints(et);

        if (et_arr[1] > st_arr[1])
        {
            // month of test end is greater than month of test start
            // change day of end to day of start + 1
            et_arr[2] = st_arr[2] + 1;
        }

        var df_arr = [];
        for (i=2; i<et_arr.length; i++) {
            df_arr.push(et_arr[i] - st_arr[i]);
        }

        var seconds = df_arr[0] * 24 * 3600 + df_arr[1] * 3600 + df_arr[2] * 60 + df_arr[3];
        return seconds;

    }

    // convert timestamp to array of ints
    const timestamp_to_ints = (tmsp) =>{
        var dt = tmsp.split("H")[0].split("-");
        var tm = tmsp.split("H")[1].split(":");
        var str_arr = dt.concat(tm);
        var nums = [];
        for (i=0; i<str_arr.length; i++) {
            nums.push(parseInt(str_arr[i]));
        }
        return nums;
    }

    // set log_file_name variable, will be defined as = instrument_serial_number_timestamp.txt
    var log_file_name = '';

    // on entering serial number, set start time, create log_file_name, and reveal the next row
    $('#serial-number').on('input', function() {

        var sn = $('input#serial-number').val();
        var st_time = get_time()

        $('span.serial-number').html(sn);
        $('span.start-time').html(st_time);

        // update log_file_name defined in scope outside of thi function
        log_file_name = $('span.instrument').html() + "_" + sn + "_" + st_time.split(":").join("-") + ".txt";

        $('p.inst_sn_timestamp').removeClass("hidden").show();
        show_next_test_plan_row();
    });

    // on radio button click, reveal the next row
    $("input:radio").change(function() {
        show_next_test_plan_row();
    });

    // on automated test button click, submit test parameters to run_test task
    $("button.automated-tests").click(function () {

        // disable test submit button
        $(this).addClass("disabled");
        // $(this).html("in progress, please wait");

        // submit test start post
        $.ajax({
            type: "POST",
            url: $('span.automated-submit-url').html(),
            contentType:'application/json',            // sending this type of data to server
            data: JSON.stringify({'instrument': $('span.instrument').html(),
                                  'serial_number': $('span.serial-number').html(),
                                  'log_file_name': log_file_name}),  // data to send
            dataType: 'json',                          // expecting json back from server
            success: function (jsondata) {
                if (jsondata['submission_success']) {

                    // display job id and hidden fields
                    $('span.job-id').html(jsondata['job_id']);
                    $('span.log-file-name').html(log_file_name);
                    $('p.job-submission').removeClass('hidden').show();
                    $('p.log-file-name').removeClass('hidden').show();
                    $('.testpanel').removeClass('hidden').show();

                    // start results polling
                    job_polling(jsondata['job_id']);

                } else {
                    $('.job-errors').removeClass('hidden').html(jsondata['message']);
                }
            },
            error: function (responsedata) {
                // errors caught on server side and passed back in success block
                console.log("JSON ERROR!!");
                console.log(responsedata);
                $('p.job-errors').removeClass('hidden').html("Problem submitting automated job start request.");
            }
        });
    });

    // get log file contents
    const log_file_contents = () => {

        if ($('pre.tpb').text())
        {
            var numlines = $('pre.tpb').text().match(/\n\r?/g).length + 1;
        } else {
            var numlines = 0;
        }

        $.ajax({
            type: "POST",
            url: $('span.log-file-url').html(),
            contentType:'application/json',            // sending this type of data to server
            data: JSON.stringify({'log_file_name': log_file_name,
                                  'numlines': numlines}),  // data to send
            dataType: 'json',                          // expecting json back from server
            success: function (jsondata) {

                if ("errors" in jsondata)
                {


                }
                else if (jsondata["html"])
                {
                    $('pre.tpb').append(jsondata["html"]);
                    var scroll_container = $('.testpanel-body')
                    var height = scroll_container[0].scrollHeight;
                    scroll_container.scrollTop(height);

                }
            },
            error: function (responsedata) {
                // errors caught on server side and passed back in success block
                console.log("LOG FILE POST REQUEST: JSON ERROR!!")
                console.log(responsedata)
            },
            complete: function () {

            }
        });
    }

    // automated test status polling
    const job_polling = (job_id) => {
        $.ajax({
            type: "POST",
            url: $('span.polling-url').html(),
            contentType:'application/json',            // sending this type of data to server
            data: JSON.stringify({'job_id': job_id}),  // data to send
            dataType: 'json',                          // expecting json back from server
            success: function (jsondata) {

                if ("errors" in jsondata)
                {

                    hideLoading();

                    var error_html = "<div class=\"error-list\"><h5 class=\"text-danger\">Form Errors:</h5><ul>";

                    for (i=0; i < jsondata['errors'].length; i++) {
                        error_html += "<li class='text-danger'>" + jsondata['errors'][i] + "</li>";
                    }
                    error_html += "</ul></div>";

                    $('.job-errors').removeClass('hidden').html(error_html).show();

                    show_next_test_plan_row();

                }
                else if (jsondata["complete"])
                {
                    console.log(jsondata['data']['result']);

                    // read log file on last time
                    log_file_contents();

                    // fill out test results section
                    $('span.end-time').html(get_time());
                    $('span.test-duration').html(test_duration($('span.start-time').html(), $('span.end-time').html()));
                    $('span.log-file-path').html(jsondata['data']['log_file_path']);
                    $('span.results-csv-path').html(jsondata['data']['results_csv_path']);

                    $('span.test-result').html(jsondata['data']['result']['result'].toUpperCase());
                    if (jsondata['data']['result']['result'] == 'pass')
                    {
                        $('span.test-result').addClass('text-success');
                    }
                    else if (jsondata['data']['result']['result'] == 'fail')
                    {
                        $('span.test-result').addClass('text-danger');
                    }

                    // show results section and scroll page down
                    $('tr.test-summary').removeClass("hidden").show();
                    $('html, body').animate({scrollTop: $(document).height()}, 'slow');

                }   // end if complete
                else
                {
                    // read log file
                    log_file_contents();

                    // wait 1 second then make callback again
                    setTimeout( function(){job_polling(job_id);}, 200);

                    // scroll page down
                    $('html, body').animate({scrollTop: $(document).height()}, 'slow');
                }

            },
            error: function (responsedata) {
                // errors caught on server side and passed back in success block
                console.log("JOB STATUS POST REQUEST: JSON ERROR!!")
                console.log(responsedata)
            },
            complete: function () {

            }
        });
    }

});