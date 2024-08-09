from typing import Any, Dict, List, Text

from actions.checkers.api_error_checker import EJApiErrorManager
from ej.constants import EJCommunicationError
from ej.conversation import Conversation
from ej.user import User
from rasa_sdk import Action, Tracker
from rasa_sdk.events import ActionExecuted, EventType, SessionStarted, SlotSet


class ActionSessionStart(Action):
    def name(self) -> Text:
        return "action_session_start"

    @staticmethod
    def fetch_slots(tracker: Tracker) -> List[EventType]:
        """Collect slots that contain the user's name and phone number."""

        slots = []
        custom_channel_metadata = tracker.events[0]["value"]
        if custom_channel_metadata:
            contact_name = custom_channel_metadata.get("contact_name")
            if contact_name is not None:
                slots.append(SlotSet(key="contact_name", value=contact_name))
        return slots

    async def run(
        self, dispatcher, tracker: Tracker, domain: Dict[Text, Any]
    ) -> List[Dict[Text, Any]]:

        # the session should begin with a `session_started` event
        events = [SessionStarted()]

        # any slots that should be carried over should come after the
        # `session_started` event
        events.extend(self.fetch_slots(tracker))

        # an `action_listen` should be added at the end as a user message follows
        events.append(ActionExecuted("action_listen"))

        return events


class ActionGetConversation(Action):
    """
    Authenticates the chatbot user on EJ API and requests initial conversation data.
    This action is called on the beginner of every new conversation.
    """

    def name(self):
        return "action_get_conversation"

    # TODO: refactors this method using the Checkers architecture.
    # Use ActionAskVote as an example.
    def run(self, dispatcher, tracker, domain):
        self.slots = []
        conversation_id = tracker.get_slot("conversation_id")
        if conversation_id:
            username = User.get_name_from_tracker_state(tracker.current_state())
            user = User(tracker, name=username)

            try:
                conversation_data = Conversation.get_by_id(
                    conversation_id, user.tracker
                )
            except EJCommunicationError:
                ej_api_error_manager = EJApiErrorManager()
                return ej_api_error_manager.get_slots()

            tracker.slots["conversation_title"] = conversation_data.get("text")
            tracker.slots["anonymous_votes_limit"] = conversation_data.get(
                "anonymous_votes_limit"
            )
            tracker.slots["participant_can_add_comments"] = conversation_data.get(
                "participants_can_add_comments"
            )

            user.authenticate()

            conversation = Conversation(tracker)
            self._set_slots(conversation, user)
        else:
            dispatcher.utter_message(template="utter_no_selected_conversation")
            return [FollowupAction("action_session_start")]
        return self.slots

    def _set_slots(self, conversation: Conversation, user: User):
        self.slots = [
            SlotSet("conversation_text", conversation.title),
            SlotSet("conversation_id_cache", conversation.id),
            SlotSet("anonymous_votes_limit", conversation.anonymous_votes_limit),
            SlotSet(
                "participant_can_add_comments",
                conversation.participant_can_add_comments,
            ),
            SlotSet(
                "has_completed_registration",
                user.has_completed_registration,
            ),
            SlotSet("access_token", user.tracker.get_slot("access_token")),
            SlotSet("refresh_token", user.tracker.get_slot("refresh_token")),
        ]
