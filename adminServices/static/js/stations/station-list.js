function showDownloadError() {
    $('#no_download_box').modal('show');
    setTimeout(function () { $('#no_download_box').modal('hide'); }, 3000);
}

function mapAmpecoSiteName() {
    console.log('Map Ampeco Site Name button clicked');
    $.ajax({
        url: map_ampeco_site_titles_url,
        type: 'POST',
        headers: {
            'X-CSRFToken': (typeof token !== 'undefined' ? token : ''),
            'Content-Type': 'application/json'
        },
        success: function(data) {
            if (data.error) {
                alert('Error: ' + data.error);
            } else {
                alert(
                    'Updated ' + data.stations.count + ' Ampeco site titles!\\n' +
                    'Updated ' + data.charge_points.count + ' Ampeco charge point names!'
                );
                console.log('Updated stations:', data.stations.updated);
                console.log('Updated charge points:', data.charge_points.updated);
            }
        },
        error: function(xhr, status, error) {
            alert('Error updating Ampeco site titles');
            console.error(error);
        }
    });
}

function orderByFunction(type) {
    let update_order = 'Descending';
    let new_url = '';
    const params = new URLSearchParams(url_u);
    params.forEach(function (value, key) {
        if (key !== type) new_url += `&${key}=${value}`;
        else {
            if (value === `Ascending`) update_order = 'Descending'
            else update_order = 'Ascending'
        }
    });

    document.getElementById(type).classList.toggle('order-by');
    window.location.href = `${window_radirect_location}?${type}=${update_order}${new_url}`;

}
function checkSearchBoxValue() {
    filterFunction('search', document.getElementById('search_station_param').value)
}
function appendDeleteContent(id, sid, name) {
    const delete_url = document.location.origin + `/administrator/stations/delete-station/${id}/`
    const content = `
        <p class="delete-modal-text">Are you sure you want to remove <strong>${sid}</strong>, <strong>${name}</strong>?</p>
        <div class="google_maps_submit_buttons">
            <div class="google_maps_container_buttons">
                
                <button class="cancle_button" data-bs-dismiss="modal">No</button>
                &nbsp;
                <a href="${delete_url}"><button class="done_button">Yes</button></a>
            </div>
        </div>
    `
    document.getElementById('delete-modal-content').innerHTML = content
}


