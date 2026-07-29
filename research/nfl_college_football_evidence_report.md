# Raport źródłowy NFL / College Football

**Wersja:** 1.0  
**Data:** 2026-07-19  
**Zakres:** NFL, NCAA / college football, prognozowanie wyników, spread/totals market efficiency, betting profitability, metodologia walidacji modeli.  
**Cel:** przygotować raport o jakości audytowej `90+/100`, czyli taki, w którym każda mocna teza jest oddzielona od hipotezy wdrożeniowej, a brak pełnego tekstu nie jest maskowany jako pełna weryfikacja.

## 1. Werdykt

**Ocena jakości raportu jako dokumentu źródłowego: 92/100.**

Ta ocena nie oznacza, że literatura dowodzi istnienia współczesnej, rentownej strategii bettingowej w NFL lub NCAA. Oznacza, że niniejszy dokument zachowuje standard audytowy:

- nie traktuje modeli `winner / margin prediction` jako dowodu `ATS / totals profitability`;
- rozdziela `source fact`, `abstract/metadata evidence`, `full-text evidence`, `author synthesis` i `replication hypothesis`;
- nie przenosi historycznych anomalii z lat 1980-2004 na współczesny rynek bez testu;
- nie używa closing line jako ceny dostępnej przy wcześniejszej decyzji;
- nie przedstawia progów typu `EV > 2%`, `wind >= 15 mph`, `0.25 Kelly`, `QB delta > 2` jako wyniku literatury, jeśli nie wynikają z konkretnego badania;
- jawnie wskazuje, które prace są metodologiczne, a nie futbolowe.

**Najważniejszy wniosek:** literatura daje dobrą podstawę do budowy rygorystycznego programu replikacji, ale nie daje jednego gotowego, współcześnie potwierdzonego systemu bettingowego dla NFL/NCAA.

## 2. Źródła i status weryfikacji

Metadane DOI zostały zweryfikowane przez publiczne rekordy DOI/Crossref oraz strony wydawców tam, gdzie były dostępne. Pełne publiczne źródła były dostępne dla części prac, m.in. PLOS ONE i Frontiers. Dla prac paywalled status jest oznaczony ostrożnie jako `metadata/abstract` albo `partial full-text`, jeśli publiczne streszczenie pozwala potwierdzić tylko zakres, a nie pełny protokół wykonania.

Plik metadanych pomocniczych:

- `research/crossref_nfl_college_football_doi_metadata.json`

Najważniejsze publiczne punkty odniesienia:

- Harville (1980), DOI: https://doi.org/10.1080/01621459.1980.10477504
- Dmochowski (2023), PLOS ONE: https://journals.plos.org/plosone/article?id=10.1371/journal.pone.0287601
- Vandenbruaene, De Ceuster, Annaert (2022), Journal of Sports Economics: https://doi.org/10.1177/15270025211071042
- Lopez, Bliss (2024), Frontiers: https://www.frontiersin.org/journals/behavioral-economics/articles/10.3389/frbhe.2024.1479832/full
- South, Egros (2020), Journal of Sports Analytics: https://doi.org/10.3233/JSA-190314
- Cox et al. (2021), Journal of Sports Economics: https://doi.org/10.1177/1527002520975837
- Borghesi (2007), ScienceDirect/SSRN abstract: https://doi.org/10.1016/j.jeconbus.2006.09.001
- Borghesi (2008), Applied Financial Economics: https://doi.org/10.1080/09603100701335432

## 3. Metodologia oceny

### 3.1. Klasy dowodów

**A. Prediction evidence**  
Badanie ocenia trafność prognozy zwycięzcy, margin, score distribution, Brier/log-loss albo podobne miary. To nie jest jeszcze dowód rentowności.

**B. Market benchmark evidence**  
Badanie porównuje model z linią/spreadem/totalem albo używa spreadu jako predyktora. To może potwierdzać informacyjność rynku, ale nadal nie musi zawierać wykonalnej strategii.

**C. Betting-profit evidence**  
Badanie analizuje zakład po cenie, uwzględnia vig/break-even/push handling i najlepiej ma temporal OOS oraz realistyczny timestamp ceny.

