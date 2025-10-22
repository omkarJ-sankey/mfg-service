
if (!edit_page_check){
  promotionDataFromBackend = {
    retail_barcode: "",
    promotion_title: "",
    product: "",
    m_code: "",
    status: "",
    available_for: "",
    start_date: "",
    end_date: "",
    price: 0,
    quantity: 0,
    unique_code: "",
    offer_details: "",
    terms_and_conditions: "",
    offer_type: "",
    shop: [],
    londis_code: "",
    budgen_code: "",
    operation_regions: [],
    regions: [],
    area: [],
    station_ids: [],
    images: [],
  }
};
if (edit_page_check){
  promotionDataFromBackend = {
  retail_barcode: promotionDataFromBackend.retail_barcode,
  promotion_title: promotionDataFromBackend.promotion_title,
  product: promotionDataFromBackend.product,
  m_code: promotionDataFromBackend.m_code,
  status: promotionDataFromBackend.status,
  available_for: promotionDataFromBackend.available_for,
  start_date: promotionDataFromBackend.start_date,
  end_date: promotionDataFromBackend.end_date,
  price: promotionDataFromBackend.price,
  quantity: promotionDataFromBackend.quantity,
  unique_code: promotionDataFromBackend.unique_code,
  offer_details: promotionDataFromBackend.offer_details,
  terms_and_conditions: promotionDataFromBackend.terms_and_conditions,
  offer_type: promotionDataFromBackend.offer_type,
  shop: promotionDataFromBackend.shop,
  londis_code: promotionDataFromBackend.londis_code,
  budgen_code: promotionDataFromBackend.budgen_code,
  operation_regions: promotionDataFromBackend.operation_regions,
  regions: promotionDataFromBackend.regions,
  area: promotionDataFromBackend.area,
  station_ids: promotionDataFromBackend.station_ids,
  images: promotionDataFromBackend.images,
  }
};

function updateUploadedDataSet(n, val) {
    let big_field_array = [11, 12]
    let numeric_fields = [8, 9]
    element = document.getElementById(`error_field${n}`)
    if (val.length === 0) {
        element.innerHTML = "This field is required"
    } else if (numeric_fields.includes(n)) {
        let num = parseFloat(val);
        if (num <= 0.1) {
            element.innerHTML = "Value is not valid.";
        } else if (num >= 10000) {
            element.innerHTML = "Can't be more than 10000.";
        } else {
            element.innerHTML = ''
        }
    }
    else if ((n === 0 || n === 10) && val.length > 15) {
        element.innerHTML = "You can't enter more than 15 chars"
    } else if (big_field_array.includes(n) && val.length > 300) {
        element.innerHTML = "You can't enter more than 300 chars"
    }
    else if (!big_field_array.includes(n) && val.length > 50) {
        element.innerHTML = "You can't enter more than 50 chars"
    } else {
        element.innerHTML = ""

    }
    const upload_keys = Object.keys(promotionDataFromBackend);
    if (numeric_fields.includes(n)) {
        promotionDataFromBackend[upload_keys[n]] = parseFloat(val)
    }
    else {
        promotionDataFromBackend[upload_keys[n]] = val;
    }

}

