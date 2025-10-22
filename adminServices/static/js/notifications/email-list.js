function orderByFunction(type) {
    $("#loader_for_mfg_ev_app").show();
    let update_order = 'Descending';
    let new_url = '';
    const keys_for_ordering = ['order_by_scheduled_time', 'order_by_delivered_time'];
    const params = new URLSearchParams(url_u);
    params.forEach(function (value, key) {
        if (key !== type) {
            if (!keys_for_ordering.includes(key)) new_url += `&${key}=${value}`;
        }
        else {
            if (value === `Ascending`) update_order = 'Descending'
            else update_order = 'Ascending'
        }
    });
    document.getElementById(type).classList.toggle('order-by');
    window.location.href = `${window_radirect_location}?${type}=${update_order}${new_url}`;
}

function appendDeleteContent(id, subject) {
    const delete_url = document.location.origin + `/administrator/notifications/delete-email-notification/${id}`
    const content = `
        <p class="delete-modal-text">Are you sure you want to delete <strong>${subject}</strong>?</p>
        <div class="google_maps_submit_buttons">
            <div class="google_maps_container_buttons">
                
                <button class="cancle_button" data-bs-dismiss="modal">No</button>
                &nbsp;
                <a href="${delete_url}"><button class="done_button">Yes</button></a>
            </div>
        </div>
    `
    document.getElementById('delete-modal-content').innerHTML = content
}