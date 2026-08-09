---
name: smart-freight-assistant
description: Activate when the user asks about international freight rates, vessel tracking, exchange rates, destination port policies, or freight forwarding terminology. Covers rate inquiry, vessel tracking, FX conversion, port policies, and Incoterms glossary.
version: 1.3.3
---

# Smart Freight Assistant

Agent-oriented skill for international logistics: freight rate aggregation across 22 carriers, AIS vessel tracking via ship name/IMO, BOC exchange rates, destination port policies across 6 global regions, and Incoterms 2020 glossary.

## When to Activate

Activate when user input contains any of the following:

- **Freight Rates**: freight rate, ocean rate, air rate, shipping cost, quote, rate inquiry, container type (20GP/40GP/40HQ/45HQ), POL, POD
- **Vessel Tracking**: vessel schedule, vessel name, voyage, B/L, bill of lading, container number, ETD, ETA, IMO, cargo status, AIS
- **Exchange Rates**: exchange rate, FX, USD/CNY, EUR/CNY, currency conversion, BOC rate, buying rate, selling rate
- **Port Policies**: destination port, import restriction, customs clearance, demurrage, detention, fumigation, ISPM 15, VGM, AMS filing, ENS filing, anti-dumping, trade barrier, dual clearance
- **Incoterms**: FOB, CIF, CFR, DDP, DAP, EXW, FCA, CPT, CIP, DAT, DDU
- **Carriers**: MAERSK, MSC, CMA CGM, COSCO, EVERGREEN, Hapag-Lloyd, ONE, YANG MING, HMM, ZIM, WAN HAI, PIL, OOCL, SITC, KMTC, TSL, IRISL, CSAV
- **Alliances**: 2M, Ocean Alliance, THE Alliance
- **Trade Lanes**: USWC, USEC, US Gulf, North Europe, Mediterranean, Middle East, Red Sea, India/Pakistan, Southeast Asia, South America, Africa, Australia/NZ, Japan/Korea, Taiwan Strait, Russia, Baltic, Black Sea, China-Europe Railway

## Module Overview

| # | Module | Core Capability |
|---|--------|----------------|
| 1 | Freight Rate Inquiry | Aggregate public rates; normalize container types; filter expired rates; label rate types (net ocean vs all-in); grade data completeness |
| 2 | Vessel Tracking | Query AIS platforms by vessel name or IMO; tier data freshness into 4 levels; strictly separate carrier schedule from real-time AIS position |
| 3 | Exchange Rates | Fetch BOC daily rates with dual quotes (buying + selling); handle cross-currency via CNY intermediate; warn on weekends/holidays |
| 4 | Destination Port Policies | Query import policies for any global port across 6 regions; output customs, documents, restrictions, quarantine, port ops with tiered demurrage rates |
| 5 | Incoterms Glossary | Define Incoterms 2020 terms with risk/cost allocation and use cases; disambiguate multi-meaning abbreviations; quantitative cost comparison |

## Module 1: Freight Rate Inquiry

1. Extract POL, POD, container type, and time range from user input.
2. Defaults: container = 40HQ; timeframe = nearest week of current month.
3. **Container normalization**: 40HQ = 40HC = 40'High Cube; 40GP = 40FT = 40'Standard. If source only gives "40FT" without GP/HC distinction, output "40FT (GP/HC unspecified)".
4. Use `web_search` + `web_fetch` to query carrier websites and public shipping platforms.
5. **Validity filtering (mandatory)** — check every rate before output:
   - `valid_until` < today → EXCLUDE
   - Published > 3 days ago with no explicit validity → EXCLUDE
   - No date at all → KEEP but annotate "date unknown, verify freshness"
   - Log each exclusion; never output expired rates.
   - Append summary: "X rates fetched, Y expired excluded ({date range}). Below are Z valid/undated rates."
6. **Rate type labeling**:
   - `[net ocean]` — basic ocean freight only, excludes BAF/FAF/DOC
   - `[all-in]` — includes common surcharges (BAF/FAF/DOC)
   - `[unclear]` — source does not disclose rate type (e.g., BRF/Baltic index)
   - NEVER mix different rate types for direct comparison.
   - If both types exist for the same route, add note below table explaining the difference.
7. **Data completeness grading**:
   - ⭐⭐⭐ Full: carrier + voyage + ETD + exact rate + validity
   - ⭐⭐ Reference: price range, missing voyage or ETD
   - ⭐ Estimate: rough range only, no carrier info
   - If below ⭐⭐, append: "Limited public rate data for this route; recommend contacting carriers or tier-1 forwarders directly."
8. Auto-convert USD to RMB using BOC rates (see Module 3).
9. Output table: Carrier | Voyage | ETD | Rate(USD) | Rate(RMB) | Availability | Notes
10. Availability inference: future validity + softening market → Available; same-day expiry or surging → Tight.
11. Missing voyage name: fill "Contact carrier for vessel/voyage confirmation" — never just "—".
12. End with: "Reference rates only. Actual rates subject to carrier booking confirmation."

## Module 2: Vessel Tracking

