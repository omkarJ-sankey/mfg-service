

var selectedItemID = 0;


function addBrandDefaultImageFunc(){
  $('#image_path_src').val("");
  $('#add_brand_default_name').val("");
  $("#add_images_container").html(` <div id="d-flex flex-column"  class="mr-tp">
                  <input type="file" id="i_file"  name="filename" hidden accept=".jpeg,.jpg,.png"/>
                  <label for="i_file" class="add_images_label"><b class=" pick-img">Add Image</b</label>              
                  </div>`);
}

function updateBrandDefaultImageDetails(){
  const id = $('#default_image_id').val();
  const brand = $('#edit_brand_default_name').val();
  const url = $('#edit_brand_default_image').val();
  const app_version = $('#update_app_version').val();


  const requestData = {
      "id":id,
      "brand":brand,
      "url":url,
      "app_version":app_version
  };

  $('#loader_for_mfg_ev_app').show();

  $.ajax({
      url: update_default_image_url,
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

function addBrandDefaultImageDetails(){
  const brand = $('#add_brand_default_name').val();
  const app_version = $('#app_version').val();
  const url = $('#image_path_src').val();
  const requestData = {
      "brand":brand,
      "url":url,
      "app_version": app_version
  };
  
  $('#loader_for_mfg_ev_app').show();
  $.ajax({
      url: add_default_image_url,
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
function editBrandDefaultImageDetailsFunc(id, brand, app_version, url){    
  $("#add_images_container1").html(`<div class="default_image_preview_container">
                      <div id='discard1' class='discard'>x</div>
                      <img class="default_preview_image_ service_image view-con-img" src=${group_png_url} >
                  </div>`);
  $('#edit_brand_default_name').val(brand);
  $('#edit_brand_default_image').val(url);
  $('#update_app_version').val(app_version);
  $('.default_preview_image_').attr("src",url);
  $('#default_image_id').val(id);
}
function switchToDefaultImageEditor(){   
  const brand = $('.view-con-typ').html();
  const app_version = $('#view_app_version').html();
  const url = $('.view-con-img').attr('src');
  $('#editDefaultImage').modal('show');
  editBrandDefaultImageDetailsFunc(selectedItemID,brand,app_version,url);
}
function viewBrandDefaultImageDetailsFunc(id,type,app_version,img){
  selectedItemID = id;
  $('.view-con-typ').html(type);
  $('#view_app_version').html(app_version);
  $('.view-con-img').attr("src",img);
}


// Add and Preview Image
$(document).on('change', '#i_file' , function(event) {

if (event.target.files){
 const reader = new FileReader();  
 reader.readAsDataURL(event.target.files[0]);
 reader.onload = (eventdata) => {

  let url = eventdata.target.result;

  $('#image_path_src').val(url);
 
  $("#add_images_container").html(`<div class="default_image_preview_container"><div id='discard' class='discard'>x</div><img  class="default_preview_image_" src=${url} ></div>`);
  
  }
  }
});

// Discard Selected Add Image
$(document).on('click', '#discard' , function(event) {
$('#image_path_src').val("");
$("#add_images_container").html(`<div id="d-flex flex-column"  class="mr-tp">
                  <input type="file" id="i_file"  name="filename" hidden accept=".jpeg,.jpg,.png"/>
                  <label for="i_file" class="add_images_label"><b class=" pick-img">Add Image</b</label>
              
                  </div>`);

});

// Discard Selected Update Image
$(document).on('click', '#discard1' , function(event) {
$('#conn_img').val("");
$("#add_images_container1").html(`<div id="d-flex flex-column"  class="mr-tp">
                  <input type="file" id="i_file1"  name="filename" hidden accept=".jpeg,.jpg,.png"/>
                  <label for="i_file1" class="add_images_label"><b class=" pick-img">Add Image</b</label>
              
                  </div>`);
});

// Update and Preview Image
$(document).on('change', '#i_file1' , function(event) {
if (event.target.files){
 const reader = new FileReader();  
 reader.readAsDataURL(event.target.files[0]);
 reader.onload = (eventdata) => {

  let url = eventdata.target.result;

  $('#edit_brand_default_image').val(url);
 
  $("#add_images_container1").html(`<div class="default_image_preview_container"><div id='discard1' class='discard'>x</div><img class="default_preview_image_" src=${url} ></div>`);
  
  }
  }
});
// Tooltips
$(function () {
$('[data-toggle="tooltip"]').tooltip()
});
function clearSelected() {
  document.getElementById('default_brand_img').classList.add('menu-item');
}
function importData() {
const input = document.createElement('input');
input.type = 'file';
input.click();
}
//Amenities Search
$(document).ready(function(){
  $("#search-default-images-brands").on("keyup",function(){
    var value = $(this).val().toLowerCase();
    $("#table-amenities tbody tr:has(td)").filter(function(){
      $(this).toggle($(this).text().toLowerCase().indexOf(value) > -1)
    });
  });
  clearSelected();
});

function toggleBrandDefaultImageViewer(img_url){
  document.getElementById("default_image_viewer_container_id").classList.toggle("viewer_active");
  $('#default_image_preview_id').attr("src",img_url);
}