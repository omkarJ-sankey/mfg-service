$(function () {
    $("#from_date").datepicker();
});
$(function () {
    $("#to_date").datepicker();
});

function filterFunction(type, val) {
    if (type === 'from_site') {
        var list = document.getElementsByClassName("to_site_options");
        for (var i = 0; i < list.length; i++) {
            list[i].style.display = 'block';
        }
        document.getElementById(`to_site_option${val}`).style.display = 'none';
    }
    let new_url = ''
    const params = new URLSearchParams(url_u);
    params.forEach(function (value, key) {
        if (key !== type) new_url += `&${key}=${value}`
    });
    if (type) window.location.href = `${window_radirect_location}?${type}=${val}${new_url}`;


}

const slider = document.querySelector('#sliding_table');
let isDown = false;
let startX;
let scrollLeft;

slider.addEventListener('dblclick', (e) => {
    isDown = true;
    if (startX) startX = null;
    else {
        startX = e.pageX - slider.offsetLeft;
        scrollLeft = slider.scrollLeft;
    }
});
slider.addEventListener('mousemove', (e) => {
    if (!isDown) return;
    e.preventDefault();
    if (startX) {

        const x = e.pageX - slider.offsetLeft;
        const walk = (x - startX) * 4; //scroll-fast
        slider.scrollLeft = scrollLeft - walk;
    }
});
// import file logic
function onCSVUpload() {

    $('#loader_for_mfg_ev_app').show();
    let file = $("#selectSheet").get(0).files[0];

    var data = new FormData()
    data.append('file', file)
    $.ajax({
        url: import_reconciliation_data_url,
        data: file,
        headers: { "X-CSRFToken": token },
        // dataType: 'form-data',
        type: 'POST',
        processData: false,
        success: function (res, status) {
            $('#loader_for_mfg_ev_app').hide();
            document.getElementById('bulk_upload_res_error').classList.remove('active_errors')
            document.getElementById('empty_column_errors').classList.remove('active_errors')
            document.getElementById('bulk_upload_res_error').innerHTML = ''
            document.getElementById('empty_column_errors').innerHTML = ''
            if (res.status) {

                if (res.fields) {
                    document.getElementById('empty_column_errors').classList.add('active_errors')
                    let error = ''
                    for (var i = 0; i < res.data.length; i++) {
                        error += `<p class="error_fields">${i + 1}.${res.data[i]}</p>`
                    }

                    var content = `
                                <div>
                                    <h6 class="filed_error_heading">Following columns are missing in "reconciliation_Worldpay-Acquiri" tab</h6><br>
                                    <div class="fields_errors">
                                        ${error}
                                    <div>
                                </div>`
                    $("#empty_column_errors").append(content)
                }
                else {

                    document.getElementById('empty_column_errors').innerHTML = ''
                    document.getElementById('empty_column_errors').classList.remove('active_errors')
                    addData(res.data);
                }
            }
            else {

                document.getElementById('bulk_upload_res_error').classList.add('active_errors')
                document.getElementById('bulk_upload_res_error').innerHTML = ''
                $('#bulk_upload_res_error').append(`<h6 class="bulk_upload_error">${res.message}</h6>`)
            }
        },
        error: function (res) {
            $('#loader_for_mfg_ev_app').hide();
        }
    });


}
function copy(id) {
    var copyText = document.getElementById(id);
    copyText.select();
    copyText.setSelectionRange(0, 99999)
    document.execCommand("copy");
}
function addData(list) {
    if (list && list.length > 0) {
        var retailBHTML = '';
        var productHTML = '';
        list.map(item => {
            productHTML += ` <div class="retail_style"><button onclick="copy('${item['Transaction date']}')" class="copy_icon">copy</button><a  id ='${item['Transaction date']}'>${item['Transaction date']}</a></div>`
            retailBHTML += ` <div class="retail_style"><button onclick="copy('${item["Order ID"]}')" class="copy_icon">copy</button><a  id ='${item["Order ID"]}'>${item["Order ID"]}</a></div>`
        });
        $('#errorheader')[0].style.display = 'block'
        $('#prodduct').html(productHTML);
        $('#retailbarcode').html(retailBHTML);
        $('#csverrorcount').text(list.length);
        $('#csverrorcount').text(list.length);
        $('#filename').text($('#selectSheet')[0].files[0].name);
        $('#upload').attr("disabled", true);
    }

}
function printError(data) {
    if (data) {
        const finalout = $('#containerlisterror')[0].innerHTML;
        const style = `
            <style>
                .show_error_list {
                        display: flex;
                        justify-content: center;
                    }
                .copy_icon{
                        display:none;
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
        var frameDoc = frame1.contentWindow ? frame1.contentWindow : frame1.contentDocument.document ? frame1.contentDocument.document : frame1.contentDocument;
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
    var frameDoc = frame1.contentWindow ? frame1.contentWindow : frame1.contentDocument.document ? frame1.contentDocument.document : frame1.contentDocument;
    frameDoc.document.open();
    frameDoc.document.write(`<html><head><title>${title}</title>`);
    frameDoc.document.write('</head><body>');
    frameDoc.document.write(contents);
    frameDoc.document.write('</body></html>');
    return false;
}