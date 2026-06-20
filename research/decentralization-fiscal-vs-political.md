# Fiscal Devolution Versus Political Devolution

Status: synthesis note for The Unelected City.

The working conclusion from the RBI municipal-finance reports, the State
Finance Commission histories, and the Finance Commission commentary on urban
local bodies is that India has a real but incomplete system of local
government.

The important distinction is between:

- fiscal devolution: who gets money, how much, on what formula, and with what
  reporting duties;
- political devolution: who controls elected local institutions, staff,
  planning, land, policing, and binding decision-making power;
- administrative devolution: who actually executes services and signs off on
  implementation.

The sources in this repo speak most strongly to the first category. They are
much weaker on the second.

## What The Sources Show

| Evidence surface | What it shows | What it does not show |
|---|---|---|
| RBI municipal-finance reports | Municipal corporations have real revenue, real transfers, and real dependence on State and Union channels. Property tax and user charges matter. | They do not show that local bodies control the larger levers of urban power. |
| SFC histories | States vary sharply in whether they constitute SFCs, publish reports, lay ATRs, and apply formulas. | An SFC report alone does not prove real local autonomy on the ground. |
| FC commentary on ULBs | The Union level keeps pushing accounts, property tax reform, online disclosure, and ATRs because State-side implementation is uneven. | It does not prove that political power has been transferred to municipalities. |

## The Pattern

The pattern is not that local government is fake. The pattern is that local
government often exists in legal form while the main instruments of power stay
above it.

In practice, many cities and towns have:

- elected bodies;
- budget heads;
- grant transfers;
- tax instruments that exist in law;
- audit requirements;
- periodic SFC or FC attention.

But they often do not have:

- land control;
- staffing control;
- police control;
- planning control;
- stable own-source revenue;
- discretion over major spending;
- clean public evidence that devolution was actually implemented.

That is why the phrase "gram swaraj" often reads as a political promise more
than a complete description of institutional reality.

## Repo-Level Interpretation

For The Unelected City, the data model should not treat "local government exists" as the
same thing as "local government has power."

Use three separate flags:

```yaml
fiscal_devolution: partial_or_uneven
political_devolution: weak_or_unproven
administrative_devolution: state_dependent
```

And when a city is studied, check four questions separately:

1. Is the body legally constituted?
2. Does it control meaningful money?
3. Does it control meaningful functions and staff?
4. Can the public see the report, ATR, budget line, and receipt line?

If the answer to the first is yes but the others are weak, the city has local
government in form, not full devolution in substance.

## Delhi

Delhi is the clearest reminder that the categories must stay separate.

Delhi has municipal finance machinery, but it is not a normal State city. It
has a national-capital constitutional wrapper, special NCT rules, separate
municipal bodies, and Union-level involvement. That makes it a special fiscal
and political case, not a standard example of political decentralization.

## Practical Consequence

The repo should describe Indian urban governance as a layered system:

- legal local bodies exist;
- fiscal devolution is partial and conditional;
- political devolution is often weaker than the rhetoric;
- administrative control is fragmented across State and Union layers.

That is the cleaner reading of the evidence than a simple "swaraj has arrived"
story.
