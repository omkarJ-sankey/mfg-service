const SHOP_CONST = "shop";
const AMENITY_CONST = "amenity";
const OPS_REGION_CONST = "opsRegion";
const REGION_CONST = "region";
const AREA_CONST = "area";
const STATION_CONST = "station";
$(function () {
  $("#start_date").datepicker({
    dateFormat: "dd/mm/yy",
    showOn: "button",
    minDate: -60,
    buttonImage:
      "https://mfgevqastorage.blob.core.windows.net/static/images/calendar-1.png",
    buttonImageOnly: true,
    buttonText: "Select date",
  });
});
$(function () {
  $("#end_date").datepicker({
    dateFormat: "dd/mm/yy",
    showOn: "button",
    minDate: 0,
    buttonImage:
      "https://mfgevqastorage.blob.core.windows.net/static/images/calendar-1.png",
    buttonImageOnly: true,
    buttonText: "Select date",
  });
});

function showFromDatePicker() {
  $("#start_date").datepicker("show");
}
function showToDatePicker() {
  $("#end_date").datepicker("show");
}

function show_info_box(x) {
  document.getElementById(`show_tooltip_${x}`).style.display = "block";
}
function hide_info_box(x) {
  document.getElementById(`show_tooltip_${x}`).style.display = "none";
}
// if (!promotion_data_from_backend) {
//     if (shop_and_store_list.includes('Budgens')) promotions_data_to_upload['shop'].push('Budgens');
//     if (shop_and_store_list.includes('Londis')) promotions_data_to_upload['shop'].push('Londis');
// }

function restrictWordInNumberFields(id) {
  var value = document.getElementById(id).value;
  if (value.includes("e"))
    document.getElementById(id).value = value.replace("e", "");
  if (value.length === 0) document.getElementById(id).value = 0;
}
var uploaded_images = [];
var remove_images = [];
var uploaded_images_copy = [];
var backup_station_ids = [];
var final_upload_images = [];
let temp_uploaded_images = [];

var promotion_submit_button = null;

function toggleModal() {
  const modal = document.getElementById("side_modal_id");
  modal.classList.toggle("active");
  let content_to_be_embed_in_side_modal;

  var content_image_container = "";
  if (uploaded_images.length > 0) {
    temp_uploaded_images = [...uploaded_images];
    for (var i = 0; i < uploaded_images.length; i++) {
      content_image_container += `<div class="img-download">
                    <img src=${uploaded_images[i]} class="promotion_img_tag_style" alt="image">
                    <b class="promotion_discard_button-style"data="${i}" id="discard_edit" ref="${uploaded_images[i]}" onclick="removeAssignedImage(this)" class="discard">x</b>
                    </div>`;
    }
  } else {
    content_image_container = `<div class="text_container"><div class="text_for_images"><p>Click 'Add Images' to add images here</p></div></div>`;
  }
  content_to_be_embed_in_side_modal = ` <div class="content_of_modal"> 
        <div class="side_modal_heading">
            <p>Assign images</p>
            <button class="close_button" onclick="toggleModal();"><img src=${cross_icon_image_url}></button>

        </div>
        <div class="side_modal_heading1">
            <p id="add_images_count">0${uploaded_images.length} added</p>
            
            <input type="file" id="i_file" name="filename" hidden accept=".jpeg,.jpg,.png"/>
            <label for="i_file" class="add_images_label">Add images</label>
        </div>
        <div class="horizontal-lines"></div>
        <div id="add_images_container">
            ${content_image_container}
        </div>
    </div>
    <div class="add_images_button_cotainer">
        <button class="cancel_image_button" onclick="toggleModal();">Cancel</button>
        <button class="assign_image" onclick="appendImages();">Assign</button>
    </div>`;
  $("#dynamic_content_container").html(content_to_be_embed_in_side_modal);
}
let add_new_image = [];

function add_new_image_in_container() {
  temp_uploaded_images = [...add_new_image];
  $("#add_images_container").html(`<div class="img-download">
    <img src=${temp_uploaded_images[0]} class="promotion_img_tag_style" alt="image">
    <b class="promotion_discard_button-style"data="${uploaded_images.length}" ref="${temp_uploaded_images[0]}" id="discard_edit" onclick="removeAssignedImage(this)" class="discard">x</b>
    </div>`);
  $("#restrict_image_upload").modal("hide");
}
function do_not_add_new_image_in_container() {
  add_new_image = [];
  $("#restrict_image_upload").modal("hide");
}
$(document).on("change", "#i_file", function (event) {
  if (event.target.files) {
    const reader = new FileReader();
    reader.onload = (event_data) => {
      let url = event_data.target.result;
      if (temp_uploaded_images.length > 0) {
        $("#restrict_image_upload").modal("show");
        add_new_image = [];
        add_new_image.push(url);
      } else {
        if (temp_uploaded_images.length === 0)
          $("#add_images_container").html(`<div class="img-download">
                        <img src=${url} class="promotion_img_tag_style" alt="image">
                        <b class="promotion_discard_button-style"data="${temp_uploaded_images.length}" ref="${url}" id="discard_edit" onclick="removeAssignedImage(this)" class="discard">x</b>
                        </div>`);
        else
          $("#add_images_container").append(`<div class="img-download">
                        <img src=${url} class="promotion_img_tag_style" alt="image">
                        <b class="promotion_discard_button-style"data="${temp_uploaded_images.length}" ref="${url}" id="discard_edit" onclick="removeAssignedImage(this)" class="discard">x</b>
                        </div>`);
        temp_uploaded_images.push(url);
        $("#add_images_count").html(`0${temp_uploaded_images.length} added`);
      }
    };
    reader.readAsDataURL(event.target.files[0]);
  }
});

function removeAssignedImage(event) {
  remove_images.push(event.getAttribute("ref"));
  temp_uploaded_images.splice(event.getAttribute("data"), 1);

  if (temp_uploaded_images.length == 0) {
    $("#add_images_container").html(
      `<div class="text_container"><div class="text_for_images"><p>Click 'Add Images' to add images here</p></div></div>`
    );
  } else {
    const tempArray = temp_uploaded_images;
    temp_uploaded_images = [];
    tempArray.forEach((url) => {
      if (temp_uploaded_images.length === 0) {
        $("#add_images_container").html(`<div class="img-download">
                <img src=${url} class="promotion_img_tag_style" alt="image">
                <b class="promotion_discard_button-style" data="${temp_uploaded_images.length}" ref="${url}" id="discard_edit" onclick="removeAssignedImage(this)" class="discard">x</b>
                </div>`);
      } else {
        $("#add_images_container").append(`<div class="img-download">
                <img src=${url} class="promotion_img_tag_style" alt="image">
                <b class="promotion_discard_button-style" data="${temp_uploaded_images.length}" ref="${url}" id="discard_edit" onclick="removeAssignedImage(this)" class="discard">x</b>
                </div>`);
      }
      temp_uploaded_images.push(url);
    });
  }
  if (temp_uploaded_images.length < 10)
    $("#add_images_count").html(`0${temp_uploaded_images.length} added`);
  else $("#add_images_count").html(`${temp_uploaded_images.length} added`);
}

function addRemovedImages() {
  remove_images.forEach((x) => {
    uploaded_images.push(x);
  });
  remove_images = [];
}

function appendImages() {
  uploaded_images = temp_uploaded_images;
  remove_images = [];
  let content_for_image_container = "";
  for (var i = 0; i < uploaded_images.length; i++) {
    content_for_image_container += `<img src=${uploaded_images[i]} >`;
  }

  final_upload_images = [];
  uploaded_images.forEach((x) => {
    final_upload_images.push(x);
  });
  $("#images_container").html(content_for_image_container);
  toggleModal();
}

