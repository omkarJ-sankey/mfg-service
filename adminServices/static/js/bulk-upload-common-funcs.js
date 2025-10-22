

function removePreviosResults() {
    $('#errorheader')[0].style.display = 'none';

    document.getElementById('upload_message').style.display = 'flex';
    document.getElementById('bulk_upload_res_error').innerHTML = '';
    document.getElementById('bulk_upload_res_error').classList.remove('active_errors');

    document.getElementById('empty_column_errors').innerHTML = '';
    document.getElementById('empty_column_errors').classList.remove('active_errors');

    document.getElementById('bulk_upload_res_sucess').classList.remove('active_success')
    document.getElementById('bulk_upload_res_sucess').innerHTML = ''
}


function unableUploadButton() {
    let file = $("#selectSheet").get(0).files[0];
    $('#filename').text($('#selectSheet')[0].files[0].name)
    if (file) $('#upload').prop("disabled", false);
    $('#bulk_upload_error_list').html('');
    $('#errorheader')[0].style.display = 'none';


    document.getElementById('bulk_upload_res_error').innerHTML = '';
    document.getElementById('bulk_upload_res_error').classList.remove('active_errors');

    document.getElementById('empty_column_errors').innerHTML = '';
    document.getElementById('empty_column_errors').classList.remove('active_errors');

    document.getElementById('bulk_upload_res_sucess').classList.remove('active_success')
    document.getElementById('bulk_upload_res_sucess').innerHTML = ''
}

let successfully_upload = false
var bulk_progress_checker;

function progressChecker() {
    bulk_progress_checker = setInterval(function () {
        getBulkUploadProgress();
    }, 30000)
}

function getBulkUploadProgress() {
    $.ajax({
        url: bulk_upload_progress_bar_url,
        headers: { "X-CSRFToken": token },
        type: 'GET',
        processData: false,
        success: function (res, status) {
            if (res['errors_export_ready'] === true) {
                document.getElementById('error_export_button').style.display = 'block';
                document.getElementById('upload_message').style.display = 'flex';
            }
            if (res['status'] === false) {
                clearInterval(bulk_progress_checker);
                document.getElementById('progress_bar').value = "100"
                document.getElementById('progess_count').innerHTML = `${100}%`
            } else {
                document.getElementById('progress_bar').value = res['percentage']
                document.getElementById('progess_count').innerHTML = `${res['percentage']}%`
            }
        },
        error: function (error) {
            console.log(error);
        }
    });

}

document.getElementById('progress_bar_box').style.display = 'none';
document.getElementById('error_export_button').style.display = 'none';
if (progress_running_session === 'True') {
    progressChecker();
    document.getElementById('progress_bar_box').style.display = 'block';
    document.getElementById('upload_message').style.display = 'none';
}

if (errors_export_ready === 'True') {
    document.getElementById('error_export_button').style.display = 'block';
    document.getElementById('upload_message').style.display = 'flex';
}

function closeModalFunction() {
    if (successfully_upload) {
        $('#loader_for_mfg_ev_app').show();
        location.reload()
    }
    $('#filename').text('')
    $('#upload').prop("disabled", true);
    $('#selectSheet').val('');
}

function copy(id) {
    var copyText = document.getElementById(id);
    copyText.select();
    copyText.setSelectionRange(0, 99999)
    document.execCommand("copy");
}

function addData(list, colum_identifier) {
    if (list && list.length > 0) {
        var error_list_html = '';
        if (list.length > 0) {
            error_list_html += `
                        <div class="flex-error-box">
                            <div class="width50">
                                <b>Retail Barcode</b>
                            </div>
                            <div class="width50">
                                <b>Issues in Sheet</b>
                            </div>
                        </div><hr>`;
        }
        list.map(item => {
            error_list_html += `
                <div class="flex-error-box">
                    <div class="width50">
                        <button onclick="copy('${item[colum_identifier]}')" class="copy_icon">copy</button><a  id ='${item["Retail Barcode"]}'>${item["Retail Barcode"]}</a>
                        
                    </div>
                    <div class="width50">
                        <button onclick="copy('${item['Error']}')" class="copy_icon">copy</button><a  id ='${item['Error']}'>${item['Error']}</a>
                    </div>
                </div>
                <hr>    
            `
        });
        $('#errorheader')[0].style.display = 'block'
        $('#bulk_upload_error_list').html(error_list_html);
        $('#csverrorcount').text(list.length);
        $('#upload').attr("disabled", true)
    }

}

function getFrameWindow(frame) {
    if (frame.contentWindow) return frame.contentWindow
    else if(frame.contentDocument.document) return frame.contentDocument.document
    else return frame.contentDocument
}

function printError(data) {
    if (data) {
        var finalout = $('#containerlisterror')[0].innerHTML;
        var style = `
        <style>
            .show_error_list {
                    display: flex;
                    justify-content: center;
                }
            .copy_icon{
                    display:none;
                }
            .flex-error-box{
                width: 100%;
                display: flex; 
            }
            .width50 {
                    width: 50%;
                }
            html{
                font-family:'Roboto';
            }
        </style>
            `
        var frame1 = document.createElement('iframe');
        frame1.name = "frame1";
        frame1.style.position = "absolute";
        frame1.style.top = "-1000000px";
        document.body.appendChild(frame1);

        var frameDoc = getFrameWindow(frame1);
        frameDoc.document.open();
        frameDoc.document.write(`<html><head>${style}<title >All invalid entries (Promotions)</title>`);
        frameDoc.document.write('</head><body class="show_error_list">');
        frameDoc.document.write(finalout);
        frameDoc.document.write('</body></html>');
        frameDoc.document.close();
        setTimeout(function () {
            window.frames["frame1"].focus();
            window.frames["frame1"].print();
            document.body.removeChild(frame1);
        }, 500);
        return false;
    }
}

function PrintDiv(divid, title) {
    var frame1 = document.createElement('iframe');
    frame1.name = "frame1";
    frame1.style.position = "absolute";
    frame1.style.top = "-1000000px";
    document.body.appendChild(frame1);
    var frameDoc = getFrameWindow(frame1);    
    frameDoc.document.open();
    frameDoc.document.write(`<html><head><title>${title}</title>`);
    frameDoc.document.write('</head><body>');
    frameDoc.document.write(contents);
    frameDoc.document.write('</body></html>');
    return false;
}
