const COSTA_COFFE_TEXT = 'Costa Coffee';
const GENERIC_OFFERS = 'Generic Offers';
const LOYALTY_OFFERS = 'Loyalty Offers';
const FREE_LOYALTY_TEXT = 'Free';
const DISPLAY_NONE_STYLE_TEXT = "none";
const DISPLAY_BLOCK_STYLE_TEXT = "block";
let trigger_sites = new Set();
let triggerCostaCountKwh = '';

function charCountSubject(value, textarea) {
    var max = 60;
    var length = textarea.length;
    if (length > max) {
        textarea = textarea.substring(0, 60);
    }
    else {
        $(`#text-count-for-${value}`).text(max - length);
    }
}

function charCountDescription(value, textarea) {
    var max = 100;
    var length = textarea.length;

    if (length > max) {
        textarea = textarea.substring(0, 100);
    }
    else {
        $(`#text-count-for-${value}`).text(max - length);
    }
}
if (!edit_page_check) {
    promotionDataFromBackend = {
        loyalty_title: "",
        unique_code: "",
        category: "",
        bar_code_std: "",
        redeem_type: "",
        loyalty_type: "",
        start_date: "",
        end_date: "",
        cycle_duration: 0,
        number_of_total_issuances: 0,
        number_of_paid_purchases: 0,
        qr_refresh_time: 5,
        status: "",
        offer_details: "",
        terms_and_conditions: "",
        redeem_product_code: "",
        redeem_product: "",
        redeem_product_promotional_code: "",
        expiry_in_days: 0,
        reward_activated_notification_title: '',
        reward_activated_notification_description: '',
        reward_activated_notification_expiry: 0,
        reward_activated_notification_screen: 'Default Notification Screen',
        reward_activated_notification_type_of_notification: '',
        reward_expiration_notification_title: '',
        reward_expiration_notification_description: '',
        reward_expiration_notification_expiry: 0,
        reward_expiration_notification_before_x_number_of_days: 0,
        reward_expiration_notification_screen: 'Default Notification Screen',
        reward_expiration_notification_type_of_notification: '',
        reward_expiry_notification_trigger_time: '',
        promotion_image: '',
        reward_image: '',
        reward_activated_notification_image: '',
        reward_expiration_notification_image: '',
        loyalty_products: [],
        shop: [],
        operation_regions: [],
        regions: [],
        area: [],
        station_ids: [],
        images: [],
        loyalty_list_footer_message: "",
        offer_type: "",
        occurance_status: '',
        steps_to_redeem: '',
        occurrences: [],
        trigger_sites: [],
        transaction_count_for_costa_kwh_consumption: '',
        detail_site_check: false,
        visibility: '',//50
        is_car_wash: false,
        display_on_charging_screen: true,
    };
}
if (edit_page_check) {
    promotionDataFromBackend = {
        loyalty_title: promotionDataFromBackend.loyalty_title,
        unique_code: promotionDataFromBackend.unique_code,
        category: promotionDataFromBackend.category,
        bar_code_std: promotionDataFromBackend.bar_code_std,
        redeem_type: promotionDataFromBackend.redeem_type,
        loyalty_type: promotionDataFromBackend.loyalty_type,
        start_date: promotionDataFromBackend.start_date,
        end_date: promotionDataFromBackend.end_date,
        cycle_duration: promotionDataFromBackend.cycle_duration,
        number_of_total_issuances: promotionDataFromBackend.number_of_total_issuances,
        number_of_paid_purchases: promotionDataFromBackend.number_of_paid_purchases ? promotionDataFromBackend.number_of_paid_purchases : 0,
        qr_refresh_time: promotionDataFromBackend.qr_refresh_time ? promotionDataFromBackend.qr_refresh_time : 5,
        status: promotionDataFromBackend.status,
        offer_details: promotionDataFromBackend.offer_details,
        terms_and_conditions: promotionDataFromBackend.terms_and_conditions,
        redeem_product_code: promotionDataFromBackend.redeem_product_code,
        redeem_product: promotionDataFromBackend.redeem_product,
        redeem_product_promotional_code: promotionDataFromBackend.redeem_product_promotional_code,
        expiry_in_days: promotionDataFromBackend.expiry_in_days ? promotionDataFromBackend.expiry_in_days : 0,
        reward_activated_notification_title: promotionDataFromBackend.reward_activated_notification_title,
        reward_activated_notification_description: promotionDataFromBackend.reward_activated_notification_description,
        reward_activated_notification_expiry: promotionDataFromBackend.reward_activated_notification_expiry ? promotionDataFromBackend.reward_activated_notification_expiry : 0,
        reward_activated_notification_screen: promotionDataFromBackend.reward_activated_notification_screen ? promotionDataFromBackend.reward_activated_notification_screen : 'Default Notification Screen',
        reward_activated_notification_type_of_notification: promotionDataFromBackend.reward_activated_notification_type_of_notification,
        reward_expiration_notification_title: promotionDataFromBackend.reward_expiration_notification_title,
        reward_expiration_notification_description: promotionDataFromBackend.reward_expiration_notification_description,
        reward_expiration_notification_expiry: promotionDataFromBackend.reward_expiration_notification_expiry ? promotionDataFromBackend.reward_expiration_notification_expiry : 0,
        reward_expiration_notification_before_x_number_of_days: promotionDataFromBackend.expire_reward_before_x_number_of_days ? promotionDataFromBackend.expire_reward_before_x_number_of_days : 0,
        reward_expiration_notification_screen: promotionDataFromBackend.reward_expiration_notification_screen ? promotionDataFromBackend.reward_expiration_notification_screen : 'Default Notification Screen',
        reward_expiration_notification_type_of_notification: promotionDataFromBackend.reward_expiration_notification_type_of_notification,
        reward_expiry_notification_trigger_time: promotionDataFromBackend.reward_expiry_notification_trigger_time,
        promotion_image: promotionDataFromBackend.image ? promotionDataFromBackend.image : '',
        reward_image: promotionDataFromBackend.reward_image ? promotionDataFromBackend.reward_image : '',
        reward_activated_notification_image: promotionDataFromBackend.reward_activated_notification_image ? promotionDataFromBackend.reward_activated_notification_image : '',
        reward_expiration_notification_image: promotionDataFromBackend.reward_expiration_notification_image ? promotionDataFromBackend.reward_expiration_notification_image : '',
        loyalty_products: promotionDataFromBackend.loyalty_products,
        shop: promotionDataFromBackend.shop,
        operation_regions: promotionDataFromBackend.operation_regions,
        regions: promotionDataFromBackend.regions,
        area: promotionDataFromBackend.area,
        station_ids: promotionDataFromBackend.station_ids,
        images: [],
        loyalty_list_footer_message: promotionDataFromBackend.loyalty_list_footer_message ? promotionDataFromBackend.loyalty_list_footer_message : "",
        offer_type: promotionDataFromBackend.offer_type,
        occurance_status: promotionDataFromBackend.occurance_status,
        steps_to_redeem: promotionDataFromBackend.steps_to_redeem,
        occurrences: promotionDataFromBackend.occurrences,
        trigger_sites: promotionDataFromBackend.trigger_sites ? promotionDataFromBackend.trigger_sites : [],
        transaction_count_for_costa_kwh_consumption: promotionDataFromBackend.transaction_count_for_costa_kwh_consumption ? promotionDataFromBackend.transaction_count_for_costa_kwh_consumption : '',
        detail_site_check: promotionDataFromBackend.detail_site_check,
        visibility: promotionDataFromBackend.visibility ? promotionDataFromBackend.visibility:null,
        is_car_wash: promotionDataFromBackend.is_car_wash ? promotionDataFromBackend.is_car_wash:false,
        display_on_charging_screen: promotionDataFromBackend.display_on_charging_screen ? promotionDataFromBackend.display_on_charging_screen:true,
    };
    charCountSubject(
        'subject1',
        promotionDataFromBackend.reward_activated_notification_title || ''
    );
    charCountDescription(
        'description1',
        promotionDataFromBackend.reward_activated_notification_description || ''
    );
    charCountSubject(
        'subject2',
        promotionDataFromBackend.reward_expiration_notification_title || ''
    );
    charCountDescription(
        'description2',
        promotionDataFromBackend.reward_expiration_notification_description || ''
    );
    loyaltyContentToggler(promotionDataFromBackend.loyalty_type);
    offerContentTogglerBasedOnOfferType(promotionDataFromBackend.offer_type)
};

document.addEventListener('DOMContentLoaded', () => {
    handleTriggerKWhVisibility();

    const loyaltyTypeDropdown = document.getElementById('loyalty_type_dropdown');
    const redeemTypeDropdown = document.getElementById('redeem_type_dropdown');
    // console.log(`Loyalty Type: ${promotionDataFromBackend.loyalty_type}, Redeem Type: ${promotionDataFromBackend.redeem_type}`);
    
    if (loyaltyTypeDropdown) {
        loyaltyTypeDropdown.addEventListener('change', handleTriggerKWhVisibility);
    }
    if (redeemTypeDropdown) {
        redeemTypeDropdown.addEventListener('change', handleTriggerKWhVisibility);
    }
});


