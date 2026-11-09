"""V1b. Closure calendar by venue type, England and Wales, 1 March 2020 to 31 December 2021.

Seven venue types: pubs and bars, restaurants and cafes, takeaways, cinemas, theatres and concert venues,
gyms and fitness centres, nightclubs. For every 2020 LTLA and day the closure value is
    1    premises closed to the public for the venue's main service (takeaway or delivery only, for food venues)
    0.5  partial closure: indoor closed with outdoor service allowed (pubs, bars, restaurants, cafes);
         or, for pubs and bars only, drink-led trade banned (substantial-meal rule, or the Welsh 18:00 close
         with no alcohol, 4-19 Dec 2020)
    0    open (possibly with curfews, table service or group limits)
The hospitality states and flags come from the B4 panel (extension/data/clean/b4_restrictions_daily_ltla20.csv.gz),
which was read from the same regulations. The other venue types follow the rules in RULES below, each cited to
a regulation and checked against the downloaded legislation.gov.uk text (made or point-in-time) when the script
runs: a rule whose text check fails stops the build.

Outputs (extension/venue_mix/data/):
  v1_regulation_calendar.csv        the rules with citations and the result of each text check
  v1_closure_daily_ltla20.csv.gz    336 LTLAs x 671 days x 7 venue types (wide)
  v1_closure_daily_lad23.csv.gz     318 LADs (2020-population-weighted means of predecessors)
  v1_closure_shares_lad23.csv       share of days closed by venue type and window, per LAD
  v1_validation.csv                 spot checks
"""
import re

import numpy as np
import pandas as pd

from vm_common import CLEAN, DATA, LEG, VENUES, VRAW

VLEG = VRAW / "legislation"
LEICESTER, OADBY = "E06000016", "E07000135"
LCR = ["E06000006", "E08000011", "E08000012", "E08000013", "E08000014", "E08000015"]

WINDOWS = {
    "main": ("2020-03-23", "2021-03-22"),       # census year: 23 Mar 2020 to the day before Census Day 2021
    "yr_jun2021": ("2020-07-01", "2021-06-30"),  # ONS migration year ending June 2021
    "reopen": ("2021-04-01", "2021-07-31"),      # April to July 2021
}

