$(document).ready(function () {
  $("#hold_payment_message").hide();
})
const validateAmount = (amount) => {
  if (!amount.length) {
    $('#hold_payment_error').html("This field is required.");
    return false;
  } else if (isNaN(amount)) {
    $('#hold_payment_error').html("Please enter numeric value.");
    return false;
  } else if (Number(amount) <= 0) {
    $('#hold_payment_error').html("Amount should be greater than 0.");
    return false;
  } else if (!/^\d+(\.\d{0,2})?$/.test(amount)) {
    $('#hold_payment_error').html("Maximum two digits allowed after decimal.");
    return false;
  } else {
    $('#hold_payment_error').html("");
    return true;
  }
}
const ApproveHoldPayment = (actionType) => {
  $('#loader_for_mfg_ev_app').show();
  paymentData = {
    "actionType": actionType,
    "editedAmount": "Not available",
  }
  let editedHoldPaymentAmount = $("#edit_hold_payment_input").val();
  let noError = false;
  if (actionType === 'Edit') {
    noError = validateAmount(editedHoldPaymentAmount);
  } else if (actionType === 'Approve') {
    noError = true;
  }
  if (noError) {
    $(".cancle_button").click();
    paymentData.editedAmount = Number(editedHoldPaymentAmount);
    $.ajax({
      url: approve_hold_payment_url,
      data: JSON.stringify(paymentData),
      headers: { "X-CSRFToken": token },
      type: 'POST',
      success: function (res) {
        $('#loader_for_mfg_ev_app').hide()
        $("#hold_payment_message").html(res.message);
        if (res.status === true) {
          $("#edit_hold_payment_input").val("");
          $("#hold_payment_message").addClass("alert-success");
          window.location.href = '/administrator/session-transactions/hold-payments-list/'
        } else {
          $("#hold_payment_message").addClass("alert-danger");
        }
        $("#edit-btn-id").prop("disabled", true);
        $("#approve-btn-id").prop("disabled", true);
        $("#hold_payment_message").show();
        if ("updated_data" in res) {
          $("#hold-payment-amount-to-be-paid").html(res.updated_data.paid_amount)
          $("#payment-status-screening").html(res.updated_data.paid_status)
          if(res.status===true){
            $("#hold-payment-payment-time").html(res.updated_data.payment_time)
          }
        }
      },
      error: function (err) {
        $('#loader_for_mfg_ev_app').hide();
        $("#hold_payment_message").addClass("alert-danger");
        $("#hold_payment_message").html("Failed to proccess session due to unknown error");
      }
    });
  }
  else{
    $('#loader_for_mfg_ev_app').hide()
  }
}