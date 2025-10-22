window.onload = function () {
    displayAttachmentsToView();
    checkStatus();
}
$('.footer-year').html(`${new Date().getFullYear()}`);
let error_count = 0;
// disabling the navigation if status is delivered
function checkStatus() {
    if (email_status === 'Delivered' || email_status === 'In Progress') {
        document.getElementById("update-email-notification-btn").style.pointerEvents = "none";
        document.getElementById("view-email-save-as-draft").style.pointerEvents = "none";
        document.getElementById("send-email-now-view-page").style.pointerEvents = "none";
        document.getElementById("draft-schedule-send-div").hidden = true;
        document.getElementById("cancel-btn-container").hidden = true;
        document.getElementById("update-email-div").hidden = true;
        opacity_classes = document.querySelectorAll(".opacity-if-delivered");
        opacity_classes.forEach(element => {
            element.style.opacity = 0.5
        });
    }
}
document.getElementById('update-email-div').onclick = () => {
    $('#loader_for_mfg_ev_app').show();
}
//validations for date and time
function validate_date_and_time() {
    $('#date-time-error').html("")
    let schedule_date_string = $('#schedule-date').val().split('/')
    let schedule_time_string = $('#schedule-time').val().split(':')
    let schedule_date_time = new Date(Date.UTC(
        schedule_date_string[2],
        schedule_date_string[1] - 1,
        schedule_date_string[0],
        schedule_time_string[0],
        schedule_time_string[1]
    ));
    if ($('#schedule-date').val() === '' || $('#schedule-time').val() === '' || schedule_date_time < new Date()) {
        error_count += 1;
        $('#date-time-error').html("Please select valid date and time")
    }
    return !(error_count > 0)
}

// displaying the attachments
function displayAttachmentsToView() {
    inner_html_content_for_attchment_view = ''
    files_list.forEach((file) => {
        fileExtension = (file).substr((file).lastIndexOf('.') + 1);
        file_name = file.split("images/")[1]
        if (["xls", "xlsx", "csv"].includes(fileExtension.toLowerCase())) {
            file_type_image = excel_icon
        }
        else if (["png", "jpg", "jpeg"].includes(fileExtension.toLowerCase())) {
            file_type_image = image_icon
        }
        else if (["doc", "docx"].includes(fileExtension.toLowerCase())) {
            file_type_image = document_icon
        }
        else if (["pdf"].includes(fileExtension.toLowerCase())) {
            file_type_image = pdf_icon
        }
        else {
            file_type_image = common_filetype_icon
        }
        inner_html_content_for_attchment_view += `<div class="view-file-type-image-container"><img id="view-file-type-image" src=${file_type_image} alt=""><div class="file-name-div"><p class="file-name-para">${file_name}</p></div></div>`
    });
    if (inner_html_content_for_attchment_view !== '') {
        $("#email-notification-attachment-div").html(inner_html_content_for_attchment_view);
    }
    else {
        $("#email-notification-attachment-div").html('No attachments')
    }
}

let subject_element = document.getElementById("cancel-email-notification")
subject_element.onclick = () => {
    $("#confirm-msg-para").html(`Are you sure you want to remove the <span id="subject-name-span-in-cancel">${$("#view-subject").html()}</span> Notification?`);
}

date_to_schedule = {
    dateFormat: 'dd/mm/yy',
    showOn: "button",
    minDate: 0,
    buttonImage: "https://mfgevqastorage.blob.core.windows.net/static/images/calendar-1.png",
    buttonImageOnly: true,
    buttonText: "Select date"
}

$(function () {
    $("#schedule-date").datepicker(date_to_schedule);
});

function showToDatePicker() {
    $("#schedule-date").datepicker('show')
}

document.getElementById('send-email-now-view-page').onclick = () => {
    $('#loader_for_mfg_ev_app').show();
  }
document.getElementById('view-email-notification-schedule-btn').onclick = () => {

    if (validate_date_and_time()) {
        $('#loader_for_mfg_ev_app').show();
        $.ajax({
            url: schedule_email_notification_url,
            headers: { "X-CSRFToken": token },
            type: 'POST',
            dataType: 'json',
            data: {
                'schedule_date': $('#schedule-date').val(),
                'schedule_time': $('#schedule-time').val()
            },
            success: function (data) {
                if (data.status == 200) {
                    location.replace(list_of_email_notification_url)
                }
                else {
                    $('#loader_for_mfg_ev_app').hide();
                    $('#date-time-error').html(data.message)
                }
            },
            error: function (_error) {
                $('#loader_for_mfg_ev_app').hide();
            }
        });
    }
    else {
        error_count = 0;
    }

}
