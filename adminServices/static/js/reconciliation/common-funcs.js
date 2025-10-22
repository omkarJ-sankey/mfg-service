


function appendCommentsContent(id) {
    var content = `
        
        <input type="text" id="comment_box" class="transaction_comment_box_styl">
            <p class="error_field" id="comment_error"></p>
            <div class="google_maps_submit_buttons">
            
            <div class="google_maps_container_buttons">
                <button class="cancle_button" data-bs-dismiss="modal">Cancel</button>
                &nbsp;
                <button class="done_button" onclick="make_comment(${id});" >Done</button>
            </div>
        </div>
    `
    document.getElementById('delete-modal-content').innerHTML = content
}



function make_comment(id) {

    var comment = document.getElementById('comment_box').value;
    if (comment.length < 1) {
        document.getElementById('comment_error').innerHTML = "Please enter a comment"
    }
    else {
        document.getElementById(`comment_box_${id}`).innerHTML = comment
        $.ajax({
            url: do_comment_url,
            data: { 'getdata': JSON.stringify({ 'transaction_id': id, 'comment': comment }) },
            headers: { "X-CSRFToken": token },
            dataType: 'json',
            type: 'POST',

            success: function (res, status) {
                alert(status);

            },
            error: function (res) {
                alert(res);
            }
        });
        $("#staticBackdrop").modal('hide')
    }

}

