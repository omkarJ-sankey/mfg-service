
const detail_content = document.getElementById('detail_content');


const tableStartingData = `

    <div class="audit_trail_details_table_container">
                
    <table class="audit_details_table">
        <tr>
            <th class="audit_table_heading_text">Field Name</th>
            <th class="audit_table_heading_text">New Value</th>
            <th class="audit_table_heading_text">Old Value</th>
        </tr>
`;
const tableStartingDataWithWhitShade = `

    <div class="audit_trail_details_table_container">
                
    <table class="audit_details_table">
        <tr>
            <th class="audit_table_heading_text_with_white_shade">Field Name</th>
            <th class="audit_table_heading_text_with_white_shade">New Value</th>
            <th class="audit_table_heading_text_with_white_shade">Old Value</th>
        </tr>
`;
const tableEndingData = `</table>
    </div>
`;

const returnTableContentData = (dataContent) => {
    if (dataContent === 0) return "0";
    if (!dataContent) return 'Not provided';
    if (typeof (dataContent) == 'string' && dataContent.split(blobUrl).length > 1) {
        return `
            <img class="auditTableImages" src="${dataContent}">
        `;
    }
    return dataContent;
}

const returnStringAndNumberDataContent = (newData, oldData, returnTableWithWhiteShade = false) => {

    let tableContent = ``;
    for (const property in (newData) ? newData : oldData) {
        if (property !== "id") {
            if (
                newData && oldData &&
                newData[property] && oldData[property] &&
                (
                    typeof (newData[property]) == 'string' ||
                    typeof (newData[property]) == 'number'
                )
            ) {

                tableContent += `
                    <tr >
                        <td class="normal_text bold_text
                        ${newData[property] !== oldData[property] && 'values_changed_row'
                    }"
                        >${property}</td>
                        <td class="normal_text
                        ${newData[property] !== oldData[property] && 'values_changed_row'
                    }">${returnTableContentData(newData[property])}</td>
                        <td class="normal_text
                        ${newData[property] !== oldData[property] && 'values_changed_row'
                    }">${returnTableContentData(oldData[property])}</td>
                    </tr>
                `;
            } else if (newData &&
                newData[property] &&
                (
                    typeof (newData[property]) == 'string' ||
                    typeof (newData[property]) == 'number'
                )
            ) {
                tableContent += `
                    <tr >
                        <td class="normal_text bold_text"
                        >${property}</td>
                        <td class="normal_text">${returnTableContentData(newData[property])}</td>
                        <td class="normal_text">-</td>
                    </tr>
                `;
            } else if (oldData &&
                oldData[property] &&
                (
                    typeof (oldData[property]) == 'string' ||
                    typeof (oldData[property]) == 'number'
                )
            ) {
                tableContent += `
                    <tr >
                        <td class="normal_text bold_text"
                        >${property}</td>
                        <td class="normal_text">-</td>
                        <td class="normal_text">${returnTableContentData(oldData[property])}</td>
                    </tr>
                `;
            } else if (
                newData && (
                    typeof (newData[property]) == 'string' ||
                    typeof (newData[property]) == 'number'
                ) ||
                oldData && (
                    typeof (oldData[property]) == 'string' ||
                    typeof (oldData[property]) == 'number'
                )
            ) {
                tableContent += `
                    <tr >
                        <td class="normal_text bold_text"
                        >${property}</td>
                        <td class="normal_text">${(newData) ?
                        returnTableContentData(newData[property]) :
                        '-'
                    }</td>
                        <td class="normal_text">${(oldData) ?
                        returnTableContentData(oldData[property]) :
                        '-'
                    }</td>
                    </tr>
                `;
            }
        }
    }
    if (returnTableWithWhiteShade)
        return tableStartingDataWithWhitShade + tableContent + tableEndingData;
    return tableStartingData + tableContent + tableEndingData;
}


