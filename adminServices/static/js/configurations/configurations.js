
selectedItemID = 0;

function editConnectorDetails(id, type,sorting_order, app_version, url, alt_image_path) {
  $("#add_images_container1").html(`<div class="profile_container">
                      <div id='discard1' class='discard'>x</div>
                      <img  class="profile_image_ service_image" src=${group_png_url} >
                  </div>`);

  $("#add_alt_images_container2").html(`<div class="profile_container">
      <div id='discard_edit_alt_img' class='discard'>x</div>
      <img  class="profile_image_ edit_alt_conn_image service_image" src=${group_png_url} >
  </div>`);

  const connector_names = connectors_names_list
  if (connector_names.includes(type)) $('#conn_type').val(type);
  else $('#conn_type').val("null");
  $('#conn_img').val(url);
  $('#alt_image_edit_path_src').val(alt_image_path);
  $('.profile_image_').attr("src", url);
  $('.edit_alt_conn_image').attr("src", alt_image_path);
  $('#conn_id').val(id);
  $('#update_sorting_order').val(sorting_order);
  $('#update_app_version').val(app_version);
}

function openConnectorEditor() {
  const type = $('.view-con-typ').html();
  const url = $('.view-con-img').attr('src');
  const altUrl = $('.view-alt-con-img').attr('src');
  const sorting_order = $('#view_sorting_order').html();
  const app_version = $('#view_app_version').html();
  $('#editConnector').modal('show');
  editConnectorDetails(selectedItemID, type,sorting_order, app_version,url, altUrl);
}

$('#add_sorting_order').on('input', function (e) {
  setTimeout(function(){ checkUniqueIdAvailability('add_sorting_order',
      'add_sorting_order_error','add_connector_btn'); }, 200);
  
});

$('#update_sorting_order').on('input', function (e) {
  setTimeout(function(){ checkUniqueIdAvailability('update_sorting_order',
      'update_sorting_order_error','update_connector_btn','conn_id'); }, 200);
  
});
function addConnector() {
  $('#image_path_src').val("");
  $('#connector_plug_type').val("");
  $('#add_sorting_order').val("");
  $("#add_images_container").html(` <div id="d-flex flex-column"  class="mr-tp">
                    <input type="file" id="i_file"  name="filename" hidden accept=".jpeg,.jpg,.png"/>
                    <label for="i_file" class="add_images_label"><b class=" pick-img">Add Image</b</label>              
                    </div>`);
  $("#add_alt_images_container").html(` <div id="d-flex flex-column" class="mr-tp">
      <input type="file" id="i_alt_file" name="alt_image_path" hidden accept=".jpeg,.jpg,.png" />
      <label for="i_alt_file" class="add_images_label"><strong class=" pick-img">Add
              Image</strong></label>

  </div>`);
}

function updateConnector() {
  const id = $('#conn_id').val();
  const type = $('#conn_type').val();
  const sorting_order = $('#update_sorting_order').val();
  const app_version = $('#update_app_version').val();
  const url = $('#conn_img').val();
  const altUrl = $('#alt_image_edit_path_src').val();

  const requestData = {
    "id": id,
    "type": type,
    "sorting_order": sorting_order,
    "app_version": app_version,
    "url": url,
    "altUrl": altUrl,
  };

  $('#loader_for_mfg_ev_app').show();
  $.ajax({
    url: update_connector_url,
    type: 'POST',
    dataType: 'json',
    contentType: 'application/json',
    data: JSON.stringify(requestData),
    headers: { "X-CSRFToken": token },
    success: function (result) {
      location.reload();
    },
    error: function (result) {
      $('#loader_for_mfg_ev_app').hide();
      customAlert('Please enter valid data or image with proper size');
    }
  });
}

function addConnectorDetails() {
  const type = $('#connector_plug_type').val();
  const url = $('#image_path_src').val();
  const altUrl = $('#alt_image_path_src').val();
  const sorting_order = $("#add_sorting_order").val();
  const app_version = $("#app_version").val();

  const requestData = {
    "type": type,
    "url": url,
    "sorting_order": sorting_order,
    "app_version": app_version,
    "altUrl": altUrl,
  };
  $('#loader_for_mfg_ev_app').show();
  $.ajax({
    url: add_connector_url,
    type: 'POST',
    dataType: 'json',
    contentType: 'application/json',
    data: JSON.stringify(requestData),
    headers: { "X-CSRFToken": token },
    success: function (result) {
      location.reload();
    },
    error: function (result) {

      $('#loader_for_mfg_ev_app').hide();
      customAlert('Please enter valid data or image with proper size');
    },
  });
}


function viewConnectorDetails(id, type, sorting_order, app_version,img, altImg) {
  selectedItemID = id;
  $('.view-con-typ').html(type);
  $('.view-con-img').attr("src", img);
  $('.view-alt-con-img').attr("src", altImg);
  $("#view_sorting_order").html(sorting_order);
  $("#view_app_version").html(app_version? app_version: 'NA');
}

