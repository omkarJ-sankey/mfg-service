function showDownloadError() {
  $("#no_download_box").modal("show");
  setTimeout(function () {
    $("#no_download_box").modal("hide");
  }, 3000);
}

const formErrors = {};
const minValue = 0.1;
const maxValue = 100;
let hasErrorsIn3DSConfigurations = false;

const fieldValidations = (fieldValue, fieldId) => {
  if (!fieldValue && fieldValue !== 0) return "are required";
  else if (isNaN(fieldValue)) return "must be a valid number";
  else if (
    fieldId === "total_transactions_within__trigger_value" || fieldId === "kwh_consumed_within__trigger_value"
      ? fieldValue < 0
      : fieldValue < minValue
  ) return (fieldId === "total_transactions_within__trigger_value" || fieldId === "kwh_consumed_within__trigger_value")
      ? "must not be negative"
      : `must be at least ${minValue}`;
  else if (fieldValue > maxValue) return `must not exceed ${maxValue}`;
  return "";
};

const fieldValidationLogic = (field) => {
  let fieldIndetifier = `${field.id.split("__")[0]}`;
  // Clear previous error messages
  let errorContainer = document.getElementById(
    fieldIndetifier + "__conditions_error_box"
  );
  errorContainer.innerHTML = "";
  document
    .querySelectorAll("." + fieldIndetifier + "__inputs")
    .forEach((subField) => {
      let errorMessage = fieldValidations(subField.value, subField.id);
      let fieldDOMObject = document.getElementById(subField.getAttribute("id"));
      fieldDOMObject.style.border = "1px solid #CCCCCC";
      if (field.checked && errorMessage.length > 0) {
        hasErrorsIn3DSConfigurations = true;
        errorContainer.innerHTML += `<li>${subField.getAttribute(
          "fieldName"
        )} ${errorMessage}</li>`;
        fieldDOMObject.style.border = "1px solid red";
      }
    });
};

// Function to validate the form
const validateForm = () => {
  hasErrorsIn3DSConfigurations = false;
  document.querySelectorAll(".three-3ds-checkbox").forEach((field) => {
    if (field.getAttribute('id') != 'trigger_three_ds_for_all_transaction_checkbox') fieldValidationLogic(field);
  });
  document.getElementById("submit3DSConfig").style.background =
    hasErrorsIn3DSConfigurations
      ? "#444444"
      : "#E2373F 0% 0% no-repeat padding-box";
  if (!hasErrorsIn3DSConfigurations)
    $("#confirm3DSConfigurations").modal("show");
};

// Function to validate the form
const validateuser3DSForm = () => {
  const three_ds_user_email = document.getElementById("three_ds_user_email");
  const three_ds_status = document.getElementById("three_ds_status");
  if (three_ds_user_email.checkValidity() && three_ds_status.checkValidity()){
    $("#modal_user_email").html(three_ds_user_email.value);
    $("#confirm3DSConfigurations").modal("show");
  } else {
    three_ds_user_email.reportValidity();
    three_ds_status.reportValidity();
  }
};

const showSubmitFormLoader = () => $("#loader_for_mfg_ev_app").show();

function appendRemove3DSModalContent(id, email) {
  const delete_url =
    document.location.origin +
    `/administrator/three-ds-config/remove-user-specific-3ds-config/${id}/`;
  const content = `
        <p class="delete-modal-text">Are you sure you want to disable 3DS for <strong>${email}</strong>?</p>
        <div class="google_maps_submit_buttons">
            <div class="google_maps_container_buttons">
                <button class="cancle_button" data-bs-dismiss="modal">No</button>
                &nbsp;
                <a href="${delete_url}" onclick="showSubmitFormLoader();"><button class="done_button">Yes</button></a>
            </div>
        </div>
    `;
  document.getElementById("remove-3ds-conf-email-content").innerHTML = content;
}

let from_date_object = {
  dateFormat: "dd/mm/yy",
  showOn: "button",
  buttonImage:
    "https://mfgevqastorage.blob.core.windows.net/static/images/calendar-1.png",
  buttonImageOnly: true,
  buttonText: "Select date",
  beforeShowDay: function (date) {
    var selectedDate = $("#from_date").datepicker("getDate");

    if (selectedDate && date.getTime() === selectedDate.getTime()) {
      return [true, "highlight-selected-date", "Selected Date"];
    } else {
      return [true, "", ""];
    }
  },
};

$(function () {
  $("#from_date").datepicker(from_date_object);
});

$(function () {
  $("#to_date").datepicker({
    dateFormat: "dd/mm/yy",
    showOn: "button",
    buttonImage:
      "https://mfgevqastorage.blob.core.windows.net/static/images/calendar-1.png",
    buttonImageOnly: true,
    buttonText: "Select date",
    minDate: $("#from_date").datepicker("getDate"),
    maxDate: $("#from_date").datepicker("getDate")
      ? new Date(
          $("#from_date")
            .datepicker("getDate")
            .setDate(
              $("#from_date").datepicker("getDate").getDate() +
                dashboard_data_days_limit
            )
        )
      : 0,
    beforeShowDay: function (date) {
      var selectedDate = $("#to_date").datepicker("getDate");

      if (selectedDate && date.getTime() === selectedDate.getTime()) {
        return [true, "highlight-selected-date", "Selected Date"];
      } else {
        return [true, "", ""];
      }
    },
  });
});

function showFromDatePicker() {
  $("#from_date").datepicker("show");
}
function showToDatePicker() {
  $("#to_date").datepicker("show");
}