// function to fetch data  for select list checkbox
function selectedOptionsText(id, text) {
  document.getElementById(id).innerHTML = text;
}

// function refreshCheckList(target) {
//     var status = true;
//     var selected_options = '';
//     $("input:checkbox[id=" + target + "]").each(function () {
//         var $this = $(this);
//         if (!$this.is(":checked")) {
//             status = false;
//         }
//         else {
//             switch (target) {
//                 // case 'sel-reg-shop':
//                 //     if (promotions_data_to_upload.shop.includes('All')) {
//                 //         const pos = promotions_data_to_upload.shop.indexOf('All')
//                 //         promotions_data_to_upload.shop.splice(pos, 1)
//                 //     }
//                 //     if (!promotions_data_to_upload.shop.includes($(this).attr("ref"))) promotions_data_to_upload.shop.push($(this).attr("ref"))
//                 //     break;
//                 // case 'sel-reg-amenity':
//                 //     if (promotions_data_to_upload.shop.includes('All')) {
//                 //         const pos = promotions_data_to_upload.shop.indexOf('All')
//                 //         promotions_data_to_upload.shop.splice(pos, 1)
//                 //     }
//                 //     if (!promotions_data_to_upload.shop.includes($(this).attr("ref"))) promotions_data_to_upload.shop.push($(this).attr("ref"))
//                 //     break;
//                 case 'sel-opr-reg':
//                     if (operation_regions.includes('All')) {
//                         const pos = operation_regions.indexOf('All')
//                         operation_regions.splice(pos, 1)
//                     }
//                     if (!operation_regions.includes($(this).attr("ref"))) operation_regions.push($(this).attr("ref"));
//                     break;
//                 case 'sel-reg':
//                     if (regions.includes('All')) {
//                         const pos = regions.indexOf('All')
//                         regions.splice(pos, 1)
//                     }
//                     if (!regions.includes($(this).attr("ref"))) regions.push($(this).attr("ref"));
//                     break;
//                 case 'sel-reg-area':
//                     if (areas.includes('All')) {
//                         const pos = areas.indexOf('All')
//                         areas.splice(pos, 1)
//                     }
//                     if (!areas.includes($(this).attr("ref"))) areas.push($(this).attr("ref"));
//                     break;
//                 default:
//                     if (promotions_data_to_upload.stations.includes('All')) {
//                         const pos = promotions_data_to_upload.stations.indexOf('All')
//                         promotions_data_to_upload.stations.splice(pos, 1)
//                     }
//                     if (parseInt($(this).attr("ref"))) {

//                         if (!promotions_data_to_upload.stations.includes(parseInt($(this).attr("ref")))) promotions_data_to_upload.stations.push(parseInt($(this).attr("ref")))
//                     }
//             }
//             if (target === 'sel-reg-stn') {
//                 if (searchStationId(parseInt($(this).attr("ref")))) selected_options += searchStationId(parseInt($(this).attr("ref"))) + ',';
//             }
//             else selected_options += $(this).attr("ref") + ',';
//         }
//     });

//     switch (target) {
//         case 'sel-reg-shop':
//             status ? selectedOptionsText('shop_text', 'All') : selectedOptionsText('shop_text', (selected_options == "" ? 'Select' : selected_options));
//             break;
//         case 'sel-reg-amenity':
//             status ? selectedOptionsText('amenity_text', 'All') : selectedOptionsText('amenity_text', (selected_options == "" ? 'Select' : selected_options));
//             break;
//         case 'sel-opr-reg':
//             status ? selectedOptionsText('operation_region_text', 'All') : selectedOptionsText('operation_region_text', (selected_options == "" ? 'Select' : selected_options));
//             break;
//         case 'sel-reg':
//             status ? selectedOptionsText('region_text', 'All') : selectedOptionsText('region_text', (selected_options == "" ? 'Select' : selected_options));
//             break;
//         case 'sel-reg-area':
//             status ? selectedOptionsText('area_text', 'All') : selectedOptionsText('area_text', (selected_options == "" ? 'Select' : selected_options));
//             break;
//         default:
//             status ? selectedOptionsText('stations_text', 'All') : selectedOptionsText('stations_text', (selected_options == "" ? 'Select' : selected_options));
//     }

//     $('#' + target + '-all').prop('checked', status);

// }

$(document).ready(function () {
  const terms = $("#terms").val();
  const offers = $("#offers").val();
  $("#terms").val(terms.trim());
  $("#offers").val(offers.trim());
  if ($("#steps_to_redeem").length > 0){
    const steps_to_redeem = $("#steps_to_redeem").val();
    $("#steps_to_redeem").val(steps_to_redeem.trim());
  }
});

function searchStationId(id) {
  for (var i of all_stations) {
    if (parseInt(i[0]) == id) {
      return i[1];
    }
  }
}

// function checkboxSelectedStation(val) {
//     const checkbxes = document.getElementsByClassName('stationsch')
//     let selected_options = ''
//     if (val) {
//         if (promotions_data_to_upload.stations.includes(val)) {
//             var pos = promotions_data_to_upload.stations.indexOf(val)
//             promotions_data_to_upload.stations.splice(pos, 1)
//             if (val === 'All') {
//                 for (var i = 0; i < checkbxes.length; i++) {
//                     checkbxes[i].checked = false;
//                 }
//                 promotions_data_to_upload.stations = [];
//             } else {

//                 promotions_data_to_upload.stations.forEach((element, index) => {
//                     if (searchStationId(element)) selected_options += ` ${searchStationId(element)},`
//                 });

//                 document.getElementById('stations_text').innerHTML = selected_options;
//             }
//         } else {
//             if (val === 'All') {
//                 promotions_data_to_upload.stations = [val]
//                 for (i = 0; i < checkbxes.length; i++) {
//                     checkbxes[i].checked = true
//                 }
//                 document.getElementById('stations_text').innerHTML = "All";
//             } else {

//                 if (!promotions_data_to_upload.stations.includes('All')) {

//                     promotions_data_to_upload.stations.push(val)
//                     promotions_data_to_upload.stations.forEach((element, index) => {
//                         if (searchStationId(element)) selected_options += ` ${searchStationId(element)},`
//                     });

//                     document.getElementById('stations_text').innerHTML = 'selected_options';
//                 }
//             }
//         }
//         if (promotions_data_to_upload.stations.length === 0) document.getElementById('stations_text').innerHTML = "Select"

//     } else {
//         promotions_data_to_upload.stations.forEach(element => {
//             if (searchStationId(element)) selected_options += ` ${searchStationId(element)},`
//         });

//         document.getElementById('stations_text').innerHTML = (
//             selected_options.length? selected_options : 'Select'
//         );
//     }

//     promotion_submit_button.classList.remove('disabled')
//     promotion_submit_button.removeAttribute("disabled");
// }

// function checkboxSelectedArea(val) {

//     promotion_submit_button.classList.add('disabled')
//     promotion_submit_button.setAttribute("disabled", true);
//     $('#checkbosx4').html('Loading....');
//     document.getElementById('checkbosx3_loader').style.width = '100%';
//     document.getElementById('checkbosx3_loader').style.height = '100%';
//     document.getElementById('checkbosx3').style.overflowY = 'hidden';
//     document.getElementById('checkbosx3_loader').innerHTML = "Please wait...";
//     if (val) {
//         const checkbxes = document.getElementsByClassName('areach')