const stationConnectorsChargePointsAndLoyaltyProductsForatter = (
    newDataChargePoints,
    oldDataChargePoints,
    contentText,
    isChargePoint = true,
    returnTableWithWhiteShade = false
) => {
    let chargePointsContentData = '';
    let newDataChargePointsIds = newDataChargePoints.map(newChargePoints => newChargePoints.id);
    let oldDataChargePointsIds = oldDataChargePoints.map(oldChargePoints => oldChargePoints.id);
    let newChargePointindex = 0;
    let oldChargePointindex = 0;
    let chargePointIndex = 0;

    let loopLength = (newDataChargePoints.length > oldDataChargePoints.length) ? newDataChargePoints.length : oldDataChargePoints.length;

    while (
        loopLength !== chargePointIndex
    ) {
        chargePointsContentData += `<p class="content_block_name">${contentText} ${chargePointIndex + 1}</p>`;

        if (
            newDataChargePoints[newChargePointindex] &&
            oldDataChargePoints[oldChargePointindex] &&
            newDataChargePoints[newChargePointindex].id ===
            oldDataChargePoints[oldChargePointindex].id
        ) {
            chargePointsContentData += returnStringAndNumberDataContent(
                newDataChargePoints[newChargePointindex],
                oldDataChargePoints[oldChargePointindex],
                returnTableWithWhiteShade
            );
            if (isChargePoint) {
                chargePointsContentData += stationConnectorsChargePointsAndLoyaltyProductsForatter(
                    newDataChargePoints[newChargePointindex].connectors,
                    oldDataChargePoints[oldChargePointindex].connectors,
                    "Connector",
                    false,
                    true
                )
            }
            newChargePointindex += 1;
            oldChargePointindex += 1;
        } else if (
            newDataChargePoints[newChargePointindex] &&
            !oldDataChargePointsIds.includes(
                newDataChargePoints[newChargePointindex].id
            )
        ) {
            chargePointsContentData += returnStringAndNumberDataContent(
                newDataChargePoints[newChargePointindex],
                null,
                returnTableWithWhiteShade
            );
            if (isChargePoint) {
                chargePointsContentData += stationConnectorsChargePointsAndLoyaltyProductsForatter(
                    newDataChargePoints[newChargePointindex].connectors,
                    [],
                    "Connector",
                    false,
                    true
                )
            }
            newChargePointindex += 1;
        } else if (
            oldDataChargePoints[oldChargePointindex] &&
            !newDataChargePointsIds.includes(
                oldDataChargePoints[oldChargePointindex].id
            )
        ) {
            chargePointsContentData += returnStringAndNumberDataContent(
                null,
                oldDataChargePoints[oldChargePointindex],
                returnTableWithWhiteShade
            );
            if (isChargePoint) {
                chargePointsContentData += stationConnectorsChargePointsAndLoyaltyProductsForatter(
                    [],
                    oldDataChargePoints[oldChargePointindex].connectors,
                    "Connector",
                    false,
                    true
                )
            }
            oldChargePointindex += 1;
        }

        if (isChargePoint) chargePointsContentData += '<div class="horizontal-lines audit-data-dividers"></div>';
        chargePointIndex += 1;
    }
    return chargePointsContentData
}

const servicesIdsArrayCompare = (_arrayOne, _arrayTwo) => {
    if (
        !Array.isArray(_arrayOne)
        || !Array.isArray(_arrayTwo)
        || _arrayOne.length !== _arrayTwo.length
    ) {
        return false;
    }

    // .concat() to not mutate arguments
    const arrayOne = _arrayOne.concat().sort();
    const arrayTwo = _arrayTwo.concat().sort();

    for (let i = 0; i < arrayOne.length; i++) {
        if (arrayOne[i] !== arrayTwo[i]) {
            return false;
        }
    }
    return true;
}
const getStationShopsAndImagesContent = (
    newContent,
    oldContent,
    isImageContent = false,
    isEntireDataDeleted = false
) => {
    let areServicesDifferent
    if (!isEntireDataDeleted) {

        areServicesDifferent = servicesIdsArrayCompare(
            newContent.map(service => service.id),
            oldContent.map(service => service.id)
        )
    } else {
        areServicesDifferent = isEntireDataDeleted
    }
    let innerNewContent = newContent.map(service =>
        (isImageContent) ? (
            `
                <img class="imageContent" src="${service.image_path}">
            `
        ) :
            (
                `
                <div class="audit_services_image">
                    <img class="servicesContent" src="${service.image_path}">
                </div>
            `
            )
    ).join('');

    let innerOldContent = oldContent.map(service =>
        (isImageContent) ? (
            `
                <img class="imageContent" src="${service.image_path}">
            `
        ) :
            (
                `
                <div class="audit_services_image">
                    <img class="servicesContent" src="${service.image_path}">
                </div>
            `
            )
    ).join('');

    let shopAndImageContentData = `<div 
        class="audit_sevices_comparison_box"> 
        <div class="audit_content_container_with_text">
            <span class="image_container_info_text">New data</span>
            <div class="audit_images_container 
                ${!areServicesDifferent ? 'not_matched_data ' : ''}
                ${isImageContent ? 'images_box' : ''}
            ">
                ${innerNewContent}
            </div>
        </div>
        <div class="audit_content_container_with_text">
            <span class="image_container_info_text">Old data</span>
            <div class="audit_images_container 
                ${!areServicesDifferent ? 'not_matched_data ' : ''}
                ${isImageContent ? 'images_box' : ''}
            ">
                ${innerOldContent}
            </div>
        </div>
    </div>`;
    return shopAndImageContentData;
}