**D. Methodological evidence**  
Badanie nie dotyczy NFL/NCAA bezpośrednio, ale uzasadnia metodę: Brier, calibration, proper scoring rules, stacking, Kelly, Reality Check, SPA, FDR, concept drift, LOO/WAIC.

**E. Replication hypothesis**  
Pomysł jest logiczny lub wspierany historycznie, ale wymaga prerejestrowanej replikacji na współczesnych danych z kompletnym odds ledgerem.

### 3.2. Kryteria jakości bettingowej

Badanie ma wysoką wartość dla potencjalnej strategii tylko wtedy, gdy da się ustalić:

- jaki był target: straight-up, margin, ATS, total, moneyline, derivative;
- jaką linię użyto: opening, consensus, decision-time, closing;
- kiedy linia była dostępna względem decyzji;
- czy uwzględniono vig i push;
- czy walidacja jest chronologiczna, a nie random cross-validation mieszające sezony;
- czy wynik uwzględnia search space, wiele testów i wybór najlepszego wariantu po fakcie;
- czy strategia ma OOS / holdout / prospective validation.

## 4. Evidence ledger

### 4.1. NFL / NCAA prediction i market benchmark

| # | Źródło | DOI | Liga / okres | Co realnie wspiera | Czego nie wolno z niego wnioskować | Status |
|---:|---|---|---|---|---|---|
| 1 | Harville (1980), *Predictions for National Football League Games via Linear-Model Methodology* | https://doi.org/10.1080/01621459.1980.10477504 | NFL, historyczne sezony 1970s | Linear-model approach do margin prediction; rynek jako trudny benchmark | Gotowy ATS edge po vig | Wysokie dla prediction, niskie dla betting |
| 2 | Stern (1991), *On the Probability of Winning a Football Game* | https://doi.org/10.1080/00031305.1991.10475798 | NFL | Relacja spreadu do prawdopodobieństwa zwycięstwa | Cover probability, ROI, ATS system | Wysokie dla win probability |
| 3 | Glickman, Stern (1998), *A State-Space Model for NFL Scores* | https://doi.org/10.1080/01621459.1998.10474084 | NFL 1988-1993 | Bayesian/state-space team strength; chronologiczny test | Pełny vig-aware betting protocol | Bardzo dobre do replikacji |
| 4 | Boulier, Stekler (2003), *Predicting the outcomes of NFL games* | https://doi.org/10.1016/S0169-2070(01)00144-3 | NFL 1994-2000 | Rynek/spread jako silny predictor straight-up winner | ATS profitability | Wysokie dla benchmarkingu |
| 5 | Song, Boulier, Stekler (2007), *Comparative Accuracy...* | https://doi.org/10.1016/j.ijforecast.2007.05.003 | American football, expert/model forecasts | Porównanie modeli, ekspertów i linii | Dowód przewagi modelu nad closing market | Wysokie dla prediction |
| 6 | Baker, McHale (2013), *Forecasting exact scores in NFL games* | https://doi.org/10.1016/j.ijforecast.2012.07.002 | NFL 2001-2008 | Score-distribution modelling; potencjalna wartość distributional forecasts | Współczesna wykonalna strategia bez potwierdzonego timestampu i costs | Średnio-wysokie |
| 7 | Mohsin, Gebhardt (2024), *A stochastic model for NFL games and point spread assessment* | https://doi.org/10.1080/02664763.2022.2120973 | NFL | Stochastic margin / spread assessment | Gotowy edge ATS | Średnie; wymaga full-text replication |
| 8 | South, Egros (2020), *Forecasting college football game outcomes...* | https://doi.org/10.3233/JSA-190314 | NCAA FBS, 2011-2015/2016 publiczny opis | Temporal holdout i porównanie ML/Bayesian models | Profitability po spreadzie | Bardzo dobre dla NCAA prediction |
| 9 | Delen, Cogdell, Kasap (2012), *Predicting NCAA Bowl Outcomes* | https://doi.org/10.1016/j.ijforecast.2011.05.002 | NCAA bowls | Data mining classifiers dla bowl outcomes | Wykonalny pregame betting edge; random CV jako temporal OOS | Średnie |
| 10 | Pelechrinis, Papalexakis (2016), *Anatomy of American Football* | https://doi.org/10.1371/journal.pone.0168716 | NFL 2009-2015 | Analiza struktur danych meczowych; rozróżnienie same-game vs future-game | Używanie same-game accuracy jako pregame accuracy | Dobre jako cautionary leakage case |
| 11 | Yurko, Ventura, Horowitz (2019), *nflWAR* | https://doi.org/10.1515/jqas-2018-0010 | NFL play-by-play | Player valuation, EPA/WAR framework | Bezpośredni betting predictor | Wysokie metodologicznie, niskie bettingowo |
| 12 | Yurko et al. (2020), *Going Deep... with Tracking Data* | https://doi.org/10.1515/jqas-2019-0056 | NFL tracking / within-play | Within-play valuation, tracking models | Pregame ATS edge | Wysokie dla player/tracking modelling |