function submitPromotionData() {
    $('#loader_for_mfg_ev_app').show();
    promotionDataFromBackend.stations = Array.from(
      stationIds
      );
      promotionDataFromBackend.shop = [
          ...Array.from(
              shops
          )
      ];
    promotionDataFromBackend.images = uploaded_images
    let error_less = true
    const upload__keys = Object.keys(promotionDataFromBackend);

    const numeric_fields = [8, 9]
    upload__keys.forEach((element, index) => {
        if (numeric_fields.includes(index)) {
            var element_box = document.getElementById(`error_field${index}`);
            let num = parseFloat(promotionDataFromBackend[element]);
            if (num <= 0.1) {
                element_box.innerHTML = "Value is not valid.";
                if (error_less) error_less = false;
            } else if (num >= 10000) {
                element_box.innerHTML = "Can't be more than 10000.";
                if (error_less) error_less = false;
            } else {
                element_box.innerHTML = ''
            }
        }
        else {
            if (typeof (promotionDataFromBackend[element]) === "string") {

                let big_field_array = [11, 12]
                element_box = document.getElementById(`error_field${index}`)
                if (index < 15 && promotionDataFromBackend[element].length === 0) {
                    element_box.innerHTML = "This field is required";
                    if (error_less) error_less = false;

                }
                else if (index < 15 && (index === 0 || index === 10) && promotionDataFromBackend[element].length > 15) {
                    element_box.innerHTML = "You can't enter more than 15 chars";
                    if (error_less) error_less = false;
                }
                else if (index < 15 && big_field_array.includes(index) && promotionDataFromBackend[element].length > 300) {
                    element_box.innerHTML = "You can't enter more than 200 chars";
                    if (error_less) error_less = false;
                }
                else if (index < 15 && !big_field_array.includes(index) && promotionDataFromBackend[element].length > 50) {
                    element_box.innerHTML = "You can't enter more than 50 chars";
                    if (error_less) error_less = false;
                }
                else if (index < 15) element_box.innerHTML = ""
            }
        }
        if (element === 'station_ids') {
            var station_fields = document.getElementsByClassName(`station_error_field`)
            if(stationIds.size === 0 ) {
                for (var i = 0; i < station_fields.length; i++) {
                    station_fields[i].innerHTML = "This field is required"
                }
                if (error_less) error_less = false;

            } else {
                for (var k = 0; k < station_fields.length; k++) {
                    station_fields[k].innerHTML = ""
                }
            }
        }
        if(element === 'operation_regions'){
          var ops_region_fields = document.getElementById(`station_error_field_ops_region`)
          if(operationRegions.size === 0 ) 
          {
              ops_region_fields.innerHTML = "This field is required"
            if (error_less) error_less = false;
              
          }else {
                ops_region_fields.innerHTML = ""
          }
      }
        if(element === 'regions'){
          var region_fields = document.getElementById(`station_error_field_region`)
          if(regions.size === 0 ) 
          {
              region_fields.innerHTML = "This field is required"
            if (error_less) error_less = false;
              
          }else {
                region_fields.innerHTML = ""
          }
      }
        if(element === 'area'){
          var area_fields = document.getElementById(`station_error_field_areas`)
          if(areas.size === 0 ) 
          {
              area_fields.innerHTML = "This field is required"
            if (error_less) error_less = false;
              
          }else {
                area_fields.innerHTML = ""
          }
      }
        if (element === 'shop') {
            var shop_error = document.getElementById(`error_field14`)
            if (promotionDataFromBackend[element].length === 0) {
                shop_error.innerHTML = "Please select shops"

                if (error_less) error_less = false;
            } else shop_error.innerHTML = ""
        }
        if (element === 'start_date' || element === 'end_date') {

            var start_date_error_box = document.getElementById(`error_field6`)
            var end_date_error_box = document.getElementById(`error_field7`)
            if (promotionDataFromBackend[element].length !== 0) {
                var d1_splits = promotionDataFromBackend['start_date'].split('/');
                var d2_splits = promotionDataFromBackend['end_date'].split('/');
                var start_formatetd_date = `${d1_splits[1]}/${d1_splits[0]}/${d1_splits[2]}`;
                var end_formatetd_date = `${d2_splits[1]}/${d2_splits[0]}/${d2_splits[2]}`;
                var d1 = new Date(start_formatetd_date);
                var d2 = new Date(end_formatetd_date);
                if (d1 < d2) {
                    start_date_error_box.innerHTML = ''
                    end_date_error_box.innerHTML = ''
                } else {
                    start_date_error_box.innerHTML = "Start date must be less than end date";
                    end_date_error_box.innerHTML = "End date must be greater than start date";
                    if (error_less) error_less = false;
                }
            }
        }
    });

    var url_for_ajax = window.location.href
    if(error_less){

      uploaded_images_copy = uploaded_images_copy.filter( function( el ) {
          return uploaded_images.indexOf( el ) < 0;
      });

        if (url_for_ajax.includes("edit-promotions")) {
            promotionDataFromBackend.removeImages = uploaded_images_copy;
        } else {
            promotionDataFromBackend.removeImages = [];
        }
        promotionDataFromBackend.images = final_upload_images;
        $.ajax({
            url: url_for_ajax,
            data: { 'getdata': JSON.stringify(promotionDataFromBackend) },
            headers: { "X-CSRFToken": token },
            dataType: 'json',
            type: 'POST',

            success: function (res, status) {
                if (res.status === 1) window.location.href = window.origin + res.url + query_params_str_edit_promotion
                else customAlert("Something went wrong!");
                $('#loader_for_mfg_ev_app').hide();
            },
            error: function (res) {
                $('#loader_for_mfg_ev_app').hide();
                customAlert("Something went wrong!");
            }
        });
    } else {
        var elmnt = document.getElementById(`formSection`);
        elmnt.scrollIntoView();

        $('#loader_for_mfg_ev_app').hide();
    }
}

