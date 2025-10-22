document.getElementById("unsubscribe-to-email-btn").disabled = true
$('#bulk-modal-upload').prop("disabled", true);
if (document.getElementById('selectSheet').value.length == 0){
  document.getElementById("progress_bar_box").hidden = true

}
function removeFiles() {
    $('#filename').text("")
    document.getElementById('selectSheet').value = null;
    $('#bulk-modal-upload').prop("disabled", true);
    if (document.getElementById('selectSheet').value.length == 0){
      document.getElementById("progress_bar_box").hidden = true
    }
}
function removeSuccessErrorExpotButton() {
    document.getElementById('bulk_upload_res_error').innerHTML = '';
    document.getElementById('bulk_upload_res_error').classList.remove('active_errors');

    document.getElementById('bulk_upload_res_sucess').innerHTML = ''
    document.getElementById('bulk_upload_res_sucess').classList.remove('active_success')

    document.getElementById('error_export_button').style.display = 'none';
    $("#progess_count").html(`0%`);
    document.getElementById("progress_bar").value = "0"

}
function removePreviosData() {
    document.getElementById('upload_message').style.display = 'flex';
    removeSuccessErrorExpotButton();
    removeFiles();
}
function unableUploadButton() {
    let file = $("#selectSheet").get(0).files[0];
    $('#filename').text($('#selectSheet')[0].files[0].name)
    if (file) $('#bulk-modal-upload').prop("disabled", false);
    if (document.getElementById('selectSheet').value.length == 0){
      document.getElementById("progress_bar_box").hidden = true
    }
}
function removeMessages() {
    $("#unsubscribe-user-error").html("")
    $("#unsubscribe-user-success").html("");
}

document.getElementById("cancel").onclick = () => {
    removeMessages();
    $("#email-input").val("")
}

function emailValidator(value) {
    const regex = /^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]+$/;
    if (!regex.test(value) || value.trim().length == 0) {
        $("#unsubscribe-user-error").html("Invalid user emailID");
        document.getElementById("unsubscribe-to-email-btn").disabled = true;
    }
    else {
        $("#unsubscribe-user-error").html("");
        document.getElementById("unsubscribe-to-email-btn").disabled = false;
    }
}

function getProgress() {
    $.ajax({
        url: get_progress_url,
        headers: { "X-CSRFToken": token },
        type: 'GET',
        success: function (res) {
            progress_value = res.response.progress_value
            document.getElementById("progress_bar").value = progress_value
            $("#progess_count").html(`${progress_value}%`);
            if (Number(progress_value) < 100) {
                getProgress();
            }
            else {
                document.getElementById('bulk_upload_res_sucess').classList.add('active_success')
                document.getElementById('bulk_upload_res_sucess').innerHTML = ''
                $('#bulk_upload_res_sucess').append(`<h6 class="bulk_upload_success">Emails Unsubscribed Successfully</h6>`)
                $('.custom_file_upload').show();
                document.getElementById("bulk-modal-close").disabled = false;
                document.getElementById("bulk-modal-upload").disabled = false;
                removeFiles();
            }
        },
        error: function (error) {
            console.log(error)
        }
    });
}
function sendUserEmail() {
    let user_email = $("#email-input").val()
    if (user_email.length != 0) {
        $('#loader_for_mfg_ev_app').show();
        $.ajax({
            url: unsubscribe_email_url,
            data: JSON.stringify({
                "email": user_email
            }),
            headers: { "X-CSRFToken": token },
            type: 'POST',
            success: function (res) {
                $('#loader_for_mfg_ev_app').hide();
                if (res.response.status) {
                    $("#email-input").val("")
                    $(".view-email-notification-btns").click()
                    $("#unsubscribe-user-success").html(res.response.message);
                } else {
                    $(".view-email-notification-btns").click()
                    $("#unsubscribe-user-error").html(res.response.message);
                }
            },
            error: function (_) {
                $('#loader_for_mfg_ev_app').hide();
            }
        });
    }
}
function processCSV() {
    let file = $("#selectSheet").get(0).files[0];
    if (document.getElementById('selectSheet').value.length){
      document.getElementById("progress_bar_box").hidden = false
    }
    else{
      document.getElementById("progress_bar_box").hidden = true
    }
    if (file) {
        $('#loader_for_mfg_ev_app').show();
        removeSuccessErrorExpotButton();
        document.getElementById('upload_message').style.display = 'none';
        $.ajax({
            url: uploadSheet_unsubscribe_email_url,
            data: file,
            headers: { "X-CSRFToken": token },
            type: 'POST',
            processData: false,
            success: function (res) {
                $('#loader_for_mfg_ev_app').hide();
                if (res.response.status == false) {
                    document.getElementById('upload_message').style.display = 'flex';
                    document.getElementById('bulk_upload_res_error').classList.add('active_errors')
                    document.getElementById('bulk_upload_res_error').innerHTML = ''
                    $('#bulk_upload_res_error').append(`<h6 class="bulk_upload_error">${res.response.error}</h6>`)
                }
                else {
                    // $('#bulkupload').modal({ backdrop: 'static', keyboard: false })
                    $('.custom_file_upload').hide();
                    document.getElementById("bulk-modal-close").disabled = true;
                    document.getElementById("bulk-modal-upload").disabled = true;
                    getProgress();
                    if (res.response.status == true && res.response.error != '') {
                        document.getElementById('error_export_button').style.display = 'block';
                        document.getElementById('upload_message').style.display = 'flex';
                        document.getElementById('bulk_upload_res_error').classList.add('active_errors')
                        document.getElementById('bulk_upload_res_error').innerHTML = ''
                        $('#bulk_upload_res_error').append(`<h6 class="bulk_upload_error">${res.response.error}</h6>`)
                    }
                }
            },
            error: function (error) {
                document.getElementById('upload_message').style.display = 'flex';
                $('#loader_for_mfg_ev_app').hide();
                if (error.status === 504) customAlert('Timeout - Please minimize data, and try again.');
                else if (error.status === 502) customAlert(`${error.statusText} , please try again.`);
                else customAlert(`Bulk upload intruppted due to - ${error.responseText}, please try again.`);
            }
        });
    }
    else {
        removeSuccessErrorExpotButton()
        document.getElementById('upload_message').style.display = 'flex';
        document.getElementById('bulk_upload_res_error').classList.add('active_errors')
        document.getElementById('bulk_upload_res_error').innerHTML = ''
        $('#bulk_upload_res_error').append(`<h6 class="bulk_upload_error">"Please select a file"</h6>`)
    }
}