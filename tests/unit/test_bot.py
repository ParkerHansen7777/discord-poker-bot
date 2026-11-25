
from poker_bot.bot import PokerBot


def test_bot_initializes():
    bot = PokerBot()

    assert bot is not None
    assert bot.intents.guilds is True
    assert bot.intents.members is True
    assert bot.intents.message_content is False