//         var selected_options = ''
//         if (areas.includes(val)) {
//             const pos = areas.indexOf(val)
//             if (pos === 0) areas = areas.splice(1, areas.length)
//             else areas.splice(pos, 1);
//             if (val === 'All') {
//                 for (var i = 0; i < checkbxes.length; i++) {
//                     checkbxes[i].checked = false
//                 }
//                 areas = [];
//             } else {
//                 areas.forEach((element, index) => {
//                     selected_options += ` ${element},`
//                 });
//                 document.getElementById('area_text').innerHTML = selected_options;
//             }
//         } else {

//             if (val === 'All') {
//                 areas = [val]
//                 for (i = 0; i < checkbxes.length; i++) {
//                     checkbxes[i].checked = true
//                 }
//                 document.getElementById('area_text').innerHTML = "All";
//             } else {
//                 if (!areas.includes('All')) {
//                     areas.push(val)
//                     areas.forEach((element, index) => {
//                         selected_options += ` ${element},`
//                     });
//                     document.getElementById('area_text').innerHTML = selected_options;
//                 }
//             }
//         }
//         if (!promotion_data_from_backend) {
//             promotions_data_to_upload.stations = []
//         }

//     } else {
//         selected_options = ''
//         areas.forEach((element, index) => {
//             selected_options += ` ${element},`
//         });

//         document.getElementById('area_text').innerHTML = selected_options;
//     }
//     if (areas.length > 0) {
//         $.ajax({
//             url: checkbox_data_for_add_promotions_url,
//             data: {
//                 'getdata': JSON.stringify({ 'area': [areas, regions, promotions_data_to_upload.shop] }),
//                 'data_to_fetch': JSON.stringify(['station_id', 'region'])
//             },
//             headers: { "X-CSRFToken": token },
//             dataType: 'json',
//             type: 'POST',

//             success: function (res, status) {
//                 var content = ''
//                 $('#checkbosx4').html('Loading....')
//                 content += `<label >
//                                 <input type="checkbox" ${areas.includes('All') ? 'checked' : ''} class="padder stationsch" id="sel-reg-stn-all" onchange="checkboxSelectedStation('All');"/>All</label>`
//                 if (promotion_data_from_backend) {
//                     if (first_time_hit_on_areas) {
//                         promotions_data_to_upload.stations = []
//                         backup_station_ids = []
//                     }
//                 } else {
//                     promotions_data_to_upload.stations = []
//                     backup_station_ids = []
//                 }
//                 res.data.map(x => {
//                     if (promotion_data_from_backend) {
//                         if (first_time_hit_on_areas) {
//                             if (!promotions_data_to_upload.stations.includes(x)) promotions_data_to_upload.stations.push(x[0])
//                         }
//                         if (!backup_station_ids.includes(x)) backup_station_ids.push(x[0]);
//                     } else {
//                         if (!promotions_data_to_upload.stations.includes(x)) promotions_data_to_upload.stations.push(x[0])
//                         if (!backup_station_ids.includes(x)) backup_station_ids.push(x[0]);
//                     }

//                     content += `<label >
//                                 <input type="checkbox" ${promotions_data_to_upload.stations.includes(x[0]) || areas.includes('All') ? 'checked' : ''} class="padder stationsch" id="sel-reg-stn" ref='${x[0]}' onchange="checkboxSelectedStation(${x[0]});refreshCheckList('sel-reg-stn')"/>${x[1]}</label>
//                             `;
//                 })
//                 $('#checkbosx4').html(content);
//                 let allSelected = false;
//                 if (
//                     // !first_time_hit_on_areas &&
//                     promotions_data_to_upload.stations.length === document.getElementsByClassName('stationsch').length - 1
//                 ){
//                     document.getElementById('sel-reg-stn-all').checked = true;
//                     promotions_data_to_upload.stations.push('All');
//                     allSelected = true;
//                 };
//                 first_time_hit_on_areas = true;
//                 document.getElementById('checkbosx3_loader').style.width = '0%';
//                 document.getElementById('checkbosx3_loader').innerHTML = "";
//                 document.getElementById('checkbosx2_loader').style.width = '0%';
//                 document.getElementById('checkbosx2_loader').innerHTML = "";
//                 document.getElementById('checkbosx1_loader').style.width = '0%';
//                 document.getElementById('checkbosx1_loader').innerHTML = "";
//                 document.getElementById('checkbosx0_loader').style.width = '0%';
//                 document.getElementById('checkbosx0_loader').innerHTML = "";

//                 document.getElementById('checkbosx3').style.overflowY = 'scroll';
//                 document.getElementById('checkbosx2').style.overflowY = 'scroll';
//                 document.getElementById('checkbosx1').style.overflowY = 'scroll';
//                 document.getElementById('checkbosx5').style.overflowY = 'scroll';

//                 if(document.getElementById('checkbosx6')){
//                     document.getElementById('checkbosx6').style.overflowY = 'scroll';
//                     document.getElementById('checkbosx6_loader').style.width = '0%';
//                     document.getElementById('checkbosx6_loader').innerHTML = "";
//                 }
//                 // if (val === 'All') checkboxSelectedStation('All');
//                 // else
//                 checkboxSelectedStation();
//                 if (allSelected) document.getElementById('stations_text').innerHTML = "All";

//             },
//             error: function () {
//                 customAlert('Something went wrong while processing areas');
//             }
//         });
//     } else {
//         $('#checkbosx4').html('')
//         document.getElementById('checkbosx3_loader').style.width = '0%';
//         document.getElementById('checkbosx3_loader').innerHTML = "";
//         document.getElementById('checkbosx2_loader').style.width = '0%';
//         document.getElementById('checkbosx2_loader').innerHTML = "";
//         document.getElementById('checkbosx1_loader').style.width = '0%';
//         document.getElementById('checkbosx1_loader').innerHTML = "";
//         document.getElementById('checkbosx0_loader').style.width = '0%';
//         document.getElementById('checkbosx0_loader').innerHTML = "";

//         document.getElementById('checkbosx3').style.overflowY = 'scroll';
//         document.getElementById('checkbosx2').style.overflowY = 'scroll';
//         document.getElementById('checkbosx1').style.overflowY = 'scroll';
//         document.getElementById('checkbosx5').style.overflowY = 'scroll';

//         if(document.getElementById('checkbosx6')){
//             document.getElementById('checkbosx6').style.overflowY = 'scroll';
//             document.getElementById('checkbosx6_loader').style.width = '0%';
//             document.getElementById('checkbosx6_loader').innerHTML = "";
//         }
//         document.getElementById('area_text').innerHTML = "Select";
//         promotions_data_to_upload.stations = [];
//         checkboxSelectedStation();
//     };

// }

// function checkboxSelectedRegion(val) {

//     promotion_submit_button.classList.add('disabled')
//     promotion_submit_button.setAttribute("disabled", true);
//     $('#checkbosx3').html('Loading....')
//     document.getElementById('checkbosx2_loader').style.width = '100%';
//     document.getElementById('checkbosx2_loader').style.height = '100%';
//     document.getElementById('checkbosx2').style.overflowY = 'hidden';
//     document.getElementById('checkbosx2_loader').innerHTML = "Please wait...";
//     if (val) {
//         const checkbxes = document.getElementsByClassName('regionch');

//         var selected_options = ''
//         if (regions.includes(val)) {
//             const pos = regions.indexOf(val)
//             if (pos === 0) regions = regions.splice(1, regions.length)
//             else regions.splice(pos, 1)
//             if (val === 'All') {
//                 for (var i = 0; i < checkbxes.length; i++) {
//                     checkbxes[i].checked = false
//                 };
//                 regions = [];
//             } else {