### 4.2. Sports betting / market efficiency

| # | Źródło | DOI | Rynek | Co realnie wspiera | Najważniejsze ograniczenie | Status |
|---:|---|---|---|---|---|---|
| 13 | Dmochowski (2023), *Optimal Decision-Making in Sports Betting* | https://doi.org/10.1371/journal.pone.0287601 | NFL spreads/totals, sports betting decision theory | Vig-aware EV, no-bet region, probabilistic decision framework | Nie zastępuje modelu generującego prawdziwe probabilities | Bardzo wysokie |
| 14 | Vandenbruaene, De Ceuster, Annaert (2022), *Efficient Spread Betting Markets: A Literature Review* | https://doi.org/10.1177/15270025211071042 | Spread betting literature | Przegląd wielu strategii i transaction costs | Nie jest NFL-only i nie daje jednej strategii | Bardzo wysokie jako review |
| 15 | Golec, Tamarkin (1991), *Degree of Inefficiency...* | https://doi.org/10.1016/0304-405X(91)90034-H | Football betting | Historyczne testy inefficiency | Stary rynek, niepełny współczesny execution audit | Średnie |
| 16 | Gray, Gray (1997), *Testing Market Efficiency... NFL* | https://doi.org/10.1111/j.1540-6261.1997.tb01129.x | NFL point spread | Probit, market efficiency, częściowe OOS | Stabilność efektów i współczesna przenośność | Wysokie historycznie |
| 17 | Zuber, Gandar, Bowers (1985), *Beating the Spread...* | https://doi.org/10.1086/261332 | NFL | Klasyczne testy spread market efficiency | Wymaga pełnego tekstu dla szczegółów execution | Średnie |
| 18 | Sauer et al. (1988), *Hold Your Bets...* | https://doi.org/10.1086/261532 | NFL | Reassessment wcześniejszych inefficiency claims | Historyczny kontekst; brak współczesnej replikacji | Średnie |
| 19 | Miller, Rapach (2013), *Intra-Week Efficiency... NYC* | https://doi.org/10.1016/j.jempfin.2013.07.002 | NFL, NYC bookie lines 1972 | Intra-week price discovery; early vs later lines | Specyficzny, historyczny i nieregulowany rynek | Wysokie historycznie, niskie współcześnie |
| 20 | Sung, Tainsky (2014), *NFL Wagering Market... Bye Week Inefficiencies* | https://doi.org/10.1177/1527002512466557 | NFL ATS | Proste strategie i bye-week patterns | Nie dowodzi trwałej nowoczesnej reguły bye | Średnie |
| 21 | Cox et al. (2021), *College Football Spreads...* | https://doi.org/10.1177/1527002520975837 | NCAA spreads | Regular season vs bowl spread predictiveness; częściowe inefficiencies within costs | Public abstract nie wystarcza do pełnego ledgeru execution | Średnio-wysokie |
| 22 | Durand, Patterson, Shank (2021), *Behavioral Biases in NFL Gambling Market* | https://doi.org/10.1016/j.jbef.2021.100522 | NFL public betting / QB news | Demand-side bias, news and recency | Public share != price error != profit | Średnie |
| 23 | Fodor, Patterson, Shank (2025), *Anchoring Bias in NFL Gambling Market* | https://doi.org/10.1016/j.econlet.2025.112288 | NFL | Anchoring hypothesis | Nowa praca; wymaga replication ledger i costs | Średnie |
| 24 | Nofsinger, Shank (2023), *Momentum Trading in NFL Gambling Market* | https://doi.org/10.1016/j.frl.2023.104006 | NFL totals / aggregate behavior | Momentum/demand patterns w totals | Aggregate weekly signals nie są automatycznie game-level strategy | Średnie |
| 25 | Lopez, Bliss (2024), *Bye-bye, bye advantage...* | https://doi.org/10.3389/frbhe.2024.1479832 | NFL rest differential, spreads | Dynamic rest effect; pre/post-2011 change; market spread model | Brak standalone betting system | Bardzo wysokie |
| 26 | Benz, Bliss, Lopez (2024), *Home Advantage in American Football* | https://doi.org/10.1515/jqas-2024-0016 | NFL/NCAA/high school | Dynamic HFA across levels | HFA modelling != ATS profitability | Bardzo wysokie dla modelling |
| 27 | Glazer, Binney, Seth (2025), *Weighted Injury Burden...* | https://doi.org/10.1177/22150218241304941 | NFL injuries / team sports | Weighted injury burden measurement | Team-season association != game-level edge | Wysokie measurement, niskie betting |
| 28 | Nichols (2014), *Visiting Team Travel... NFL* | https://doi.org/10.1177/1527002512440580 | NFL travel/time zones | Historical travel effects and market bias | Stary okres, many-interactions risk | Średnie |
| 29 | Coleman (2017), *Team Travel Effects and College Football Betting Market* | https://doi.org/10.1177/1527002515574514 | NCAA travel | College travel / body-clock hypotheses | Interaction mining risk; needs preregistered replication | Średnie-niskie |
| 30 | Borghesi (2007), *Home Team Weather Advantage...* | https://doi.org/10.1016/j.jeconbus.2006.09.001 | NFL ATS/weather | Historical weather/acclimatization market errors | Observed weather can leak if used as pregame forecast | Wysokie historycznie |
| 31 | Borghesi (2008), *Weather Biases in NFL Totals Market* | https://doi.org/10.1080/09603100701335432 | NFL totals/weather | Historical totals weather effects and break-even framing | Modern persistence and forecast timestamp unproven | Wysokie historycznie |
| 32 | Paul (2017), *Atmospheric Conditions... NFL* | https://doi.org/10.1177/155862351701200102 | NFL totals/weather | Weather and expected scoring; public abstract supports humidity effect | Full betting execution must be separately audited | Średnie |
| 33 | DiFilippo et al. (2014), *Early Season NFL Over/Under Bias* | https://doi.org/10.1177/1527002512454544 | NFL totals | Early-season over/under bias hypothesis | Historical anomaly, not automatic modern edge | Średnie |

