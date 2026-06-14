# Ahmedabad M.J. Library: Membership and Funding

This note records the current curated facts from M.J. Library's official RTI /
proactive-disclosure PDFs and the Ahmedabad budget series already carried in this
repo.

## What "membership" means

The M.J. disclosure member count is a registered-member roll for M.J. Library and
its branch network. In recent disclosures it is the sum of:

- annual members;
- lifetime members; and
- Gyanvihar reading-room members.

That distinction matters. Lifetime members accumulate, so the headline member
count can recover even when annual membership is weak.

From 2015-16 to 2025-26, total network membership rose from 20,764 to 26,834:
an increase of 6,070 members, or 29.2 percent over ten years. But annual members
fell from a 2018-19 peak of 3,194 to 505 in 2025-26, an 84.2 percent decline.
The 2025-26 membership roll is 95.3 percent lifetime members.

Against the SevenT4 Ahmedabad ward population total of 7,078,533, the 2025-26
membership count is only 0.379 percent of the city, or roughly one registered
member per 264 residents.

Source data:

- `data/cities/ahmedabad/source/libraries/mj_library_annual_stats.csv`;
- `data/cities/ahmedabad/source/libraries/mj_library_membership.csv`;
- `data/cities/ahmedabad/source/libraries/mj_library_network.json`.

## Funding split

For operational coverage, M.J. Library's own disclosure is the clean ledger
because it reconciles expenditure, library income, and AMC grant in one budget
table. The local AMC budget-code series remains useful for long-run municipal
budget priority, but it reports the AMC budget line and does not by itself
reconcile the library trust's full operating budget.

In 2025-26, M.J. Library reports:

- total budget: Rs 22.7675 crore;
- AMC grant: Rs 21.9255 crore, or 96.30 percent;
- library income: Rs 0.8420 crore, or 3.70 percent.

In 2024-25, M.J. Library reports:

- total budget: Rs 18.7415 crore;
- AMC grant: Rs 18.1195 crore, or 96.68 percent;
- library income: Rs 0.6220 crore, or 3.32 percent.

The curated finance split now covers 2021-22 through 2025-26. Source data:
`data/cities/ahmedabad/source/libraries/mj_library_finance.csv`.

## What user fees are doing

The disclosure line is "library income", not "user fees", so it should be read as
an upper bound for fee/self-income coverage. It may include membership fees,
reading-room charges, auditorium rent, deposits/fines, interest, and miscellaneous
receipts.

Even under a generous fee estimate for 2025-26:

- annual members: 505 x Rs 500 = about Rs 2.5 lakh;
- net new lifetime members from 2024-25 to 2025-26: 242 x Rs 3,000 = about Rs
  7.3 lakh;
- Gyanvihar members at the maximum annual reading-room charge: 755 x Rs 1,000 =
  about Rs 7.6 lakh.

That is about Rs 17.3 lakh, or roughly 0.76 percent of the Rs 22.7675 crore
budget. It is only about one-fifth of the disclosed Rs 84.2 lakh library-income
line. User fees are therefore not meaningful cost recovery. Their practical role
is rationing/gatekeeping access to borrowing and reading-room privileges inside a
network that is overwhelmingly paid for by AMC.

## 2025-26 cost coverage

The Rs 84.2 lakh library-income line covers only 3.70 percent of the full 2025-26
budget and 4.56 percent of recurring operations after excluding explicit capital
expense and new plans.

It can cover the book-buying line several times over, but that is because book
buying is tiny in the budget:

- books: Rs 25 lakh, 1.10 percent of total budget;
- all reading material: Rs 32.75 lakh, 1.44 percent of total budget;
- establishment/payroll: Rs 14.0415 crore, 61.67 percent of total budget;
- maintenance: Rs 1.555 crore, 6.83 percent;
- capital expense: Rs 1.58 crore, 6.94 percent;
- new plans: Rs 2.71 crore, 11.90 percent.

The finding is not that users finance books. The finding is that the book budget
is so small that a minor self-income line can cover it, while the institution's
actual operating and capital structure remains almost entirely grant-funded.

## Sources

- M.J. Library official RTI/proactive disclosure PDFs listed on
  `https://www.mjlibrary.in/assets/frontend/en-lang/content.js`.
- Full M.J. Library site-content capture:
  `data/cities/ahmedabad/source/libraries/mj_library_site_content.json`.
- Official M.J. Library PDF-link index:
  `data/cities/ahmedabad/source/libraries/mj_library_pdf_index.csv`.
- Full text exports for all 11 proactive disclosures, 2015-16 through 2025-26:
  `data/cities/ahmedabad/source/libraries/disclosures_text/`.
- Disclosure text manifest with page counts and PDF hashes:
  `data/cities/ahmedabad/source/libraries/mj_library_disclosure_text_index.csv`.
- Ahmedabad library-location inventory combining AMC library GeoJSON and the
  civic-service library scrape:
  `data/cities/ahmedabad/source/libraries/ahmedabad_library_locations.csv`.
- 2025-26 disclosure:
  `https://www.mjlibrary.in/assets/img/pdf/mj_discloser_rti_2025-26.pdf`.
- 2024-25 disclosure:
  `https://www.mjlibrary.in/assets/img/pdf/MJLibraryDiscloser_07_06_2024.pdf`.
- 2015-16 to 2023-24 disclosure PDFs listed in the membership CSV.
- AMC budget-code series:
  `data/cities/ahmedabad/source/budget/amc_budget_22yr.csv`.
