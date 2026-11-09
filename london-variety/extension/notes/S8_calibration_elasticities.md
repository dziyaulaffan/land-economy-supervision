# S8 calibration inputs: how location choice responds to local housing costs (literature check, no regressions)

Compiled 30 October 2026. Every number below was read from the paper itself: open PDFs were downloaded,
converted to text, and where the text layout was ambiguous the table page was rendered and read as an
image. No figure was taken from memory or from a secondary summary. Machine-readable version:
`extension/data/clean/s8_elasticities.csv` (26 rows, 21 verified and 5 TODO).

Target quantity: the percentage change in local population (or the annual net migration rate) per 1 per cent
rise in local rent. Sign convention: negative means population falls.

## 1. Usable verified estimates

| # | Paper (version read) | Location | Sample | Reported (SE) | Converted d ln pop / d ln rent |
|---|---|---|---|---|---|
| 1 | Diamond (2016 AER), author's final version, 27 Aug 2015 | Table 4A col 3 (preferred "full" model), Rent | US MSAs 1980-2000, non-college heads of household | -2.496 (0.451) | **-2.50** |
| 2 | same | Table 4A col 3, Rent | college heads of household | -1.312 (0.711) | **-1.31** |
| 3 | same | Table 4A col 4 (expenditure share estimated) | non-college | -2.944 (0.551) | -2.94 |
| 4 | same | Table 4A col 4 | college | -2.159 (0.821) | -2.16 |
| 5-12 | Piyapromdee (2021 REStud), accepted manuscript 1 Feb 2020 | Table 1 Panel II, "Implied Rent" (p.45) | US MSAs, Census 1980-2000 and ACS 2005-07 | natives: HS male -0.626, HS female -0.305, LS male -0.397, LS female -0.518; immigrants: HS male -1.305, HS female -1.301, LS male -0.442, LS female -1.067 (no SEs given) | same as reported |
| 13 | Suárez Serrato and Zidar (2016 AER), NBER WP 20289 rev2 | Table 6A col 1, sigma_W (text p.33) | US, 490 county groups, decadal changes 1980-2010 | sigma_W = 0.829 (0.282) | **-0.36** (= -0.30/0.829) |
| 14 | Monte, Redding and Rossi-Hansberg (2018 AER), NBER WP 21706 | Section 4 text, epsilon = 3.30; 1-alpha = 0.40 assumed | US counties, ACS 2006-10 commuting | epsilon = 3.30 (SE not in text) | -1.32 (residence choice, given workplace) |
| 15 | Ahlfeldt, Redding, Sturm and Wolf (2015 Econometrica), NBER WP 20354 | Table 5 col 3, epsilon; 1-beta = 0.25 (p.29) | Berlin city blocks, 1936/1986/2006 | epsilon = 6.694 (0.093) | -1.67 (block choice within a city) |
| 16 | Rabe and Taylor, ISER WP 2010-05 | Table 5, log house-price differential | Great Britain, BHPS 1993-2006, heads of household, inter-regional moves of 50 km or more | -0.468 (t = 2.53, SE about 0.185) | **-0.015 percentage points of population per year** (out-migration only) |
| 17 | same | Table 8 col 2, HD x private rental | private renters | -0.173 (t = 0.64) | -0.005 pp per year (not significant) |
| 18 | Rabe and Taylor, Bristol CMM slides (1993-2008) | "Migration estimates" slide, ln house prices | as above, longer panel | -0.30 (t = 1.39) | -0.009 pp per year (not significant) |

Verified, but not converted (they appear in the CSV with a blank conversion):

* Fajgelbaum, Morales, Suárez Serrato and Zidar (2019 REStud), NBER WP 21760 (revised Aug 2018), Table 1 row 3, col
  delta_W = 1 (the baseline named on p.27): epsilon_W = 1.73 (0.52), gamma_W = 0.16 (0.06). The introduction (p.2)
  translates this into a partial elasticity of state employment with respect to after-tax real wages of 1.1.
  Housing is not in the model (footnote 12) and real wages are deflated by the regional CPI. A rent elasticity
  would need an assumed housing share of that index (for example 0.3 x 1.1 = -0.33). It would also need a choice
  about whether the CPI deflator on public services counts too, so it is left blank.