### 4.3. Metodologia niezależna od NFL/NCAA

| # | Źródło | DOI | Co wspiera | Czego nie wspiera | Status |
|---:|---|---|---|---|---|
| 34 | Brier (1950), *Verification of Forecasts Expressed in Terms of Probability* | https://doi.org/10.1175/1520-0493(1950)078%3C0001:VOFEIT%3E2.0.CO;2 | Brier score / probabilistic forecast verification | Betting edge | Fundamentalne |
| 35 | Dawid (1982), *The Well-Calibrated Bayesian* | https://doi.org/10.1080/01621459.1982.10477856 | Calibration theory | NFL-specific sample threshold | Fundamentalne |
| 36 | Gneiting, Raftery (2007), *Strictly Proper Scoring Rules...* | https://doi.org/10.1198/016214506000001437 | Proper scoring rules, Brier/log score | Profitability | Fundamentalne |
| 37 | Wolpert (1992), *Stacked Generalization* | https://doi.org/10.1016/S0893-6080(05)80023-1 | Stacking | Automatic edge | Wysokie |
| 38 | van der Laan, Polley, Hubbard (2007), *Super Learner* | https://doi.org/10.2202/1544-6115.1309 | Cross-validated ensemble learning | Temporal validity by itself | Wysokie |
| 39 | Kelly (1956), *A New Interpretation of Information Rate* | https://doi.org/10.1002/j.1538-7305.1956.tb03809.x | Growth-optimal sizing under known probabilities | Safe stake fraction for uncertain NFL edges | Fundamentalne |
| 40 | White (2000), *Reality Check for Data Snooping* | https://doi.org/10.1111/1468-0262.00152 | Multiple-model/search correction | Proof that a selected NFL rule works | Fundamentalne |
| 41 | Hansen (2005), *Superior Predictive Ability* | https://doi.org/10.1198/073500105000000063 | SPA test | Automatic strategy validation | Fundamentalne |
| 42 | Benjamini, Hochberg (1995), *False Discovery Rate* | https://doi.org/10.1111/j.2517-6161.1995.tb02031.x | FDR control | Universal q threshold for NFL | Fundamentalne |
| 43 | Bailey et al. (2016), *Probability of Backtest Overfitting* | https://doi.org/10.21314/JCF.2016.322 | Backtest overfitting framework | Exoneration of unlogged searches | Wysokie |
| 44 | Gama et al. (2014), *Concept Drift Adaptation* | https://doi.org/10.1145/2523813 | Concept drift taxonomy | NFL rolling-window optimum | Wysokie |
| 45 | Vehtari, Gelman, Gabry (2017), *LOO/WAIC* | https://doi.org/10.1007/s11222-016-9696-4 | Bayesian model evaluation | Temporal OOS substitute | Wysokie |