const getStationContentData = (newData, oldData) => {
    let stationContentData = '';
    stationContentData += '<div class="horizontal-lines audit-data-dividers"></div>';
    stationContentData += `<p class="content_block_name">Working Hours Details</p>`;
    stationContentData += returnStringAndNumberDataContent(
        (newData) ? newData.working_hours : null,
        (oldData) ? oldData.working_hours : null
    );
    stationContentData += '<div class="horizontal-lines audit-data-dividers"></div>';
    stationContentData += `<p class="content_block_name">Charge Point Details</p>`;
    if (oldData) {
        stationContentData += stationConnectorsChargePointsAndLoyaltyProductsForatter(
            (newData) ? newData["charge_points"] : [],
            oldData["charge_points"],
            "Charge Point"
        );
    } else {
        stationContentData += stationConnectorsChargePointsAndLoyaltyProductsForatter(
            newData["charge_points"],
            [],
            "Charge Point"
        );
    };
    stationContentData += `<p class="content_block_name">Retail</p>`;
    stationContentData += getStationShopsAndImagesContent(
        (newData) ? newData.retails : [],
        (oldData) ? oldData.retails : [],
        isImageContent = false,
        isEntireDataDeleted = newData ? false : true
    );
    stationContentData += '<div class="horizontal-lines audit-data-dividers"></div>';
    stationContentData += `<p class="content_block_name">Images</p>`;
    stationContentData += getStationShopsAndImagesContent(
        (newData) ? newData.station_images : [],
        (oldData) ? oldData.station_images : [],
        isImageContent = true,
        isEntireDataDeleted = newData ? false : true
    );
    stationContentData += '<div class="horizontal-lines audit-data-dividers"></div>';
    stationContentData += `<p class="content_block_name">Food To Go</p>`;
    stationContentData += getStationShopsAndImagesContent(
        (newData) ? newData.food_to_go : [],
        (oldData) ? oldData.food_to_go : [],
        isImageContent = false,
        isEntireDataDeleted = newData ? false : true
    );
    stationContentData += '<div class="horizontal-lines audit-data-dividers"></div>';
    stationContentData += `<p class="content_block_name">Amenities</p>`;
    stationContentData += getStationShopsAndImagesContent(
        (newData) ? newData.amenities : [],
        (oldData) ? oldData.amenities : [],
        isImageContent = false,
        isEntireDataDeleted = newData ? false : true
    )
    stationContentData += '<div class="horizontal-lines audit-data-dividers"></div>';

    stationContentData += `<p class="content_block_name">Valeting Terminal Details</p>`;
    if (oldData) {
        stationContentData += stationConnectorsChargePointsAndLoyaltyProductsForatter(
            (newData) && newData["valating_terminals_data"] != undefined ? newData["valating_terminals_data"] : [],
            oldData["valating_terminals_data"] != undefined ? oldData["valating_terminals_data"] : [],
            "Valeting Terminal",
            false,
            false,
        );
    } else {
        stationContentData += stationConnectorsChargePointsAndLoyaltyProductsForatter(
            newData["valating_terminals_data"] != undefined ? newData["valating_terminals_data"] : [],
            [],
            "Valeting Terminal",
            false,
            false,
        );
    };
    return stationContentData
}

