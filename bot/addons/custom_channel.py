import inspect
import os
from typing import Awaitable, Callable, Text

from actions.logger import custom_logger
from rasa.core.channels.channel import (
    CollectingOutputChannel,
    InputChannel,
    UserMessage,
)
from sanic import Blueprint, response
from sanic.request import Request
from sanic.response import HTTPResponse

from .whatsapp_api_integration.message import NotSupportedMessage
from .whatsapp_api_integration.wpp_event import WhatsAppEvent


class WhatsApp(InputChannel):
    def name(self) -> Text:
        """Name of your custom channel."""
        return "whatsapp"

    def blueprint(
        self, on_new_message: Callable[[UserMessage], Awaitable[None]]
    ) -> Blueprint:
        custom_webhook = Blueprint(
            "custom_webhook_{}".format(type(self).__name__),
            inspect.getmodule(self).__name__,
        )

        @custom_webhook.route("/", methods=["GET"])
        async def health(request: Request) -> HTTPResponse:
            return HTTPResponse("ok", status=200)

        @custom_webhook.route("/webhook", methods=["GET", "POST"])
        async def receive(request: Request) -> HTTPResponse:
            if request.method == "GET":
                if request.args.get("hub.verify_token") != os.getenv(
                    "WPP_VERIFY_TOKEN", ""
                ):
                    return HTTPResponse("Invalid verify token", status=500)
                return HTTPResponse(request.args.get("hub.challenge"), status=200)

            custom_logger("WHATSAPP EVENT", request.json)

            # extracting whatsapp text message
            whatsapp_event = WhatsAppEvent(request.json)
            whatsapp_message = whatsapp_event.get_event_message()

            # Send whatsapp message to Rasa NLU
            if type(whatsapp_message) is NotSupportedMessage:
                return response.json({"status": "ok"})

            collector = CollectingOutputChannel()
            await on_new_message(
                UserMessage(
                    whatsapp_message.text,
                    collector,
                    whatsapp_event.recipient_phone,
                    input_channel=self.name(),
                )
            )

            # Retrieve Rasa answers
            bot_answers = collector.messages

            # Convert Rasa answers to WhatsApp expected format
            parser = whatsapp_event.parser_class(
                bot_answers, whatsapp_event.recipient_phone
            )
            wpp_answers = parser.parse_messages()

            # Send Rasa answers to WhatsApp
            wpp_client = whatsapp_event.wpp_client
            for message in wpp_answers:
                response_text, _ = wpp_client.send_message(message)

            return response.json({"status": "ok"})

        return custom_webhook