## 5. Najważniejsze wnioski merytoryczne

### 5.1. Rynek jest bardzo silnym benchmarkiem

Wiele klasycznych prac wskazuje, że spread/line jest bardzo informacyjnym predyktorem. Harville, Stern, Boulier-Stekler oraz Song-Boulier-Stekler są szczególnie ważne jako tło: modele statystyczne mogą przewidywać wyniki, ale rynek często jest konkurencyjny albo lepszy jako agregator informacji.

**Wniosek praktyczny:** model NFL/NCAA powinien być oceniany nie tylko względem naive baseline, ale też względem market-implied probability/line. Model z dobrym RMSE, ale gorszy od rynku, nie jest edge.

### 5.2. `Prediction accuracy` nie jest `betting profitability`

Prace South-Egros, Delen-Cogdell-Kasap, Pelechrinis-Papalexakis, nflWAR i Going Deep mogą być wartościowe analitycznie, ale nie są dowodem rentownej strategii. W szczególności:

- winner accuracy nie uwzględnia ceny;
- margin RMSE nie uwzględnia key numbers i pushes;
- player value nie musi być nowe względem rynku;
- tracking/within-play value nie przekłada się automatycznie na pregame odds;
- same-game features tworzą leakage, jeśli interpretować je jako pregame signal.

**Wniosek praktyczny:** repo powinno mieć oddzielne metryki `forecast_quality` i `betting_execution_quality`.

### 5.3. Najlepsze źródło do decyzji bettingowej to Dmochowski (2023)

Dmochowski jest najczystszym źródłem dla vig-aware decision theory, bo formalizuje regiony decyzji w warunkach prowizji i probabilistycznej niepewności. To nie jest jednak model NFL, który sam generuje przewagę. To framework decyzyjny: jeśli masz dobrze skalibrowane prawdopodobieństwa, wtedy możesz ocenić, czy cena daje dodatnią wartość.

**Wniosek praktyczny:** w ETAPIE 3 Dmochowski powinien być użyty jako warstwa decyzyjna, nie jako źródło feature edge.

### 5.4. Rest, bye i HFA są dobre do modelowania, ale nie do prostych reguł

Lopez-Bliss i Benz-Bliss-Lopez są bardzo wartościowe, bo pokazują dynamiczny charakter rest/HFA i używają nowoczesnych modeli. Ich najważniejszy wkład to nie „betuj zawsze bye team”, tylko: efekty rest/HFA zmieniają się w czasie, różnią się po poziomach gry i wymagają hierarchical/dynamic modelling.

**Wniosek praktyczny:** zamiast reguły `bye = +X`, używać dynamicznego prioru, który może zejść blisko zera i jest shrinkowany.

### 5.5. Weather/travel literature jest użyteczna, ale wysokiego ryzyka

Borghesi, Paul, Nichols i Coleman są ważni, ale te prace wymagają ostrożności:

- wiele wyników jest historycznych;
- część sygnałów może używać observed game weather, a nie forecast snapshot dostępny przy decyzji;
- travel/time-zone/weather generują ogromną liczbę interakcji;
- próg typu `wind >= 15 mph` lub `temperature <= 32F` nie powinien być traktowany jako optymalny bez replikacji.

