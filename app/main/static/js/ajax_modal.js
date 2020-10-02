$(document).ready(function() {

    $('#TestResultModal').modal({ show: false})

    // AJAX call to fetch results
    $('.modallink').click(function () {
        var data = {"testlog_id": $(this).data('id')};
        $.ajax({
            type: 'POST',
            url: $('span.modal_url').html(),
            contentType: 'application/json',
            dataType: 'html',
            data:  JSON.stringify(data),
            success: function (responsedata) {
                $('.single-result-template').html(responsedata);
                $('#TestResultModal').modal('show');
            },
            error: function (responsedata) {
                $('.single-result-template').html(responsedata);
                alert('doh');
            },
            complete: function () {

            }
        });
    });
});