const getLoyaltyContentData = (newData, oldData) => {
    let loyaltyContentData = '';
    loyaltyContentData += '<div class="horizontal-lines audit-data-dividers"></div>';
    if (
        (
            newData && "loyalty_products" in newData
        ) || (
            oldData && "loyalty_products" in oldData
    )){
        loyaltyContentData += `<p class="content_block_name">Loyalty Products</p>`;
        if (oldData) {
            loyaltyContentData += stationConnectorsChargePointsAndLoyaltyProductsForatter(
                (newData && "loyalty_products" in newData)? newData["loyalty_products"]: [],
                (oldData && "loyalty_products" in oldData)? oldData["loyalty_products"]: [],
                "Product",
                false,
                false
            );
        } else {
            loyaltyContentData += stationConnectorsChargePointsAndLoyaltyProductsForatter(
                ("loyalty_products" in newData)? newData["loyalty_products"]: [],
                [],
                "Product",
                false,
                false
            );
        };
        loyaltyContentData += '<div class="horizontal-lines audit-data-dividers"></div>';
    }
    if (
        (
            newData && "loyalty_occurrences" in newData
        ) || (
            oldData && "loyalty_occurrences" in oldData
    )){
        loyaltyContentData += `<p class="content_block_name">Loyalty Occurrences</p>`;
        if (oldData) {
            loyaltyContentData += stationConnectorsChargePointsAndLoyaltyProductsForatter(
                (newData && "loyalty_occurrences" in newData)? newData["loyalty_occurrences"]: [],
                (oldData && "loyalty_occurrences" in oldData)? oldData["loyalty_occurrences"]: [],
                "Occurrence",
                false,
                false
            );
        } else {
            loyaltyContentData += stationConnectorsChargePointsAndLoyaltyProductsForatter(
                ("loyalty_occurrences" in newData)? newData["loyalty_occurrences"]: [],
                [],
                "Occurrence",
                false,
                false
            );
        };
        loyaltyContentData += '<div class="horizontal-lines audit-data-dividers"></div>';
    }
    if (
        (
            newData && "reward_activated_notification_content" in newData
        ) ||
        (
            oldData && "reward_activated_notification_content" in oldData
        )
    ){
        loyaltyContentData += `<p class="content_block_name">Reward Activated Notification Details</p>`
        loyaltyContentData += returnStringAndNumberDataContent(
            (
                newData && "reward_activated_notification_content" in newData
            )?newData["reward_activated_notification_content"]:{},
            (
                oldData && "reward_activated_notification_content" in oldData
            )?oldData["reward_activated_notification_content"]:{}
        );

        loyaltyContentData += '<div class="horizontal-lines audit-data-dividers"></div>';
    }
    if (
        (
            newData && "reward_expiration_notification_content" in newData
        ) || (
            oldData && "reward_expiration_notification_content" in oldData
        )
    ){
        
        loyaltyContentData += `<p class="content_block_name">Reward Expiration Notification Details</p>`
        loyaltyContentData += returnStringAndNumberDataContent(
            (
                newData && "reward_expiration_notification_content" in newData
            )? newData["reward_expiration_notification_content"]: {},
            (
                oldData && "reward_expiration_notification_content" in oldData
            )?oldData["reward_expiration_notification_content"]:{}
        );
        loyaltyContentData += '<div class="horizontal-lines audit-data-dividers"></div>';
    }
    return loyaltyContentData
}
const getFileTypeImage = (fileExtension) => {
    if (["xls", "xlsx", "csv"].includes(fileExtension.toLowerCase())) {
        file_type_image = excel_icon
    }
    else if (["png", "jpg", "jpeg"].includes(fileExtension.toLowerCase())) {
        file_type_image = image_icon
    }
    else if (["doc", "docx"].includes(fileExtension.toLowerCase())) {
        file_type_image = document_icon
    }
    else if (["pdf"].includes(fileExtension.toLowerCase())) {
        file_type_image = pdf_icon
    }
    return file_type_image
}
const getEmailNotificationContentData = (newData, oldData) => {
    let areAttachmentsSame = true
    let newAttachmentsToDisplay = ''
    let oldAttachmentsToDisplay = ''
    let EmailNotificationContentData = '';
    EmailNotificationContentData += '<div class="horizontal-lines audit-data-dividers"></div>';
    EmailNotificationContentData += `<p class="content_block_name">Attachments</p>`;

    if (newData && oldData) {
        areAttachmentsSame = JSON.stringify(newData.Attachments) === JSON.stringify(oldData.Attachments);
        (newData.Attachments).forEach(element => {
            fileExtension = (element).substr((element).lastIndexOf('.') + 1);
            file_name = element.split("images/")[1]
            file_type_image = getFileTypeImage(fileExtension)
            newAttachmentsToDisplay += `<div class="stored-image-container">
                                        <img class="image-view" src="${file_type_image}" alt="">
                                        <div class="file-name-div">
                                            <p class="file-name-para">${file_name}</p>
                                        </div>
                                    </div>`
        });

        (oldData.Attachments).forEach(element => {
            fileExtension = (element).substr((element).lastIndexOf('.') + 1);
            file_name = element.split("images/")[1]
            file_type_image = getFileTypeImage(fileExtension)
            oldAttachmentsToDisplay += `<div class="stored-image-container">
                                            <img class="image-view" src="${file_type_image}" alt="">
                                            <div class="file-name-div">
                                                <p class="file-name-para">${file_name}</p>
                                            </div>
                                        </div>`
        });

    }
    else if (newData && !oldData) {
        (newData.Attachments).forEach(element => {
            fileExtension = (element).substr((element).lastIndexOf('.') + 1);
            file_name = element.split("images/")[1]
            file_type_image = getFileTypeImage(fileExtension)
            newAttachmentsToDisplay += `<div class="stored-image-container">
                                        <img class="image-view" src="${file_type_image}" alt="">
                                        <div class="file-name-div">
                                            <p class="file-name-para">${file_name}</p>
                                        </div>
                                    </div>`
        });
    }
    else {
        (oldData.Attachments).forEach(element => {
            fileExtension = (element).substr((element).lastIndexOf('.') + 1);
            file_name = element.split("images/")[1]
            file_type_image = getFileTypeImage(fileExtension)
            oldAttachmentsToDisplay += `<div class="stored-image-container">
                                            <img class="image-view" src="${file_type_image}" alt="">
                                            <div class="file-name-div">
                                                <p class="file-name-para">${file_name}</p>
                                            </div>
                                        </div>`
        });
    }
    EmailNotificationContentData +=
        `<div class="audit_sevices_comparison_box"> 
        <div class="audit_content_container_with_text">
            <span class="image_container_info_text">New data</span>
            <div class="audit_images_container 
                ${areAttachmentsSame ? '' : 'not_matched_data '}
            ">
            ${newAttachmentsToDisplay}
            </div>
        </div>
        <div class="audit_content_container_with_text">
            <span class="image_container_info_text">Old data</span>
            <div class="audit_images_container 
            ${areAttachmentsSame ? '' : 'not_matched_data '}
            ">
                ${oldAttachmentsToDisplay}
            </div>
        </div>
    </div>`;

    return EmailNotificationContentData
}