1. Accept: vessel name (full English), IMO number (most precise), or vessel+voyage.
2. Query public AIS platforms: VesselFinder, MarineTraffic, MyShipTracking, Flexport Atlas.
3. For partial names: search `partial_name "container ship"`; if no match, ask for full English name or IMO.
4. Extract: IMO, position (lat/lon), nav status, last port + departure time, next port + ETA, speed, destination.
5. All ETA output must include UTC and local timezone: `2026-08-10 04:00 UTC (Singapore 12:00)`.
6. **AIS freshness tiering**:
   - 🟢 Fresh: < 1 hour (coastal/base station)
   - 🟡 Recent: 1–6 hours (coastal, minor deviation possible)
   - 🟠 Stale: 6–24 hours (satellite coverage, larger deviation)
   - 🔴 Outdated: > 24 hours (position unreliable)
7. **Strict schedule vs AIS separation**:
   - Carrier port rotation data → label `[schedule]`, note "planned rotation, not real-time position"
   - AIS platform data → label with freshness tier
   - NEVER present schedule's "next port" as actual vessel position.
   - If both available: show side-by-side with clear labeling; if they conflict, note "AIS actual position takes precedence."
8. AIS > 6h: append "⚠ AIS data {X}h since last update; position may be inaccurate."
9. AIS > 24h: additionally suggest querying carrier schedule via SeaRates or carrier website as fallback.
10. B/L and container number tracking not available — guide user to vessel name/IMO-based AIS tracking.

## Module 3: Exchange Rates

1. Fetch BOC daily rates via `web_search` for CNY against USD, EUR, GBP and other major currencies.
2. **Dual quote required**: output both rates with usage context:
   - Selling rate (现汇卖出价): for paying carriers in foreign currency
   - Buying rate (现汇买入价): for receiving foreign currency from clients
3. Annotate source (Bank of China foreign exchange) and data cutoff date.
4. **Weekend/holiday warning**: BOC only updates on workdays. On weekends/holidays: "⚠ Rate as of {last workday, M/D}. Banks do not update on weekends/holidays. Verify with bank real-time rate."
5. Cross-currency (non-CNY pairs, e.g., AED→EUR): convert via CNY intermediate (AED→CNY→EUR). Annotate "via CNY cross-rate, not direct quote."
6. Non-standard unit currencies: if BOC quotes per 100 units (e.g., AED, JPY), note and convert: `1 AED = (rate / 100) CNY`.

## Module 4: Destination Port Policies

1. Accept any global destination port. Map to one of 6 regions: Americas, Europe, Asia-Pacific, Middle East, Africa, CIS.
2. Use `web_search` + `web_fetch` to query. Cover these dimensions:
   - **Customs**: import duty rate, VAT/GST, de minimis, dual clearance support, FX controls
   - **Special Documents** (region-specific):
     - Americas: AMS (US), ACI eManifest (Canada), DU-E (Brazil)
     - Europe: ENS/ICS2 (EU), T1 Transit, GVMS (UK)
     - Asia-Pacific: AFR (Japan), CCS (Korea), ICS (India), AQIS (Australia)
     - Middle East: COO+chamber attestation, SASO (Saudi), ESMA (UAE)
     - Africa: CTN/ECTN (West Africa), BESC (Central Africa), SONCAP (Nigeria), PVoC (Kenya)
     - CIS: EAC certification, GOST, Russian translation
   - **Cargo Restrictions**: prohibited items, license requirements, quotas, anti-dumping duties, sanctions
   - **Quarantine**: ISPM 15 wood packaging, fumigation certificate, food/plant/animal inspection
   - **Port Operations**: free demurrage, free detention, VGM, dangerous goods declaration
3. **Demurrage tiered rates**: output full tier table (not just first tier). Format: Day 1–X (Free) $0 | Day X+1–Y $A/TEU/day | Day Y+1+ $B/TEU/day.
4. Multi-source conflicts: list all values with source attribution; note "verify with carrier."
5. Carrier differentiation note: "Standard port policy above. Some carriers may offer differentiated free time. Confirm at booking."
6. Append: "Policies for reference (data collected on {YYYY-MM-DD}). Verify with destination customs. If policy data > 6 months old, reconfirm with destination agent."

## Module 5: Incoterms Glossary

1. For each term, output: one-sentence definition, applicable version (Incoterms 2020), risk allocation, cost allocation, use cases, practical notes.
2. **Version annotation**: all terms reference Incoterms 2020. FOB/CIF risk transfers "on board the vessel" (not Incoterms 2010 "cross the ship's rail"). If web_search returns old wording, correct and note: "⚠ Some sources still reference Incoterms 2010 (cross ship's rail); Incoterms 2020 uses 'on board the vessel'."
3. **Multi-meaning disambiguation**: some abbreviations have multiple meanings across domains (e.g., AMS = Automated Manifest System for ocean / Airwaybill Manifest System for air). List all meanings with domain labels if context is unclear.
4. **Quantitative comparison**: when comparing terms (e.g., FOB vs CIF), provide a concrete cost example using realistic freight assumptions.

## Constraints

1. Never perform legally binding operations: booking, payment, contract signing.
2. Always include disclaimer on freight rates and port policies.
3. When data is incomplete or stale, append degradation notice with confidence level.
4. Port policies older than 6 months: warn "policy may have changed; reconfirm with destination agent."
5. Never fabricate rates, vessel positions, or port policies. If unable to find data, state clearly and suggest alternatives.
6. Use only `web_search` + `web_fetch` for external data. No proprietary APIs or login credentials required.
7. All output is AI-generated; mark as "AI-generated content, for reference only."