* Bayer, McMillan, Murphy and Timmins (2016 Econometrica), NBER WP 17250, Table 3: financial moving-cost coefficient
  0.03515 (0.00148) minus 0.00008 (0.00001) x income, in $1000s. Note that the text on p.35 prints the constant as
  0.0315, which is inconsistent with the table. At mean income ($106.9k), the per-period marginal utility of
  income is 0.0266. Mean neighbourhood price is $429.1k (Table 1) and user cost is 5 per cent of price (about
  $21.5k a year). A static one-period choice elasticity would therefore be about -0.57. The model is dynamic, so a
  permanent price change enters every future period, and the true response to a permanent rent rise is not
  recoverable without the value function. Left blank.
* Ahlfeldt, Bald, Roth and Seidel (2020), CEP DP 1736, Appendix Table A9 col 4 (preferred): annual migration
  elasticity 0.295 (0.08) with respect to expected indirect utility, for German labour-market regions 1993-2017.
  Converting it needs the housing share and a dynamic simulation. Left blank.

## 2. Conversion notes, one per estimate type

* **Logit city choice (Diamond, Piyapromdee).** Both papers normalise the taste shock so the coefficient on log
  rent is itself d ln(population share)/d ln(rent) for a small city. The exact value is beta x (1 - s_j), where
  s_j is the group's national share in city j. Wages and amenities are held fixed, so this is a partial
  (demand-side) elasticity; the general-equilibrium population response is smaller once wages adjust. Piyapromdee's
  "implied rent" is the real-wage elasticity times a housing expenditure share. Diamond's numbers come from
  decadal changes, so they are long-run elasticities.
* **Dispersion parameter (Suárez Serrato and Zidar).** Utility is ln w - alpha ln r + amenities, with taste dispersion
  sigma_W. So d ln N / d ln r = -alpha / sigma_W. alpha = 0.30 is used, the housing share calibrated in the same
  column. A delta-method SE of about 0.12 is derived here and is not a reported figure.
* **Fréchet commuting models (Monte et al.; Ahlfeldt et al. 2015).** Residence probability is proportional to
  (rent^(1-alpha))^(-epsilon), so d ln residents / d ln rent = -epsilon x (1 - alpha), holding the workplace
  distribution fixed. These are choices of where to live given where people work. They fit within-London borough
  choice more closely than migration between local authorities, and they are much larger than migration
  elasticities.
* **Probit migration (Rabe and Taylor).** The regressor is log destination price minus log origin price, so a 1 per
  cent rise in origin prices raises the out-migration probability. The marginal effect is taken at the 1.4 per cent
  annual move rate (518 moves in 35,808 household-years, data section), giving phi(Phi^-1(0.014)) = 0.0357. The
  random-effects coefficient is rescaled by sqrt(1 - rho), with rho = 0.23. That gives 0.0147 per log point, so about **0.015
  percentage points more of the origin population leaving per year per 1 per cent higher house prices** (about a
  1 per cent rise in the out-migration rate). If in-migration fell by the same amount, the net figure would roughly
  double to -0.03 pp a year. This uses house prices, not rents, and covers only long-distance moves between
  11 regions.

## 3. TODO (excluded from the usable list)

1. Bayer, Ferreira and McMillan (2007 JPE), read as NBER WP 13236: the open version reports dollar willingness to pay
   only (Tables 6-7). The raw price coefficient was not found, or a choice elasticity; the published JPE was not
   opened.
2. Rabe and Taylor (2012, Oxford Bulletin of Economics and Statistics 74(6), doi:10.1111/j.1468-0084.2011.00682.x):
   paywalled. The published coefficient has not been seen. The 1993-2008 slides (row 18) suggest it may be smaller
   and not significant.
3. Murphy, Muellbauer and Cameron (2006), CEPR DP 5832, a British regional net- and gross-migration panel with house
   prices: no open full text was found. RePEc marks it restricted, and the Oxford WP 275 links are dead.
4. Cameron and Muellbauer (1998, Scottish Journal of Political Economy 45(4)): not opened.
5. Jackman and Savouri (1992, Economic Journal): not located.

## 4. Checked and found to contain no usable estimate

These papers were read in open versions. None reports an elasticity of population or migration with respect to
local housing costs, or a parameter that converts into one.