//                 regions.forEach((element, index) => {
//                     selected_options += ` ${element},`
//                 });

//                 document.getElementById('region_text').innerHTML = selected_options;
//             }
//         } else {
//             if (val === 'All') {
//                 regions = [val]
//                 for (var j = 0; j < checkbxes.length; j++) {
//                     checkbxes[j].checked = true
//                 }
//                 document.getElementById('region_text').innerHTML = "All";
//             } else {

//                 if (!regions.includes('All')) {

//                     regions.push(val)
//                     regions.forEach((element, index) => {
//                         selected_options += ` ${element},`
//                     });

//                     document.getElementById('region_text').innerHTML = selected_options;
//                 }
//             }
//         }
//         if (!promotion_data_from_backend) {
//             areas = []
//             promotions_data_to_upload.stations = []
//         }
//     } else {

//         selected_options = ''
//         regions.forEach((element, index) => {
//             selected_options += ` ${element},`
//         });

//         document.getElementById('region_text').innerHTML = selected_options;
//     }
//     if (regions.length > 0) {
//         $.ajax({
//             url: checkbox_data_for_add_promotions_url,
//             data: {
//                 'getdata': JSON.stringify({ 'region': [regions, operation_regions, promotions_data_to_upload.shop] }),
//                 'data_to_fetch': JSON.stringify(['area', 'operation_region'])
//             },
//             headers: { "X-CSRFToken": token },
//             dataType: 'json',
//             type: 'POST',

//             success: function (res, status) {
//                 var content = ''

//                 $('#checkbosx3').html('Loading....')
//                 content += '<div id="checkbosx3_loader"></div>'
//                 content += `<label >
//                                 <input type="checkbox" ${regions.includes('All') ? 'checked' : ''}  class="padder areach" id="sel-reg-area-all" onchange="checkboxSelectedArea('All');"/>All</label>`

//                 if (promotion_data_from_backend) {
//                     if (first_time_hit_on_regions) {
//                         areas = []
//                     }
//                 } else {
//                     areas = []
//                 }
//                 res.data.map(x => {
//                     if (promotion_data_from_backend) {
//                         if (first_time_hit_on_regions) {
//                             if (!areas.includes(x)) areas.push(x);
//                         }
//                     } else {
//                         if (!areas.includes(x)) areas.push(x);
//                     }
//                     content += `<label >
//                                             <input type="checkbox" ${areas.includes(x) || regions.includes('All') ? 'checked' : ''} class="padder areach" id="sel-reg-area"  ref='${x}' onchange="checkboxSelectedArea('${x}');refreshCheckList('sel-reg-area');"/>${x}</label>
//                             `})
//                 $('#checkbosx3').html(content);
//                 let allSelected = false;
//                 if (
//                     // !first_time_hit_on_regions &&
//                     areas.length === document.getElementsByClassName('areach').length - 1
//                 ){
//                     document.getElementById('sel-reg-area-all').checked = true;
//                     areas.push('All');
//                     allSelected = true;
//                 };
//                 if (first_time_hit_on_regions) first_time_hit_on_areas = true;
//                 first_time_hit_on_regions = true;
//                 // document.getElementById('checkbosx2_loader').style.width = '0%';
//                 // document.getElementById('checkbosx2_loader').innerHTML = "";
//                 // if (val === 'All') checkboxSelectedArea('All');
//                 // else
//                 checkboxSelectedArea();
//                 if (allSelected) document.getElementById('area_text').innerHTML = "All";
//             },
//             error: function (res) {
//                 customAlert('Something went wrong while processing regions');
//             }
//         });
//     } else {
//         $('#checkbosx3').html('<div id="checkbosx3_loader"></div>')

//         // document.getElementById('checkbosx2_loader').style.width = '0%';
//         // document.getElementById('checkbosx2_loader').innerHTML = "";
//         document.getElementById('region_text').innerHTML = "Select";
//         areas = [];
//         checkboxSelectedArea();
//     }

// }

// function checkboxSelected(val) {
//     promotion_submit_button.classList.add('disabled')
//     promotion_submit_button.setAttribute("disabled", true);
//     document.getElementById('checkbosx1_loader').style.width = '100%';
//     document.getElementById('checkbosx1_loader').style.height = '100%';
//     document.getElementById('checkbosx1').style.overflowY = 'hidden';
//     document.getElementById('checkbosx1_loader').innerHTML = "Please wait...";
//     $('#checkbosx2').html('Loading....')
//     var selected_options = ''
//     if (val) {
//         const checkbxes = document.getElementsByClassName('opsch')
//         if (operation_regions.includes(val)) {
//             const pos = operation_regions.indexOf(val)

//             if (pos === 0) operation_regions = operation_regions.splice(1, operation_regions.length)
//             else operation_regions.splice(pos, 1)
//             if (val === 'All') {
//                 for (var i = 0; i < checkbxes.length; i++) {
//                     checkbxes[i].checked = false
//                 }
//                 operation_regions = []
//             } else {

//                 operation_regions.forEach((element, index) => {
//                     selected_options += ` ${element},`
//                 });

//                 document.getElementById('operation_region_text').innerHTML = selected_options;
//             }
//         } else {

//             if (val === 'All') {

//                 operation_regions = [val]

//                 for (var i = 0; i < checkbxes.length; i++) {
//                     checkbxes[i].checked = true
//                 }
//                 document.getElementById('operation_region_text').innerHTML = "All";
//             } else {
//                 if (!operation_regions.includes('All')) {

//                     operation_regions.push(val)
//                     operation_regions.forEach((element, index) => {
//                         selected_options += ` ${element},`
//                     });

//                     document.getElementById('operation_region_text').innerHTML = selected_options;
//                 }
//             }
//         }
//         if (!promotion_data_from_backend) {

//             regions = []
//             areas = []
//             promotions_data_to_upload.stations = []
//         }
//     } else {

//         selected_options = ''
//         operation_regions.forEach((element, index) => {
//             selected_options += ` ${element},`
//         });

//         document.getElementById('operation_region_text').innerHTML = selected_options;
//     }
//     if (operation_regions.length > 0) {
//         $.ajax({
//             url: checkbox_data_for_add_promotions_url,
//             data: {
//                 'getdata': JSON.stringify({ 'operation_region': [operation_regions, null, promotions_data_to_upload.shop] }),
//                 'data_to_fetch': JSON.stringify(['region', null])
//             },
//             headers: { "X-CSRFToken": token },
//             dataType: 'json',
//             type: 'POST',

//             success: function (res, status) {
//                 var content = ''

//                 content += '<div id="checkbosx2_loader" ></div>'
//                 content += `<label >
//                                 <input type="checkbox" ${operation_regions.includes('All') ? 'checked' : ''} id="sel-reg-all" class="padder regionch" onchange="checkboxSelectedRegion('All');"/>All</label>`
//                 if (promotion_data_from_backend) {
//                     if (first_time_hit_on_operation_regions) {
//                         regions = []
//                     }

//                 } else {
//                     regions = []
//                 }

//                 res.data.map(x => {
//                     if (promotion_data_from_backend) {
//                         if (first_time_hit_on_operation_regions) {
//                             if (!regions.includes(x)) regions.push(x);
//                         }

//                     } else {
//                         if (!regions.includes(x)) regions.push(x);
//                     }