# (nation, venue types, first day, last day, value, regulation, provision, check file, must match, must not match)
# file paths: "made/x.xml" or "pit/x.xml" under B4's legislation folder (B4) or this extension's (VM)
RULES = [
    # ---------------- England
    ("E", "pubs_bars restaurants_cafes cinemas theatres_concert nightclubs gyms", "2020-03-21", "2020-03-25", 1,
     "uksi/2020/327", "Health Protection (Coronavirus, Business Closure) (England) Regulations 2020, Schedule Parts 1-2, from 2pm 21 Mar 2020",
     "B4 made/uksi_2020_327.xml", r"Cinemas\.|Indoor fitness studios, gyms", None),
    ("E", "pubs_bars restaurants_cafes cinemas theatres_concert nightclubs gyms", "2020-03-26", "2020-07-03", 1,
     "uksi/2020/350", "Health Protection (Coronavirus, Restrictions) (England) Regulations 2020, reg 4 and Schedule 2 Parts 1-2 (takeaway allowed)",
     "B4 made/uksi_2020_350.xml", r"^Theatres\.$|^Nightclubs\.$|^Concert halls\.$|gyms", None),
    ("E", "nightclubs", "2020-07-04", "2020-10-13", 1,
     "uksi/2020/684", "Health Protection (Coronavirus, Restrictions) (No. 2) (England) Regulations 2020, Schedule 2 para 1 (nightclubs, dance halls)",
     "VM pit/uksi_2020_684_2020-08-15.xml", r"^Nightclubs\.$", None),
    ("E", "cinemas theatres_concert", "2020-07-04", "2020-07-04", 0,
     "uksi/2020/684", "No. 2 Regulations: cinemas, theatres and concert halls are not in Schedule 2 (open from 4 Jul 2020; indoor performances were advised against in guidance only until 15 Aug)",
     "VM pit/uksi_2020_684_2020-07-04.xml", r"^Nightclubs\.$", r"^(Cinemas|Theatres|Concert halls)\.$"),
    ("E", "gyms", "2020-07-04", "2020-07-24", 1,
     "uksi/2020/684", "No. 2 Regulations, Schedule 2 'Indoor gyms and sports courts and facilities'",
     "VM pit/uksi_2020_684_2020-07-24.xml", r"^Indoor gyms and sports courts and facilities\.$", None),
    ("E", "gyms", "2020-07-25", "2020-07-25", 0,
     "uksi/2020/788", "No. 2 (Amendment) (No. 2) Regulations 2020, in force 25 Jul 2020: indoor gyms, pools and fitness studios removed from Schedule 2",
     "VM pit/uksi_2020_684_2020-07-25.xml", r"^Nightclubs\.$", r"Indoor gyms"),
    ("E:Leicester+Oadby", "pubs_bars restaurants_cafes cinemas theatres_concert nightclubs gyms", "2020-07-04", "2020-08-02", 1,
     "uksi/2020/685", "Health Protection (Coronavirus, Restrictions) (Leicester) Regulations 2020, Schedule (protected area per B4: Leicester to 2 Aug, Oadby and Wigston to 31 Jul)",
     "B4 pit_local/uksi_2020_685_2020-07-24.xml", r"^Cinemas except for drive-in cinemas|^Theatres\.$|^Indoor gyms and sports courts", None),
    ("E:Leicester", "gyms", "2020-08-03", "2020-09-07", 1,
     "uksi/2020/824", "Health Protection (Coronavirus, Restrictions) (Leicester) (No. 2) Regulations 2020, Schedule 'Indoor gyms' (removed with effect from 8 Sep 2020)",
     "VM pit/uksi_2020_824_2020-09-07.xml", r"^Indoor gyms and sports courts and facilities\.$", None),
    ("E:Leicester", "gyms", "2020-09-08", "2020-09-08", 0,
     "uksi/2020/824", "Leicester (No. 2) Regulations as in force 8 Sep 2020: indoor gyms no longer listed",
     "B4 pit_local/uksi_2020_824_2020-09-08.xml", r"^Nightclubs\.$", r"Indoor gyms"),
    ("E:Bolton", "pubs_bars restaurants_cafes", "2020-09-10", "2020-10-02", 1,
     "uksi/2020/974", "Health Protection (Coronavirus, Restrictions) (Bolton) Regulations 2020: hospitality takeaway only (B4 state E_bolton_closure)",
     "B4 made/uksi_2020_974.xml", r"close any premises, or part of the premises, in the protected area in which food or drink are sold for consumption on those premises", None),
    ("E", "nightclubs", "2020-10-14", "2020-11-04", 1,
     "uksi/2020/1103-1105", "Local COVID-19 Alert Level (Medium, High, Very High) Regulations 2020, Schedule 1 business closures (nightclubs, dance halls, discotheques)",
     "B4 made/uksi_2020_1103.xml", r"^nightclubs;$", None),
    ("E:Very High", "pubs_bars", "2020-10-14", "2020-11-04", 0.5,
     "uksi/2020/1105", "Very High Regulations, Schedule 1: pubs and bars closed unless serving substantial table meals (B4 flag meal_req)",
     "B4 made/uksi_2020_1105.xml", r"table meal", None),
    ("E:Liverpool City Region", "gyms", "2020-10-17", "2020-10-23", 1,
     "uksi/2020/1131", "Very High (Amendment) Regulations 2020, inserting Schedule 2A para 1 (LCR: indoor gyms, fitness and dance studios), in force 17 Oct; no longer in Schedule 2A on 24 Oct (point-in-time text)",
     "B4 pit/uksi_2020_1105_schedule2A_2020-10-23.xml", r"indoor gyms, fitness and dance studios", None),
    ("E:Liverpool City Region", "gyms", "2020-10-24", "2020-10-24", 0,
     "uksi/2020/1105", "Very High Regulations Schedule 2A as in force 24 Oct 2020: LCR gyms no longer listed",
     "B4 pit/uksi_2020_1105_schedule2A_2020-10-24.xml", r"Liverpool City Region", r"indoor gyms"),
    ("E", "pubs_bars restaurants_cafes cinemas theatres_concert nightclubs gyms", "2020-11-05", "2020-12-01", 1,
     "uksi/2020/1200", "Health Protection (Coronavirus, Restrictions) (England) (No. 4) Regulations 2020, Schedule 2 (takeaway allowed)",
     "B4 made/uksi_2020_1200.xml", r"^Cinemas\.$|^Theatres\.$|^Concert halls\.$|fitness studios, gyms", None),
    ("E", "nightclubs", "2020-12-02", "2021-01-05", 1,
     "uksi/2020/1374", "All Tiers Regulations 2020, Schedules 1-3 (and 3A): nightclubs closed in every tier",
     "VM pit/uksi_2020_1374_2020-12-02.xml", r"^nightclubs;$", None),
    ("E:Tier 2", "pubs_bars", "2020-12-02", "2021-01-05", 0.5,
     "uksi/2020/1374", "All Tiers Regulations, Schedule 2: alcohol only with a table meal (B4 flag meal_req)",
     "VM pit/uksi_2020_1374_2020-12-02.xml", r"alcohol is only served for consumption on the premises as part of a table meal", None),
    ("E:Tier 3", "pubs_bars restaurants_cafes cinemas theatres_concert", "2020-12-02", "2021-01-05", 1,
     "uksi/2020/1374", "All Tiers Regulations, Schedule 3: hospitality takeaway only; cinemas, theatres, concert halls closed; gyms open",
     "VM pit/uksi_2020_1374_2020-12-02.xml", r"^cinemas, except drive-in cinemas;$|^concert halls;$", None),
    ("E:Tier 4", "pubs_bars restaurants_cafes cinemas theatres_concert gyms", "2020-12-20", "2021-01-05", 1,
     "uksi/2020/1611", "All Tiers (Amendment) Regulations 2020 inserting Schedule 3A (Tier 4), in force 7am 20 Dec 2020: adds indoor gyms",
     "VM pit/uksi_2020_1374_2020-12-20.xml", r"^gyms,$", None),
    ("E", "pubs_bars restaurants_cafes cinemas theatres_concert nightclubs gyms", "2021-01-06", "2021-03-28", 1,
     "uksi/2021/8", "All Tiers (England) (Amendment) Regulations 2021: Tier 4 to all of England from 6 Jan 2021 (B4 state E_lockdown3)",
     "B4 made/uksi_2021_8.xml", r"Tier 4", None),
    ("E", "pubs_bars restaurants_cafes cinemas theatres_concert nightclubs gyms", "2021-03-29", "2021-04-11", 1,
     "uksi/2021/364", "Steps Regulations 2021, Schedule 1 (Step 1)",
     "VM pit/uksi_2021_364_2021-03-29.xml", r"^gyms;$|^cinemas;$", None),
    ("E", "pubs_bars restaurants_cafes", "2021-04-12", "2021-05-16", 0.5,
     "uksi/2021/364", "Steps Regulations, Schedule 2 (Step 2): hospitality outdoors only (B4 flags)",
     "VM pit/uksi_2021_364_2021-04-12.xml", r"^restaurants, including restaurants", None),
    ("E", "cinemas theatres_concert nightclubs", "2021-04-12", "2021-05-16", 1,
     "uksi/2021/364", "Steps Regulations, Schedule 2 (Step 2): cinemas, theatres, concert halls and nightclubs closed; gyms open",
     "VM pit/uksi_2021_364_2021-04-12.xml", r"^cinemas, except drive-in cinemas;$|^concert halls;$", None),
    ("E", "nightclubs", "2021-05-17", "2021-07-18", 1,
     "uksi/2021/585", "Steps (Amendment) Regulations 2021: all England to Step 3 from 17 May; Step 3 (Schedule 3) closes nightclubs only",
     "VM pit/uksi_2021_364_2021-05-17.xml", r"^nightclubs;$", None),
    ("E", "pubs_bars restaurants_cafes cinemas theatres_concert nightclubs gyms", "2021-07-19", "2021-12-31", 0,
     "uksi/2021/848", "Steps etc. (Revocation and Amendment) Regulations 2021: Steps Regulations revoked 23:55 on 18 Jul 2021",
     "B4 made/uksi_2021_848.xml", r"revoked|revocation", None),
    # ---------------- Wales
    ("W", "pubs_bars restaurants_cafes cinemas theatres_concert nightclubs gyms", "2020-03-21", "2020-07-12", 1,
     "wsi/2020/326; wsi/2020/353", "Health Protection (Coronavirus, Business Closure) (Wales) Regulations 2020; Health Protection (Coronavirus Restrictions) (Wales) Regulations 2020, Schedule 1",
     "B4 made/wsi_2020_353.xml", r"Cinemas|Theatres|Nightclubs", None),
    ("W", "pubs_bars restaurants_cafes", "2020-07-13", "2020-08-02", 0.5,
     "wsi/2020/725", "Health Protection (Coronavirus Restrictions) (No. 2) (Wales) Regulations 2020: outdoor hospitality from 13 Jul (B4 flags)",
     "VM pit/wsi_2020_725_2020-07-13.xml", r"^Public houses\.$", None),
    ("W", "theatres_concert nightclubs", "2020-07-13", "2020-10-22", 1,
     "wsi/2020/725", "No. 2 (Wales) Regulations, Schedule 1 Part 2 'Businesses and services required to be closed': theatres, concert halls, licensed venues with dancing",
     "VM pit/wsi_2020_725_2020-10-22.xml", r"^Theatres\.$|^Concert halls\.$|^Venues authorised", None),
    ("W", "cinemas", "2020-07-13", "2020-07-26", 1,
     "wsi/2020/725", "No. 2 (Wales) Regulations, Schedule 1: 'Indoor cinemas' closed",
     "VM pit/wsi_2020_725_2020-07-13.xml", r"^Indoor cinemas\.$", None),
    ("W", "cinemas", "2020-07-27", "2020-07-27", 0,
     "wsi/2020/803", "No. 2 (Wales) (Amendment) (No. 2) Regulations 2020, reg 3 in force 27 Jul 2020: cinemas may open subject to protective measures",
     "VM made/wsi_2020_803.xml", r"Regulation 3 comes into force on 27 July 2020", None),
    ("W", "gyms", "2020-07-13", "2020-08-09", 1,
     "wsi/2020/725", "No. 2 (Wales) Regulations, Schedule 1: indoor fitness studios, gyms closed (moved to the may-open list in the text in force 10 Aug 2020)",
     "VM pit/wsi_2020_725_2020-08-03.xml", r"^Indoor fitness studios, gyms, spas or other indoor leisure centres", None),
    ("W", "pubs_bars restaurants_cafes cinemas theatres_concert nightclubs gyms", "2020-10-23", "2020-11-08", 1,
     "wsi/2020/1149", "Health Protection (Coronavirus Restrictions) (No. 3) (Wales) Regulations 2020 (firebreak, 6pm 23 Oct to 8 Nov)",
     "B4 made/wsi_2020_1149.xml", r"^Cinemas\.$|^Theatres\.$|indoor fitness studios, gyms", None),
    ("W", "theatres_concert nightclubs", "2020-11-09", "2020-12-19", 1,
     "wsi/2020/1219", "Health Protection (Coronavirus Restrictions) (No. 4) (Wales) Regulations 2020, Schedule 'premises must be closed'",
     "VM pit/wsi_2020_1219_2020-11-09.xml", r"^Concert halls\.$|^Theatres\.$", None),
    ("W", "cinemas", "2020-12-04", "2020-12-19", 1,
     "wsi/2020/1409", "No. 4 (Wales) (Amendment) (No. 2) Regulations 2020, 6pm 4 Dec 2020: cinemas added to the closed list",
     "VM pit/wsi_2020_1219_2020-12-04.xml", r"^Cinemas\.$", None),
    ("W", "pubs_bars", "2020-12-04", "2020-12-19", 0.5,
     "wsi/2020/1409", "No. 4 (Wales) (Amendment) (No. 2) Regulations 2020: licensed premises close 18:00 and no alcohol (B4 flag early_close_no_alcohol)",
     "B4 made/wsi_2020_1409.xml", r"alcohol", None),
    ("W", "pubs_bars restaurants_cafes cinemas theatres_concert nightclubs gyms", "2020-12-20", "2021-04-25", 1,
     "wsi/2020/1609", "Health Protection (Coronavirus Restrictions) (No. 5) (Wales) Regulations 2020, Alert Level 4, Schedule 4 closed premises (Alert Level 3 from 27 Mar 2021 kept these closed)",
     "VM pit/wsi_2020_1609_2020-12-20.xml", r"fitness studios and gyms|^Concert halls and theatres", None),
    ("W", "pubs_bars restaurants_cafes", "2021-04-26", "2021-05-16", 0.5,
     "wsi/2021/502", "No. 5 (Wales) (Amendment) (No. 8) Regulations 2021, 6am 26 Apr 2021: outdoor hospitality at Alert Level 3 (B4 flags)",
     "B4 made/wsi_2021_502.xml", r"26 April 2021", None),
    ("W", "gyms", "2021-04-26", "2021-05-02", 1,
     "wsi/2020/1609", "No. 5 (Wales) Regulations, Schedule 5 temporary modification of Alert Level 3 to the end of 2 May 2021 (indoor fitness studios and gyms closed)",
     "VM pit/wsi_2020_1609_2021-04-26.xml", r"for the period ending at the end of the day on 2 May 2021", None),
    ("W", "gyms", "2021-05-03", "2021-05-03", 0,
     "wsi/2021/542", "No. 5 (Wales) (Amendment) (No. 9) Regulations 2021, in force 3 May 2021: Alert Level 3 without the temporary closure of gyms",
     "B4 made/wsi_2021_542.xml", r"3 May 2021", None),
    ("W", "cinemas theatres_concert", "2021-04-26", "2021-05-16", 1,
     "wsi/2020/1609", "No. 5 (Wales) Regulations, Alert Level 3 (whole of Wales, Schedule 5): cinemas, concert halls and theatres closed",
     "VM pit/wsi_2020_1609_2021-05-03.xml", r"^Concert halls and theatres, other than drive in theatres\.$", None),
    ("W", "nightclubs", "2021-05-17", "2021-08-06", 1,
     "wsi/2021/583", "No. 5 (Wales) (Amendment) (No. 11) Regulations 2021: whole of Wales Alert Level 2 from 17 May (Level 1 from 7 Jun, wsi/2021/668); nightclubs closed at Levels 1-2",
     "VM pit/wsi_2020_1609_2021-07-17.xml", r"^Nightclubs, discotheques, dance halls", None),
    ("W", "pubs_bars restaurants_cafes cinemas theatres_concert nightclubs gyms", "2021-08-07", "2021-12-31", 0,
     "wsi/2021/925", "No. 5 (Wales) (Amendment) (No. 18) Regulations 2021: Alert Level 0 from 7 Aug 2021, nightclubs open",
     "B4 made/wsi_2021_925.xml", r"7 August 2021", None),
]


