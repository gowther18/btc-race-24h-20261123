"""Dip-bounce rider for the make.fun BTC race (bars-replay/v1, Python 3.13).

Entry signal, kept from the setup that won its dev gate on 18 Nov:
  * Flat only: the close fell at least 0.30% over the last 15 bars AND
    rose at least 0.10% over the last 5 bars (the dip is turning).
    Buys the full cash balance of CBBTC.

Exits, rebuilt for this window:
  * Trailing stop: sell when the close falls 0.40% below the highest
    close seen since entry -- the position rides a rising tape instead
    of being capped by a fixed take profit.
  * Take-profit backstop: sell at +5.00% over the entry close. Inside a
    60-bar hold this needs a vertical spike (~8 sigma of this tape's
    1-minute moves); it exists so a freak run-up is banked outright
    instead of being handed back while the trailing stop catches up.
    It never binds on the dev window, so the dev numbers below are the
    trailing stop's alone.
  * Hard stop: sell at -0.50% under the entry close.
  * Max hold: 60 bars, then sell whatever the tape is doing.
  * No new entries in the last 32 bars of the window; an entry decided
    there cannot be managed before the harness flattens at the end.

Why the exits changed: this dev window (the 24 hours ending at the
opening) drifted +3.64%. Buy-and-hold made +$32.17 and the house
momentum bot +$34.94 (kit grade-local), while every active house
baseline lost (ema-cross -$114.83, rsi-bollinger -$9.32, adx-momentum
-$11.20). The 18 Nov exit shape (take profit +0.70%, 18-bar cap) loses
-$7.56 here: it pays the ~26 bps round-trip cost again and again and
steps off a rising tape at every cap. With the same entries and the
trailing exits above the bot makes +$12.97 on the dev window over 11
fills with a 1.19% max drawdown, and the result is a plateau, not a
spike: trailing stops of 0.30-0.50% with max holds of 60-240 bars all
land between +$6.50 and +$13.00, and dip thresholds of 0.25-0.35% are
all positive with these exits. The bot sits in cash between setups,
which is what keeps its drawdown near 1% whatever the window does.

Deterministic: the only state is the list of closes seen so far plus
the entry bookkeeping; no clock, no randomness, no network, no files.
Two runs on the same bars answer every batch identically.
"""

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "vendor"))

import makefun_bars

SYMBOL = "CBBTC"

# Entry: 15-bar dip and 5-bar bounce, as fractions of the close.
DIP_BARS = 15
DIP_PCT = 0.003
BOUNCE_BARS = 5
BOUNCE_PCT = 0.001
# Exit: trailing stop under the best close since entry, a take-profit
# backstop far above it, hard stop under the entry close, and a max
# hold in bars.
TRAIL_PCT = 0.004
TAKE_PROFIT = 0.05
STOP_LOSS = 0.005
MAX_HOLD_BARS = 60
# The window is 1440 one-minute bars; do not open a position that cannot
# be managed before the harness flattens everything at the last close.
# Batches are 0-based, so seq 1408 is the last bar an entry may be
# decided on (its fill lands on bar 1409).
TOTAL_BARS = 1440
LAST_ENTRY_SEQ = TOTAL_BARS - 32
# Orders may fill up to this far from the latest close (1-minute moves
# are ~0.08% std, so 100 bps is far outside a normal gap).
MAX_SLIPPAGE_BPS = 100


class DipBounceRider:
    """Keeps the closes and the open-trade bookkeeping for one run."""

    def __init__(self):
        self.closes = []
        self.entry_close = None
        self.peak_close = None
        self.hold_bars = 0

    def on_batch(self, state, batch):
        close = state.close(SYMBOL)
        if close is None:
            return []
        self.closes.append(close)

        holding = state.positions.get(SYMBOL)
        qty = holding.qty if holding is not None else 0
        if qty <= 0:
            # Flat: any entry bookkeeping from a filled sell is stale.
            self.entry_close = None
            self.peak_close = None
            self.hold_bars = 0
            return self._maybe_buy(state)
        # Holding: count the bar, lift the trailing peak, check exits.
        self.hold_bars += 1
        if self.entry_close is None:
            self.entry_close = close
        if self.peak_close is None or close > self.peak_close:
            self.peak_close = close
        if (
            close >= self.entry_close * (1 + TAKE_PROFIT)
            or close <= self.peak_close * (1 - TRAIL_PCT)
            or close <= self.entry_close * (1 - STOP_LOSS)
            or self.hold_bars >= MAX_HOLD_BARS
        ):
            self.entry_close = None
            self.peak_close = None
            self.hold_bars = 0
            return [
                {
                    "side": "sell",
                    "symbol": SYMBOL,
                    "qty": qty,
                    "max_slippage_bps": MAX_SLIPPAGE_BPS,
                }
            ]
        return []

    def _maybe_buy(self, state):
        if state.warming_up:
            return []
        if state.seq > LAST_ENTRY_SEQ:
            return []
        if len(self.closes) <= DIP_BARS:
            return []
        now = self.closes[-1]
        dip = now / self.closes[-1 - DIP_BARS] - 1
        bounce = now / self.closes[-1 - BOUNCE_BARS] - 1
        if dip < -DIP_PCT and bounce > BOUNCE_PCT and state.cash >= 1_000_000:
            self.entry_close = now
            self.peak_close = now
            self.hold_bars = 0
            return [
                {
                    "side": "buy",
                    "symbol": SYMBOL,
                    "notional_quote_units": state.cash,
                    "max_slippage_bps": MAX_SLIPPAGE_BPS,
                }
            ]
        return []


def on_hello(state):
    # Nothing to seed: the bot builds its history from the batches.
    return None


if __name__ == "__main__":
    bot = DipBounceRider()
    makefun_bars.run(bot.on_batch, on_hello=on_hello)
