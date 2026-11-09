# Workflow

The full log of every decision, check, departure and blocked source is [`london-variety/ESTIMATION_NOTES.md`](../london-variety/ESTIMATION_NOTES.md), with further notes in each extension folder. The main steps are summarised below.

## Step 1. London design (October 2026)

- Action and reason: London boroughs were ranked by hospitality and leisure units per resident in 2019, and the net migration of residents aged 20 to 29 was compared with that of older residents of the same borough and year, so that shocks common to all ages in a borough are absorbed.
- Change made: The sample start was moved to the year to June 2016 after a positive 2015 coefficient was seen, and this choice is stated in the write-up.
- Check and result: The 2020 outflow and the 2022 return hold with student and hospitality-worker controls, and disappear once teleworkability and garden access are held fixed, since they correlate with amenity density at 0.82 and -0.73 across the 32 boroughs.
- Next step: Extend to England and Wales, where the controls vary more independently of density.

## Step 2. National plan and triple difference

- Action and reason: A pre-analysis plan was written and fixed with a SHA-256 checksum before national estimation, with decision rules for the triple difference, tier, Census and rent designs.
- Change made: After the registered measure (venues per resident) gave a null result, three further measures were tried and labelled as chosen after the registered results.
- Check and result: The national estimation code reproduces the London estimates exactly. With access to food venues the London pattern reappears nationally, and that measure correlates at about 0.9 with job and resident density.
- Next step: A design with variation in lost variety within districts.

## Step 3. Venue-mix design

- Action and reason: Forty-two closure rules for seven venue types were coded from the coronavirus regulations, each checked against its legal text, and combined with each small area's mix of venues.
- Change made: A second plan was fixed before any outcome was opened, after a stopping rule on the residual variation of the treatment was passed.
- Check and result: The headline was negative and significant, and the 2001 to 2011 placebo was larger and of opposite sign, so under the registered rule the variety channel was not supported.
- Next step: Test whether dense places recovered after reopening.

## Step 4. Recovery design

- Action and reason: A third plan was fixed after the population series were built and before any recovery regression, using the test of Davis and Weinstein.
- Change made: None. No departures were made from the venue-mix and recovery plans.
- Check and result: The registered verdict is inconclusive, and a placebo on 2015 to 2019 showed that access was already related to young-adult growth before the pandemic.
- Next step: Write-up.

## Step 5. Write-up

- Action and reason: The results were written into a full report and an eight-page supervision summary, with every figure taken from the notes or the estimation outputs.
- Change made: Sample sizes were checked against the code (7,262 small areas for the recovery design and 6,797 for the venue-mix design), and the check of the 2026 food register against 2019 Business Counts was recomputed on the 316 districts used elsewhere.
- Check and result: Both documents compile without LaTeX warnings.
- Next step: Supervision discussion.

## Tools / AI assistance

- Tool and request: Claude Code, an LLM coding assistant. The question, each source, measure, comparison group and test, and the interpretation of each result were set outside the tool, and Claude Code wrote and ran the Python and R for each step and reported the output back for the next decision.
- Contribution: Downloading and cleaning the data, coding the closure rules from legislation.gov.uk, building the access and variety-days-lost measures, estimating the event studies, triple differences and instrumental-variable regressions with the wild cluster bootstrap, and drafting the LaTeX for the report and summary, which was then revised by hand.
- Checks or changes: Decision rules were fixed in three checksummed pre-analysis plans before the relevant estimation, every judgement call was logged in the notes files as it arose, analyses chosen after the registered results are labelled in the write-up, and each figure in the write-up was checked against the estimation outputs.