def text_items(spec):
    from b4_common import xml_items
    root, rel = spec.split(" ", 1)
    p = (LEG if root == "B4" else VLEG) / rel
    if not p.exists():
        return None
    return [t for _, t, _ in xml_items(p)]


def check_rules():
    rows = []
    for nat, venues, d0, d1, val, si, prov, f, must, mustnot in RULES:
        items = text_items(f)
        ok_file = items is not None
        ok_must = ok_file and all(any(re.search(p, t, re.I) for t in items) for p in must.split("|"))
        ok_not = (not ok_file) or mustnot is None or not any(re.search(mustnot, t, re.I) for t in items)
        rows.append(dict(nation=nat, venues=venues, first_day=d0, last_day=d1, closure=val, regulation=si,
                         provision=prov, text_checked=f, must_match=must, must_not_match=mustnot,
                         check_passed=bool(ok_file and ok_must and ok_not)))
    r = pd.DataFrame(rows)
    r.to_csv(DATA / "v1_regulation_calendar.csv", index=False)
    bad = r[~r.check_passed]
    if len(bad):
        print(bad[["regulation", "text_checked", "must_match", "must_not_match"]].to_string())
        raise SystemExit("regulation text check failed")
    print(f"regulation text checks: {len(r)} rules, all passed")