* Busso, Gregory and Kline (2013 AER; NBER WP 16096 and the published copy on Gregory's site).
* Kline and Moretti (2014, Annual Review; NBER WP 19659): theory only, with dispersion parameter s not estimated.
* Moretti (2011, Handbook; NBER WP 15947): theory and a survey. Footnote 15 notes that credible estimates of local
  labour supply are hard to obtain.
* Notowidigdo (2020 JOLE; NBER WP 17167): mobility-cost functions, with no rent elasticity.
* Monras (2018; IZA DP 8840): in-migration elasticities with respect to local economic shocks, not housing costs.
* Hornbeck and Moretti (NBER WP 24661): inverse elasticity of local labour supply with respect to earnings of 0.35
  (0.15 for college and 0.38 for high-school workers; p.26-27). This is with respect to nominal earnings, not rent,
  so it is not convertible without a model.
* Sá (2011, IZA DP 5893) and Xu (2025, Fiscal Studies): UK papers, but neither estimates a housing-cost elasticity of
  migration.
* No open UK study was found that estimates a rent (as opposed to house-price) elasticity of migration, or one
  specific to young adults. Rabe and Taylor (footnote 14) report that the 20-30 age group is *less* sensitive to
  house-price differentials than older groups, but they give no numbers.

## 5. Comparability caveats

* The estimates span three different margins. Choice of city or county over a decade gives -0.3 to -2.9.
  Residence choice given the workplace, within a city or a commuting network, gives -1.3 to -1.7. The annual
  probability of a long-distance move in Britain gives about -0.015 pp a year. They should not be averaged.
* The US structural estimates hold wages and amenities fixed. They are partial elasticities of demand for a small
  location, and the realised population response after wages and rents adjust is smaller.
* Several conversions rest on a housing share that the authors calibrated rather than estimated: 0.30 in
  Suárez Serrato and Zidar, 0.40 in Monte et al. and 0.25 in Ahlfeldt et al. (2015). Piyapromdee's figures embed her
  own expenditure shares.
* Version risk. Diamond was read from the August 2015 author version, whose Table 4 may be numbered differently in
  the AER (her 2013 dissertation version gives -0.953 for college and -2.832 for non-college in a different
  specification). Suárez Serrato and Zidar, Monte et al., Ahlfeldt et al. (2015), Fajgelbaum et al. and Bayer et al.
  (2016) were read as NBER working papers. Published numbers may differ.
* Piyapromdee gives no SEs for the implied rent elasticities. The Rabe and Taylor SEs are back-calculated from
  t-statistics.
* Only Rabe and Taylor are British, and they use house prices, regions and heads of household. None of the verified
  estimates is specific to young adults or to renters, apart from the insignificant private-renter interaction in
  Rabe and Taylor.
* All of these are model estimates with real uncertainty, not settled values. Standard errors are wide, especially
  for Diamond's college group (SE 0.71 on -1.31) and for Suárez Serrato and Zidar (SE 0.28 on 0.83).

## Sources opened

Diamond: https://web.stanford.edu/~diamondr/jmp_final_all_files.pdf (also the Harvard DASH dissertation). Piyapromdee:
https://discovery.ucl.ac.uk/10094994/1/Immigration_v43_Restud_R3.pdf. NBER working papers w13236, w15947, w16096,
w17167, w17250, w19659, w20289 (rev2), w20354, w21706, w21760 and w24661 at
https://www.nber.org/system/files/working_papers/wNNNNN/wNNNNN.pdf. BGK published copy:
https://users.ssc.wisc.edu/~jmgregory/EZ_AER.pdf. Monras: https://docs.iza.org/dp8840.pdf. Rabe and Taylor:
https://www.iser.essex.ac.uk/wp-content/uploads/files/working-papers/iser/2010-05.pdf and
https://bristol.ac.uk/media-library/sites/cmm/migrated/documents/birgitta-rabe.pdf. Ahlfeldt et al. 2020:
https://cep.lse.ac.uk/pubs/download/dp1736.pdf. Sá: https://docs.iza.org/dp5893.pdf. The published Suárez Serrato
and Zidar copy on zidar.princeton.edu returned a bot check and was not read.