//                     content += `<label >
//                                 <input type="checkbox"   ${regions.includes(x) || operation_regions.includes('All') ? 'checked' : ''} id="sel-reg"  class="padder regionch" ref='${x}' onchange="checkboxSelectedRegion('${x}');refreshCheckList('sel-reg');"/>${x}</label>`
//                 })
//                 $('#checkbosx2').html(content);
//                 let allSelected = false;
//                 if (
//                     // !first_time_hit_on_operation_regions &&
//                     regions.length === document.getElementsByClassName('regionch').length - 1
//                 ){
//                     document.getElementById('sel-reg-all').checked = true;
//                     regions.push('All');
//                     allSelected = true;
//                 };
//                 if (first_time_hit_on_operation_regions){
//                     first_time_hit_on_regions = true;
//                     first_time_hit_on_areas = true;
//                 };
//                 first_time_hit_on_operation_regions = true;
//                 // document.getElementById('checkbosx1_loader').style.width = '0%';
//                 // document.getElementById('checkbosx1_loader').innerHTML = "";
//                 // if (val === 'All') checkboxSelectedRegion('All');
//                 // else
//                 checkboxSelectedRegion();
//                 if (allSelected) document.getElementById('region_text').innerHTML = "All";

//             },
//             error: function (res) {
//                 customAlert('Something went wrong while processing operation regions');
//             }
//         });
//     } else {
//         // document.getElementById('checkbosx1_loader').style.width = '0%';
//         // document.getElementById('checkbosx1_loader').innerHTML = "";
//         $('#checkbosx2').html('<div id="checkbosx2_loader" ></div>');
//         document.getElementById('operation_region_text').innerHTML = "Select";
//         regions = [];
//         checkboxSelectedRegion();
//     }

// }

const serviceAvailableInDataSet = (servicesArray, allDataSet) => {
  for (let i = 0; i < servicesArray.length; i++) {
    if (allDataSet.includes(servicesArray[i])) return true;
  }
  return false;
};

// function checkboxForshops(val, is_amenity , dont_call_api) {
//     promotion_submit_button.classList.add('disabled')
//     promotion_submit_button.setAttribute("disabled", true);
//     $('#checkbosx1').html('Loading....')
//     let selection_option_id;
//     let show_loader_id;
//     let services_array;
//     let allSelectedDataString;
//     let allSelectedDataStringToggle;
//     let allCheckboxInputId;

//     if (is_amenity)
//     {
//         selection_option_id = "amenity_text";
//         show_loader_id = "checkbosx6_loader";
//         content_id = "checkbosx6";
//         services_array = all_amenities;
//         other_services = all_shops;
//         allSelectedDataString = 'amenityAll';
//         allSelectedDataStringToggle = 'shopAll';
//         allCheckboxInputId = 'sel-reg-amenity-all';
//     }
//     else
//     {
//         selection_option_id = "shop_text";
//         show_loader_id = "checkbosx0_loader";
//         content_id = "checkbosx5";
//         services_array = all_shops;
//         other_services = all_amenities;
//         allSelectedDataString = 'shopAll';
//         allSelectedDataStringToggle = 'amenityAll';
//         allCheckboxInputId = 'sel-reg-shop-all';
//     }

//     document.getElementById(show_loader_id).style.width = '100%';
//     document.getElementById(show_loader_id).style.height = '100%';
//     document.getElementById(content_id).style.overflowY = 'hidden';
//     document.getElementById(show_loader_id).innerHTML = "Please wait...";
//     let selected_options = ''
//     const checkbxes = document.getElementsByClassName('shopch');
//     const servicesLabels = document.getElementsByClassName('servicesLabel');
//     if (val) {
//         if (
//             promotions_data_to_upload.shop.includes(val) ||
//             promotions_data_to_upload.shop.includes(allSelectedDataString)
//         ) {
//             if (val === 'All') {
//                 const pos = promotions_data_to_upload.shop.indexOf(allSelectedDataString);
//                 promotions_data_to_upload.shop.splice(pos, 1);
//                 for (var i = 0; i < checkbxes.length; i++) {
//                     let serviceText = servicesLabels[i].innerHTML.split('>');
//                     document.getElementById(allCheckboxInputId).checked = false;
//                     if (services_array.includes(serviceText[serviceText.length-1])) {
//                         const serviceIndex = promotions_data_to_upload.shop.indexOf(serviceText[serviceText.length-1]);
//                         promotions_data_to_upload.shop.splice(serviceIndex, 1);
//                         checkbxes[i].checked = false;
//                     }else if (
//                         serviceText[serviceText.length-1] !== 'All' &&
//                         !promotions_data_to_upload.shop.includes(serviceText[serviceText.length-1]) &&
//                         checkbxes[i].checked
//                     ) {
//                         promotions_data_to_upload.shop.push(serviceText[serviceText.length-1])
//                     }
//                 }
//             } else {
//                 const pos = promotions_data_to_upload.shop.indexOf(val);
//                 promotions_data_to_upload.shop.splice(pos, 1);
//                 if (promotions_data_to_upload.shop.includes(allSelectedDataString)){
//                     promotions_data_to_upload.shop = promotions_data_to_upload.shop.filter(shop => services_array.includes(shop))
//                     }
//                 promotions_data_to_upload.shop.forEach((element, index) => {
//                     if (![allSelectedDataString, allSelectedDataStringToggle].includes(element)){
//                         selected_options += ` ${element},`
//                     }
//                 });
//                 document.getElementById(selection_option_id).innerHTML = selected_options;
//             }
//         } else {
//             if (val === 'All') {
//                 if (
//                     promotions_data_to_upload.shop.includes(
//                         allSelectedDataStringToggle
//                     )
//                 ) promotions_data_to_upload.shop = [allSelectedDataString, allSelectedDataStringToggle]
//                 else promotions_data_to_upload.shop = [allSelectedDataString]
//                 for (var i = 0; i < checkbxes.length; i++) {
//                     let serviceText = servicesLabels[i].innerHTML.split('>');
//                     document.getElementById(allCheckboxInputId).checked = true;
//                     if (services_array.includes(serviceText[serviceText.length-1])) {
//                         checkbxes[i].checked = true;
//                         if (serviceText[serviceText.length-1] !== 'All') promotions_data_to_upload.shop.push(serviceText[serviceText.length-1]);
//                     }else if (
//                         serviceText[serviceText.length-1] !== 'All' &&
//                         !promotions_data_to_upload.shop.includes(serviceText[serviceText.length-1]) &&
//                         checkbxes[i].checked
//                     ) {
//                         promotions_data_to_upload.shop.push(serviceText[serviceText.length-1])
//                     };
//                     // if(
//                     //     serviceText[serviceText.length-1] !== 'All' &&
//                     //     !promotions_data_to_upload.shop.includes(serviceText[serviceText.length-1]) &&
//                     //     other_services.includes(serviceText[serviceText.length-1])
//                     // ) promotions_data_to_upload.shop.push(serviceText[serviceText.length-1]);
//                 }
//                 document.getElementById(selection_option_id).innerHTML = "All";
//             } else {
//                 if (!promotions_data_to_upload.shop.includes(allSelectedDataString)) {

//                     promotions_data_to_upload.shop.push(val)
//                     let selected_options = ''
//                     promotions_data_to_upload.shop.forEach((element, _index) => {
//                         if (![allSelectedDataString, allSelectedDataStringToggle].includes(element)){
//                             selected_options += ` ${element},`
//                         }
//                     });

//                     document.getElementById(selection_option_id).innerHTML = selected_options;
//                 }
//             }
//         }
//     }
//     else {

