

var selectedItemID = 0;
function orderByFunction(type){
    let update_order = 'Descending';
    const params = new URLSearchParams(url_u);
    let new_url = '';
    params.forEach(function(value, key) {
            if (key !== type) new_url += `&${key}=${value}`;
            else {
                if (value === `Ascending`) update_order = 'Descending'
                else update_order = 'Ascending'
            }
    });
    document.getElementById(type).classList.toggle('order-by');
    window.location.href = `${window_radirect_location}?${type}=${update_order}${new_url}`;
}


$(function(){
      // bind change event to select
      $('#dynamic_select').on('change', function () {
        var url = $('#dynamic_select').val();
        window.location = "/administrator/configurations/shops/?type="+url;
      })
})

disableAddAndUpdateButtons('add_shop_button');

function updateShop(){
    const id = $('#conn_id').val();
    const name = $('#conn_type').val();
    const type = $('#conn_sub_type').val();
    const url = $('#conn_img').val();
    const unique_identifier = $('#update_unique_identifier').val();
    const requestData = {
        "id":id,
        "name":name,
        "type":type,
        "url":url,
        "unique_identifier":unique_identifier
    };

    $('#loader_for_mfg_ev_app').show();
    $.ajax({
        url:update_shops_url,
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


$('#add_unique_identifier').on('input', function (e) {
    setTimeout(function(){ checkUniqueIdAvailability('add_unique_identifier',
        'add_shop_unique_id_error','add_shop_button'); }, 200);
    
});

$('#update_unique_identifier').on('input', function (e) {
    setTimeout(function(){ checkUniqueIdAvailability('update_unique_identifier',
        'update_shop_unique_id_error','update_shop_button','conn_id'); }, 200);
    
});
function addShopDetails(){
    const name = $('#service_name').val();
    const type = $('#service_type').val();
    const url = $('#image_path_src').val();
    const unique_identifier = $('#add_unique_identifier').val();
    const requestData = {
        "service_name":name,
        "type":type,
        "url":url,
        "unique_identifier":unique_identifier
    };
    
    $('#loader_for_mfg_ev_app').show();
    $.ajax({
        url:add_shop_url,
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
function addConnector(){
    $('#image_path_src').val("");
    $('#service_name').val("");
    $('#service_type').val("");
    $('#add_unique_identifier').val("");
    const error_component = document.getElementById('add_shop_unique_id_error');
    error_component.innerHTML = '';
    $("#add_images_container").html(` <div id="d-flex flex-column"  class="mr-tp">
                    <input type="file" id="i_file"  name="filename" hidden accept=".jpeg,.jpg,.png"/>
                    <label for="i_file" class="add_images_label"><b class=" pick-img">Add Image</b</label>              
                    </div>`);
}

function editConnectorDetails(id, name, type, url,u_id){
    
    const error_component = document.getElementById('update_shop_unique_id_error');
    error_component.innerHTML = '';
    $("#add_images_container1").html(`<div class="profile_container">
                        <div id='discard1' class='discard'>x</div>
                        <img  class="profile_image_ service_image" src=${group_png_url} >
                    </div>`);
    $('#conn_type').val(name);
    $('#update_unique_identifier').val(u_id);
    $('#conn_sub_type').val(type);
    $('#conn_img').val(url);
    $('.profile_image_').attr("src",url);
    $('#conn_id').val(id);
}

function switchToShopEditor(){   
    const type = $('.view-con-typ').html();
    const sub_type = $('.view-con-sub-typ').html();
    const url = $('.view-con-img').attr('src');
    const shop_uid = $('.view-shop-id').html();
    $('#editConnector').modal('show');
    editConnectorDetails(selectedItemID,type,sub_type,url, shop_uid);
}

function viewConnectorDetails(id,type,sub,img,u_id){
    selectedItemID = id;
    $('.view-con-typ').html(type);
    $('.view-con-sub-typ').html(sub); 
    $('.view-shop-id').html(u_id);
    $('.view-con-img').attr("src",img);
}

function deleteConnector(){
    window.location.href = "/administrator/configurations/delete-shops/"+selectedItemID+"/";   
}

$(function () {
  // For Delete Connector 
    $(".del-con-itm-icn").click(function () {
            //get data from table row
            var id = $(this).parent().prev().prev().prev().prev().prev().prev().text();
            var type = $(this).parent().prev().prev().prev().prev().text();

            //assign to value for input box inside modal
            $("#del-con-msg").html(`Are you sure you want to remove <b>`+type+`</b> shop?`);

            //Delete Connector
            $("#del-con-itm").click(function () {
                window.location.href = "/administrator/configurations/delete-connector/"+id+"/";       
            })

            //Delete Aminity
            $("#del-amen-itm").click(function () {
                window.location.href = "/administrator/configurations/delete-shops/"+id+"/";       
            })

        })
   
    // For View Connector Details
    $(".view-con-itm").click(function () {
            //get data from table row
            // var id = $(this).parent().prev().prev().prev().prev().prev().text();
            // var path = $(this).parent().prev().prev().prev().prev().text();
            // var type = $(this).parent().prev().prev().prev().text();
            // var name = $(this).parent().prev().prev().text();

        })
    })

// Add and Preview Image
$(document).on('change', '#i_file' , function(event) {
 if (event.target.files){
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
   reader.onload = (event_data) => {

    let url = event_data.target.result;

        $('#conn_img').val(url);
    
        $("#add_images_container1").html(`<div class="profile_container"><div id='discard1' class='discard'>x</div><img class="profile_image_ service_image" src=${url} ></div>`);
        
        }
    }
});


// Tooltips
$(function () {
  $('[data-toggle="tooltip"]').tooltip()
})

function clearSelected() {
    document.getElementById('shop').classList.add('menu-item');
  }

function importData() {
  const input = document.createElement('input');
  input.type = 'file';
  input.click();
  
}
$(document).ready(function() {
    // Construct URL object using current browser URL
    const url = new URL(document.location);
    // Get query parameters object
    const params = url.searchParams;
    // Get value of delivery results
    const results_delivery = params.get("type");
    // Set it as the dropdown value
    $("#dynamic_select-ID").val(results_delivery);
  });
  

$(document).ready(()  => {
    clearSelected();
  });
