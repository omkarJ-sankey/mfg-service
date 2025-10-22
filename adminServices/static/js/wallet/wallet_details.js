function walletAmountWithdrawl(transactionId){
    data={
        "transaction_id": transactionId
    }
    showLoader()
    $.ajax({
        url: "/administrator/wallet/withdraw-wallet-amount/",
        data: JSON.stringify(data),
        headers: { "X-CSRFToken": token },
        type: 'POST',

        success: function (res, status) {
            location.reload();
        },
        error: function (res) {
            hideLoader();
            customAlert(res.responseText);
        }
    });
}