//         let selected_options = ''
//         promotions_data_to_upload.shop.forEach(element => {
//             if(services_array.includes(element)){
//                 document.getElementsByClassName(`shopch${element}`)[0].checked = true;
//                 if (![allSelectedDataString, allSelectedDataStringToggle].includes(element)){
//                     selected_options += ` ${element},`
//                 }
//             }
//         });
//         if (selected_options.length >0) document.getElementById(selection_option_id).innerHTML = selected_options;
//     }
//     if (
//         // !first_time_hit_on_operation_regions &&
//         promotions_data_to_upload.shop.filter(
//             shop => ![allSelectedDataString, allSelectedDataStringToggle].includes(
//                 shop
//             ) && services_array.includes(shop)
//         ).length === services_array.length
//     ){
//         document.getElementById(allCheckboxInputId).checked = true;
//         promotions_data_to_upload.shop.push(allSelectedDataString);
//         document.getElementById(selection_option_id).innerHTML = "All";
//     };
//     if (dont_call_api == null){
//         if (promotions_data_to_upload.shop.length > 0) {

//             let setAsSelected = serviceAvailableInDataSet(
//                 promotions_data_to_upload.shop,
//                 services_array
//             );
//             if (!setAsSelected) document.getElementById(selection_option_id).innerHTML = "Select";
//             $.ajax({
//                 url: checkbox_data_for_add_promotions_url,
//                 data: {
//                     'getdata': JSON.stringify({ 'shops': [null, null, promotions_data_to_upload.shop] }),
//                     'data_to_fetch': JSON.stringify(['operation_region', null])
//                 },
//                 headers: { "X-CSRFToken": token },
//                 dataType: 'json',
//                 type: 'POST',

//                 success: function (res, status) {
//                     var content = '';
//                     $('#checkbosx1').html('Loading....')
//                     content += '<div id="checkbosx1_loader" ></div>'
//                     content += `<label >
//                                     <input type="checkbox"  ${promotions_data_to_upload.shop.includes(allSelectedDataString) ? 'checked' : ''} id="sel-opr-reg-all" class="padder opsch" onchange="checkboxSelected('All');"/>All</label>`;

//                     res.data.map(x => {
//                         content += `<label >

//                                             <input type="checkbox"  ${(operation_regions.includes(x) || promotions_data_to_upload.shop.includes(allSelectedDataString) || operation_regions.includes('All')) ? 'checked' : ''} id="sel-opr-reg" ref='${x}' class="padder opsch" onchange="checkboxSelected('${x}');refreshCheckList('sel-opr-reg');"/>${x}</label>
//                                 `;
//                     })
//                     document.getElementById('operation_region_text').innerHTML = 'All'
//                     $('#checkbosx1').html(content)
//                     // document.getElementById(show_loader_id).style.width = '0%';
//                     // document.getElementById(show_loader_id).innerHTML = "";
//                     let allSelected = false;
//                     if (
//                         // !first_time_hit_on_operation_regions &&
//                         operation_regions.length === document.getElementsByClassName('opsch').length - 1
//                     ){
//                         document.getElementById('sel-opr-reg-all').checked = true;
//                         operation_regions.push('All');
//                         allSelected = true;
//                     };
//                     if (promotion_data_from_backend) {
//                         if (val) {
//                             operation_regions = [];
//                             checkboxSelected('All');
//                         }
//                         else {
//                             checkboxSelected();
//                         }

//                     } else {
//                         operation_regions = [];
//                         checkboxSelected('All');
//                     }
//                     if (allSelected) document.getElementById('operation_region_text').innerHTML = "All";
//                 },
//                 error: function (res) {
//                     customAlert('Something went wrong while processing shops');
//                 }
//             });
//         } else {
//             $('#checkbosx1').html('<div id="checkbosx1_loader" ></div>')
//             // document.getElementById(show_loader_id).style.width = '0%';
//             // document.getElementById(show_loader_id).innerHTML = "";
//             document.getElementById(selection_option_id).innerHTML = "Select";
//             operation_regions = [];
//             checkboxSelected();
//         }
//     }else{
//         // document.getElementById(show_loader_id).style.width = '0%';
//         // document.getElementById(show_loader_id).innerHTML = "";
//         if (!promotion_data_from_backend) document.getElementById(selection_option_id).innerHTML = "Select";
//     }
// }

function showCanclePopup() {
  $("#cancle_submit_warning_popup").modal("show");
}

function hideLoader() {
  $("#loader_for_mfg_ev_app").hide();
}
function showLoader() {
  $("#loader_for_mfg_ev_app").show();
}

//  condition comparing variable

const OPS_REGIONS_ADD_CONTENT_TYPES = [SHOP_CONST, AMENITY_CONST];
const REGIONS_ADD_CONTENT_TYPES = [SHOP_CONST, AMENITY_CONST, OPS_REGION_CONST];
const AREAS_ADD_CONTENT_TYPES = [
  SHOP_CONST,
  AMENITY_CONST,
  OPS_REGION_CONST,
  REGION_CONST,
];
const STATIONS_ADD_CONTENT_TYPES = [
  SHOP_CONST,
  AMENITY_CONST,
  OPS_REGION_CONST,
  REGION_CONST,
  AREA_CONST,
];

var shops = new Set([]);
var amenities = new Set([]);
let operationRegions = new Set([]);
let regions = new Set([]);
let areas = new Set([]);
let stationIds = new Set([]);

const getCheckedCheckboxesCount = (
  containerClassName,
  getAllSelectedStatus
) => {
  let counter = 0;
  let containerContent = document.querySelectorAll(`.${containerClassName}`);
  containerContent.forEach((element) => {
    if (element.checked) counter += 1;
  });
  if (getAllSelectedStatus) return containerContent.length === counter;
  return counter;
};

const allSelctionAndDelectionHandling = (inputClassName, checked) => {
  var contents = document.getElementsByClassName(inputClassName);
  for (var i = 0; i < contents.length; i++) {
    contents[i].checked = checked;
  }
};

const handleCheckboxSelection = (
  value,
  isAllClicked,
  selection,
  selectionKey,
  dataArray,
  dependency,
  depedentDataarray,
  allData = []
) => {
  if (isAllClicked) {
    if (getCheckedCheckboxesCount(`${selection}-input`, true)) {
      dataArray.clear();
      allSelctionAndDelectionHandling(`${selection}-input`, false);
    } else {
      document.getElementById(`${selection}Text`).innerHTML = "All";
      if (allData.length) dataArray = new Set(allData);
      else
        dataArray = stationsMasterDataFromBackend
          .filter((station) =>
            dependency
              ? depedentDataarray.has(station[dependency])
              : (station.shops &&
                  station.shops.some((shop) => shops.has(shop))) ||
                (station.amenities &&
                  station.amenities.some((amenity) => amenities.has(amenity)))
          )
          .map((data) => data[selectionKey]);
      allSelctionAndDelectionHandling(`${selection}-input`, true);
    }
  } else {
    dataArray.has(value) ? dataArray.delete(value) : dataArray.add(value);
    if (getCheckedCheckboxesCount(`${selection}-input`, true)) {
      document.getElementById(`${selection}Text`).innerHTML = "All";
      document.getElementById(`${selection}-all-input`).checked = true;
    } else {
      document.getElementById(`${selection}-all-input`).checked = false;
      document.getElementById(`${selection}Text`).innerHTML = Array.isArray(
        dataArray
      )
        ? dataArray.join(", ")
        : Array.from(dataArray).join(", ");
    }
  }
  dataArray = new Set(dataArray);
  if (!dataArray.size) {
    document.getElementById(`${selection}Text`).innerHTML = "Select";
  }
  return dataArray;
};