def between(d, a, b):
    return (d >= pd.Timestamp(a)) & (d <= pd.Timestamp(b))


def build_daily():
    b = pd.read_csv(CLEAN / "b4_restrictions_daily_ltla20.csv.gz", low_memory=False, parse_dates=["date"])
    d, st, E, W = b.date, b.state, b.nation == "E", b.nation == "W"
    ind, outd = b.indoor_closed.astype(float), b.outdoor_closed.astype(float)
    full = ind * outd
    out = b[["ltla20_code", "ltla20_name", "nation", "date", "state", "tier"]].copy()
    # food and drink, from the B4 flags
    out["restaurants_cafes"] = np.maximum(full, 0.5 * ind)
    out["pubs_bars"] = np.maximum.reduce([full, 0.5 * ind, 0.5 * b.meal_req.astype(float),
                                          0.5 * b.early_close_no_alcohol.astype(float)])
    out["takeaways"] = 0.0
    # England, by state
    all_closed = st.isin(["E_lockdown1", "E_lockdown2", "E_lockdown3", "E_step1", "E_leicester_closure",
                          "E_tier_dec_4"])
    cin_e = all_closed | st.isin(["E_step2", "E_tier_dec_3"])
    gym_e = (all_closed | between(d, "2020-03-21", "2020-07-24")
             | ((b.ltla20_code == LEICESTER) & between(d, "2020-07-04", "2020-09-07"))
             | ((b.ltla20_code == OADBY) & between(d, "2020-07-04", "2020-07-31"))
             | (b.ltla20_code.isin(LCR) & between(d, "2020-10-17", "2020-10-23")))
    night_e = between(d, "2020-03-21", "2021-07-18")
    # Wales, by date (national rules; the Welsh local health protection areas closed none of these venues)
    cin_w = (between(d, "2020-03-21", "2020-07-26") | between(d, "2020-10-23", "2020-11-08")
             | between(d, "2020-12-04", "2021-05-16"))
    thea_w = between(d, "2020-03-21", "2021-05-16")
    gym_w = (between(d, "2020-03-21", "2020-08-09") | between(d, "2020-10-23", "2020-11-08")
             | between(d, "2020-12-20", "2021-05-02"))
    night_w = between(d, "2020-03-21", "2021-08-06")
    out["cinemas"] = np.where(E, cin_e, cin_w).astype(float)
    out["theatres_concert"] = np.where(E, cin_e, thea_w).astype(float)
    out["gyms"] = np.where(E, gym_e, gym_w).astype(float)
    out["nightclubs"] = np.where(E, night_e, night_w).astype(float)
    return out