const returnTableData = () => {
    const { new_data, old_data } = audit_data;
    let pageData = '';
    pageData += `<p class="content_block_name">${auditPage} Details</p>`
    pageData += returnStringAndNumberDataContent(new_data[0], old_data[0]);
    switch (auditPage) {
        case "Sites":
            pageData += getStationContentData(new_data[0], old_data[0])
            break;
        case "Offers":
            pageData += getLoyaltyContentData(new_data[0], old_data[0])
            break;
        case "Email Notification":
            pageData += getEmailNotificationContentData(new_data[0], old_data[0])
            break;
    }

    return pageData
}

detail_content.innerHTML = returnTableData();


const markAsReviewed = (id) => {

    document.getElementById('review_status').innerHTML = `
        <span class="mark_as_review_text">Please wait! review update in progress...</span>
    `

    $.ajax({
        url: mark_as_reviewed_url,
        data: { 'getdata': JSON.stringify({ 'audit_id': id }) },
        headers: { "X-CSRFToken": token },
        dataType: 'json',
        type: 'POST',
        success: function (res, status) {
            document.getElementById('review_status').innerHTML = `
                    <span class="mark_as_review_text">Marked as review successfully!</span>
                `
        },
        error: function (res) {
            document.getElementById('review_status').innerHTML = `
                    <input type="checkbox" id="mark_as_review">
                    <label for="mark_as_review" class="mark_as_review_text">Mark As Reviewed, 
                    Something went wrong please try after some time.</label>
                `
        }

    });
    location.reload();
}
