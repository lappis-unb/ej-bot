import logging
from rasa.core.channels import TelegramInput, RocketChatInput
from typing import Text
from sanic import Blueprint, response
from sanic.request import Request
from sanic.response import HTTPResponse
from typing import Text, Any, Callable, Awaitable
from telebot.types import Update, Message

from rasa.core.channels.channel import UserMessage
from rasa.shared.constants import INTENT_MESSAGE_PREFIX
from rasa.shared.core.constants import USER_INTENT_RESTART

import re

logger = logging.getLogger(__name__)
from typing import Text
from rasa.core.channels import RocketChatInput

AVAILABLE_COMMANDS = [
    "help",
    "start",
]


class RocketChatInputChannel(RocketChatInput):
    @classmethod
    def name(cls) -> Text:
        return "rocketchat"

    def get_metadata(self, request):
        metadata = request.json
        return metadata


class TelegramInputChannel(TelegramInput):
    @classmethod
    def name(cls) -> Text:
        return "telegram"

    @staticmethod
    def _is_location(message: Message) -> bool:
        return message.location is not None

    @staticmethod
    def _is_user_message(message: Message) -> bool:
        return message.text is not None

    @staticmethod
    def _is_button(message: Update) -> bool:
        return message.callback_query is not None

    @staticmethod
    def _is_edited_message(message: Update) -> bool:
        return message.edited_message is not None

    @staticmethod
    def _is_command_valid(text) -> bool:
        command_is_valid = False
        for command in AVAILABLE_COMMANDS:
            regex = f".*{command}.*"
            if re.search(regex, text):
                command_is_valid = True
        return command_is_valid

    def blueprint(
        self, on_new_message: Callable[[UserMessage], Awaitable[Any]]
    ) -> Blueprint:
        telegram_webhook = Blueprint("telegram_webhook", __name__)
        out_channel = self.get_output_channel()

        @telegram_webhook.route("/", methods=["GET"])
        async def health(_: Request) -> HTTPResponse:
            return response.json({"status": "ok"})

        @telegram_webhook.route("/set_webhook", methods=["GET", "POST"])
        async def set_webhook(_: Request) -> HTTPResponse:
            s = out_channel.setWebhook(self.webhook_url)
            if s:
                logger.info("Webhook Setup Successful")
                return response.text("Webhook setup successful")
            else:
                logger.warning("Webhook Setup Failed")
                return response.text("Invalid webhook")

        @telegram_webhook.route("/webhook", methods=["GET", "POST"])
        async def message(request: Request) -> Any:
            if request.method == "POST":

                request_dict = request.json
                update = Update.de_json(request_dict)
                if not out_channel.get_me().username == self.verify:
                    logger.debug("Invalid access token, check it matches Telegram")
                    return response.text("failed")

                if self._is_button(update):
                    msg = update.callback_query.message
                    text = update.callback_query.data
                elif self._is_edited_message(update):
                    msg = update.edited_message
                    text = update.edited_message.text
                else:
                    msg = update.message
                    if msg is None:
                        logger.debug("UPDATE MSG IS NONE")
                        return response.text("success")
                    if self._is_user_message(msg):
                        text = msg.text.replace("/bot", "")
                        if msg.text[0] == "/":
                            text = msg.text[1:]
                            if not self._is_command_valid(text):
                                logger.debug("UNAVAILABLE COMMAND")
                                return response.text("success")
                        logger.debug(text)
                    elif self._is_location(msg):
                        text = '{{"lng":{0}, "lat":{1}}}'.format(
                            msg.location.longitude, msg.location.latitude
                        )
                    else:
                        return response.text("success")
                sender_id = msg.chat.id
                metadata = self.get_metadata(request)
                try:
                    if text == (INTENT_MESSAGE_PREFIX + USER_INTENT_RESTART):
                        await on_new_message(
                            UserMessage(
                                text,
                                out_channel,
                                sender_id,
                                input_channel=self.name(),
                                metadata=metadata,
                            )
                        )
                        await on_new_message(
                            UserMessage(
                                "/start",
                                out_channel,
                                sender_id,
                                input_channel=self.name(),
                                metadata=metadata,
                            )
                        )
                    else:
                        await on_new_message(
                            UserMessage(
                                text,
                                out_channel,
                                sender_id,
                                input_channel=self.name(),
                                metadata=metadata,
                            )
                        )
                except Exception as e:
                    logger.error(f"Exception when trying to handle message.{e}")
                    logger.debug(e, exc_info=True)
                    if self.debug_mode:
                        raise
                    pass

                return response.text("success")

        return telegram_webhook