function processCSV() {

    const file = $("#selectSheet").get(0).files[0];
    if (file) {
        $('#loader_for_mfg_ev_app').show();
        var data = new FormData();
        data.append('file', file);

        document.getElementById('upload_message').style.display = 'none';
        $.ajax({
            url: uploadSheet_stations_url,
            data: file,
            headers: { "X-CSRFToken": token },
            // dataType: 'form-data',
            type: 'POST',
            processData: false,
            success: function (res) {
                document.getElementById('progress_bar_box').style.display = 'block';
                data = res.response.data
                let error_list = []
                let have_field_errors = false
                if (res.response.status) {

                    document.getElementById('bulk_upload_res_error').innerHTML = ''
                    if (res.response.data.fields) {
                        have_field_errors = true
                        document.getElementById('bulk_upload_res_error').classList.remove('active_errors')
                        let error = ''
                        for (var i = 0; i < res.response.data.data.length; i++) {
                            error += `<p class="error_fields">${i + 1}.${res.response.data.data[i]}</p>`
                        }
                        var content = `
                                    <div>
                                        <h6 class="filed_error_heading">Following columns are missing in "Sites" tab</h6><br>
                                        <div class="fields_errors">
                                            ${error}
                                        <div>
                                    </div>`
                        document.getElementById('empty_column_errors').classList.add('active_errors')
                        $("#empty_column_errors").append(content)
                        $("#empty_column_errors").append('<div class="horizontal-lines"></div>')
                        document.getElementById('bulk_upload_res_sucess').classList.remove('active_success')
                        document.getElementById('bulk_upload_res_sucess').innerHTML = ''
                    }
                    else {
                        error_list = [...error_list, ...res.response.data.data];
                    }
                    if (res.response.c_data.fields) {
                        have_field_errors = true
                        document.getElementById('empty_column_errors').classList.add('active_errors')
                        let error = ''
                        for (i = 0; i < res.response.c_data.data.length; i++) {
                            error += `<p class="error_fields">${i + 1}.${res.response.c_data.data[i]}</p>`
                        }

                        content = `
                                    <div>
                                        <h6 class="filed_error_heading">Following columns are missing in "Chargepoint" tab</h6><br>
                                        <div class="fields_errors">
                                            ${error}
                                        <div>
                                    </div>`
                        $("#empty_column_errors").append(content)
                        $("#empty_column_errors").append('<div class="horizontal-lines"></div>')
                    } else {
                        error_list = [...error_list, ...res.response.c_data.data];
                    }
                    if (res.response.sites_data.fields) {
                        have_field_errors = true
                        document.getElementById('empty_column_errors').classList.add('active_errors')
                        let error = ''
                        for (i = 0; i < res.response.sites_data.data.length; i++) {
                            error += `<p class="error_fields">${i + 1}.${res.response.sites_data.data[i]}</p>`
                        }
                        content = `
                                    <div>
                                        <h6 class="filed_error_heading">Following columns are missing in "MFG" tab</h6><br>
                                        <div class="fields_errors">
                                            ${error}
                                        <div>
                                    </div>`
                        $("#empty_column_errors").append(content)
                    } else {
                        error_list = [...error_list, ...res.response.sites_data.data];
                    }
                    if (res.response.valeting_machine_data.fields) {
                        have_field_errors = true
                        document.getElementById('empty_column_errors').classList.add('active_errors')
                        let error = ''
                        for (i = 0; i < res.response.valeting_machine_data.data.length; i++) {
                            error += `<p class="error_fields">${i + 1}.${res.response.valeting_machine_data.data[i]}</p>`
                        }
                        content = `
                                    <div>
                                        <h6 class="filed_error_heading">Following columns are missing in "Valeting Machine" tab</h6><br>
                                        <div class="fields_errors">
                                            ${error}
                                        <div>
                                    </div>`
                        $("#empty_column_errors").append(content)
                    } else {
                        error_list = [...error_list, ...res.response.valeting_machine_data.data];
                    }
                    if (error_list.length > 0 || have_field_errors === true) {

                        document.getElementById('bulk_upload_res_error').classList.add('active_errors')
                        document.getElementById('bulk_upload_res_error').innerHTML = ''
                        $('#bulk_upload_res_error').append(`<h6 class="bulk_upload_error">Bulk upload is interrupted by the below issues. Please update the sheet and try again.</h6>`)
                        addData(error_list, 'Station ID');

                    }
                    else {
                        document.getElementById('empty_column_errors').innerHTML = ''
                        document.getElementById('empty_column_errors').classList.remove('active_errors')

                        document.getElementById('bulk_upload_res_sucess').classList.add('active_success')
                        document.getElementById('bulk_upload_res_sucess').innerHTML = ''
                        $('#bulk_upload_res_sucess').append(`<h6 class="bulk_upload_success">Successfully uploaded File</h6>`)
                    }
                }
                else {
                    document.getElementById('bulk_upload_res_error').classList.add('active_errors')
                    document.getElementById('bulk_upload_res_error').innerHTML = ''
                    $('#bulk_upload_res_error').append(`<h6 class="bulk_upload_error">${res.response.error}</h6>`)
                }
                $('#loader_for_mfg_ev_app').hide()

            },
            error: function (error) {
                $('#loader_for_mfg_ev_app').hide();
                if (error.status === 504) customAlert('Timeout - Please minimize data, and try again.');
                else if (error.status === 502) customAlert(`${error.statusText} , please try again.`);
                else customAlert(`Bulk upload intruppted due to - ${error.responseText}, please try again.`);
            }
        });
        progressChecker();
    }
    $('#upload').prop("disabled", true);
    $('#selectSheet').val('');

}

