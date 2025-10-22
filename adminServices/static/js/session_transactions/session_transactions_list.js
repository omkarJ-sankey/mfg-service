

function showLoaderForSessionInput(){
    if (document.getElementById("session_id_input").value.length !== 0){
        $('#loader_for_mfg_ev_app').show()
    }
}
function markAsReviewed(n, id){
    const action_boxes  = document.getElementsByClassName('active_status_box');
    
    action_boxes[n-1].innerHTML = `
        
            <div class="dropdown-menu" aria-labelledby="dropdownMenuButton${id}">
                
            </div> 
            <p>Processing...</p>
    `;
    $.ajax({
            url: change_status_view_url,     
            data: {'getdata': JSON.stringify({'session_id': id})}, 
            headers: { "X-CSRFToken": token },
            dataType: 'json',
            type: 'POST',                                                                                                                                                                                                

            success: function (res, status) {
                $('#action_status_popup').modal('show');
                document.getElementById('updated_status').innerHTML = 'Session mark as reviewed.';
                
                action_boxes[n-1].innerHTML = `
                <div class="dropdown-menu" aria-labelledby="dropdownMenuButton${id}">
                </div>
                <p>Reviewed</p>`;
            },
            error: function (res) {   
                $('#action_status_popup').modal('show');
                document.getElementById('updated_status').innerHTML = 'Something went wrong!!'  ;
                
                action_boxes[n-1].innerHTML = `
                <div class="dropdown-menu" aria-labelledby="dropdownMenuButton${id}">
                </div>
                <p>Failed to review</p>`                                                                                                                
            }

    });
    disableActionModal()
}