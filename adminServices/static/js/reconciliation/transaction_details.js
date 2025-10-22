
function displayCommentBox(check) {
    if (check) {
        var comment = document.getElementById('comment_text_box').value
        document.getElementById('comment_text').innerHTML = comment
        var id = transaction.id;

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
    document.getElementById('comment_action_box').classList.toggle('hide')
    document.getElementById('comment_text').classList.toggle('hide')
    document.getElementById('comment_text_box').classList.toggle('hide')
    document.getElementById('transaction_edit_button').classList.toggle('hide_element')
}