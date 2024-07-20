from ej.comment import Comment, CommentDialogue


class TestCommentDialogue:
    def test_rasa_comment_buttons(self, tracker, metadata):
        buttons = CommentDialogue.BUTTONS
        assert type(buttons) == list
        assert buttons[0].get("title") == "Concordar"
        assert buttons[1].get("title") == "Discordar"
        assert buttons[2].get("title") == "Pular"

        assert buttons[0].get("payload") == "1"
        assert buttons[1].get("payload") == "-1"
        assert buttons[2].get("payload") == "0"

    def test_rasa_comment_utter(self, tracker, metadata):
        comment = Comment("1", "um comentário", tracker)
        user_voted_comments = 1
        total_comments = 4
        comment_utter = CommentDialogue.get_utter_message(
            metadata, comment.content, user_voted_comments, total_comments
        )
        dialogue_comment_message = (
            f"*{comment.content}* \n O que você acha disso? \n\n"
            f"{user_voted_comments + 1} de {total_comments} comentários."
        )

        assert comment_utter == {
            "text": dialogue_comment_message,
            "buttons": CommentDialogue.BUTTONS,
        }