def to_lad23(daily):
    lk = pd.read_csv(CLEAN / "b4_ltla20_to_lad23.csv")
    x = daily.merge(lk[["ltla20_code", "lad23_code", "weight"]], on="ltla20_code")
    for v in VENUES:
        x[v] = x[v] * x.weight
    g = x.groupby(["lad23_code", "date"])
    lad = g[VENUES].sum().div(g.weight.sum(), axis=0).reset_index()
    lad["nation"] = lad.lad23_code.str[0]
    return lad


def shares(lad):
    rows = []
    for w, (a, b) in WINDOWS.items():
        s = lad[between(lad.date, a, b)].groupby("lad23_code")[VENUES].mean()
        s.columns = [f"closed_{w}_{v}" for v in VENUES]
        rows.append(s)
    out = pd.concat(rows, axis=1).reset_index()
    out["nation"] = out.lad23_code.str[0]
    return out


def validate(daily, lad, sh):
    v = []

    def chk(name, cond):
        v.append(dict(check=name, passed=bool(cond)))

    at = lambda dt: daily[daily.date == pd.Timestamp(dt)]
    for dt in ["2020-04-15", "2020-11-15", "2021-02-01"]:
        x = at(dt)
        x = x[x.nation == "E"] if dt == "2020-11-15" else x
        chk(f"{dt}: every venue type except takeaways closed (1) in every LTLA",
            (x[[c for c in VENUES if c != "takeaways"]] == 1).all().all() and (x.takeaways == 0).all())
    x = at("2020-08-20")
    e = x[x.nation == "E"]
    chk("2020-08-20 England: only nightclubs closed, except Leicester gyms",
        (e.nightclubs == 1).all() and (e.loc[e.ltla20_code != LEICESTER, ["pubs_bars", "restaurants_cafes",
                                                                          "cinemas", "theatres_concert", "gyms"]] == 0).all().all()
        and e.loc[e.ltla20_code == LEICESTER, "gyms"].eq(1).all())
    w = x[x.nation == "W"]
    chk("2020-08-20 Wales: theatres and nightclubs closed, cinemas, gyms and hospitality open",
        (w.theatres_concert == 1).all() and (w.nightclubs == 1).all()
        and (w[["cinemas", "gyms", "pubs_bars", "restaurants_cafes"]] == 0).all().all())
    x = at("2020-10-20")
    chk("2020-10-20: Liverpool gyms closed, Manchester gyms open",
        x.loc[x.ltla20_code == "E08000012", "gyms"].eq(1).all() and x.loc[x.ltla20_code == "E08000003", "gyms"].eq(0).all())
    chk("2020-10-20: Very High pubs 0.5, Medium pubs 0",
        x.loc[x.state == "E_tier_oct_3", "pubs_bars"].eq(0.5).all() and x.loc[x.state == "E_tier_oct_1", "pubs_bars"].eq(0).all())
    x = at("2020-12-10")
    chk("2020-12-10 Tier 3: hospitality, cinemas, theatres closed, gyms open",
        (x.loc[x.state == "E_tier_dec_3", ["pubs_bars", "restaurants_cafes", "cinemas", "theatres_concert"]] == 1).all().all()
        and x.loc[x.state == "E_tier_dec_3", "gyms"].eq(0).all())
    chk("2020-12-10 Tier 2: pubs 0.5, restaurants and cinemas open",
        x.loc[x.state == "E_tier_dec_2", "pubs_bars"].eq(0.5).all()
        and (x.loc[x.state == "E_tier_dec_2", ["restaurants_cafes", "cinemas"]] == 0).all().all())
    x = at("2021-04-20")
    e, w = x[x.nation == "E"], x[x.nation == "W"]
    chk("2021-04-20 England Step 2: food 0.5, cinemas/theatres/nightclubs 1, gyms 0",
        (e[["pubs_bars", "restaurants_cafes"]] == 0.5).all().all() and (e[["cinemas", "theatres_concert", "nightclubs"]] == 1).all().all()
        and (e.gyms == 0).all())
    chk("2021-04-20 Wales: all six closed (outdoor hospitality from 26 Apr)",
        (w[[c for c in VENUES if c != "takeaways"]] == 1).all().all())
    x = at("2021-06-01")
    chk("2021-06-01: only nightclubs closed in both nations",
        (x.nightclubs == 1).all() and (x[[c for c in VENUES if c != "nightclubs"]] == 0).all().all())
    x = at("2021-07-25")
    chk("2021-07-25: England nightclubs open, Wales nightclubs closed",
        x.loc[x.nation == "E", "nightclubs"].eq(0).all() and x.loc[x.nation == "W", "nightclubs"].eq(1).all())
    chk("LAD panel has 318 LADs x 671 days", lad.lad23_code.nunique() == 318 and lad.date.nunique() == 671)
    m = sh.set_index("lad23_code")
    chk("main window: nightclubs closed every day in every LAD", np.allclose(m.closed_main_nightclubs, 1))
    chk("main window: takeaways never closed", np.allclose(m.closed_main_takeaways, 0))
    vv = pd.DataFrame(v)
    vv.to_csv(DATA / "v1_validation.csv", index=False)
    print(vv.to_string(index=False))
    assert vv.passed.all()


def main():
    check_rules()
    daily = build_daily()
    daily.to_csv(DATA / "v1_closure_daily_ltla20.csv.gz", index=False)
    lad = to_lad23(daily)
    lad.to_csv(DATA / "v1_closure_daily_lad23.csv.gz", index=False)
    sh = shares(lad)
    sh.to_csv(DATA / "v1_closure_shares_lad23.csv", index=False)
    validate(daily, lad, sh)
    pd.set_option("display.width", 200)
    for w in WINDOWS:
        cols = [f"closed_{w}_{v}" for v in VENUES]
        print(f"\nwindow {w}: share of days closed, by nation (mean, min, max over LADs)")
        print(sh.groupby("nation")[cols].agg(["mean", "min", "max"]).T.round(3).to_string())


if __name__ == "__main__":
    main()
