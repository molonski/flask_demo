
$(document).ready(function() {

    // start querying job status on page load
    const start_job_polling = () => {

        var job_id = $('span.job-id').html();

        if (job_id) {
            job_polling(job_id);
        }

        $('tr.submit').hide();
    }

    // consolidate hide loading message code to its own function
    const hideLoading = () => {
        // hide loading message
        $('.loading').hide();

        // clear job id
        $('span.job-id').html('');

        // show submit button again
        $('tr.submit').show();
    }

    // function to check report job status
    const job_polling = (job_id) => {

        $.ajax({
            type: "POST",
            url: "/production-reports/job-status/",
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

                    $('.error-list').html(error_html);

                    // show submit button again
                    $('tr.submit').show()

                }
                else if (jsondata["complete"])
                {
                    $( "#progressbar" ).progressbar({  value: 100 });

                    hideLoading();

                    $('.error-list').hide();

                    // show submit button again
                    $('tr.submit').show()

                    // job done render report
                    $('.report-results').html(jsondata['html']);

                    if (jsondata['data']['test_count'] > 0) {
                        // Plotly Plots
                        var layout = {autosize: false,
                                      width: 500,
                                      height: 400,
                                      margin: {
                                        l: 50,
                                        r: 50,
                                        b: 20,
                                        t: 20,
                                        pad: 20
                                      }
                                      };

                        // All Test Pass Rates - Pie Chart
                        var all_pie = [{
                            values: jsondata['data']['all_pie']['values'],
                            labels: jsondata['data']['all_pie']['labels'],
                            marker: {
                                colors: jsondata['data']['all_pie']['colors'],
                            },
                            title: {
                                    text: 'Pass Rates for All Tests<br>&nbsp;<br>&nbsp;',
                                    font: {family: 'Arial',
                                           size: 20}
                            },
                            type: 'pie'
                        }];
                        Plotly.newPlot('all-results-pie', all_pie, layout, {showSendToCloud:false});

                        // Unique Serial Number Pass Rates - Pie Chart
                        var sn_pie = [{
                            values: jsondata['data']['sn_pie']['values'],
                            labels: jsondata['data']['sn_pie']['labels'],
                            marker: {
                                colors: jsondata['data']['sn_pie']['colors'],
                            },
                            title: {
                                    text: 'Pass Rates by Unique SN<br>&nbsp;<br>&nbsp;',
                                    font: {family: 'Arial',
                                           size: 20},
                            },
                            type: 'pie'
                        }];
                        Plotly.newPlot('unique-sn-results-pie', sn_pie, layout, {showSendToCloud:false});

                        // Test Duration - Bar Chart
                        var duration_bar = [{
                            type: 'bar',
                            x: jsondata['data']['duration_bar']['x'],
                            y: jsondata['data']['duration_bar']['y'],
                            width: jsondata['data']['duration_bar']['widths']
                        }];
                        var last_x = jsondata['data']['duration_bar']['x'][jsondata['data']['duration_bar']['x'].length - 1];
                        var duration_layout = {
                            xaxis: {
                                title: {
                                    text: 'Time (min)',
                                    font: {
                                        family: 'Arial',
                                        size: 14
                                    }
                                },
                                range: [0, Math.floor(last_x + 1)]
                            },
                            yaxis: {
                                title: {
                                    text: 'Number Of Tests',
                                    font: {
                                        family: 'Arial',
                                        size: 14
                                    }
                                },
                            }
                        };
                        Plotly.newPlot('duration-bar', duration_bar, duration_layout, {showSendToCloud:false});

                        // Retest Rates - Bar Chart
                        var retest_bar = [{
                            type: 'bar',
                            x: jsondata['data']['retest_bar']['x'],
                            y: jsondata['data']['retest_bar']['y'],
                            width: jsondata['data']['retest_bar']['widths']
                        }];
                        var retest_layout = {
                            title: {
                                    text: 'Retest Counts<br>&nbsp;<br>&nbsp;',
                                    font: {family: 'Arial',
                                           size: 20},
                                },
                            xaxis: {
                                title: {
                                    text: 'Number of Retests',
                                    font: {
                                        family: 'Arial',
                                        size: 14
                                    }
                                },
                                range: [1, 10]
                            },
                            yaxis: {
                                title: {
                                    text: 'Number of Units Retested',
                                    font: {
                                        family: 'Arial',
                                        size: 14
                                    }
                                },
                            }
                        };
                        Plotly.newPlot('retest-bar', retest_bar, retest_layout, {showSendToCloud:false});

                        // Retest Pass Rates - Pie Chart
                        var retest_pie = [{
                            values: jsondata['data']['retest_pie']['values'],
                            labels: jsondata['data']['retest_pie']['labels'],
                            marker: {
                                colors: jsondata['data']['retest_pie']['colors'],
                            },
                            title: {
                                    text: 'Retest Pass/Fail Results<br>&nbsp;<br>&nbsp;',
                                    font: {family: 'Arial',
                                           size: 20},
                            },
                            type: 'pie'
                        }];
                        Plotly.newPlot('retest-pie', retest_pie, layout, {showSendToCloud:false});


                        // activate datatables
                        $('#sensors').DataTable({
                            data: jsondata['data']['sensors'],
                            columns: jsondata['data']['table_column_names'],
                            "paging": false
                        });

                        $('#calcs').DataTable({
                            data: jsondata['data']['calcs'],
                            columns: jsondata['data']['table_column_names'],
                            "paging": false
                        });

                        $('#components').DataTable({
                            data: jsondata['data']['components'],
                            columns: jsondata['data']['table_column_names'],
                            "paging": false

                        });

                    }   // end if test_count > 0

                }   // end if complete
                else
                {
                    $( "#progressbar" ).progressbar({  value: jsondata['progress'] });
                    // wait 1 second then make callback again
                    setTimeout( function(){job_polling(job_id);}, 1000);
                }

            },
            error: function (responsedata) {
                // errors caught on server side and passed back in success block
                console.log("JSON ERROR!!")
                console.log(responsedata)
            },
            complete: function () {

            }
        });
    }

    start_job_polling()

    // set initial job polling status to 0
    $( "#progressbar" ).progressbar({  value: 0 });

});