const updateLoyaltyData = (type, value) => {
  let isAllClicked = value === "All";
  switch (type) {
    case SHOP_CONST:
      shops = handleCheckboxSelection(
        value,
        isAllClicked,
        SHOP_CONST,
        SHOP_CONST,
        shops,
        null,
        null,
        all_shops
      );
      operationRegions.clear();
      regions.clear();
      areas.clear();
      stationIds.clear();
      break;
    case AMENITY_CONST:
      amenities = handleCheckboxSelection(
        value,
        isAllClicked,
        AMENITY_CONST,
        AMENITY_CONST,
        amenities,
        null,
        null,
        all_amenities
      );
      operationRegions.clear();
      regions.clear();
      areas.clear();
      stationIds.clear();
      break;
    case OPS_REGION_CONST:
      operationRegions = handleCheckboxSelection(
        value,
        isAllClicked,
        OPS_REGION_CONST,
        "operation_region",
        operationRegions,
        null,
        null
      );
      regions.clear();
      areas.clear();
      stationIds.clear();
      break;
    case REGION_CONST:
      regions = handleCheckboxSelection(
        value,
        isAllClicked,
        REGION_CONST,
        "region",
        regions,
        "operation_region",
        operationRegions
      );
      areas.clear();
      stationIds.clear();
      break;
    case AREA_CONST:
      areas = handleCheckboxSelection(
        value,
        isAllClicked,
        AREA_CONST,
        "area",
        areas,
        "region",
        regions
      );
      stationIds.clear();
      break;
    case STATION_CONST:
      stationIds = handleCheckboxSelection(
        value,
        isAllClicked,
        STATION_CONST,
        "station_id",
        stationIds,
        "area",
        areas
      );
      break;
  }
  isAllClicked = document.getElementById(`${type}-all-input`).checked;
  showAssignLoyaltyData(type, isAllClicked);
};

const handleInitialShopsAndAmenitySelection = (data, selection) => {
  data.forEach((element) => {
    document.getElementById(`${selection}-${element}-checkbox`).checked = true;
  });
  let selectedText = Array.from(data).join(", ");
  if (getCheckedCheckboxesCount(`${selection}-input`, true)) {
    document.getElementById(`${selection}Text`).innerHTML = "All";
    document.getElementById(`${selection}-all-input`).checked = true;
  } else {
    document.getElementById(`${selection}Text`).innerHTML = selectedText
      ? selectedText
      : "Select";
  }
};

const dropdownContentHandler = (selection, data, depedentDataarray = null) => {
  let contentData = Array.from(data);
  if (selection === AREA_CONST) {
    contentData = contentData.map((area) => parseInt(area));
    contentData.sort(function (a, b) {
      return a - b;
    });
  } else contentData.sort();
  let content = `<label ><input type="checkbox" ${
    !depedentDataarray ||
    (depedentDataarray && data.size === depedentDataarray.size)
      ? "checked"
      : ""
  } value="All" class="padder" id = "${selection}-all-input" onchange="updateLoyaltyData('${selection}', 'All')"/>All</label>`;
  if (contentData.length) {
    contentData.forEach((element) => {
      content += `<label ><input type="checkbox" class="padder ${selection}-input" ${
        !depedentDataarray || depedentDataarray.has(String(element))
          ? "checked"
          : ""
      } onchange="updateLoyaltyData('${selection}','${element}');">${element}</label>`;
    });
    if (!depedentDataarray)
      document.getElementById(`${selection}Text`).innerHTML = "All";
    else {
      depedentDataarray = Array.from(depedentDataarray);
      if (selection === AREA_CONST) {
        depedentDataarray = depedentDataarray.map((area) => parseInt(area));
        depedentDataarray.sort(function (a, b) {
          return a - b;
        });
      } else contentData.sort();
      document.getElementById(`${selection}Text`).innerHTML =
        !depedentDataarray.length
          ? "Select"
          : data.size === depedentDataarray.length
          ? "All"
          : Array.from(depedentDataarray).sort().join(", ");
    }
  } else {
    if (screenIdentifier === "promotions_screen") {
      content = "Please select a Shop";
    } else if (selection==="region" && data.size === 0) {
      content = "Please select Operation Region";
    } else if (selection==="area" && data.size === 0) {
      content = "Please select Region";
    } else if (selection==="station" && data.size === 0) {
      content = "Please select Area";
    } else{
      content = "Please select Shop or Amenity";
    }

    document.getElementById(`${selection}Text`).innerHTML = "Select";
  }
  return content;
};

const showAssignLoyaltyData = (
  type,
  isAllClicked = false,
  loadEditInitialContent = false
) => {
  if (loadEditInitialContent) {
    // variables to handle duplicate content from rendering in UI
    let tempOperationRegions = new Set();
    let tempRegions = new Set();
    let tempAreas = new Set();
    let tempStationId = new Set();
    stationsMasterDataFromBackend.forEach((stationData) => {
      if (
        (stationData.shops &&
          stationData.shops.some((shop) => shops.has(shop))) ||
        (amenities.size &&
          stationData.amenities &&
          stationData.amenities.some((amenity) => amenities.has(amenity)))
      ) {
        tempOperationRegions.add(stationData.operation_region);
      }
      if (
        operationRegions.has(stationData.operation_region) &&
        ((stationData.shops &&
          stationData.shops.some((shop) => shops.has(shop))) ||
          (amenities.size &&
            stationData.amenities &&
            stationData.amenities.some((amenity) => amenities.has(amenity))))
      ) {
        tempRegions.add(stationData.region);
      }
      if (
        regions.has(stationData.region) &&
        ((stationData.shops &&
          stationData.shops.some((shop) => shops.has(shop))) ||
          (amenities.size &&
            stationData.amenities &&
            stationData.amenities.some((amenity) => amenities.has(amenity))))
      ) {
        tempAreas.add(stationData.area);
      }
      if (
        areas.has(stationData.area) &&
        ((regions.has(stationData.region) &&
          stationData.shops &&
          stationData.shops.some((shop) => shops.has(shop))) ||
          (amenities.size &&
            stationData.amenities &&
            stationData.amenities.some((amenity) => amenities.has(amenity))))
      ) {
        tempStationId.add(stationData.station_id);
      }
    });
    $("#ops-region-checkboxes").html(
      dropdownContentHandler(
        OPS_REGION_CONST,
        tempOperationRegions,
        operationRegions
      )
    );
    $("#region-checkboxes").html(
      dropdownContentHandler(REGION_CONST, tempRegions, regions)
    );
    $("#area-checkboxes").html(
      dropdownContentHandler(AREA_CONST, tempAreas, areas)
    );
    $("#station-checkboxes").html(
      dropdownContentHandler(STATION_CONST, tempStationId, stationIds)
    );
  } else {
    stationsMasterDataFromBackend.forEach((stationData) => {
      var addContent = false;
      if (!isAllClicked) {
        switch (type) {
          case "pageOnload":
          case SHOP_CONST:
          case AMENITY_CONST:
            addContent =
              (stationData.shops &&
                stationData.shops.some((shop) => shops.has(shop))) ||
              (stationData.amenities &&
                amenities.size &&
                stationData.amenities.some((amenity) =>
                  amenities.has(amenity)
                ));
            break;
          case OPS_REGION_CONST:
            addContent =
              ((stationData.shops &&
                stationData.shops.some((shop) => shops.has(shop))) ||
                (stationData.amenities &&
                  stationData.amenities.some((amenity) =>
                    amenities.has(amenity)
                  ))) &&
              operationRegions.has(stationData.operation_region);
            break;
          case REGION_CONST:
            addContent =
              ((stationData.shops &&
                stationData.shops.some((shop) => shops.has(shop))) ||
                (stationData.amenities &&
                  stationData.amenities.some((amenity) =>
                    amenities.has(amenity)
                  ))) &&
              operationRegions.has(stationData.operation_region) &&
              regions.has(stationData.region);
            break;
          case AREA_CONST:
            addContent =
              ((stationData.shops &&
                stationData.shops.some((shop) => shops.has(shop))) ||
                (stationData.amenities &&
                  stationData.amenities.some((amenity) =>
                    amenities.has(amenity)
                  ))) &&
              operationRegions.has(stationData.operation_region) &&
              regions.has(stationData.region) &&
              areas.has(stationData.area);
            break;
        }
      } else {
        addContent = true;
      }
      if (addContent) {
        if (OPS_REGIONS_ADD_CONTENT_TYPES.includes(type))
          operationRegions.add(stationData.operation_region);
        if (REGIONS_ADD_CONTENT_TYPES.includes(type))
          regions.add(stationData.region);
        if (AREAS_ADD_CONTENT_TYPES.includes(type)) areas.add(stationData.area);
        if (STATIONS_ADD_CONTENT_TYPES.includes(type))
          stationIds.add(stationData.station_id);
      }
    });

    if (OPS_REGIONS_ADD_CONTENT_TYPES.includes(type))
      $("#ops-region-checkboxes").html(
        dropdownContentHandler(OPS_REGION_CONST, operationRegions)
      );
    if (REGIONS_ADD_CONTENT_TYPES.includes(type))
      $("#region-checkboxes").html(
        dropdownContentHandler(REGION_CONST, regions)
      );
    if (AREAS_ADD_CONTENT_TYPES.includes(type))
      $("#area-checkboxes").html(dropdownContentHandler(AREA_CONST, areas));
    if (STATIONS_ADD_CONTENT_TYPES.includes(type))
      $("#station-checkboxes").html(
        dropdownContentHandler(STATION_CONST, stationIds)
      );
  }
};