// Prefill Offer Visibility on edit
document.addEventListener('DOMContentLoaded', function () {
    if (typeof edit_page_check !== 'undefined' && edit_page_check && promotionDataFromBackend && promotionDataFromBackend.visibility) {
        let visibility = promotionDataFromBackend.visibility;
        let checkboxes = document.querySelectorAll('.loyalty-visibility-input');
        let text = document.getElementById('loyaltyVisibilityText');
        let selected = [];

        checkboxes.forEach(cb => cb.checked = false);

        if (
            visibility === "All Users" ||
            visibility === "ALL" ||
            visibility === "All" ||
            (Array.isArray(visibility) && visibility.length === 2)
        ) {
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

        loyaltyVisibility.clear();
        checkboxes.forEach(cb => {
            if (cb.checked) loyaltyVisibility.add(cb.value);

        });
    }
});

function updateLoyaltyVisibility() {
    loyaltyVisibility.clear();
    document.querySelectorAll('.loyalty-visibility-input').forEach(cb => {
        if (cb.checked) loyaltyVisibility.add(cb.value);
    });
    const text = document.getElementById('loyaltyVisibilityText');
    if (loyaltyVisibility.size === 2) {
        text.innerText = "All Users";
        promotionDataFromBackend.loyalty_visibility = "All Users";
    } else if (loyaltyVisibility.size === 1) {
        text.innerText = Array.from(loyaltyVisibility)[0];
        promotionDataFromBackend.loyalty_visibility = Array.from(loyaltyVisibility)[0];
    } else {
        text.innerText = "Select";
        promotionDataFromBackend.loyalty_visibility = "";
    }
}


window.onload = function () {
    updateDescriptionCount();
    updateSubjectCount();
}
function isFloat(n) {
    return Number(n) === n && n % 1 !== 0;
}

function handleTriggerKWhVisibility() {
    const loyaltyType = document.getElementById('loyalty_type_dropdown').value;
    const redeemType = document.getElementById('redeem_type_dropdown').value;
    const triggerKWhField = document.getElementById('triggerKWhField');
    const triggerKWhInput = document.getElementById('trigger_kwh_count_input');
    // console.log(`Loyalty Type: ${loyaltyType}, Redeem Type: ${redeemType}`);
    
    if (loyaltyType === 'Costa Coffee' && redeemType === 'Count') {
        triggerKWhField.style.display = 'block';
        triggerKWhInput.disabled = false;
    } else {
        triggerKWhField.style.display = 'none';
        triggerKWhInput.value = '';
        triggerKWhInput.disabled = true;
        
        document.getElementById('error_field48').innerHTML = '';
        if (promotionDataFromBackend) promotionDataFromBackend.transaction_count_for_costa_kwh_consumption = '';
    }
}

function loyaltyContentToggler(loyalty_type) {
    const triggerRedeemAvailableField = document.getElementById('triggerRedeemAvailableField');
    const cycleDurationField = document.getElementById('cycleDurationField');

    const notificationsSectionRedirectorElement = document.getElementById('notificationsSectionRedirector');
    const numberOfIssuanceContainerElement = document.getElementById('numberOfIssuanceContainer');
    const notificationsContainerElement = document.getElementById('notifications_container');
    const redeemTypeToggleTextElement = document.getElementById('redeem_type_toggle_text');
    const numberOfPaidPurchasesElement = document.getElementById('number_of_paid_purchases');
    const triggerSitesContainer1 = document.getElementById('trigger_sites_container');
    const detailSiteCheckContainer = document.getElementById('detailSiteCheckContainer');

    switch (loyalty_type) {
        case COSTA_COFFE_TEXT:
            triggerRedeemAvailableField.style.display = DISPLAY_BLOCK_STYLE_TEXT;
            cycleDurationField.style.display = DISPLAY_BLOCK_STYLE_TEXT;

            notificationsSectionRedirectorElement.style.display = DISPLAY_BLOCK_STYLE_TEXT;
            numberOfIssuanceContainerElement.style.display = DISPLAY_BLOCK_STYLE_TEXT;
            notificationsContainerElement.style.display = DISPLAY_BLOCK_STYLE_TEXT;
            redeemTypeToggleTextElement.innerHTML = "Voucher Issuance Trigger Value";
            numberOfPaidPurchasesElement.placeholder = "Enter promotion issuance trigger value";
            triggerSitesContainer1.style.display = DISPLAY_BLOCK_STYLE_TEXT;
            detailSiteCheckContainer.style.display = DISPLAY_BLOCK_STYLE_TEXT;
            break;
        case FREE_LOYALTY_TEXT:
            triggerRedeemAvailableField.style.display = DISPLAY_NONE_STYLE_TEXT;
            cycleDurationField.style.display = DISPLAY_NONE_STYLE_TEXT;

            notificationsSectionRedirectorElement.style.display = DISPLAY_BLOCK_STYLE_TEXT;
            numberOfIssuanceContainerElement.style.display = DISPLAY_BLOCK_STYLE_TEXT;
            notificationsContainerElement.style.display = DISPLAY_BLOCK_STYLE_TEXT;
            triggerSitesContainer1.style.display = DISPLAY_NONE_STYLE_TEXT;
            detailSiteCheckContainer.style.display = DISPLAY_BLOCK_STYLE_TEXT;
            break;
        default:
            triggerRedeemAvailableField.style.display = DISPLAY_BLOCK_STYLE_TEXT;
            cycleDurationField.style.display = DISPLAY_BLOCK_STYLE_TEXT;

            notificationsSectionRedirectorElement.style.display = DISPLAY_NONE_STYLE_TEXT;
            numberOfIssuanceContainerElement.style.display = DISPLAY_NONE_STYLE_TEXT;
            notificationsContainerElement.style.display = DISPLAY_NONE_STYLE_TEXT;
            triggerSitesContainer1.style.display = DISPLAY_NONE_STYLE_TEXT;
            detailSiteCheckContainer.style.display = DISPLAY_BLOCK_STYLE_TEXT;

            redeemTypeToggleTextElement.innerHTML = "Number of Purchases";
            numberOfPaidPurchasesElement.placeholder = "Enter purchase count for redemption";
    }
}


function offerContentTogglerBasedOnOfferType(offer_type) {
    const loyaltyProductsSection = document.getElementById('loyaltyProductsSection');
    const loyaltyProductSectionRedirector = document.getElementById('loyaltyProductSectionRedirector');
    // fields that need to be toggled
    const loyaltyTypeField = document.getElementById('loyaltyTypeField');
    const redeemTypeField = document.getElementById('redeemTypeField');
    const cycleDurationField = document.getElementById('cycleDurationField');
    const numberOfIssuanceContainer = document.getElementById('numberOfIssuanceContainer');
    const triggerRedeemAvailableField = document.getElementById('triggerRedeemAvailableField');
    const qrExpiryField = document.getElementById('qrExpiryField');
    const footerMessageField = document.getElementById('footerMessageField');
    const setOccurrencesField = document.getElementById('setOccurrencesField');
    const detailSiteCheckContainer = document.getElementById('detailSiteCheckContainer');
    // const triggerSitesContainer2 = document.getElementById('trigger_sites_container');
    const carWashField = document.getElementById('carWashField');
    

    if (offer_type === GENERIC_OFFERS){
        loyaltyProductsSection.style.display = DISPLAY_NONE_STYLE_TEXT;
        loyaltyProductSectionRedirector.style.display = DISPLAY_NONE_STYLE_TEXT;
        loyaltyTypeField.style.display=DISPLAY_NONE_STYLE_TEXT;
        redeemTypeField.style.display=DISPLAY_NONE_STYLE_TEXT;
        cycleDurationField.style.display=DISPLAY_NONE_STYLE_TEXT;
        numberOfIssuanceContainer.style.display=DISPLAY_NONE_STYLE_TEXT;
        triggerRedeemAvailableField.style.display=DISPLAY_NONE_STYLE_TEXT;
        qrExpiryField.style.display=DISPLAY_NONE_STYLE_TEXT;
        footerMessageField.style.display=DISPLAY_NONE_STYLE_TEXT;
        setOccurrencesField.style.display=DISPLAY_NONE_STYLE_TEXT;
        detailSiteCheckContainer.style.display = "none";
        promotionDataFromBackend.detail_site_check = false;
        // triggerSitesContainer2.style.display = DISPLAY_NONE_STYLE_TEXT;
        carWashField.style.display = DISPLAY_NONE_STYLE_TEXT;
        document.getElementById('car_wash_dropdown').value = '';
        document.getElementById('error_field50').innerHTML = '';
        loyaltyOccurrencesSectionToggler('No', called_via_input=false);
    } else {
        loyaltyContentToggler(promotionDataFromBackend.loyalty_type);
        loyaltyProductsSection.style.display = DISPLAY_BLOCK_STYLE_TEXT;
        loyaltyProductSectionRedirector.style.display = DISPLAY_BLOCK_STYLE_TEXT;
        loyaltyTypeField.style.display=DISPLAY_BLOCK_STYLE_TEXT;
        redeemTypeField.style.display=DISPLAY_BLOCK_STYLE_TEXT;
        cycleDurationField.style.display=DISPLAY_BLOCK_STYLE_TEXT;
        numberOfIssuanceContainer.style.display=DISPLAY_BLOCK_STYLE_TEXT;
        triggerRedeemAvailableField.style.display=DISPLAY_BLOCK_STYLE_TEXT;
        qrExpiryField.style.display=DISPLAY_BLOCK_STYLE_TEXT;
        footerMessageField.style.display=DISPLAY_BLOCK_STYLE_TEXT;
        setOccurrencesField.style.display=DISPLAY_BLOCK_STYLE_TEXT;
        detailSiteCheckContainer.style.display = "block";
        carWashField.style.display = DISPLAY_BLOCK_STYLE_TEXT;
        // triggerSitesContainer2.style.display = DISPLAY_BLOCK_STYLE_TEXT;
        loyaltyOccurrencesSectionToggler('Yes', called_via_input=false);
    }
}

const dateValidator = () => {
    var d1_splits = promotionDataFromBackend['start_date'].split('/');
    var d2_splits = promotionDataFromBackend['end_date'].split('/');
    
    if (promotionDataFromBackend['start_date'].length === 0 || promotionDataFromBackend['end_date'].length === 0){
        customAlert('Please select start date and end date.');
        return false
    }
    var start_formatetd_date = `${d1_splits[1]}/${d1_splits[0]}/${d1_splits[2]}`;
    var end_formatetd_date = `${d2_splits[1]}/${d2_splits[0]}/${d2_splits[2]}`;
    var d1 = new Date(start_formatetd_date);
    var d2 = new Date(end_formatetd_date);
    if (d1 > d2) {
        customAlert('Start date must be less than end date.');
        return false;
    }
    return true
}

function loyaltyOccurrencesSectionToggler(value, called_via_input = true) {
    const loyaltyOccurrencesSection = document.getElementById('loyaltyOccurrencesSection');
    const loyaltyOccuranceSectionRedirector = document.getElementById('loyaltyOccuranceSectionRedirector');
    const startDateContainer = document.getElementById('startDateContainer');
    const endDateContainer = document.getElementById('endDateContainer');
    let validDatesSelected = true; 
    if (called_via_input) {
        validDatesSelected = dateValidator();
    }
    if (validDatesSelected) {
        if (value === 'Yes'){
            loyaltyOccurrencesSection.style.display = DISPLAY_BLOCK_STYLE_TEXT;
            loyaltyOccuranceSectionRedirector.style.display = DISPLAY_BLOCK_STYLE_TEXT;
            if (called_via_input){
                startDateContainer.innerHTML = `<div class="datepicker1 mt-3" >${promotionDataFromBackend.start_date? promotionDataFromBackend.start_date : 'Date not selected'}</div>`;
                endDateContainer.innerHTML = `<div class="datepicker1 mt-3" > ${promotionDataFromBackend.end_date? promotionDataFromBackend.end_date : 'Date not selected'}</div>`;
                startDateContainer.classList.add('disbaled_background');
                endDateContainer.classList.add('disbaled_background');
            }
        }else{
            loyaltyOccurrencesSection.style.display = DISPLAY_NONE_STYLE_TEXT;
            loyaltyOccuranceSectionRedirector.style.display = DISPLAY_NONE_STYLE_TEXT;
            if (called_via_input){
                startDateContainer.innerHTML = `<input disabled type="text" id="start_date" value="${promotionDataFromBackend.start_date}" placeholder="Start date"  onchange="updateUploadedDataSet(6, this.value);"  class="datepicker1" >`;
                endDateContainer.innerHTML = `<input disabled type="text" id="end_date" value="${promotionDataFromBackend.end_date}" placeholder="End date"  onchange="updateUploadedDataSet(7, this.value);"  class="datepicker1" >`;
                $("#start_date").datepicker({
                    dateFormat: "dd/mm/yy",
                    showOn: "button",
                    minDate: -60,
                    buttonImage:
                    "https://mfgevqastorage.blob.core.windows.net/static/images/calendar-1.png",
                    buttonImageOnly: true,
                    buttonText: "Select date",
                });
                $("#end_date").datepicker({
                    dateFormat: "dd/mm/yy",
                    showOn: "button",
                    minDate: 0,
                    buttonImage:
                    "https://mfgevqastorage.blob.core.windows.net/static/images/calendar-1.png",
                    buttonImageOnly: true,
                    buttonText: "Select date",
                });
                startDateContainer.classList.remove('disbaled_background');
                endDateContainer.classList.remove('disbaled_background');
                countClickedForOccurrence = 0;
                promotionDataFromBackend.occurrences = [];
                $("#LoyaltyOccurrenceContainer").html('');
            }
        }
    }
}

function loyaltyRedeemToggler(redeem_val) {
    const redeem_text_box_txt = document.getElementById('redeem_type_toggle_text');
    const number_of_paid_purchases_box = document.getElementById('number_of_paid_purchases');
    if (promotionDataFromBackend['loyalty_type'] !== COSTA_COFFE_TEXT) {
        if (redeem_val === "Amount") {
            redeem_text_box_txt.innerHTML = "Total Amount";
            number_of_paid_purchases_box.placeholder = "Enter total amount for redemption";
        }
        else {
            redeem_text_box_txt.innerHTML = "Number of Purchases";
            number_of_paid_purchases_box.placeholder = "Enter purchase count for redemption";
        }
        // else {
        //     redeem_text_box_txt.innerHTML="Voucher Issuance Trigger Value";
        //     number_of_paid_purchases_box.placeholder = "Enter promotion issuance trigger value";
        // }
    }
}
function updateUploadedDataSet(n, val) {
    let nonMandatoryField = [42, 44]
    let big_field_array = [19, 20, 24, 25];
    let large_field_array = [13, 45]
    let larger_field_array = [14]
    let numeric_fields = [8, 9, 10, 11, 18, 21, 26, 27];
    let decimal_fields = [8, 11, 18, 21, 26, 27];
    let barcode_fields = [15, 17];
    let redeem_expiry = document.getElementById('redeem_expiry').value
    let loyalty_type_value = document.getElementById('loyalty_type_dropdown').value


    if (n === 44 && !dateValidator()){
        document.getElementById('occurance_status_dropdown').innerHTML =`
            <option value="" selected>Select</option>
            <option value="Yes">Yes</option>
            <option value="No">No</option>
        `;
        return;
    }
    document.getElementById('notifications_container').classList.remove('page-section')
    if ([COSTA_COFFE_TEXT,FREE_LOYALTY_TEXT].includes(loyalty_type_value) ) {
        document.getElementById('notifications_container').classList.add('page-section')
    }
    element = document.getElementById(`error_field${n}`)
    // if (n === 49) {
    //     if (promotionDataFromBackend.offer_type !== LOYALTY_OFFERS) {
    //         promotionDataFromBackend.detail_site_check = false;
    //         element.innerHTML = "";
    //         return;
    //     }
    //     promotionDataFromBackend.detail_site_check = (val === "1");
    //     if (val === "0") {
    //         element.innerHTML = "Detail site check is recommended.";
    //     } else {
    //         element.innerHTML = "";
    //     }
    //     return;
    // }
    if (nonMandatoryField.includes(n) && val.length > 100) {
        element.innerHTML = "You can't enter more than 100 chars"
    } else if (val.length === 0 && !nonMandatoryField.includes(n)) {
        element.innerHTML = "This field is required"
    } else if (numeric_fields.includes(n)) {
        let num = parseFloat(val);
        if (num < 0.1) {
            element.innerHTML = "Value is not valid.";
        } else if (num >= 1000 && n === 10) {
            element.innerHTML = "Should be less than 1000.";
        } else if (num > 10000 && n!==9) {
            element.innerHTML = "Can't be more than 10000.";
        } else if (num > 100000 && n===9) {
            element.innerHTML = "Can't be more than 100000.";
        } else if (decimal_fields.includes(n) && isFloat(parseFloat(val))
        ) {
            element.innerHTML = "Value is not valid."
        }
        else if (n === 27 && val > redeem_expiry) {
            element.innerHTML = "Value should be less than redeem expiry"
        }
        else {
            element.innerHTML = ''
        }
    } else if (barcode_fields.includes(n)) {
        let num = parseFloat(val);
        if (num < 0) {
            element.innerHTML = "Value is not valid.";
        } else if (isFloat(num)) {
            element.innerHTML = "Value is not valid.";
        } else if (n === 15 && val.length > 15 ) {
            element.innerHTML = "Can't be more than 15 digits.";
        }else if (`${val}`.length > 25) {
            element.innerHTML = "Can't be more than 25 digits.";
        } else {
            element.innerHTML = ''
        }
    }
    else if (big_field_array.includes(n) && val.length > 300) {
        element.innerHTML = "You can't enter more than 300 chars"
    }
    else if (large_field_array.includes(n) && val.length >= 1000) {
        element.innerHTML = "You can't enter more than 1000 chars"
    }
    else if (larger_field_array.includes(n) && val.length >= 4000) {
        element.innerHTML = "You can't enter more than 4000 chars"
    }
    else if (!large_field_array.includes(n) && !big_field_array.includes(n) && !nonMandatoryField.includes(n) && val.length > 50 && !larger_field_array.includes(n)) {
        element.innerHTML = "You can't enter more than 50 chars"
    }
    else {
        element.innerHTML = ""
    }
    let upload_keys = Object.keys(promotionDataFromBackend);
    numeric_fields.includes(n) ? promotionDataFromBackend[upload_keys[n]] = parseFloat(val) : promotionDataFromBackend[upload_keys[n]] = val;
}
function renderTriggerSitesCheckboxes() {
    const triggerSitesContainer = document.getElementById('trigger-sites-checkboxes');
    if (!triggerSitesContainer || !stationsMasterDataFromBackend) return;
    triggerSitesContainer.innerHTML = '';

    let preSelected = [];
    
    if (edit_page_check && Array.isArray(promotionDataFromBackend.trigger_sites)) {
        preSelected = promotionDataFromBackend.trigger_sites.map(String);
        trigger_sites = new Set(preSelected);
    }

    const allLabel = document.createElement('label');
    allLabel.innerHTML = `<input type="checkbox" class="padder trigger_sites-input" id="trigger_sites-all-input" onchange="handleTriggerSitesSelection('All', true)"/>All`;
    triggerSitesContainer.appendChild(allLabel);

    stationsMasterDataFromBackend.forEach(station => {
        const checked = preSelected.includes(String(station.station_id)) ? 'checked' : '';
        const label = document.createElement('label');
        label.innerHTML = `<input type="checkbox" class="padder trigger_sites-input" value="${station.station_id}" onchange="handleTriggerSitesSelection('${station.station_id}', false)" ${checked}/> ${station.station_id}`;
        triggerSitesContainer.appendChild(label);
    });

    setTimeout(() => {
        const allInput = document.getElementById('trigger_sites-all-input');
        const checkboxes = document.querySelectorAll('.trigger_sites-input:not(#trigger_sites-all-input)');
        if (trigger_sites.size === checkboxes.length) {
            allInput.checked = true;
        }
        updateTriggerSitesText();
    }, 0);
}

function handleTriggerSitesSelection(value, isAllClicked) {
    const allInput = document.getElementById('trigger_sites-all-input');
    const checkboxes = document.querySelectorAll('.trigger_sites-input:not(#trigger_sites-all-input)');
    if (isAllClicked) {
        if (allInput.checked) {
            trigger_sites = new Set(stationsMasterDataFromBackend.map(station => String(station.station_id)));
            checkboxes.forEach(cb => cb.checked = true);
        } else {
            trigger_sites.clear();
            checkboxes.forEach(cb => cb.checked = false);
        }
    } else {
        const checkbox = Array.from(checkboxes).find(cb => cb.value == value);
        if (checkbox && checkbox.checked) {
            trigger_sites.add(value);
        } else {
            trigger_sites.delete(value);
        }
        if (trigger_sites.size === checkboxes.length) {
            allInput.checked = true;
        } else {
            allInput.checked = false;
        }
    }
    updateTriggerSitesText();
}

function updateTriggerSitesText() {
    const selectedCount = trigger_sites.size;
    const triggerSitesText = document.getElementById('triggerSitesText');
    if (triggerSitesText) {
        triggerSitesText.innerText = selectedCount > 0 ? `${selectedCount} Selected` : 'Select';
    }
}

$(document).ready(function () {
    renderTriggerSitesCheckboxes();
});
var loyalty_products = []
var occurrences = []

if (promotionDataFromBackend) loyalty_products = promotionDataFromBackend.loyalty_products;
if (promotionDataFromBackend) occurrences = promotionDataFromBackend.occurrences;
let deleted_loyalty_produucts_from_frontend = [];
let deleted_loyalty_occurrences_from_frontend = [];

function updateUploadedDataLoyaltyOccurrences(n, m, val, updated_lp) {
    
    let upload_keys = Object.keys(promotionDataFromBackend.occurrences[n - 1]);
    let loyalty_occurrences_data = promotionDataFromBackend.occurrences[n - 1];
    // loyalty products object location wise validation.
    lp_element = document.getElementById(`loyalty_occurrence_error${n - 1}${m}`);
    if (m === 0 && promotionDataFromBackend.occurrences.find((occurrence,index)=> index !== n - 1 && !deleted_loyalty_occurrences_from_frontend.includes(index) &&occurrence.date === val)) {
        lp_element.innerHTML = "Occurrence is already set for selected date";
    } else if (val.length === 0) {
        lp_element.innerHTML = "This field is required";
    }else lp_element.innerHTML = "";
    if (updated_lp) loyalty_occurrences_data[upload_keys[m + 2]] = val;
    else loyalty_occurrences_data[upload_keys[m]] = val;
}


function updateUploadedDataLoyaltyProducts(n, m, val, updated_lp) {
    let upload_keys = Object.keys(promotionDataFromBackend.loyalty_products[n - 1]);
    let loyalty_product_data = promotionDataFromBackend.loyalty_products[n - 1];
    // loyalty products object location wise validation.
    const loyalty_products_barcode_fields = [0, 1];
    const loyalty_products_numeric_fields = [3, 4];
    const loyalty_redeem_product_position = 4
    lp_element = document.getElementById(`loyaltyproducterror${n - 1}${m}`);
    if (updated_lp) loyalty_product_data[upload_keys[m + 2]] = val;
    else loyalty_product_data[upload_keys[m]] = val;
    if (val.length === 0) {
        lp_element.innerHTML = "This field is required";
    }
    else if (loyalty_products_numeric_fields.includes(m) && (parseInt(val) || parseFloat(val))) {
        let num = parseFloat(val);
        if (num < 0 && m === loyalty_redeem_product_position) {
            lp_element.innerHTML = "Value is not valid.";
        } else if (num < 0.1 && m != loyalty_redeem_product_position) {
            lp_element.innerHTML = "Value is not valid.";
        } else if (num > 10000) {
            lp_element.innerHTML = "Can't be more than 10000.";
        } else {
            lp_element.innerHTML = ''
        }
    } else if (loyalty_products_barcode_fields.includes(m)) {
        let num = parseFloat(val);
        if (isFloat(num)) {
            lp_element.innerHTML = "Value is not valid.";
        } else if (num < 0) {
            lp_element.innerHTML = "Value is not valid.";
        } else if (m === 1 && val.length > 15 ) {
            lp_element.innerHTML = "Can't be more than 15 digits.";
        } else if (`${val}`.length > 25) {
            lp_element.innerHTML = "Can't be more than 25 digits.";
        } else {
            lp_element.innerHTML = ''
        }
    }
    else if (val.length > 15 && m === 0) {
        lp_element.innerHTML = "You can't enter more than 15 chars"
    } else if (val.length > 25) {
        lp_element.innerHTML = "You can't enter more than 25 chars"
    } else lp_element.innerHTML = ""
}
function appendChargePointForm(clicked) {
    $("#LoyaltyProductContainer").append(` 
    
        <div class="charge_point_details" id="loyalty_prouct_id__${clicked}"
            >

            <div class="charge_point_heading collapsible">
                <div class="chargepoint_heading_container">
                    <span>Product ${clicked}</span>
                    <div class="delete_bar deleted"
                        onclick="removeLoyaltyProductConfirmation('loyalty_prouct_id__${clicked}', ${clicked})"></div>
                </div>
            
            </div>
            <div class="content">
                <div class="charge_point_form">                                                                                                                                                                                              
                    <div class="charge_point_fields">
                    
                        <label    class="labels">Product PLU</label>
                        <input type="number"    class="inputs" placeholder="Enter product PLU" onkeyup="updateUploadedDataLoyaltyProducts(${clicked},${0},this.value);"> 
                        
                        <p class="error_field" id="loyaltyproducterror${clicked - 1}0"></p>
                    </div>                                                                                                                                                                                              
                    <div class="charge_point_fields">
                    
                        <label    class="labels">Product code</label>
                        <input type="number"    class="inputs" placeholder="Enter product code or barcode" onchange="updateUploadedDataLoyaltyProducts(${clicked},${1},this.value);"> 
                        
                        <p class="error_field" id="loyaltyproducterror${clicked - 1}1"></p>
                    </div>                                                                                                                                                                                             
                    <div class="charge_point_fields">
                    
                        <label    class="labels">Product</label>
                        <input type="text"    class="inputs" placeholder="Enter product name" onchange="updateUploadedDataLoyaltyProducts(${clicked},${2},this.value);"> 
                        
                        <p class="error_field" id="loyaltyproducterror${clicked - 1}2"></p>
                    </div>
                                                                                                                                                                                         
                    <div class="charge_point_fields">
                    
                        <label    class="labels">Price</label>
                        <input type="number"    class="inputs" placeholder="Enter product price" onchange="updateUploadedDataLoyaltyProducts(${clicked},${3},this.value);"> 
                        
                        <p class="error_field" id="loyaltyproducterror${clicked - 1}3"></p>
                    </div>                                                                                                                                                              
                    <div class="charge_point_fields">
                    
                        <label    class="labels">Price After Promotion</label>
                        <input type="number"    class="inputs" placeholder="Enter price after promotion" onchange="updateUploadedDataLoyaltyProducts(${clicked},${4},this.value);"> 
                        
                        <p class="error_field" id="loyaltyproducterror${clicked - 1}4"></p>
                    </div>
                    <div class="charge_point_fields">
                    
                        <label    class="labels">Status</label>
                        <div class="station_select-box charge_point_field">
                            <select   class="dropdown_input small_dropdown_input" onchange="updateUploadedDataLoyaltyProducts(${clicked},${5},this.value);">
                                <option value="">Select</option>
                                <option value="Active">Active</option>
                                <option value="Inactive">Inactive</option>
                            </select>
                        </div>
                        <p class="error_field" id="loyaltyproducterror${clicked - 1}5"></p>
                    </div>


                </div>

            </div>
            </div>
    `);
}

function calculateDaysDifference() {
    const currentDate = new Date(); // Get the current date
    let start_date_splits = promotionDataFromBackend.start_date.split('/') 
    let end_date_splits = promotionDataFromBackend.end_date.split('/') 
    const start = new Date(`${start_date_splits[1]}-${start_date_splits[0]}-${start_date_splits[2]}`);
    const end = new Date(`${end_date_splits[1]}-${end_date_splits[0]}-${end_date_splits[2]}`);    
    // Calculate differences in milliseconds
    const startDiff = Math.floor((start - currentDate) / (1000 * 60 * 60 * 24)) + 1;
    const endDiff = Math.floor((end - currentDate) / (1000 * 60 * 60 * 24)) + 1;
    
    return { startDiff, endDiff };
}


function appendOccurrenceForm(clicked) {
    $("#LoyaltyOccurrenceContainer").append(` 
    
        <div class="charge_point_details" id="loyalty_occurrence_id${clicked}"
            >

            <div class="charge_point_heading collapsible">
                <div class="chargepoint_heading_container">
                    <span>Occurrence ${clicked}</span>
                    <div class="delete_bar deleted"
                        onclick="removeLoyaltyOccurrenceConfirmation('loyalty_occurrence_id${clicked}', ${clicked})"></div>
                </div>
            
            </div>
            <div class="content">
                <div class="charge_point_form">  
                                                                                                                                                                                                                 
                    <div class="station_fields">
                        <label    class="labels">Date</label>
                        <div class="date_container1" onclick="showFromDatePicker()" id="startDateContainer">
                            <input disabled type="text" id="start_date_${clicked}" placeholder="Occurrence date"  onchange="updateUploadedDataLoyaltyOccurrences(${clicked},${0},this.value);" class="datepicker1">
                        </div>
                        <p class="error_field" id="loyalty_occurrence_error${clicked - 1}0"></p>
                    </div>                                                                                                                                                                                              
                    <div class="station_fields">
                    
                        <label    class="labels">Start Time</label>
                        <div class="time_box" id="startTimeContainer">
                            <div class="time_select-box"> 
                                <input type="time" placeholder="Start time"  onchange="updateUploadedDataLoyaltyOccurrences(${clicked},${1},this.value);" class="selectt select_time_loyalty">
                            </div>
                        </div>
                        <p class="error_field" id="loyalty_occurrence_error${clicked - 1}1"></p>
                    </div>                                                                                                                                                                                            
                    <div class="station_fields">
                    
                        <label    class="labels">End Time</label>
                        <div class="time_box" id="endTimeContainer">
                            <div class="time_select-box">
                                <input type="time" placeholder="End time"  onchange="updateUploadedDataLoyaltyOccurrences(${clicked},${2},this.value);" class="selectt select_time_loyalty">
                            </div>
                        </div>
                        <p class="error_field" id="loyalty_occurrence_error${clicked - 1}2"></p>
                    </div> 
                </div>

            </div>
            </div>
    `);
    
    let {startDiff, endDiff} = calculateDaysDifference();
    $(`#start_date_${clicked}`).datepicker({
        dateFormat: "dd/mm/yy",
        showOn: "button",
        minDate: startDiff,
        maxDate: endDiff,
        buttonImage:
            "https://mfgevqastorage.blob.core.windows.net/static/images/calendar-1.png",
        buttonImageOnly: true,
        buttonText: "Select date",
    });
}

const loyaltyImageContainerHandler = (image_type) => {
    let image_container = null;
    let assigned_image_to = null;
    switch (image_type) {
        case "loyalty_image":
            image_container = "loyalty_image_container";
            assigned_image_to = "promotion_image";
            break;
        case "loyalty_reward_image":
            image_container = "loyalty_reward_image_container";
            assigned_image_to = "reward_image";
            break;
        case "reward_activated_notificaton_image":
            image_container = "reward_activated_notificaton_image_container";
            assigned_image_to = "reward_activated_notification_image";
            break;
        case "reward_expiration_notificaton_image":
            image_container = "reward_expiration_notificaton_image_container";
            assigned_image_to = "reward_expiration_notification_image";
            break;
        default:
            break;
    }
    return [image_container, assigned_image_to]
}

// image handling
const uploadPromotionsImage = (event, image_type, assign_default_image = false) => {
    let [image_container, assigned_image_to] = loyaltyImageContainerHandler(image_type);
    $(`#${image_container}`).html()
    const reader = new FileReader();
    reader.onload = (event_data) => {
        let url = event_data.target.result;
        if (image_container) {
            $(`#${image_container}`).html(`<div class="img-download">
                <img src=${url} alt="image">
                <b class="promotion_discard_button-style" id="discard_edit" onclick="removeAssignedLoyaltyImages('${image_type}', ${assign_default_image})" class="discard">x</b>
            </div>`);
            promotionDataFromBackend[assigned_image_to] = url;
        }
    }
    reader.readAsDataURL(event.target.files[0]);
}

const removeAssignedLoyaltyImages = (image_type, assign_default_image = false) => {
    let [image_container, assigned_image_to] = loyaltyImageContainerHandler(image_type);
    document.getElementById(`${image_type}`).value = ''
    if (image_container) {
        $(`#${image_container}`).html(
            assign_default_image ? `<div class="img-download">
                <img src=${notification_default_image} alt="image">
            </div>`:
                `<div class="empty_box_text"><p>Click 'Assign' button to add images</p></div>`
        );
        promotionDataFromBackend[assigned_image_to] = '';
    }
}

$(document).on("change", "#loyalty_image", function (event) {
    if (event.target.files.length) uploadPromotionsImage(
        event,
        'loyalty_image'
    )
}
);

$(document).on("change", "#loyalty_reward_image", function (event) {
    if (event.target.files.length) uploadPromotionsImage(
        event,
        'loyalty_reward_image'
    )
}
);
$(document).on("change", "#reward_activated_notificaton_image", function (event) {
    if (event.target.files.length) uploadPromotionsImage(
        event,
        'reward_activated_notificaton_image',
        true
    )
}
);
$(document).on("change", "#reward_expiration_notificaton_image", function (event) {
    if (event.target.files.length) uploadPromotionsImage(
        event,
        'reward_expiration_notificaton_image',
        true
    )
}
);

// image handling end of code

let status_list = ['Active', 'Inactive']
$(document).ready(function () {
    let data_to_render_first = '';
    let occurrences_data_to_render_first = '';

    // fields that need to be toggled
    const loyaltyOccurrencesSection = document.getElementById('loyaltyOccurrencesSection');
    const loyaltyOccuranceSectionRedirector = document.getElementById('loyaltyOccuranceSectionRedirector');
    if (edit_page_check){
        if (promotionDataFromBackend.occurance_status != 'Yes'){
            loyaltyOccurrencesSection.style.display = DISPLAY_NONE_STYLE_TEXT;
            loyaltyOccuranceSectionRedirector.style.display = DISPLAY_NONE_STYLE_TEXT;
        }
        if(promotionDataFromBackend.offer_type === GENERIC_OFFERS){
            const loyaltyProductsSection = document.getElementById('loyaltyProductsSection');
            const loyaltyProductSectionRedirector = document.getElementById('loyaltyProductSectionRedirector');
            const loyaltyTypeField = document.getElementById('loyaltyTypeField');
            const redeemTypeField = document.getElementById('redeemTypeField');
            const cycleDurationField = document.getElementById('cycleDurationField');
            const numberOfIssuanceContainer = document.getElementById('numberOfIssuanceContainer');
            const triggerRedeemAvailableField = document.getElementById('triggerRedeemAvailableField');
            const qrExpiryField = document.getElementById('qrExpiryField');
            const footerMessageField = document.getElementById('footerMessageField');
            const setOccurrencesField = document.getElementById('setOccurrencesField');
            
            loyaltyProductsSection.style.display = DISPLAY_NONE_STYLE_TEXT;
            loyaltyProductSectionRedirector.style.display = DISPLAY_NONE_STYLE_TEXT;
            loyaltyTypeField.style.display=DISPLAY_NONE_STYLE_TEXT;
            redeemTypeField.style.display=DISPLAY_NONE_STYLE_TEXT;
            cycleDurationField.style.display=DISPLAY_NONE_STYLE_TEXT;
            numberOfIssuanceContainer.style.display=DISPLAY_NONE_STYLE_TEXT;
            triggerRedeemAvailableField.style.display=DISPLAY_NONE_STYLE_TEXT;
            qrExpiryField.style.display=DISPLAY_NONE_STYLE_TEXT;
            footerMessageField.style.display=DISPLAY_NONE_STYLE_TEXT;
            setOccurrencesField.style.display=DISPLAY_NONE_STYLE_TEXT;
        }else {
            loyaltyContentToggler(promotionDataFromBackend.loyalty_type);
        }
        loyaltyOccurrencesSectionToggler(promotionDataFromBackend.occurance_status, called_via_input=true);
    }else{
        loyaltyOccurrencesSection.style.display = DISPLAY_NONE_STYLE_TEXT;
        loyaltyOccuranceSectionRedirector.style.display = DISPLAY_NONE_STYLE_TEXT;
    }
    let iterationLength = loyalty_products.length;
    promotionDataFromBackend.loyalty_products = [];
    for (var c = 0; c < iterationLength; c++) {
        lp = loyalty_products[c];
        let object_to_push = {}
        object_to_push = {
            lp_on_updation: true,
            lp_id: lp.id,
            product_plu: lp.product_plu,
            product_bar_code: lp.product_bar_code,
            product: lp.desc,
            price: lp.price ? lp.price : 0,
            redeem_product_promotion_price: lp.redeem_product_promotion_price ? lp.redeem_product_promotion_price : 0,
            status: lp.status,
            deleted: false,
        }
        let loyalty_product_status_html = ''
        for (var i = 0; i < status_list.length; i++) {
            if (status_list[i] === lp.status) {
                loyalty_product_status_html += `<option selected value="${status_list[i]}">${status_list[i]}</option>`
            }
            else {

                loyalty_product_status_html += `<option value="${status_list[i]}">${status_list[i]}</option>`
            }
        }
        data_to_render_first += `
        <div class="charge_point_details" id="loyalty_prouct_id__${c + 1}"
        >

            <div class="charge_point_heading collapsible">
                <div class="chargepoint_heading_container">
                    <span>Product ${c + 1}</span>
                    <div class="delete_bar deleted"
                        onclick="removeLoyaltyProductConfirmation('loyalty_prouct_id__${c + 1}', ${c + 1},${lp.id})"></div>
                </div>
            </div>
            <div class="content">
                <div class="charge_point_form">                                                                                                                                                                                              
                    <div class="charge_point_fields">
                    
                        <label    class="labels">Product PLU</label>
                        <input type="number"   value="${lp.product_plu}" class="inputs" placeholder="Enter product PLU" onkeyup="updateUploadedDataLoyaltyProducts(${c + 1},${0},this.value, ${true});"> 
                        
                        <p class="error_field" id="loyaltyproducterror${c}0"></p>
                    </div>                                                                                                                                                                                              
                    <div class="charge_point_fields">
                    
                        <label    class="labels">Product code</label>
                        <input type="text"  value="${lp.product_bar_code}"  class="inputs" placeholder="Enter product code or barcode" onchange="updateUploadedDataLoyaltyProducts(${c + 1},${1},this.value, ${true});"> 
                        
                        <p class="error_field" id="loyaltyproducterror${c}1"></p>
                    </div>                                                                                                                                                                                            
                    <div class="charge_point_fields">
                    
                        <label    class="labels">Product</label>
                        <input type="text"  value="${lp.desc}"  class="inputs" placeholder="Enter product name" onchange="updateUploadedDataLoyaltyProducts(${c + 1},${2},this.value, ${true});"> 
                        
                        <p class="error_field" id="loyaltyproducterror${c}2"></p>
                    </div>
                                                                                                                                   
                    <div class="charge_point_fields">
                    
                        <label    class="labels">Price</label>
                        <input type="number"   value="${lp.price}" class="inputs" placeholder="Enter product price" onchange="updateUploadedDataLoyaltyProducts(${c + 1},${3},this.value,${true});"> 
                        
                        <p class="error_field" id="loyaltyproducterror${c}3"></p>
                    </div>                                                                                                       
                    <div class="charge_point_fields">
                    
                        <label    class="labels">Price After Promotion</label>
                        <input type="number"   value="${lp.redeem_product_promotion_price}" class="inputs" placeholder="Enter price after promotion" onchange="updateUploadedDataLoyaltyProducts(${c + 1},${4},this.value,${true});"> 
                        
                        <p class="error_field" id="loyaltyproducterror${c}4"></p>
                    </div>
                    <div class="charge_point_fields">
                    
                        <label    class="labels">Status</label>
                        <div class="station_select-box charge_point_field">
                            <select   class="dropdown_input small_dropdown_input" onchange="updateUploadedDataLoyaltyProducts(${c + 1},${5},this.value, ${true});">
                                <option value="">Select</option>
                                ${loyalty_product_status_html}
                            </select>
                        </div>
                        <p class="error_field" id="loyaltyproducterror${c}5"></p>
                    </div>
                                                                         
                </div>

                </div>

            </div>


            </div>
        
        `
        promotionDataFromBackend.loyalty_products.push(object_to_push);
    }
    $("#LoyaltyProductContainer").append(data_to_render_first)

    let countClicked1 = loyalty_products.length
    if (!edit_page_check) {

        const loyaltyProductDataDummy = {
            product_plu: '',
            product_bar_code: '',
            product: '',
            price: 0,
            redeem_product_promotion_price: 0,
            status: '',
            lp_id: null,
            deleted: false,
        }
        countClicked1 = countClicked1 + 1;
        promotionDataFromBackend.loyalty_products.push(loyaltyProductDataDummy)
        appendChargePointForm(countClicked1)
    }

    $("#addChargePointButton").click(function () {
        var loyaltyProductDataToUpload = {
            product_plu: '',
            product_bar_code: '',
            product: '',
            price: 0,
            redeem_product_promotion_price: 0,
            status: '',
            lp_id: null,
            deleted: false,
        }
        countClicked1 = countClicked1 + 1;
        appendChargePointForm(countClicked1)
        promotionDataFromBackend.loyalty_products.push(loyaltyProductDataToUpload)
    });
    let iterationLengthForOccurences = occurrences.length;
    promotionDataFromBackend.occurrences = [];
    for (let o = 0; o < iterationLengthForOccurences; o++) {
        occ = occurrences[o];
        let occurrence_object_to_push = {}
        occurrence_object_to_push = {
            occurrence_on_updation: true,
            occurrence_id: occ.id,
            date: occ.date,
            start_time: occ.start_time,
            end_time: occ.end_time,
            deleted: false,
        }
        occurrences_data_to_render_first += `
        <div class="charge_point_details" id="loyalty_occurrence_id${o + 1}"
        >

            <div class="charge_point_heading collapsible">
                <div class="chargepoint_heading_container">
                    <span>Occurrence ${o + 1}</span>
                    <div class="delete_bar deleted"
                        onclick="removeLoyaltyOccurrenceConfirmation('loyalty_occurrence_id${o + 1}', ${o + 1},${occ.id})"></div>
                </div>
            </div>
            <div class="content">
                <div class="charge_point_form">                                                                                                                                                                                              
                    <div class="station_fields">
                        <label    class="labels">Date</label>
                        <div class="date_container1" onclick="showFromDatePicker()" id="startDateContainer">
                            <input disabled type="text" id="start_date_${o+1}" value="${occ.date}" placeholder="Occurrence date"  onchange="updateUploadedDataLoyaltyOccurrences(${o + 1},${0},this.value, ${true});" class="datepicker1" >
                        </div>
                        <p class="error_field" id="loyalty_occurrence_error${o}0"></p>
                    </div>                                                                                                                                                                                              
                    <div class="station_fields">
                    
                        <label    class="labels">Start Time</label>
                        <div class="time_box" id="startTimeContainer">
                            <div class="time_select-box"> 
                                <input type="time" value="${occ.start_time}" placeholder="Start time"  onchange="updateUploadedDataLoyaltyOccurrences(${o + 1},${1},this.value, ${true});" class="selectt select_time_loyalty">
                            </div>
                        </div>
                        <p class="error_field" id="loyalty_occurrence_error${o}1"></p>
                    </div>                                                                                                                                                                                            
                    <div class="station_fields">
                    
                        <label    class="labels">End Time</label>
                        <div class="time_box" id="endTimeContainer">
                            <div class="time_select-box">
                                <input type="time" value="${occ.end_time}" placeholder="End time"  onchange="updateUploadedDataLoyaltyOccurrences(${o + 1},${2},this.value, ${true});" class="selectt select_time_loyalty">
                            </div>
                        </div>
                        <p class="error_field" id="loyalty_occurrence_error${o}2"></p>
                    </div>                                            
                </div>

                </div>

            </div>


            </div>
        
        `;
        promotionDataFromBackend.occurrences.push(occurrence_object_to_push);
    }
    $("#LoyaltyOccurrenceContainer").append(occurrences_data_to_render_first);
    
    let {startDiff, endDiff} = calculateDaysDifference();
    for (let o = 0; o < iterationLengthForOccurences; o++) {
        $(`#start_date_${o+1}`).datepicker({
            dateFormat: "dd/mm/yy",
            showOn: "button",
            minDate: startDiff,
            maxDate: endDiff,
            buttonImage:
                "https://mfgevqastorage.blob.core.windows.net/static/images/calendar-1.png",
            buttonImageOnly: true,
            buttonText: "Select date",
        });
    }
    let countClickedForOccurrence = occurrences.length;    
    $("#addOccurrencesButton").click(function () {
        var loyaltyOccurrenceDataToUpload = {
            date: '',
            start_time: '',
            end_time: '',
            occurrence_id: null,
            deleted: false,
        };
        countClickedForOccurrence = countClickedForOccurrence + 1;
        appendOccurrenceForm(countClickedForOccurrence);
        promotionDataFromBackend.occurrences.push(loyaltyOccurrenceDataToUpload);
    });

}
);


function removeLoyaltyProductConfirmation(id, number) {

    document.getElementById('loyalty_product_delete_modal_content').innerHTML = `
        <div class="heading">
            <h5>Remove Loyalty Product</h5>
            <button type="button" class="btn-close" onclick="assign_map_values(true);" data-bs-dismiss="modal" aria-label="Close"></button>

        </div>
        <div class="modal-body delete_chargepoint_confirmation_modal_body_styl" >
            <h6 > Are you sure you want to remove loyalty product ${number}</h6>
            <div class="google_maps_submit_buttons">
                <div class="google_maps_container_buttons">
                    <button class="cancle_button" data-bs-dismiss="modal">No</button>
                    <button onclick="removeLoyaltyProduct(${id},${number});"  class="done_button" >Yes</button>
                </div>
            </div>
        </div>
    `
    $('#delete_loyalty_product_confirmation_model').modal('show');
}
function removeLoyaltyProduct(id, number) {
    id.style.display = 'none';
    $('#delete_loyalty_product_confirmation_model').modal('hide');
    document.getElementById('loyalty_product_delete_modal_content').innerHTML = '';
    deleted_loyalty_produucts_from_frontend.push(number - 1);
}

function removeLoyaltyOccurrenceConfirmation(id, number) {
    
    document.getElementById('loyalty_occurrence_delete_modal_content').innerHTML = `
        <div class="heading">
            <h5>Remove Loyalty Occurrence</h5>
            <button type="button" class="btn-close" onclick="assign_map_values(true);" data-bs-dismiss="modal" aria-label="Close"></button>

        </div>
        <div class="modal-body delete_chargepoint_confirmation_modal_body_styl" >
            <h6 > Are you sure you want to remove loyalty occurrence ${number}</h6>
            <div class="google_maps_submit_buttons">
                <div class="google_maps_container_buttons">
                    <button class="cancle_button" data-bs-dismiss="modal">No</button>
                    <button onclick="removeLoyaltyOccurrence(${id},${number});"  class="done_button" >Yes</button>
                </div>
            </div>
        </div>
    `
    $('#delete_loyalty_occurrence_confirmation_model').modal('show');
}
function removeLoyaltyOccurrence(id, number) {
    id.style.display = 'none';
    $('#delete_loyalty_occurrence_confirmation_model').modal('hide');
    document.getElementById('loyalty_occurrence_delete_modal_content').innerHTML = '';
    deleted_loyalty_occurrences_from_frontend.push(number - 1);
}


function convertToSeconds(timeValue) {
    if (timeValue) {
        let [hours, minutes] = timeValue.split(":").map(Number);
        return  hours * 3600 + minutes * 60;
    } 
    return 0;
}


function showVisibilityCheckbox(id) {
    var checkboxes = document.getElementById(id);
    if (checkboxes.style.display === "block") {
        checkboxes.style.display = "none";
    } else {
        checkboxes.style.display = "block";
    }
}

let loyaltyVisibility = new Set();

function updateLoyaltyVisibility() {
    loyaltyVisibility.clear();
    document.querySelectorAll('.loyalty-visibility-input').forEach(cb => {
        if (cb.checked) loyaltyVisibility.add(cb.value);
    });
    const text = document.getElementById('loyaltyVisibilityText');
    if (loyaltyVisibility.size === 2) text.innerText = "All Users";
    else if (loyaltyVisibility.size === 1) text.innerText = Array.from(loyaltyVisibility)[0];
    else text.innerText = "Select";
}

function validateLoyaltyVisibility() {
    const errorBox = document.getElementById('error_field_loyalty_visibility');
    if (loyaltyVisibility.size === 0) {
        errorBox.innerHTML = "This field is required";
        return false;
    } else {
        errorBox.innerHTML = "";
        return true;
    }
}

const toMinutes = (time) => {
    let [hours, minutes] = time.split(':').map(Number);
    return hours * 60 + minutes;
};

function submitPromotionData() {
    $('#loader_for_mfg_ev_app').show();
    promotionDataFromBackend.images = uploaded_images
    let error_less = true;
    const upload__keys = Object.keys(promotionDataFromBackend);
    const nonMandatoryField = [42]
    const big_field_array = [19, 20, 24, 25];
    const large_field_array = [13]
    const larger_field_array = [14]
    const barcode_fields = [15, 17];
    const decimal_fields = (
        [COSTA_COFFE_TEXT,FREE_LOYALTY_TEXT].includes(promotionDataFromBackend["loyalty_type"])
    ) ? [8, 11, 18, 21, 26, 27] : [8, 11, 18];
    const numeric_fields = (
        [COSTA_COFFE_TEXT,FREE_LOYALTY_TEXT].includes(promotionDataFromBackend["loyalty_type"])
    ) ? [8, 9, 10, 11, 18, 21, 26, 27] : [8, 10, 11, 18];
    const redeem_expiry = document.getElementById('redeem_expiry').value
    let ignore_fields_validation = [];
    if (promotionDataFromBackend["offer_type"] === GENERIC_OFFERS){
        ignore_fields_validation = [4, 5, 8, 9, 10, 11, 42, 44, 45];
        promotionDataFromBackend["cycle_duration"] = 0;
        promotionDataFromBackend["redeem_type"] = '';
        promotionDataFromBackend["loyalty_type"] = '';
        promotionDataFromBackend["number_of_total_issuances"] = 0;
        promotionDataFromBackend["number_of_paid_purchases"] = 0;
        promotionDataFromBackend["qr_refresh_time"] = 0;
        promotionDataFromBackend["loyalty_list_footer_message"] = '';
    }
    else if (promotionDataFromBackend["loyalty_type"] === FREE_LOYALTY_TEXT) {
        ignore_fields_validation = [8, 10, 44];
        promotionDataFromBackend["cycle_duration"] = 0;
        promotionDataFromBackend["number_of_paid_purchases"] = 0;
    }
    upload__keys.forEach((element, index) => {
        if (!ignore_fields_validation.includes(index)) {
            if (numeric_fields.includes(index)) {
                element_box = document.getElementById(`error_field${index}`);
                let num = parseFloat(promotionDataFromBackend[element]);
                if (num < 0.1) {
                    element_box.innerHTML = "Value is not valid.";
                    if (error_less) error_less = false;
                } else if (decimal_fields.includes(index) && isFloat(parseFloat(num))
                ) {
                    element.innerHTML = "Value is not valid."
                    if (error_less) error_less = false;
                } else if (num >= 1000 && index === 10) {
                    element_box.innerHTML = "Should be less than 1000.";
                    if (error_less) error_less = false;
                } else if (num > 10000 && index!==9) {
                    element_box.innerHTML = "Can't be more than 10000.";
                    if (error_less) error_less = false;
                } else if (num > 100000 && index===9) {
                    element_box.innerHTML = "Can't be more than 100000.";
                    if (error_less) error_less = false;
                }
                else if (num < Number(numberOfIssuedVouchers) && index === 9) {
                    element_box.innerHTML = `${numberOfIssuedVouchers} rewards are already issued.`;
                    if (error_less) error_less = false;
                }
                else if (index === 27 && promotionDataFromBackend[element] > redeem_expiry && [COSTA_COFFE_TEXT,FREE_LOYALTY_TEXT].includes( promotionDataFromBackend["loyalty_type"])) {
                    element.innerHTML = "Value should be less than redeem expiry."
                    if (error_less) error_less = false;
                }
                else {
                    element_box.innerHTML = '';
                }
            } else if (barcode_fields.includes(index)) {
                element_box = document.getElementById(`error_field${index}`);
                let num = parseFloat(promotionDataFromBackend[element]);
                if (isFloat(num) || num < 0) {
                    element_box.innerHTML = "Value is not valid.";
                    if (error_less) error_less = false;
                } else if (`${promotionDataFromBackend[element]}`.length > 25) {
                    element_box.innerHTML = "Can't be more than 25 digits.";
                    if (error_less) error_less = false;
                } else if (isNaN(num)) {
                    element_box.innerHTML = "This field is required";
                    if (error_less) error_less = false;
                } else {
                    element_box.innerHTML = '';
                }
            } else {
                if (typeof (promotionDataFromBackend[element]) === "string") {
                    element_box = document.getElementById(`error_field${index}`);
                    let loyalty_type_helper = [COSTA_COFFE_TEXT,FREE_LOYALTY_TEXT].includes(promotionDataFromBackend["loyalty_type"])
                    if (nonMandatoryField.includes(index) && promotionDataFromBackend[element].length > 100) {
                        element_box.innerHTML = "You can't enter more than 100 chars";
                        if (error_less) error_less = false;
                    }
                    else if ((
                        (
                            loyalty_type_helper &&
                            index < 31
                        ) || (
                            !loyalty_type_helper &&
                            index !== 9 &&
                            index < 19
                        )
                    ) && promotionDataFromBackend[element].length === 0
                    ) {
                        element_box.innerHTML = "This field is required";
                        if (error_less) error_less = false;
                    }
                    else if ((
                        (
                            loyalty_type_helper &&
                            index < 31
                        ) || (
                            !loyalty_type_helper &&
                            index !== 9 &&
                            index < 19
                        )
                    ) && big_field_array.includes(index) && promotionDataFromBackend[element].length > 300
                    ) {
                        element_box.innerHTML = "You can't enter more than 100 chars";
                        if (error_less) error_less = false;
                    }
                    else if ((
                        (
                            loyalty_type_helper &&
                            index < 31
                        ) || (
                            !loyalty_type_helper &&
                            index !== 9 &&
                            index < 19
                        )
                    ) && large_field_array.includes(index) && promotionDataFromBackend[element].length >= 1000
                    ) {
                        element_box.innerHTML = "You can't enter more than 1000 chars";
                        if (error_less) error_less = false;
                    }
                    else if ((
                        (
                            loyalty_type_helper &&
                            index < 31
                        ) || (
                            !loyalty_type_helper &&
                            index !== 9 &&
                            index < 19
                        )
                    ) && larger_field_array.includes(index) && promotionDataFromBackend[element].length >= 4000
                    ) {
                        element_box.innerHTML = "You can't enter more than 4000 chars";
                        if (error_less) error_less = false;
                    }
                    else if ((
                        (
                            loyalty_type_helper &&
                            index < 31
                        ) || (
                            !loyalty_type_helper &&
                            index !== 9 &&
                            index < 19
                        )
                    ) && !big_field_array.includes(index) && !large_field_array.includes(index) && !nonMandatoryField.includes(index) && promotionDataFromBackend[element].length > 50 && !larger_field_array.includes(index)
                    ) {
                        element_box.innerHTML = "You can't enter more than 50 chars";
                        if (error_less) error_less = false;
                    }
                    else if (
                        (
                            loyalty_type_helper &&
                            index < 31
                        ) || (
                            !loyalty_type_helper &&
                            index !== 9 &&
                            index < 19
                        )
                    ) element_box.innerHTML = ""
                }
            }
            if (element === 'trigger_sites' && document.getElementById('loyalty_type_dropdown').value === COSTA_COFFE_TEXT && ['Count', 'kWh'].includes(document.getElementById('redeem_type_dropdown').value)) {
                console.log(`trigger Sites: ${trigger_sites} size: ${trigger_sites.size}`);
                
                var station_fields = document.getElementsByClassName(`trigger_sites_error_field`)
                if (trigger_sites.size === 0) {
                    for (i = 0; i < station_fields.length; i++) {
                        station_fields[i].innerHTML = "This field is required"
                    }
                    if (error_less) error_less = false;
                    
                } else {
                    for (i = 0; i < station_fields.length; i++) {
                        station_fields[i].innerHTML = ""
                    }
                }
            }
            if (element === 'station_ids') {
                // console.log(`Stations: ${stationIds} size: ${stationIds.size}`);
                var station_fields = document.getElementsByClassName(`station_error_field`)
                if (stationIds.size === 0) {
                    for (i = 0; i < station_fields.length; i++) {
                        station_fields[i].innerHTML = "This field is required"
                    }
                    if (error_less) error_less = false;

                } else {
                    for (i = 0; i < station_fields.length; i++) {
                        station_fields[i].innerHTML = ""
                    }
                }
            }
            if (element === 'operation_regions') {
                var ops_region_fields = document.getElementById(`station_error_field_ops_region`)
                if (operationRegions.size === 0) {
                    ops_region_fields.innerHTML = "This field is required"
                    if (error_less) error_less = false;

                } else {
                    ops_region_fields.innerHTML = ""
                }
            }
            if (element === 'regions') {
                var region_fields = document.getElementById(`station_error_field_region`)
                if (regions.size === 0) {
                    region_fields.innerHTML = "This field is required"
                    if (error_less) error_less = false;

                } else {
                    region_fields.innerHTML = ""
                }
            }
            if (element === 'area') {
                var area_fields = document.getElementById(`station_error_field_areas`)
                if (areas.size === 0) {
                    area_fields.innerHTML = "This field is required"
                    if (error_less) error_less = false;

                } else {
                    area_fields.innerHTML = ""
                }
            }
            if (element === 'start_date' || element === 'end_date') {
                var start_date_error_box = document.getElementById(`error_field6`);
                var end_date_error_box = document.getElementById(`error_field7`);
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
                    }
                    else {
                        start_date_error_box.innerHTML = "Start date must be less than end date";
                        end_date_error_box.innerHTML = "End date must be greater than start date"
                    }
                    // }
                }
            }
            if (
                promotionDataFromBackend["offer_type"] !== GENERIC_OFFERS &&
                typeof (promotionDataFromBackend[element]) === "object" &&
                element === "loyalty_products"
            ) {
                const loyalty_products_barcode_fields = [0, 1]
                const loyalty_products_numeric_fields = [3, 4]
                const loyalty_redeem_product_position = 4
                const update_loyalty_products_barcode_fields = [2, 3]
                const update_loyalty_products_numeric_fields = [5, 6]
                const update_loyalty_redeem_product_position = 6
                promotionDataFromBackend.loyalty_products.forEach((elm, i) => {
                    if (!deleted_loyalty_produucts_from_frontend.includes(i)) {
                        const loyaltyProduct__keys = Object.keys(elm);
                        let cp = promotionDataFromBackend.loyalty_products[i]
                        loyaltyProduct__keys.forEach((elm1, j) => {
                            if (elm1 !== 'deleted') {
                                if (cp[elm1] !== null) {
                                    if (loyaltyProduct__keys.includes("lp_on_updation")) {

                                        if (j > 1) {
                                            if (cp[elm1].length === 0) {
                                                document.getElementById(`loyaltyproducterror${i}${j - 2}`).innerHTML = "This field is required";
                                                if (error_less) error_less = false;
                                            } else if (update_loyalty_products_numeric_fields.includes(j)) {
                                                let num = parseFloat(cp[elm1]);
                                                if ((num < 0 || isNaN(num)) && j === update_loyalty_redeem_product_position) {
                                                    document.getElementById(`loyaltyproducterror${i}${j - 2}`).innerHTML = "Value is not valid.";
                                                    if (error_less) error_less = false;
                                                } else if (num < 0.1 && j != update_loyalty_redeem_product_position) {
                                                    document.getElementById(`loyaltyproducterror${i}${j - 2}`).innerHTML = "Value is not valid.";
                                                    if (error_less) error_less = false;
                                                } else if (num > 10000) {
                                                    document.getElementById(`loyaltyproducterror${i}${j - 2}`).innerHTML = "Can't be more than 10000.";
                                                    if (error_less) error_less = false;
                                                } else {
                                                    document.getElementById(`loyaltyproducterror${i}${j - 2}`).innerHTML = '';
                                                }

                                            } else if (update_loyalty_products_barcode_fields.includes(j)) {
                                                let num = parseFloat(cp[elm1]);
                                                if (isFloat(num) || num < 0) {
                                                    document.getElementById(`loyaltyproducterror${i}${j - 2}`).innerHTML = "Value is not valid.";
                                                    if (error_less) error_less = false;
                                                } else if (`${cp[elm1]}`.length > 15 && j === 3) {
                                                    document.getElementById(`loyaltyproducterror${i}${j - 2}`).innerHTML = "Can't be more than 15 digits.";
                                                    if (error_less) error_less = false;
                                                } else if (`${cp[elm1]}`.length > 25) {
                                                    document.getElementById(`loyaltyproducterror${i}${j - 2}`).innerHTML = "Can't be more than 25 digits.";
                                                    if (error_less) error_less = false;
                                                } else {
                                                    document.getElementById(`loyaltyproducterror${i}${j - 2}`).innerHTML = ''
                                                }
                                            }
                                            else document.getElementById(`loyaltyproducterror${i}${j - 2}`).innerHTML = ""
                                        }
                                    }
                                    else {
                                        if (loyalty_products_numeric_fields.includes(j)) {
                                            let num = parseFloat(cp[elm1]);
                                            if ((num < 0 || isNaN(num)) && j === loyalty_redeem_product_position) {
                                                document.getElementById(`loyaltyproducterror${i}${j}`).innerHTML = "Value is not valid.";
                                                if (error_less) error_less = false;
                                            } else if (num < 0.1 && j != loyalty_redeem_product_position) {
                                                document.getElementById(`loyaltyproducterror${i}${j}`).innerHTML = "Value is not valid.";
                                                if (error_less) error_less = false;
                                            } else if (num > 10000) {
                                                document.getElementById(`loyaltyproducterror${i}${j}`).innerHTML = "Can't be more than 10000.";
                                                if (error_less) error_less = false;
                                            } else {
                                                document.getElementById(`loyaltyproducterror${i}${j}`).innerHTML = '';
                                            }
                                        } else if (loyalty_products_barcode_fields.includes(j)) {
                                            let num = parseFloat(cp[elm1]);
                                            if (!num || isFloat(num) || num < 0) {
                                                document.getElementById(`loyaltyproducterror${i}${j}`).innerHTML = "Value is not valid.";
                                                if (error_less) error_less = false;
                                            } else if (`${cp[elm1]}`.length > 15 && j===1) {
                                                document.getElementById(`loyaltyproducterror${i}${j}`).innerHTML = "Can't be more than 15 digits.";
                                                if (error_less) error_less = false;
                                            } else if (`${cp[elm1]}`.length > 25) {
                                                document.getElementById(`loyaltyproducterror${i}${j}`).innerHTML = "Can't be more than 25 digits.";
                                                if (error_less) error_less = false;
                                            } else {
                                                document.getElementById(`loyaltyproducterror${i}${j}`).innerHTML = ''
                                            }
                                        }
                                        else if (cp[elm1].length === 0) {
                                            document.getElementById(`loyaltyproducterror${i}${j}`).innerHTML = "This field is required";
                                            if (error_less) error_less = false;
                                        } else document.getElementById(`loyaltyproducterror${i}${j}`).innerHTML = ""
                                    }
                                }
                            }
                        })
                    }
                    else {
                        promotionDataFromBackend.loyalty_products[i]['deleted'] = true
                    }
                });
            }

            if (
                promotionDataFromBackend["offer_type"] !== GENERIC_OFFERS &&
                promotionDataFromBackend["occurance_status"] === 'Yes' &&
                typeof (promotionDataFromBackend[element]) === "object" &&
                element === "occurrences"
            ) {
                promotionDataFromBackend.occurrences.forEach((elm, oi) => {
                    if (!deleted_loyalty_occurrences_from_frontend.includes(oi)) {
                        const loyaltyProduct__keys = Object.keys(elm);
                        let occ = promotionDataFromBackend.occurrences[oi];
                        let startMinutes = toMinutes(occ['start_time']);
                        let endMinutes = toMinutes(occ['end_time']);
                        loyaltyProduct__keys.forEach((elm1, oj) => {
                            if (elm1 !== 'deleted' && elm1 !== 'occurrence_id' && elm1 !== 'occurrence_on_updation') {
                                if (occ[elm1] !== null) {
                                    let lp_element;
                                    // Ensure start time is smaller than end time
                                    if (loyaltyProduct__keys.includes("occurrence_on_updation")) lp_element = document.getElementById(`loyalty_occurrence_error${oi}${oj - 2}`);
                                    else lp_element = document.getElementById(`loyalty_occurrence_error${oi}${oj}`);
                                    if (occ[elm1].length === 0) {
                                        lp_element.innerHTML = "This field is required";
                                        if (error_less) error_less = false;
                                    }else lp_element.innerHTML = "";
                                    if (promotionDataFromBackend.occurrences.map((occurrence, index)=> !deleted_loyalty_occurrences_from_frontend.includes(index) && oi != index && occurrence.date === occ[elm1]).includes(true)  && elm1 === 'date') {
                                        lp_element.innerHTML = "Duplicate date occurrences found";
                                        if (error_less) error_less = false;
                                    }
                                    if (startMinutes > endMinutes && elm1 === 'start_time') {
                                        lp_element.innerHTML = "Start time must be earlier than end time";
                                        if (error_less) error_less = false;
                                    }
                                    if (startMinutes > endMinutes && elm1 === 'end_time') {
                                        lp_element.innerHTML = "End time must be greater than start time";
                                        if (error_less) error_less = false;
                                    }
                                }
                            }
                        });

                    }
                    else {
                        promotionDataFromBackend.occurrences[oi]['deleted'] = true
                    }
                });
            }
        }
    });
    const isCostaCount =
        promotionDataFromBackend['loyalty_type'] === COSTA_COFFE_TEXT &&
        promotionDataFromBackend['redeem_type'] === 'Count';

        triggerCostaCountKwh = document.getElementById('trigger_kwh_count_input').value;
        // console.log(`[DEBUG] Trigger Costa Count Kwh: ${triggerCostaCountKwh}`);
        const errorField = document.getElementById('error_field48');
    
    if (isCostaCount) {
        // console.log(`[DEBUG] Costa Count Trigger Kwh: ${triggerCostaCountKwh}`);
        
        if (triggerCostaCountKwh === null || triggerCostaCountKwh === '') {
            errorField.innerHTML = 'This field is required';
            error_less = false;
        } else if (triggerCostaCountKwh < 0) {
            errorField.innerHTML = 'Value should be 0 or greater than 0';
            error_less = false;
        } else if (triggerCostaCountKwh > 10000) {
            errorField.innerHTML = "Can't be more than 10000.";
            error_less = false;
        } else {
            errorField.innerHTML = '';
            promotionDataFromBackend.transaction_count_for_costa_kwh_consumption=triggerCostaCountKwh;
        }
    } else {
        errorField.innerHTML = '';
    }

    if (!validateLoyaltyVisibility()) {
        const loyalty_visibility_error = document.getElementById('error_field_loyalty_visibility');
        loyalty_visibility_error = "This field is required"
        error_less = false;
    }

    const offerType = document.getElementById('offer_type_dropdown') ? document.getElementById('offer_type_dropdown').value : promotionDataFromBackend.offer_type;
    if (offerType === LOYALTY_OFFERS) {
        const carWashValue = document.getElementById('car_wash_dropdown').value;
        const carWashError = document.getElementById('error_field50');
        if (!carWashValue) {
            carWashError.innerHTML = "This field is required";
            error_less = false;
        } else {
            carWashError.innerHTML = "";
            promotionDataFromBackend.is_car_wash = (carWashValue === "true");
        }
    } else {
        promotionDataFromBackend.is_car_wash = false;
    }

    
    if (loyaltyVisibility.size === 2) {
        promotionDataFromBackend.loyalty_visibility = "All Users";
    } else if (loyaltyVisibility.size === 1) {
        promotionDataFromBackend.loyalty_visibility = Array.from(loyaltyVisibility)[0];
    } else {
        promotionDataFromBackend.loyalty_visibility = "";
    }

    var url_for_ajax = window.location.href
    if (error_less) {
        // console.log('promotionDataFromBackend ::', promotionDataFromBackend);
        promotionDataFromBackend.stations = Array.from(
            stationIds
        );
        promotionDataFromBackend.shop = [
            ...Array.from(
                shops
            ),
            ...Array.from(
                amenities
            )
        ];
        promotionDataFromBackend.trigger_sites = Array.from(trigger_sites);
        promotionDataFromBackend.transaction_count_for_costa_kwh_consumption=triggerCostaCountKwh;
        
        // uploaded_images_copy = uploaded_images_copy.filter( function( el ) {
        //     return uploaded_images.indexOf( el ) < 0;
        // });

        // if(url_for_ajax.includes("edit-promotions")){
        //     promotionDataFromBackend.removeImages = uploaded_images_copy;
        // }else{
        //     promotionDataFromBackend.removeImages = [];
        // }
        // promotionDataFromBackend.images = final_upload_images;
        $.ajax({
            url: url_for_ajax,
            data: { 'getdata': JSON.stringify(promotionDataFromBackend) },
            headers: { "X-CSRFToken": token },
            dataType: 'json',
            type: 'POST',

            success: function (res, status) {
                if (res.status === 1) window.location.href = window.origin + res.url + query_params_str_edit_promotion
                else customAlert(res.message);
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