function deleteConnector() {
  window.location.href = "/administrator/configurations/delete-connector/" + selectedItemID + "/";
}

$(function () {

  // For Delete Connector 
  $(".del-con-itm-icn").click(function () {
    //get data from table row
    var id = $(this).parent().prev().prev().prev().prev().prev().prev().text();
    var type = $(this).parent().prev().prev().prev().text();

    //assign to value for input box inside modal
    $("#del-con-msg").html(`Are you sure you want to remove <b>` + type + `</b> connector?`);

    //Delete Connector
    $("#del-con-itm").click(function () {
      window.location.href = "/administrator/configurations/delete-connector/" + id + "/";
    })
  })

})


// Add and Preview Image
$(document).on('change', '#i_file', function (event) {

  if (event.target.files) {
    const reader = new FileReader();
    reader.readAsDataURL(event.target.files[0]);
    reader.onload = (eventdata) => {

    let url = eventdata.target.result;

    $('#image_path_src').val(url);

    $("#add_images_container").html(`<div class="profile_container"><div id='discard' class='discard'>x</div><img class="profile_image_ service_image" src=${url} ></div>`);

    }
  }
});

// Discard Selected Add Image
$(document).on('click', '#discard', function (eventdata) {
  $('#image_path_src').val("");
  $("#add_images_container").html(`<div id="d-flex flex-column"  class="mr-tp">
                    <input type="file" id="i_file"  name="filename" hidden accept=".jpeg,.jpg,.png"/>
                    <label for="i_file" class="add_images_label"><b class=" pick-img">Add Image</b</label>
                
                    </div>`);

});

// Discard Selected Update Image
$(document).on('click', '#discard1', function (eventdata) {
  $('#conn_img').val("");
  $("#add_images_container1").html(`<div id="d-flex flex-column"  class="mr-tp">
                    <input type="file" id="i_file1"  name="filename" hidden accept=".jpeg,.jpg,.png"/>
                    <label for="i_file1" class="add_images_label"><b class=" pick-img">Add Image</b</label>
                
                    </div>`);

});


// Update and Preview Image
$(document).on('change', '#i_file1', function (event) {
  if (event.target.files) {
    const reader = new FileReader();
    reader.readAsDataURL(event.target.files[0]);
    reader.onload = (eventdata) => {
      let url = eventdata.target.result;
      $('#conn_img').val(url);

      $("#add_images_container1").html(`<div class="profile_container"><div id='discard1' class='discard'>x</div><img class="profile_image_ service_image" src=${url} ></div>`);

    }
  }
});



$(document).on('change', '#i_alt_file', function (event) {

  if (event.target.files) {
    const reader = new FileReader();
    reader.readAsDataURL(event.target.files[0]);
    reader.onload = (eventdata) => {

    let url = eventdata.target.result;

    $('#alt_image_path_src').val(url);

    $("#add_alt_images_container").html(`<div class="profile_container"><div id='discard_alt_img' class='discard'>x</div><img class="profile_image_ service_image" src=${url} ></div>`);

    }
  }
});


$(document).on('change', '#i_alt_edit_file', function (event) {

  if (event.target.files) {
    const reader = new FileReader();
    reader.readAsDataURL(event.target.files[0]);
    reader.onload = (eventdata) => {

    let url = eventdata.target.result;

    $('#alt_image_edit_path_src').val(url);

    $("#add_alt_images_container2").html(`<div class="profile_container"><div id='discard_edit_alt_img' class='discard'>x</div><img class="profile_image_ service_image" src=${url} ></div>`);

    }
  }
});

$(document).on('click', '#discard_alt_img', function (eventdata) {
  $('#alt_image_path_src').val("");
  $("#add_alt_images_container").html(` <div id="d-flex flex-column" class="mr-tp">
      <input type="file" id="i_alt_file" name="alt_image_path" hidden accept=".jpeg,.jpg,.png" />
      <label for="i_alt_file" class="add_images_label"><strong class=" pick-img">Add
              Image</strong></label>

  </div>`);

});
$(document).on('click', '#discard_edit_alt_img', function (eventdata) {
  $('#alt_image_edit_path_src').val("");
  $("#add_alt_images_container2").html(` <div id="d-flex flex-column" class="mr-tp">
      <input type="file" id="i_alt_edit_file" name="alt_image_path" hidden accept=".jpeg,.jpg,.png" />
      <label for="i_alt_edit_file" class="add_images_label"><strong class=" pick-img">Add
              Image</strong></label>

  </div>`);

});

// Connector search
$(document).ready(function () {
  
  clearSelected();
});



// Tooltips
$(function () {
  $('[data-toggle="tooltip"]').tooltip()
})


// Cleare Previously Selected Menue Option
function clearSelected() {
  document.getElementById('conn').classList.add('menu-item');
}

function importData() {
  const input = document.createElement('input');
  input.type = 'file';
  input.click();
}