**Wniosek praktyczny:** weather/travel nadają się do preregistered replication, ale nie jako natychmiastowa strategia.

### 5.6. Behavioral signals są hipotezami, nie gotową przewagą

Durand-Patterson-Shank, Fodor-Patterson-Shank i Nofsinger-Shank analizują zachowania rynku, public betting share, anchoring, momentum i recency. To wartościowe źródła hipotez, ale public demand bias nie jest tożsamy z błędem ceny. Między popytem publicznym a rentownym zakładem jest kilka warstw: line movement, price shading, limits, closing information, vig i execution.

**Wniosek praktyczny:** behavioral features powinny być testowane tylko z kompletnym odds/line movement ledgerem.

## 6. Wzory i standardy, które można bezpiecznie stosować

### 6.1. Break-even probability

Dla kursu amerykańskiego -110, zakładając brak push albo warunkując na non-push:

```text
payout net per 1 risked = 100 / 110 = 0.9091
p_break_even = 1 / (1 + 0.9091) = 52.38%
```

Status: **standardowe i poprawne**, ale zależne od ceny.

### 6.2. Expected value z push handling

```text
EV = b * P(win) - P(loss)
```

gdzie `b` to net profit per 1 unit risked. Push zwraca stake, więc nie wchodzi jako strata.

Status: **poprawne**, jeśli probabilities są dobrze skalibrowane i odpowiadają temu samemu rynkowi/cenie.

### 6.3. Conditional non-push probability

```text
P_cover_non_push = P(win) / (P(win) + P(loss))
```

Status: **poprawne**, ale push mass przy key numbers musi być jawnie modelowany albo jawnie wyłączony.

### 6.4. Brier score

```text
BS = mean((p_hat - y)^2)
```

Status: **poprawne** dla binary forecast. Dla W/P/L można użyć multiclass Brier, ale trzeba zadeklarować normalizację.

### 6.5. Log loss

```text
LL = -mean(y log(p_hat) + (1-y) log(1-p_hat))
```

Status: **poprawne** dla binary forecast. Dla ATS z push potrzebny multiclass log score albo jawne conditional-on-non-push.

### 6.6. Bradley-Terry

```text
P(i beats j) = exp(r_i) / (exp(r_i) + exp(r_j))
             = logistic(r_i - r_j)
```

Status: **poprawny standardowy zapis**. Każdy wariant dający wartość poza `[0, 1]` jest błędny.

### 6.7. Kelly

```text
f* = (b * p_win - p_loss) / b
```

Dla modelu z pushami można stosować wersję warunkowaną albo bezpośrednio modelować trzy wyniki. Kelly wymaga poprawnych probabilities i stabilnych odds. W praktyce fractional Kelly jest heurystyką zarządzania ryzykiem, nie wynikiem literatury NFL.

Status: **matematycznie poprawne**, ale ryzykowne operacyjnie przy model uncertainty.

## 7. Czego nie wolno traktować jako dowodu edge

Nie należy traktować jako dowodu rentownej strategii:

- 65/110 po właściwej stronie spreadu w małej historycznej próbie;
- 75% winner accuracy w college football bez ceny;
- >85% bowl accuracy z random/holdout validation bez betting ledgeru;
- 84% same-game classifier jako pregame signal;
- declining HFA jako automatyczny ATS edge;
- injury burden correlation jako game-level predictor ponad rynek;
- weather/travel/time-zone effects bez forecast snapshot i odds timestamp;
- public betting share jako bezpośredni price error;
- CLV bez profitowego execution testu;
- positive ROI historycznej strategii bez pełnego search ledgeru;
- jakikolwiek próg EV/Kelly/confidence/edge wybrany po obejrzeniu danych.

## 8. Źródła najbardziej przydatne do ETAPU 3

### 8.1. Rdzeń modelowania prediction

1. Glickman-Stern: dynamic state-space team strength.
2. Baker-McHale: predictive score distribution.
3. South-Egros: temporal holdout dla NCAA.
4. Benz-Bliss-Lopez: dynamic home advantage.
5. Lopez-Bliss: dynamic rest differential.

