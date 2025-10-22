(function () {
    "use strict";

    function Pagination() {

        const objJson = paginationObj;

        let prevButton = document.getElementById('button_prev');
        let nextButton = document.getElementById('button_next');
        let searchInput = document.getElementById('search-input');
        const recordCount = document.getElementById('record_count');


        const clickPageNumber = document.querySelectorAll('.clickPageNumber');

        let current_page = 1;
        let records_per_page = paginationCount;
        let objLength = objJson.length;

        // document.querySelectorAll('#update-configurations').forEach(btn => {
        //     btn.addEventListener('click', function () {
        //       const id = this.getAttribute('data-id');
        //       window.location.href = `/update-ocpi-configurations/${id}`;
        //     });
        //   });

        this.init = function () {
            changePage(1);
            selectedPage();
            clickPage();
            addEventListeners();
            
        }
        let selectPageData = function (config_page, conf_data) {
            let table_data;
            switch (config_page) {
                case "map_markers":
                    table_data = `<tr>
                <td hidden>${conf_data.id}</td>
                <td hidden>${conf_data.get_image_path}</td>
                <td class="config_table" data-toggle="modal" onclick="viewMarkerDetails('${conf_data.id}','${conf_data.map_marker_key}','${conf_data.get_image_path}','${conf_data.indicator_type}')" data-target="#viewIndicators" class="con-typ td_text text-left view-con-itm left_20px">${conf_data.map_marker_key}</td>
                
                <td  data-toggle="modal" onclick="viewMarkerDetails('${conf_data.id}','${conf_data.map_marker_key}','${conf_data.get_image_path}','${conf_data.indicator_type}')" data-target="#viewIndicators" class="text-center td_text view-con-itm view-connector-details-modal"><img class="amenities_table_images" src=${conf_data.get_image_path} alt=""></td>
                
                <td class=" td_text text-right config_shops_icon">
                        <img data-toggle="modal" data-target="${conf_data.indicator_type == "brand_indicator" ? '#editBrandConnector' : '#editEVConnector'}" onclick="${conf_data.indicator_type == "brand_indicator" ? "editBrandMarkerDetails" : "editEVMarkerDetails"}('${conf_data.id}','${conf_data.map_marker_key}','${conf_data.get_image_path}')" title="Edit"  src="${pencilEditImage}" class="delete-icn conf-edit-icn" alt="">
                    
                </td>
            </tr>
            `;
                    break;
                case "connectors":
                    table_data = `
                    <tr>
                        <td hidden>${conf_data.id}</td>
                        <td hidden>${conf_data.get_image_path}</td>
                        <td  class="left_20px td_text conn_table" data-toggle="modal" onclick="viewConnectorDetails('${conf_data.id}','${conf_data.connector_plug_type}','${conf_data.sorting_order}','${conf_data.app_version}','${conf_data.get_image_path}', '${conf_data.get_alt_image_path}')" data-target="#viewConnector" class="con-typ view-con-itm">${conf_data.connector_plug_type}</td>
                        <td  data-toggle="modal" onclick="viewConnectorDetails('${conf_data.id}','${conf_data.connector_plug_type}','${conf_data.sorting_order}','${conf_data.app_version}','${conf_data.get_image_path}', '${conf_data.get_alt_image_path}')" data-target="#viewConnector" class="text-center td_text view-con-itm conn_table ">${conf_data.connector_plug_type_name}</td>
                        <td  data-toggle="modal" onclick="viewConnectorDetails('${conf_data.id}','${conf_data.connector_plug_type}','${conf_data.sorting_order}','${conf_data.app_version}','${conf_data.get_image_path}', '${conf_data.get_alt_image_path}')" data-target="#viewConnector" class="text-center td_text view-con-itm conn_table ">${conf_data.sorting_order ? conf_data.sorting_order : 'Not provided'}</td>
                        <td  data-toggle="modal" onclick="viewConnectorDetails('${conf_data.id}','${conf_data.connector_plug_type}','${conf_data.sorting_order}','${conf_data.app_version}','${conf_data.get_image_path}', '${conf_data.get_alt_image_path}')" data-target="#viewConnector" class="text-center td_text view-con-itm conn_table ">${conf_data.app_version ? conf_data.app_version : 'Not provided'}</td>
                        <td  data-toggle="modal" onclick="viewConnectorDetails('${conf_data.id}','${conf_data.connector_plug_type}','${conf_data.sorting_order}','${conf_data.app_version}','${conf_data.get_image_path}', '${conf_data.get_alt_image_path}')" data-target="#viewConnector" class="text-center td_text view-con-itm"><img class="amenities_table_images" src="${conf_data.get_image_path}" alt=""></td>
                        <td  data-toggle="modal" onclick="viewConnectorDetails('${conf_data.id}','${conf_data.connector_plug_type}','${conf_data.sorting_order}','${conf_data.app_version}','${conf_data.get_image_path}', '${conf_data.get_alt_image_path}')" data-target="#viewConnector" class="text-center td_text view-con-itm"><img class="amenities_table_images" src="${conf_data.get_alt_image_path}" alt=""></td>
                        <td class="text-right config_shops_icon">
                                <img data-toggle="modal" id="del-con" data-id=${conf_data.id} data-target="#deleteConnector"  title="Delete" src="${deleteRowImage}" class="delete-icn del-con-itm-icn conn_table" alt="">
                        <img data-toggle="modal" data-target="#editConnector" onclick="editConnectorDetails('${conf_data.id}','${conf_data.connector_plug_type}','${conf_data.sorting_order}','${conf_data.app_version}','${conf_data.get_image_path}', '${conf_data.get_alt_image_path}')" title="Edit" src="${pencilEditImage}" class="delete-icn" alt="">
                        </td>
                    </tr>
                `
                    break;
                case "amenities":
                    table_data = `
                <tr>
                    <td hidden>${conf_data.id}</td>
                    <td hidden>${conf_data.get_image_path}</td>
                    <td class="config_table" data-toggle="modal" onclick="viewConnectorDetails('${conf_data.id}','${conf_data.service_name}','${conf_data.get_image_path}','${conf_data.get_image_path_with_text}','${conf_data.service_unique_identifier}')" data-target="#viewAmenities" class="con-typ td_text text-left view-con-itm left_20px">${conf_data.service_name}</td>
                    <td class="config_table" data-toggle="modal" onclick="viewConnectorDetails('${conf_data.id}','${conf_data.service_name}','${conf_data.get_image_path}','${conf_data.get_image_path_with_text}','${conf_data.service_unique_identifier}')" data-target="#viewAmenities" class="con-typ td_text text-left view-con-itm left_20px">
                        ${conf_data.service_unique_identifier ? conf_data.service_unique_identifier : "Not provided"}    
                    
                    </td>
                    <td  data-toggle="modal" onclick="viewConnectorDetails('${conf_data.id}','${conf_data.service_name}','${conf_data.get_image_path}','${conf_data.get_image_path_with_text}','${conf_data.service_unique_identifier}')" data-target="#viewAmenities" class="text-center td_text view-con-itm view-connector-details-modal"><img class="amenities_table_images" src="${conf_data.get_image_path}" alt=""></td>
                    <td  data-toggle="modal" onclick="viewConnectorDetails('${conf_data.id}','${conf_data.service_name}','${conf_data.get_image_path}','${conf_data.get_image_path_with_text}','${conf_data.service_unique_identifier}')" data-target="#viewAmenities" class="text-center td_text view-con-itm view-connector-details-modal"><img class="amenities_table_images" src="${conf_data.get_image_path_with_text}" alt=""></td>
                    
                    <td class=" td_text text-right config_shops_icon">
                            <img data-toggle="modal" id="del-anem" data-id=${conf_data.id} data-target="#deleteAmenities"  title="Delete" src="${deleteRowImage}"  class="delete-icn del-con-itm-icn conf-del-icn"alt="">
                        <img data-toggle="modal" data-target="#editConnector" onclick="editConnectorDetails('${conf_data.id}','${conf_data.service_name}','${conf_data.get_image_path}','${conf_data.get_image_path_with_text}','${conf_data.service_unique_identifier}')" title="Edit"  src="${pencilEditImage}" class="delete-icn conf-edit-icn" alt="">
                    </td>
                </tr>
                `
                    break;
                case "shops":
                    table_data = `
                    <tr>
                        <td hidden>${conf_data.id}</td>
                        <td hidden>${conf_data.get_image_path}</td>
                        <td class="config_table" data-toggle="modal" onclick="viewConnectorDetails('${conf_data.id}','${conf_data.service_name}','${conf_data.service_type}','${conf_data.get_image_path}','${conf_data.service_unique_identifier}')" data-target="#viewAmenities" class="con-typ td_text text-left view-con-itm left_20px">${conf_data.service_name}</td>
                        <td class="config_table" data-toggle="modal" onclick="viewConnectorDetails('${conf_data.id}','${conf_data.service_name}','${conf_data.service_type}','${conf_data.get_image_path}','${conf_data.service_unique_identifier}')" data-target="#viewAmenities" class="con-typ td_text text-left view-con-itm left_20px">
                            ${conf_data.service_unique_identifier ? conf_data.service_unique_identifier : "Not provided"}    
                        
                        </td>
                        <td  data-toggle="modal" onclick="viewConnectorDetails('${conf_data.id}','${conf_data.service_name}','${conf_data.service_type}','${conf_data.get_image_path}','${conf_data.service_unique_identifier}')" data-target="#viewAmenities" class="text-center td_text view-con-itm view-connector-details-modal"><img class="amenities_table_images" src="${conf_data.get_image_path}" alt=""></td>
                        <td class="config_table" data-toggle="modal" onclick="viewConnectorDetails('${conf_data.id}','${conf_data.service_name}','${conf_data.service_type}','${conf_data.get_image_path}','${conf_data.service_unique_identifier}')" data-target="#viewAmenities" class="con-typ td_text text-left view-con-itm left_20px">${conf_data.service_type}</td>
                        <td class=" td_text text-right config_shops_icon">
                                <img data-toggle="modal" id="del-anem" data-id=${conf_data.id} data-target="#deleteAmenities"  title="Delete" src="${deleteRowImage}"  class="delete-icn del-con-itm-icn conf-del-icn"alt="">
                            <img data-toggle="modal" data-target="#editConnector" onclick="editConnectorDetails('${conf_data.id}','${conf_data.service_name}','${conf_data.service_type}','${conf_data.get_image_path}','${conf_data.service_unique_identifier}')" title="Edit"  src="${pencilEditImage}" class="delete-icn conf-edit-icn" alt="">
                        </td>
                    </tr>
                `
                    break;
                case "base_configurations":

                    table_data = `
                    <tr>
                        <td hidden>${conf_data.id}</td>                             
                        <td class="config_table" data-toggle="modal" onclick="viewBaseConfigurationDetails(
                                '${conf_data.id}',
                                '${b64EncodeUnicode(conf_data.base_configuration_name)}',
                                '${b64EncodeUnicode(conf_data.base_configuration_key)}',
                                '${b64EncodeUnicode(conf_data.description)}',
                                '${b64EncodeUnicode(conf_data.base_configuration_value)}',
                                '${b64EncodeUnicode(conf_data.add_to_cache)}',
                                '${b64EncodeUnicode(conf_data.frequently_used)}'
                            )" data-target="#viewBasConfigurations" class="con-typ td_text text-left view-con-itm left_20px">
                                ${conf_data.base_configuration_name ? conf_data.base_configuration_name : "Not provided"}
                        </td> 
                        <td class="config_table" data-toggle="modal"  onclick="viewBaseConfigurationDetails(
                                '${conf_data.id}',
                                '${b64EncodeUnicode(conf_data.base_configuration_name)}',
                                '${b64EncodeUnicode(conf_data.base_configuration_key)}',
                                '${b64EncodeUnicode(conf_data.description)}',
                                '${b64EncodeUnicode(conf_data.base_configuration_value)}',
                                '${b64EncodeUnicode(conf_data.add_to_cache)}',
                                '${b64EncodeUnicode(conf_data.frequently_used)}'
                            )" data-target="#viewBasConfigurations" class="con-typ td_text text-left view-con-itm left_20px">
                                ${conf_data.base_configuration_key}
                        </td>                                
                        <td class="config_table" data-toggle="modal"  onclick="viewBaseConfigurationDetails(
                                '${conf_data.id}',
                                '${b64EncodeUnicode(conf_data.base_configuration_name)}',
                                '${b64EncodeUnicode(conf_data.base_configuration_key)}',
                                '${b64EncodeUnicode(conf_data.description)}',
                                '${b64EncodeUnicode(conf_data.base_configuration_value)}',
                                '${b64EncodeUnicode(conf_data.add_to_cache)}',
                                '${b64EncodeUnicode(conf_data.frequently_used)}'
                            )" data-target="#viewBasConfigurations" class="con-typ td_text text-left view-con-itm left_20px">
                                ${conf_data.description ? conf_data.description : "Not provide"}
                        </td>                             
                        <td class="config_table" data-toggle="modal"  onclick="viewBaseConfigurationDetails(
                                '${conf_data.id}',
                                '${b64EncodeUnicode(conf_data.base_configuration_name)}',
                                '${b64EncodeUnicode(conf_data.base_configuration_key)}',
                                '${b64EncodeUnicode(conf_data.description)}',
                                '${b64EncodeUnicode(conf_data.base_configuration_value)}',
                                '${b64EncodeUnicode(conf_data.add_to_cache)}',
                                '${b64EncodeUnicode(conf_data.frequently_used)}'
                            )" data-target="#viewBasConfigurations" class="con-typ td_text text-left view-con-itm left_20px">
                                ${conf_data.base_configuration_value}
                        </td>                        
                        <td class="config_table" data-toggle="modal"  onclick="viewBaseConfigurationDetails(
                                '${conf_data.id}',
                                '${b64EncodeUnicode(conf_data.base_configuration_name)}',
                                '${b64EncodeUnicode(conf_data.base_configuration_key)}',
                                '${b64EncodeUnicode(conf_data.description)}',
                                '${b64EncodeUnicode(conf_data.base_configuration_value)}',
                                '${b64EncodeUnicode(conf_data.add_to_cache)}',
                                '${b64EncodeUnicode(conf_data.frequently_used)}'
                            )" data-target="#viewBasConfigurations" class="con-typ td_text text-left view-con-itm left_20px">
                                ${conf_data.add_to_cache ? "Yes" : "No"}
                        </td>                        
                        <td class="config_table" data-toggle="modal"  onclick="viewBaseConfigurationDetails(
                                '${conf_data.id}',
                                '${b64EncodeUnicode(conf_data.base_configuration_name)}',
                                '${b64EncodeUnicode(conf_data.base_configuration_key)}',
                                '${b64EncodeUnicode(conf_data.description)}',
                                '${b64EncodeUnicode(conf_data.base_configuration_value)}',
                                '${b64EncodeUnicode(conf_data.add_to_cache)}',
                                '${b64EncodeUnicode(conf_data.frequently_used)}'
                            )" data-target="#viewBasConfigurations" class="con-typ td_text text-left view-con-itm left_20px">
                                ${conf_data.frequently_used ? "Yes" : "No"}
                            </td>                        
                        <td class=" td_text text-right config_shops_icon">
                            
                            <img data-toggle="modal" data-target="#updateBasConfigurations" 
                                onclick="updateBasConfigurationsDetailsFunc(
                                    '${conf_data.id}',
                                    '${b64EncodeUnicode(conf_data.base_configuration_name)}',
                                    '${b64EncodeUnicode(conf_data.base_configuration_key)}',
                                    '${b64EncodeUnicode(conf_data.description)}',
                                    '${b64EncodeUnicode(conf_data.base_configuration_value)}',
                                    '${b64EncodeUnicode(conf_data.add_to_cache)}',
                                    '${b64EncodeUnicode(conf_data.frequently_used)}'
                                )" title="Edit"  src="${pencilEditImage}" 
                                class="delete-icn conf-edit-icn" alt=""
                            >
                        </td>
                    </tr>
                `
                    break;

                case "ocpi_configurations":
                table_data = `
                <tr>
                    <td hidden>${conf_data.id}</td>                             
                    <td class="config_table" data-toggle="modal">
                    <a id="update-configurations" data-id=${conf_data.id} class="no-style-link">
                            ${conf_data.name ? conf_data.name : "Not provided"}
                    </a>
                    </td> 
                    <td class="config_table" data-toggle="modal">
                        ${conf_data.endpoint}
                    </td>                                
                    <td class="config_table" data-toggle="modal"  onclick="viewBaseConfigurationDetails(
                            '${conf_data.id}',
                            '${b64EncodeUnicode(conf_data.name)}',
                            '${b64EncodeUnicode(conf_data.endpoint)}',
                            '${b64EncodeUnicode(conf_data.token)}',
                        )" data-target="#viewBasConfigurations" class="con-typ td_text text-left view-con-itm left_20px">
                            ${conf_data.party_id ? conf_data.party_id : "Not provided"}
                    </td>                             
                    <td class="config_table" data-toggle="modal"  onclick="viewBaseConfigurationDetails(
                            '${conf_data.id}',
                            '${b64EncodeUnicode(conf_data.name)}',
                            '${b64EncodeUnicode(conf_data.endpoint)}',
                            '${b64EncodeUnicode(conf_data.token)}',
                        )" data-target="#viewBasConfigurations" class="con-typ td_text text-left view-con-itm left_20px">
                            ${conf_data.country_code}
                    </td>
                    </td>                             
                    <td class="config_table" data-toggle="modal"  onclick="viewBaseConfigurationDetails(
                            '${conf_data.id}',
                            '${b64EncodeUnicode(conf_data.name)}',
                            '${b64EncodeUnicode(conf_data.endpoint)}',
                            '${b64EncodeUnicode(conf_data.token)}',
                        )" data-target="#viewBasConfigurations" class="con-typ td_text text-left view-con-itm left_20px">
                            ${conf_data.status}
                    </td>
                </tr>
                `
                break;
                case "default_images":                    
                    table_data = `
                    <tr>
                        <td hidden>${conf_data.id}</td>                             
                        <td hidden>${conf_data.get_image}</td>
                        <td class="config_table" data-toggle="modal" onclick="viewBrandDefaultImageDetailsFunc('${conf_data.id}','${conf_data.base_configuration_name}','${conf_data.app_version}','${conf_data.get_image}')" data-target="#viewDefaultImages" class="con-typ td_text text-left view-con-itm left_20px">${conf_data.base_configuration_name ? conf_data.base_configuration_name : "Not provided"}</td>
                        <td class="config_table" data-toggle="modal" onclick="viewBrandDefaultImageDetailsFunc('${conf_data.id}','${conf_data.base_configuration_name}','${conf_data.app_version}','${conf_data.get_image}')" data-target="#viewDefaultImages" class="con-typ td_text text-left view-con-itm left_20px">${conf_data.app_version ? conf_data.app_version : "Not provided"}</td>
                        <td data-toggle="modal"  class="text-center td_text view-con-itm view-connector-details-modal ">
                            <div class="d-flex align-items-center default_image_flex_box">
                                
                                <div class="default_images_container image_container_box" data-toggle="modal" onclick="viewBrandDefaultImageDetailsFunc('${conf_data.id}','${conf_data.base_configuration_name}','${conf_data.app_version}','${conf_data.get_image}')" data-target="#viewDefaultImages" >
                                    <img class="brand_default_table_images" src="${conf_data.get_image}" alt="">
                                    
                                </div>
                                <div class="image_container_box">
                                    <span class="view_default_image_btn" onclick="toggleBrandDefaultImageViewer('${conf_data.get_image}')">View Image</span>
                                </div>
                            </div>
                        </td>
                        
                        <td class=" td_text text-right config_shops_icon">
                            
                            <img data-toggle="modal" data-target="#editDefaultImage" onclick="editBrandDefaultImageDetailsFunc('${conf_data.id}','${conf_data.base_configuration_name}','${conf_data.app_version}','${conf_data.get_image}')" title="Edit"  src="${pencilEditImage}" class="delete-icn conf-edit-icn" alt="">
                        </td>
                    </tr>
                `
                    break;

            }
            return table_data;
        }

        let selectFilterData = function (config_page) {
            let table_filter_data;
            switch (config_page) {
                case "map_markers":
                    table_filter_data = objJson.filter(obj =>
                        obj.map_marker_key && obj.map_marker_key.toLowerCase().includes(searchInput.value.toLowerCase()));
                    break;
                case "connectors":
                    table_filter_data = objJson.filter(obj =>
                        (obj.connector_plug_type && obj.connector_plug_type.toLowerCase().includes(searchInput.value.toLowerCase()))
                    );
                    break;
                case "amenities":
                    table_filter_data = objJson.filter(obj =>
                        (obj.service_name && obj.service_name.toLowerCase().includes(searchInput.value.toLowerCase()))
                    );
                    break;
                case "shops":
                    table_filter_data = objJson.filter(obj =>
                        (obj.service_name && obj.service_name.toLowerCase().includes(searchInput.value.toLowerCase()))
                    );
                    break;
                case "base_configurations":
                    table_filter_data = objJson.filter(obj =>
                        (obj.base_configuration_name && obj.base_configuration_name.toLowerCase().includes(searchInput.value.toLowerCase())) ||
                        (obj.base_configuration_key && obj.base_configuration_key.toLowerCase().includes(searchInput.value.toLowerCase())) ||
                        (obj.base_configuration_value && obj.base_configuration_value.toLowerCase().includes(searchInput.value.toLowerCase()))
                    );
                    break;
                case "ocpi_configurations":
                    table_filter_data = objJson.filter(obj =>
                        (obj.name && obj.name.toLowerCase().includes(searchInput.value.toLowerCase()))
                    );
                    let status = document.getElementById('cpo_status_filter');
                    if (status.value !== "") {
                        table_filter_data = table_filter_data.filter(obj => (
                            obj.status && (obj.status.toLowerCase() === status.value.toLowerCase())
                        )
                    );
                    }                    
                    break;
                case "default_images":
                    table_filter_data = objJson.filter(obj =>
                        (obj.base_configuration_name && obj.base_configuration_name.toLowerCase().includes(searchInput.value.toLowerCase())));
                    break;

            }
            return table_filter_data;
        }
        let selectedPage = function () {
            let page_number = document.getElementById('page_number').getElementsByClassName('clickPageNumber');
            for (let i = 0; i < page_number.length; i++) {
                if (i == current_page - 1) {
                    page_number[i].classList.add("active_pagination_button");
                }
                else {
                    page_number[i].classList.remove("active_pagination_button");
                }
            }
        }

        let checkButtonOpacity = function () {
            current_page == 1 ? prevButton.classList.add('disabled_button') : prevButton.classList.remove('disabled_button');
            current_page == numPages() ? nextButton.classList.add('disabled_button') : nextButton.classList.remove('disabled_button');
        }

        let changePage = function (page) {
            const listingTable = document.getElementById('listingTable');

            if (page < 1) {
                page = 1;
            }
            if (page > (numPages() - 1)) {
                page = numPages();
            }

            listingTable.innerHTML = "";
            let tableData = objJson;

            if (paginationFor === "ocpi_configurations") {
                tableData = selectFilterData(paginationFor);
            } else if (searchInput.value.length !== 0) {
                tableData = selectFilterData(paginationFor);
            }
            objLength = tableData.length;
            let pagination_button_box = document.getElementById('pagination_button_box')


            pagination_button_box.innerHTML = "";
            if (objLength === 0) {
                recordCount.innerHTML = "No records";
            }
            else {
                if (page === 0) page = 1
                for (var i = (page - 1) * records_per_page; i < (page * records_per_page) && i < tableData.length; i++) {

                    listingTable.innerHTML += selectPageData(paginationFor, tableData[i]);
                }
                recordCount.innerHTML = `<strong>${(current_page - 1) * 10 + 1}</strong>-<strong>${current_page * 10 < objLength ? current_page * 10 : objLength}</strong> of <strong>${objLength}</strong> records`;
                pagination_button_box.innerHTML = `
            <span class="pagination_button prev" id="button_prev">Previous</span>
            <span id="page_number"></span>
            <span class="pagination_button next" id="button_next">Next</span>
            `;

                prevButton = document.getElementById('button_prev');
                nextButton = document.getElementById('button_next');
                searchInput = document.getElementById('search-input');
                pageNumbers(tableData);

                checkButtonOpacity();
                selectedPage();
                addEventListeners();
            }

        }

        let prevPage = function () {
            if (current_page > 1) {
                current_page--;
                changePage(current_page);
            }
        }

        let nextPage = function () {
            if (current_page < numPages()) {
                current_page++;
                changePage(current_page);
            }
        }
        let filterData = function () {
            current_page = 1;
            changePage(current_page);

        }

        let addEventListeners = function () {
            prevButton.addEventListener('click', prevPage);
            nextButton.addEventListener('click', nextPage);
            searchInput.addEventListener('keyup', filterData);
            if (paginationFor === "ocpi_configurations") {
                let statusFilter = document.getElementById('cpo_status_filter');
                statusFilter.addEventListener('change', filterData);
    }
        }
        let clickPage = function () {
            document.addEventListener('click', function (e) {
                if (e.target.nodeName == "SPAN" && e.target.classList.contains("clickPageNumber")) {
                    current_page = e.target.textContent;
                    changePage(current_page);
                }
            });
        }

        let pageNumbers = function (obj) {
            let pageNumber = document.getElementById('page_number');
            pageNumber.innerHTML = "";

            for (let i = 1; i < numPages() + 1; i++) {
                pageNumber.innerHTML += "<span class='clickPageNumber pagination_button'>" + i + "</span>";
            }
        }

        let numPages = function () {
            return Math.ceil(objLength / records_per_page);
        }
    }
    let pagination = new Pagination();
    pagination.init();
})();

// document.querySelectorAll('#update-configurations').forEach(btn => {
//     btn.addEventListener('click', function () {
//       const id = this.getAttribute('data-id');
//       window.location.href = `/administrator/configurations/update-ocpi-configurations/${id}`;
//     });
//   });
