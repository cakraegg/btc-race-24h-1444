"""Thrust bot for make.fun btc-race-24h-20261118-1444.

A long-only cbBTC/USDC bot that trades only on violent one-minute up-bars
("thrusts") and exits fast. It speaks agent-fun/bars-replay/v1 through the
vendored kit shim (vendor/makefun_bars.py): the shim owns the wire, this file
owns the decisions. One hello, then one batch per bar, exactly one reply per
batch echoing its seq, with the orders decided on that bar.

Why thrusts: on the dev window a 1-minute log return above +0.30% is followed
by +0.52% on average over the next 10 bars (3 of 3 events clear the ~36 bps
round-trip cost), while 15-minute momentum breakouts and 60-minute dip buys
both lose money there. So the bot waits in cash, buys the whole cash on a
thrust bar, and is out within 12 bars, a 50 bps trailing stop, or a 40 bps
hard stop -- whichever comes first. In the quiet half of the dev window it
simply never trades, so it never bleeds: dev PnL +$6.65 on 3 round trips,
max drawdown 0.69%.

The dip leg is the backup entry for a crash day with no thrust bar: the price
has fallen at least 1% over the last hour and this bar bounced at least
+0.20%. It uses the same 12-bar hold and the same stops, and at most three
dip trades per run. On the dev window it fires on no bar the thrust leg does
not already take, so it costs nothing there; it exists so a violent down day
still gives the bot a trade to take.

Everything is deterministic: integer prices from the bar feed, float log
returns of those integers, no clock, no environment, no randomness. Two runs
on the same bars produce byte-identical replies.
"""

import math
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "vendor"))
import makefun_bars

SYMBOL = "CBBTC"

# A 1-minute log return at or above this is a thrust: buy the whole cash.
THRUST_THR = 0.003
# Longest a thrust trade is held, in bars.
THRUST_HOLD = 12
# Dip leg: the price fell at least this much over the last 60 bars and this
# bar bounced at least this much. Same hold and stops as a thrust trade.
DIP_THR = 0.010
DIP_BOUNCE = 0.002
DIP_HOLD = 12
# At most this many dip trades per run.
MAX_DIP_TRADES = 3
# Exit: sell when the close falls this far below the entry close (hard stop)
# or below the best close since entry (trailing stop), in basis points.
STOP_BPS = 40
TRAIL_BPS = 50
# Max slippage on every order, in bps from the latest close (2%): wide enough
# that a fill after a jump bar is never refused, tight enough to refuse a
# wild gap.
SLIP_BPS = 200
# Bars to wait after an exit before a new entry.
COOLDOWN = 20


class ThrustBot:
    """Keeps the close history and the open trade; decides one reply per batch."""

    def __init__(self):
        self.closes = []
        self.entry_close = None
        self.peak = None
        self.entry_bar = None
        self.hold = THRUST_HOLD
        self.dip_trades = 0
        self.cooldown_until = -1
        self.exiting = False
        self.exit_bar = -1

    def _buy(self, state):
        return [{"side": "buy", "symbol": SYMBOL,
                 "notional_quote_units": state.cash,
                 "max_slippage_bps": SLIP_BPS}]

    def _sell(self, state):
        pos = state.positions[SYMBOL]
        return [{"side": "sell", "symbol": SYMBOL, "qty": pos.qty,
                 "max_slippage_bps": SLIP_BPS}]

    def on_batch(self, state, batch):
        bar = state.latest.get(SYMBOL)
        if bar is None or state.warming_up:
            return []
        close = int(bar["c"])
        self.closes.append(close)
        k = state.seq
        pos = state.positions.get(SYMBOL)
        if pos is not None:
            if self.entry_close is None:
                # The fill landed on this bar: anchor the stops to its close.
                self.entry_close = close
                self.peak = close
                self.entry_bar = k
            if close > self.peak:
                self.peak = close
            entry = self.entry_close
            sell = False
            if close * 10000 <= entry * (10000 - STOP_BPS):
                sell = True
            elif close * 10000 <= self.peak * (10000 - TRAIL_BPS):
                sell = True
            elif k - self.entry_bar >= self.hold:
                sell = True
            if sell:
                self.exiting = True
                self.exit_bar = k
                return self._sell(state)
            return []
        if self.exiting:
            # The position is gone: clear the trade and start the cooldown.
            self.exiting = False
            self.entry_close = None
            self.peak = None
            self.cooldown_until = self.exit_bar + COOLDOWN
        if k < self.cooldown_until or len(self.closes) < 2:
            return []
        # Thrust entry: this bar jumped at least +0.30% in one minute.
        r1 = math.log(close / self.closes[-2])
        if r1 >= THRUST_THR:
            self.hold = THRUST_HOLD
            return self._buy(state)
        # Dip entry: at least -1% over the last hour, and this bar bounced
        # at least +0.20%. Checked after the thrust, so a bar that is both
        # a thrust and a dip bounce is always managed as a thrust.
        if self.dip_trades < MAX_DIP_TRADES and len(self.closes) >= 61:
            r60 = math.log(close / self.closes[k - 60])
            if r60 <= -DIP_THR and r1 >= DIP_BOUNCE:
                self.dip_trades += 1
                self.hold = DIP_HOLD
                return self._buy(state)
        return []


makefun_bars.run(ThrustBot().on_batch)
