


var selectedItemID = 0;
function addOCPIConfiguration(){
  $('#db_var_name').val("");
  $('#var_name').val("");
  $('#var_value').val("");
  $('#desc').val("");
}

function addOCPIConfDetails(){
  const name = $('#var_name').val();
  const endpoint = $('#var_endpoint').val();
  // const var_value = $('#var_value').val();
  const ocpi_token = $('#var_token').val();
  // const add_to_cache = $('#add_to_cache').is(':checked');
  // const frequently_used_var = $('#frequently_used_var').is(':checked');
  const requestData = {
    "name":name,
    "endpoint":endpoint,
    "ocpi_token":ocpi_token,
    // "desc":desc,
    // "add_to_cache": add_to_cache,
    // "frequently_used": frequently_used_var
  };
  $('#loader_for_mfg_ev_app').show();
  $.ajax({
      url: ocpi_add_credentials_url,
      type: 'POST',
      dataType: 'json',
      contentType: 'application/json',
      data: JSON.stringify(requestData),
      headers: { "X-CSRFToken": token },

      success: function (res, _status) {
        // console.log("res 2 id : ",res)
        if (res.status) {
            // window.location.href = window.origin + res.url + ocpi_add_credentials_url
            // customAlert(res.message)
            location.reload();

        }
        else {
            $('#loader_for_mfg_ev_app').hide();
            customAlert("Failed to register token")
        }
      },
      error: function (res) {
          $('#loader_for_mfg_ev_app').hide();
          customAlert("Something went wrong");
      }


  });
}
function updateBasConfigurationsDetailsFunc(
    id,
    base_conf_name,
    base_conf_key,
    base_conf_desc,
    base_conf_value,
    add_to_cache,
    frequently_used_var,
  ){
    $('#edit_db_var_name').val(UnicodeDecodeB64(base_conf_name));
    $('#edit_var_name').val(UnicodeDecodeB64(base_conf_key));
    $('#edit_var_value').val(UnicodeDecodeB64(base_conf_value));
    $('#edit_desc').val(UnicodeDecodeB64(base_conf_desc));
    $('#base_conf_id').val(id);
    $('#add_to_cache_edit').prop('checked', UnicodeDecodeB64(add_to_cache)==='true');
    $('#frequently_used_edit_var').prop('checked', UnicodeDecodeB64(frequently_used_var)==='true');
}
function switchToBaseconfEditor(){   
  const base_conf_name = b64EncodeUnicode($('.view-db-var-name').html());
  const base_conf_key = b64EncodeUnicode($('.view-var-name').html());
  const base_conf_desc = b64EncodeUnicode($('.view-desc').html());
  const base_conf_value = b64EncodeUnicode($('.view-var-value').html());
  const add_to_cache = b64EncodeUnicode(($('.add-to-cache-desc').html() === 'Yes'? "true":"false"));
  const frequently_used_var = b64EncodeUnicode(($('.frequently-used-var-desc').html() === 'Yes'? "true":"false"));
  $('#updateBasConfigurations').modal('show');
  updateBasConfigurationsDetailsFunc(
    selectedItemID,
    base_conf_name,
    base_conf_key,
    base_conf_desc,
    base_conf_value,
    add_to_cache,
    frequently_used_var
  );
}
function viewBaseConfigurationDetails(
  id,
  base_conf_name,
  base_conf_key,
  base_conf_desc,
  base_conf_value,
  add_to_cache,
  frequently_used_var,
){
  selectedItemID = id;
  $('.view-db-var-name').html(UnicodeDecodeB64(base_conf_name));
  $('.view-var-name').html(UnicodeDecodeB64(base_conf_key));
  $('.view-var-value').html(UnicodeDecodeB64(base_conf_value));
  $('.view-desc').html(UnicodeDecodeB64(base_conf_desc));
  $('.add-to-cache-desc').html(UnicodeDecodeB64(add_to_cache)==="true"?'Yes':'No');
  $('.frequently-used-var-desc').html(UnicodeDecodeB64(frequently_used_var)==="true"?'Yes':'No');
}


// Tooltips
$(function () {
$('[data-toggle="tooltip"]').tooltip()
})

function clearSelected() {
  document.getElementById('ocpi_configuration').classList.add('menu-item');
}
function importData() {
const input = document.createElement('input');
  input.type = 'file';
  input.click();

}

$(document).ready(function(){
clearSelected();
$('#listingTable').on('click', '#update-configurations', function(e) {
        e.preventDefault();
        const id = $(this).data('id');
        if (id) {
            window.location.href = `/administrator/configurations/update-ocpi-configurations/${id}/`;
        }
    });
});



document.addEventListener('DOMContentLoaded', function() {
        var statusBox = document.getElementById('statusBox');
        if (statusBox) {
            statusBox.addEventListener('click', function() {
                if (statusBox.textContent.trim().toLowerCase() === 'active') {
                    statusBox.textContent = 'Inactive';
                } else {
                    statusBox.textContent = 'Active';
                }
            });
        }
    });


function submitUpdatedCredentialsData(){

//  var config_id = ocpi_details.id
  var dataToUpload = {
    id: config_id,
  };

  let name =  document.getElementById('upload_name_data').value;
  let emsp_token= document.getElementById('upload_emsp_token_data').value;
  let status= document.getElementById('statusBox').textContent.trim();
  let cpo_token = document.getElementById('upload_cpo_token_data').value;
  let endpoint = document.getElementById('upload_endpoint_data').value;
  if (prev_data["name"] !== name){
    dataToUpload["name"]=name
  }
  if (prev_data["token"] !== emsp_token){
    dataToUpload["token"]=emsp_token
  }
  if (prev_data["status"] !== status){
    dataToUpload["status"]=status
  }
  dataToUpload["cpo_token"] = cpo_token
  dataToUpload["endpoint"] = endpoint
  
  $('#loader_for_mfg_ev_app').show();
        $.ajax({
            url: update_ocpi_data_url,
            data: JSON.stringify(dataToUpload),
            headers: { "X-CSRFToken": token },
            dataType: 'json',
            type: 'POST',
            contentType: 'application/json',

            success: function (res, _status) {

                if (res.status) {
                  location.reload();
                    // window.location.href = window.origin + res.url
                    // console.log(" window.origin + res.url : ",window.origin + res.url)
                }
                else {
                    $('#loader_for_mfg_ev_app').hide();
                    location.reload()
                    customAlert(res.message)
                    // try {
                    //     if (res.message == "Unable to update credentials") {
                    //         scrollPageFunction('formSection')
                    //         document.getElementById(`error_field0`).innerHTML = res.message;
                    //     }
                    // }
                    // catch (err) {
                    // }
                    // customAlert(res.message)
                }
            },
            error: function (res) {
                $('#loader_for_mfg_ev_app').hide();
                customAlert("Something went wrong");
            }
        });
}