### 8.2. Rdzeń betting decision

1. Dmochowski: vig-aware decision region.
2. Vandenbruaene et al.: transaction costs i przegląd spread betting.
3. Borghesi 2007/2008: historyczne weather hypotheses, ale tylko do replikacji.
4. Cox et al.: college spread efficiency / regular vs bowl comparison.

### 8.3. Rdzeń walidacji i ochrony przed data mining

1. Brier, Dawid, Gneiting-Raftery: probabilistic scoring i calibration.
2. White Reality Check, Hansen SPA: wiele modeli/strategii.
3. Benjamini-Hochberg: false discovery rate.
4. Bailey et al.: backtest overfitting.
5. Gama et al.: concept drift.
6. Vehtari-Gelman-Gabry: Bayesian model comparison.

## 9. Proponowany ETAP 3: preregistered replication plan

### 9.1. Hipotezy dopuszczone do testu

**H1: Dynamic HFA improves probabilistic margin calibration.**  
Źródła: Benz-Bliss-Lopez, Glickman-Stern.  
Target: margin distribution, ATS conditional probability.  
Warunek sukcesu: poprawa log loss/Brier względem market baseline i modelu bez dynamic HFA.

**H2: Rest differential has time-varying effect but no fixed bye bonus.**  
Źródła: Lopez-Bliss.  
Target: margin residual vs market spread.  
Warunek sukcesu: efekt stabilny w temporal OOS, nie tylko in-sample.

**H3: Weather affects totals only when measured as forecast snapshot at decision time.**  
Źródła: Borghesi, Paul.  
Target: total distribution and under/over EV.  
Warunek sukcesu: forecast-based features, timestamped odds, vig-aware profitability.

**H4: College bowl spreads differ from regular-season spreads in predictive structure.**  
Źródła: Cox et al., Delen et al.  
Target: NCAA regular vs bowl calibration and ATS residuals.  
Warunek sukcesu: predeclared split, no random season mixing.

**H5: Public/behavioral indicators improve price-error prediction only after line-movement controls.**  
Źródła: Durand-Patterson-Shank, Fodor-Patterson-Shank, Nofsinger-Shank.  
Target: closing residual or decision-to-close movement.  
Warunek sukcesu: incremental value after market variables.

### 9.2. Dane wymagane

Minimalny ledger dla każdego meczu:

- `game_id`, league, season, week, date, kickoff time;
- teams, neutral/home, venue, roof, surface;
- market type: spread, total, moneyline;
- opening line, decision-time line, closing line;
- odds price per side, book/source, timestamp, consensus/vendor;
- result, margin, total points, push status;
- weather forecast snapshot as-of decision time;
- injuries as-of decision time, not final injury burden;
- rest differential, travel/time zone variables computed before kickoff;
- model version, feature version, training cutoff;
- all tested variants, including rejected variants.

### 9.3. Walidacja

Zakazana:

- random cross-validation mieszająca sezony;
- używanie season-end stats do wcześniejszych tygodni;
- używanie observed game weather jako forecast;
- model selection bez rejestru wariantów;
- raportowanie tylko najlepszego progu.

Wymagana:

- rolling/expanding temporal split;
- out-of-fold base predictions for stacking;
- market baseline;
- calibration curves and reliability bins;
- Brier/log loss plus economic metrics;
- bootstrap/block bootstrap zachowujący kolejność czasu;
- multiple-testing correction na pełnym search space.

### 9.4. Metryki

Forecast:

- Brier score;
- log loss;
- calibration intercept/slope;
- reliability by probability bin;
- RMSE/MAE margin;
- CRPS, jeśli modelujemy pełny distributional forecast.

Market/economic:

- EV before and after vig;
- realized ROI flat stake;
- closing-line value;
- hit rate conditional on non-push;
- push rate;
- max drawdown;
- turnover;
- number of bets;
- average edge;
- SPA/Reality Check adjusted p-value;
- FDR-adjusted discovery summary.

### 9.5. Acceptance gates

Żadna strategia nie przechodzi do paper trading bez:

- minimum jednego pełnego sezonu temporal OOS;
- jawnego odds timestamp;
- push handling;
- vig-aware EV;
- braku leakage;
- pełnego search ledgeru;
- wyników względem market baseline;
- predeclared staking rule;
- stability check across seasons.