window.onload = function () {
  if (promotionDataFromBackend) {
    $("#submit_button_container")
      .html(`<button class="cancle_button"  onclick="showCanclePopup();">Cancel</button>
        <button class="done_button" id="promotion_submit_button" onclick="submitPromotionData();">Submit</button>`);
    // operation_regions = promotion_data_from_backend.operation_regions
    // regions = promotion_data_from_backend.regions
    // areas = promotion_data_from_backend.area
    // promotions_data_to_upload.stations = promotion_data_from_backend.stations
    uploaded_images = promotionDataFromBackend.images;
    uploaded_images_copy = promotionDataFromBackend.images;
    uploaded_images.forEach((x) => {
      final_upload_images.push(x);
    });
    const keys_from_data = Object.keys(promotionDataFromBackend);
    const keys_from_fe_data = Object.keys(promotionDataFromBackend);
    keys_from_data.forEach((element, index) => {
      if (keys_from_fe_data.includes(element)) {
        if (typeof promotionDataFromBackend[element] === "string") {
          promotionDataFromBackend[
            element
          ] = `${promotionDataFromBackend[element]}`;
        }
        if (typeof promotionDataFromBackend[element] === "number") {
          promotionDataFromBackend[element] = promotionDataFromBackend[element];
        }
        // if (element === 'shop') {
        //     promotions_data_to_upload['shop'] = promotion_data_from_backend['shop']
        // }
      }
    });
    promotion_submit_button = document.getElementById(
      "promotion_submit_button"
    );
    // if (promotion_add_edit) {
    //     checkboxForshops(null, false);
    // } else {

    //     checkboxForshops(null, false);
    //     checkboxForshops(null, true, true);
    // }
  } else {
    $("#submit_button_container")
      .html(`<button class="cancle_button" onclick="showCanclePopup();">Cancel</button>
        <button class="done_button" id="promotion_submit_button" onclick="submitPromotionData();">Submit</button>`);
    promotion_submit_button = document.getElementById(
      "promotion_submit_button"
    );
    // if (promotion_add_edit) {

    //     checkboxForshops(null, false);
    // } else {
    //     checkboxForshops(null, false);
    //     checkboxForshops(null, true, true);
    // }
  }
  shops = new Set(
    !edit_page_check
      ? ["Budgens", "Londis"]
      : all_shops.filter((shop) => {
          return prevShopsAndAmenities.includes(shop);
        })
  );
  amenities = new Set(
    !edit_page_check
      ? []
      : all_amenities.filter((amenity) => {
          return prevShopsAndAmenities.includes(amenity);
        })
  );
  operationRegions = new Set(
    !edit_page_check ? [] : promotionDataFromBackend.operation_regions
  );
  regions = new Set(!edit_page_check ? [] : promotionDataFromBackend.regions);
  areas = new Set(!edit_page_check ? [] : promotionDataFromBackend.area);
  stationIds = new Set(
    !edit_page_check ? [] : promotionDataFromBackend.station_ids
  );
  trigger_sites = new Set(
    !edit_page_check ? [] : promotionDataFromBackend.trigger_sites
  );
  if (edit_page_check) {
    showAssignLoyaltyData("pageOnload", true, true);
    handleInitialShopsAndAmenitySelection(shops, SHOP_CONST);
    handleInitialShopsAndAmenitySelection(amenities, AMENITY_CONST);
  } else {
    showAssignLoyaltyData(SHOP_CONST);
    handleInitialShopsAndAmenitySelection(shops, SHOP_CONST);
  }

if (edit_page_check && promotionDataFromBackend && promotionDataFromBackend.visibility) {
        let visibility = promotionDataFromBackend.visibility;
        let checkboxes = document.querySelectorAll('.loyalty-visibility-input');
        let text = document.getElementById('loyaltyVisibilityText');
        let selected = []; 
        if (visibility === "ALL" || visibility === "All" || visibility === "All Users") {
            checkboxes.forEach(cb => cb.checked = true);
            text.innerText = "All Users";
        } else {
            checkboxes.forEach(cb => {
                if (cb.value === visibility) {
                    cb.checked = true;
                    selected.push(cb.value);
                }
            });
            text.innerText = selected.length ? selected[0] : "Select";
        }
    }

    // Pre-fill Car Wash on edit
    if (edit_page_check && promotionDataFromBackend && promotionDataFromBackend.is_car_wash !== undefined) {
        document.getElementById('car_wash_dropdown').value = String(promotionDataFromBackend.is_car_wash);
    }

    // Show/hide Car Wash field based on Offer Type
    const offerType = promotionDataFromBackend ? promotionDataFromBackend.offer_type : null;
    if (offerType === "Loyalty Offers") {
        document.getElementById('carWashField').style.display = "block";
    } else {
        document.getElementById('carWashField').style.display = "none";
    }



// function toggleCarWashField() {
//         const offerType = promotionDataFromBackend ? promotionDataFromBackend.offer_type : null;
//         const carWashField = document.getElementById('carWashField');
//         if (offerType === "Loyalty Offers") {
//             carWashField.style.display = "block";
//         } else {
//             carWashField.style.display = "none";
//             document.getElementById('car_wash_dropdown').value = '';
//         }
//     }

//     // Pre-fill Car Wash value on edit
//     if (edit_page_check && promotionDataFromBackend && typeof promotionDataFromBackend.is_car_wash !== "undefined") {
//         document.getElementById('car_wash_dropdown').value = String(promotionDataFromBackend.is_car_wash);
//     }

//     // Call toggle on load
//     toggleCarWashField();

//     // If offer type can be changed on the page, add a change event:
//     const offerTypeDropdown = document.getElementById('offer_type_dropdown');
//     if (offerTypeDropdown) {
//         offerTypeDropdown.addEventListener('change', function() {
//             promotionDataFromBackend.offer_type = this.value;
//             toggleCarWashField();
//         });
//     }

};
