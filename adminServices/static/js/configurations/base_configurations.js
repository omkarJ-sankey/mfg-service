


var selectedItemID = 0;
function addBasConfiguration(){
  $('#db_var_name').val("");
  $('#var_name').val("");
  $('#var_value').val("");
  $('#desc').val("");
  $('#add_to_cache').prop('checked', false);
  $('#frequently_used_var').prop('checked', false);
}

function updateAmenity(){
  const id = $('#base_conf_id').val();
  const db_var_name = $('#edit_db_var_name').val();
  const var_name = $('#edit_var_name').val();
  const var_value = $('#edit_var_value').val();
  const desc = $('#edit_desc').val();
  const add_to_cache = $('#add_to_cache_edit').is(':checked');
  const frequently_used_var = $('#frequently_used_edit_var').is(':checked');
  const requestData = {
      "id":id,
      "db_var_name":db_var_name,
      "var_name":var_name,
      "var_value":var_value,
      "desc":desc,
      "add_to_cache":add_to_cache,
      "frequently_used":frequently_used_var
  };
  $('#loader_for_mfg_ev_app').show();

  $.ajax({
      url: update_amenity_url,
      type: 'POST',
      dataType: 'json',
      contentType: 'application/json',
      data: JSON.stringify(requestData),
      headers: { "X-CSRFToken": token },
      success: function (result) {
          location.reload();
      },
      error:  function (result) {
          
          $('#loader_for_mfg_ev_app').hide();
          customAlert('Please enter valid data or image with proper size'); 
      }        
  });
}
function addBaseConfDetails(){
  const db_var_name = $('#db_var_name').val();
  const var_name = $('#var_name').val();
  const var_value = $('#var_value').val();
  const desc = $('#desc').val();
  const add_to_cache = $('#add_to_cache').is(':checked');
  const frequently_used_var = $('#frequently_used_var').is(':checked');
  const requestData = {
    "db_var_name":db_var_name,
    "var_name":var_name,
    "var_value":var_value,
    "desc":desc,
    "add_to_cache": add_to_cache,
    "frequently_used": frequently_used_var
  };
  $('#loader_for_mfg_ev_app').show();
  $.ajax({
      url: add_base_conf_url,
      type: 'POST',
      dataType: 'json',
      contentType: 'application/json',
      data: JSON.stringify(requestData),
      headers: { "X-CSRFToken": token },
      success: function (result) {
          location.reload();
      },
      error:  function (result) {
          
          $('#loader_for_mfg_ev_app').hide();
          customAlert('Please enter valid data or image with proper size'); 
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
  document.getElementById('base_configuration').classList.add('menu-item');
}
function importData() {
const input = document.createElement('input');
  input.type = 'file';
  input.click();

}
//Amenities Search
$(document).ready(function(){

clearSelected();
});