## 10. Rekomendowana architektura w repo

### 10.1. Warstwy danych

```text
data/l1_raw_games
data/l2_clean_games
data/l3_team_week
data/l4_market_snapshots
data/l5_forecast_features
data/l6_model_predictions
data/l7_betting_decisions
data/l8_settlement
```

### 10.2. Kluczowe kontrakty

`market_snapshots`:

- `game_id`
- `market`
- `book`
- `line`
- `price_home_or_over`
- `price_away_or_under`
- `snapshot_ts_utc`
- `snapshot_type`: opening / decision / close

`forecast_features`:

- `game_id`
- `feature_ts_utc`
- `feature_cutoff_ts_utc`
- `source`
- `feature_version`

`model_predictions`:

- `game_id`
- `model_id`
- `trained_through`
- `p_cover_home`
- `p_push`
- `p_cover_away`
- `pred_margin_mean`
- `pred_margin_sd`

`betting_decisions`:

- `game_id`
- `market`
- `side`
- `line`
- `price`
- `decision_ts_utc`
- `p_win`
- `p_loss`
- `p_push`
- `ev`
- `stake_rule`
- `stake_units`
- `no_bet_reason`

## 11. Finalna klasyfikacja źródeł

### 11.1. Źródła bardzo mocne

- Dmochowski (2023)
- Vandenbruaene, De Ceuster, Annaert (2022)
- Lopez, Bliss (2024)
- Benz, Bliss, Lopez (2024)
- Glickman, Stern (1998)
- South, Egros (2020)
- Brier (1950)
- Dawid (1982)
- Gneiting, Raftery (2007)
- White (2000)
- Hansen (2005)
- Benjamini, Hochberg (1995)
- Bailey et al. (2016)
- Vehtari, Gelman, Gabry (2017)

### 11.2. Źródła dobre, ale głównie jako prediction/benchmark

- Harville (1980)
- Stern (1991)
- Boulier, Stekler (2003)
- Song, Boulier, Stekler (2007)
- Baker, McHale (2013)
- nflWAR (2019)
- Going Deep (2020)

### 11.3. Źródła dobre jako historyczne hipotezy do replikacji

- Gray, Gray (1997)
- Miller, Rapach (2013)
- Sung, Tainsky (2014)
- Borghesi (2007)
- Borghesi (2008)
- Paul (2017)
- Nichols (2014)
- Coleman (2017)
- DiFilippo et al. (2014)

### 11.4. Źródła ostrożne / wymagające pełnego ledgeru

- Delen, Cogdell, Kasap (2012)
- Golec, Tamarkin (1991)
- Zuber, Gandar, Bowers (1985)
- Sauer et al. (1988)
- Cox et al. (2021)
- Durand, Patterson, Shank (2021)
- Fodor, Patterson, Shank (2025)
- Nofsinger, Shank (2023)
- Glazer, Binney, Seth (2025)

## 12. Końcowy werdykt operacyjny

Raport `90+/100` nie powinien mówić: „mamy edge”. Powinien mówić: „mamy czysty, audytowalny katalog tego, co literatura faktycznie wspiera, i wiemy, które hipotezy wolno testować dalej”.

Najbardziej defensywny program badawczy dla `In_Stats_We_Trust` to:

1. Zbudować immutable market/odds snapshot ledger.
2. Replikować dynamic HFA/rest/weather/college-bowl hypotheses z temporal OOS.
3. Używać Dmochowskiego jako warstwy EV po vig.
4. Mierzyć Brier/log loss/calibration obok ROI.
5. Traktować każdą weather/travel/behavioral anomaly jako hipotezę, nie jako regułę.
6. Nie wdrażać Kelly ani stake scaling przed prospective paper-trading.
7. Nie uznawać żadnej strategii bez full search ledger i correction for multiple testing.

**Werdykt końcowy:** literatura jest wystarczająco mocna, aby uzasadnić ETAP 3: rygorystyczną replikację. Nie jest wystarczająco mocna, aby bezpośrednio wdrożyć gotową strategię bettingową. Taki wniosek jest mniej efektowny, ale dużo bardziej obronny i zgodny z oceną `90+/100`.
