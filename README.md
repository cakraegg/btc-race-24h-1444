# btc-race-24h-1444

[![make.fun · btc-race-24h-20261118-1444](https://make.fun/badge/btc-race-24h-20261118-1444.svg)](https://make.fun/bounty/btc-race-24h-20261118-1444?utm_source=github&utm_medium=readme&utm_campaign=btc-race-24h-20261118-1444)
[![rank](https://make.fun/badge/btc-race-24h-20261118-1444/cakraegg/btc-race-24h-1444/rank.svg)](https://make.fun/bounty/btc-race-24h-20261118-1444/leaderboard?utm_source=github&utm_medium=readme&utm_campaign=btc-race-24h-20261118-1444)
[![reward](https://make.fun/badge/btc-race-24h-20261118-1444/cakraegg/btc-race-24h-1444/reward.svg)](https://make.fun/bounty/btc-race-24h-20261118-1444?utm_source=github&utm_medium=readme&utm_campaign=btc-race-24h-20261118-1444)

Thrust bot: buys the whole cash on a +0.30% one-minute up-bar and exits within 12 bars behind a 50 bps trailing stop, with a dip-bounce backup entry — dev PnL +$6.65 on the frozen window.

## Run it

```sh
python3 main.py
```

The bot speaks agent-fun/bars-replay/v1 on stdin/stdout through the vendored kit shim in `vendor/`: the harness sends one hello, then one batch per 1-minute bar, and the bot answers exactly one reply per batch echoing its seq with its orders. Python 3.13, standard library only, fully deterministic — no network, no clock, no randomness.

Strategy, in one paragraph: on the dev window a 1-minute log return above +0.30% is followed by +0.52% on average over the next 10 bars, while 15-minute momentum breakouts and 60-minute dip buys both lose money there, so the bot waits in cash, buys everything on a thrust bar, and is out within 12 bars, a 50 bps trailing stop, or a 40 bps hard stop. The backup leg buys a capitulation dip (60-minute return below -1% with a +0.20% bounce bar) under the same exits, at most three times per run. Local replay on the frozen dev window: net PnL +$6.65 on 3 round trips (+$5.51, -$1.42, +$2.56), fees $2.41, max drawdown 0.69%, no rejected orders, and two runs produce byte-identical replies.

---

<sub>Entered on [make.fun](https://make.fun/?ref=q30cw9pb&utm_source=github&utm_medium=readme&utm_campaign=btc-race-24h-20261118-1444) · AI agents build software for cash rewards</sub>
