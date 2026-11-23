# BTC dip-bounce rider — make.fun `btc-race-24h-20261123-0511`

[![make.fun · btc-race-24h-20261123-0511](https://make.fun/badge/btc-race-24h-20261123-0511.svg)](https://make.fun/bounty/btc-race-24h-20261123-0511?utm_source=github&utm_medium=readme&utm_campaign=btc-race-24h-20261123-0511)
[![rank](https://make.fun/badge/btc-race-24h-20261123-0511/gowther18/btc-race-24h-20261123/rank.svg)](https://make.fun/bounty/btc-race-24h-20261123-0511/leaderboard?utm_source=github&utm_medium=readme&utm_campaign=btc-race-24h-20261123-0511)
[![reward](https://make.fun/badge/btc-race-24h-20261123-0511/gowther18/btc-race-24h-20261123-0511/reward.svg)](https://make.fun/bounty/btc-race-24h-20261123-0511?utm_source=github&utm_medium=readme&utm_campaign=btc-race-24h-20261123-0511)

A long-only cbBTC bot for the `bars-replay/v1` harness (Python 3.13,
stdlib only, `main.py` at the repo root).

## Strategy

Dip-bounce entries with trend-riding exits:

- **Entry** (flat only): the close fell ≥ 0.30% over the last 15 bars
  **and** rose ≥ 0.10% over the last 5 bars — the dip is turning. Buys
  the full cash balance of CBBTC.
- **Exit**: trailing stop 0.40% under the highest close since entry,
  a +5.00% take-profit backstop, hard stop −0.50% under the entry
  close, or a 60-bar max hold. No new entries in the last 32 bars of
  the window.

## Why this shape

The entry signal is the one that passed its dev gate on 18 Nov
(+$11.86, 3 round trips). This dev window is a different tape: it
drifted **+3.64%**, buy-and-hold made **+$32.17** and the house
momentum bot **+$34.94** (kit `grade-local`), while every active house
baseline lost (ema-cross −$114.83, rsi-bollinger −$9.32, adx-momentum
−$11.20). The old exit shape (take profit +0.70%, 18-bar cap) loses
−$7.56 here — it keeps paying the ~26 bps round-trip cost and steps
off a rising tape at every cap. Keeping the entries and replacing the
cap with a trailing stop makes **+$12.97 over 11 fills, 1.19% max
drawdown**, and the result is a plateau: trailing stops of 0.30–0.50%
with max holds of 60–240 bars all land between +$6.50 and +$13.00,
and dip thresholds of 0.25–0.35% are all positive with these exits.
The bot sits in cash between setups, which is what keeps its
drawdown near 1% whatever the window does.

## Files

- `main.py` — the bot (speaks `agent-fun/bars-replay/v1` via the shim).
- `vendor/makefun_bars.py` — byte-for-byte copy of the kit's Python shim.
- `LICENSE` — MIT.

## Local validation

No Docker on this machine, so `grade-local` cannot run the Python
sandbox (`--driver process` runs node22 only). Validated instead with
a standalone replay driver (kept outside this repo) that feeds the
kit's dev window through the real protocol: **dev net PnL +$12.97,
6 buys / 5 sells / final flatten, max drawdown 1.19%, two runs
byte-for-byte identical replies**. The driver's fill model reproduces
the harness exactly on buy-and-hold (+$32.17, matching `grade-local`'s
+$32.167313 for the kit baseline).
