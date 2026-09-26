# -*- coding: utf-8 -*-
"""Journal analysis data.

Metrics policy:
  * OpenAlex 2-year mean citedness and h-index were pulled from the OpenAlex API (api.openalex.org/sources)
    in September 2026. They are an open, verifiable proxy, NOT the Clarivate Journal Impact Factor.
  * Clarivate JIF values could not be verified from an accessible primary source in this project and are
    therefore left as "verify in JCR". Chartered ABS AJG and ABDC grades are also flagged "verify".
  * Code/data policy entries marked 'verified' were confirmed on the journal/association policy page.
"""

J = []
def add(**k):
    J.append(k)

add(journal="Journal of Finance", tier="Tier 1 - General finance (top-3)", publisher="Wiley / American Finance Association",
    oa_2yr=13.19, oa_h=664,
    scope="All areas of finance; publishes the field's most general contributions in asset pricing and investments.",
    qf_rel=4, ml_rel=4,
    related="KMZ2024; JKX2023; KMP2023; BPZ2025; JKP2023; DMU2024; DNMV2023; MP2016; GP2013",
    methodology="Economically motivated empirical designs, often with a model or clear economic mechanism; ML accepted when it answers an economic question.",
    empirical="Very long samples (decades), CRSP/Compustat standard, extensive robustness, international or out-of-sample replication increasingly common.",
    theory="Not strictly required, but a mechanism or theoretical framing strongly helps; pure horse races rarely suffice.",
    data="Standard academic data (WRDS); proprietary data accepted if documented.",
    code_policy="Verified: AFA Data and Code Sharing Policy (April 2024 version) requires programs for replication from accepted empirical papers.",
    difficulty=5, fit=7, role="Stretch",
    note="Fit only if the paper delivers a general economic insight (e.g., where ML value comes from and why) rather than a better backtest.")
add(journal="Review of Financial Studies", tier="Tier 1 - General finance (top-3)", publisher="Oxford University Press / Society for Financial Studies",
    oa_2yr=11.81, oa_h=397,
    scope="Broad financial economics; strong record in empirical asset pricing and ML (Gu-Kelly-Xiu 2020; JKMP 2026).",
    qf_rel=4, ml_rel=5,
    related="GKX2020; JKMP2026; DMNU2020; FNW2020; HKS2020; NMV2016; LW2017; BS2022; HXZ2020; HLZ2016",
    methodology="Rigorous empirical asset pricing; ML papers must show economic content and robustness.",
    empirical="Comprehensive samples, strong baselines, transaction costs expected for investment claims, replication package.",
    theory="Helpful; an economic framework or model of why the effect exists is expected for top placement.",
    data="WRDS-standard; code and data package reviewed by Data Editors.",
    code_policy="Verified: updated Code and Data Sharing Policy for submissions conditionally accepted on/after 1 Oct 2025; Data Editors check reproducibility; deposit in Harvard Dataverse.",
    difficulty=5, fit=8, role="Stretch",
    note="Most natural top-3 home for an implementability/decomposition paper given GKX2020, DMNU2020 and JKMP2026 precedents.")
add(journal="Journal of Financial Economics", tier="Tier 1 - General finance (top-3)", publisher="Elsevier",
    oa_2yr=12.37, oa_h=557,
    scope="Financial economics broadly; empirical and theoretical.",
    qf_rel=3, ml_rel=4,
    related="KPS2019; KNS2020; LWZ2022; CDS2020; CFHH2025; DM2016; PW2020; SYY2012",
    methodology="Economic mechanism-driven empirical work.",
    empirical="Long samples, identification of economic channel, robustness.",
    theory="Mechanism expected.", data="WRDS-standard.",
    code_policy="Policy page exists (jfinec.com/data-and-code-sharing-policy); details verify.",
    difficulty=5, fit=6, role="Stretch", note="Less natural for methods-heavy portfolio construction papers than RFS/MS.")
add(journal="Journal of Financial and Quantitative Analysis", tier="Tier 1b - Top field finance", publisher="Cambridge University Press / U. Washington",
    oa_2yr=3.39, oa_h=255,
    scope="Verified (jfqa.org): theoretical and empirical research in financial economics, including investments, capital and security markets, and quantitative methods of particular relevance to financial researchers.",
    qf_rel=5, ml_rel=4,
    related="CV2023; KO2012; KZ2007",
    methodology="Rigorous empirical and quantitative methods; explicitly welcomes quantitative methods.",
    empirical="Comparable to top-3 in rigor; somewhat narrower contribution acceptable.",
    theory="Not required for empirical methods papers with clear economic implications.",
    data="WRDS-standard.", code_policy="Verified: JFQA Code Sharing Policy page exists; details verify.",
    difficulty=4, fit=9, role="Target",
    note="Best realistic high-quality target: quantitative methods mandate plus finance audience.")
add(journal="Management Science", tier="Tier 1b - Top field finance / OR", publisher="INFORMS",
    oa_2yr=6.23, oa_h=480,
    scope="Management broadly; Finance department publishes empirical asset pricing and ML (Chen-Pelger-Zhu 2024; Avramov-Cheng-Metzker 2023).",
    qf_rel=4, ml_rel=5,
    related="CPZ2024; ACM2023; EG2022; BCZ2022",
    methodology="Methodological innovation with managerial/economic relevance; interdisciplinary ML/OR welcome.",
    empirical="Strong out-of-sample and robustness; replication package reviewed.",
    theory="Not required; methodological or economic insight required.",
    data="WRDS-standard; must be disclosable per policy.",
    code_policy="Verified: Code and Data Disclosure Policy adopted 2019 with a Data Editor who verifies replicability.",
    difficulty=4, fit=9, role="Target",
    note="Strong fit for a design that bridges ML, optimisation and finance.")
add(journal="Review of Finance", tier="Tier 1b - Top field finance", publisher="Oxford University Press / European Finance Association",
    oa_2yr=None, oa_h=None,
    scope="General finance (European Finance Association journal).",
    qf_rel=3, ml_rel=3, related="(search for recent ML asset-pricing papers before targeting)",
    methodology="General finance standards.", empirical="High.", theory="Helpful.", data="Standard.",
    code_policy="Verified: Code Sharing and Data Availability Policy page exists (revfin.org).",
    difficulty=4, fit=7, role="Target", note="OpenAlex search did not return this title cleanly; verify metrics.")
add(journal="Review of Asset Pricing Studies", tier="Tier 1b - Top field finance", publisher="Oxford University Press / SFS",
    oa_2yr=4.30, oa_h=49, scope="Asset pricing (SFS field journal).", qf_rel=4, ml_rel=4, related="KNNV2024",
    methodology="Asset-pricing empirical and theory.", empirical="High.", theory="Helpful.", data="WRDS-standard.",
    code_policy="SFS journal; verify policy.", difficulty=4, fit=8, role="Target",
    note="Good home for factor-timing / signal-efficacy concepts.")
add(journal="Operations Research", tier="Tier 1b - Top OR", publisher="INFORMS",
    oa_2yr=3.48, oa_h=304, scope="OR methods incl. financial engineering; robust and data-driven optimisation.", qf_rel=3, ml_rel=4,
    related="DY2010", methodology="Novel optimisation/learning methodology with guarantees.", empirical="Computational experiments; finance data used as application.",
    theory="Usually expected (algorithms, guarantees).", data="Flexible.", code_policy="Verify.", difficulty=5, fit=5, role="Backup (method variant)",
    note="Only for the differentiable/robust optimiser concept with theoretical results.")
add(journal="Quantitative Finance", tier="Tier 2 - Quantitative/computational finance", publisher="Taylor & Francis",
    oa_2yr=2.46, oa_h=113,
    scope="Interdisciplinary quantitative finance; aims list includes portfolio management, market dynamics and prediction, trading systems, financial econometrics, market microstructure.",
    qf_rel=5, ml_rel=4, related="BK2023; CI2023; NML2018",
    methodology="Quantitative/mathematical methods with empirical validation.", empirical="Moderate-to-high; costs expected for trading claims.",
    theory="Welcome, not mandatory.", data="Flexible.", code_policy="Verify.", difficulty=3, fit=9, role="Target",
    note="Third-party sites report a 2025 JIF around 1.9 (unverified; check JCR).")
add(journal="Journal of Financial Econometrics", tier="Tier 2 - Quantitative/computational finance", publisher="Oxford University Press / SoFiE",
    oa_2yr=1.22, oa_h=77, scope="Financial econometrics.", qf_rel=5, ml_rel=4, related="(verify recent ML papers)",
    methodology="Econometric rigor; inference emphasis.", empirical="High for inference.", theory="Econometric theory valued.", data="Flexible.",
    code_policy="Verify.", difficulty=4, fit=7, role="Target (inference-heavy variant)", note="Fits if inference framework (SPA/MCS for decomposition) is a core contribution.")
add(journal="Journal of Econometrics", tier="Tier 2 - Econometrics (top)", publisher="Elsevier", oa_2yr=2.95, oa_h=333,
    scope="Econometric methodology.", qf_rel=3, ml_rel=4, related="GKX2021; CW2007; KP2015",
    methodology="New econometric methods with theory.", empirical="Application.", theory="Required.", data="Flexible.", code_policy="Verify.",
    difficulty=5, fit=4, role="Not recommended (unless new estimator)", note="Needs formal econometric contribution.")
add(journal="Journal of Business & Economic Statistics", tier="Tier 2 - Econometrics", publisher="Taylor & Francis / ASA", oa_2yr=1.86, oa_h=234,
    scope="Applied statistics and econometrics.", qf_rel=3, ml_rel=4, related="HAN2005; DM1995", methodology="Statistical methods with applications.",
    empirical="Moderate.", theory="Often.", data="Flexible.", code_policy="Verify.", difficulty=4, fit=5, role="Backup (inference variant)", note="")
add(journal="International Journal of Forecasting", tier="Tier 2 - Forecasting", publisher="Elsevier / International Institute of Forecasters",
    oa_2yr=3.79, oa_h=188, scope="Forecasting methods and evaluation, incl. forecast combination.", qf_rel=3, ml_rel=5,
    related="(forecast combination literature)", methodology="Forecast evaluation rigor; combination methods.", empirical="Moderate-high.", theory="Optional.",
    data="Flexible.", code_policy="Verify.", difficulty=3, fit=7, role="Target (combination-focused variant)",
    note="Fits a dynamic forecast-combination paper; must still show economic value.")
add(journal="European Journal of Operational Research", tier="Tier 2 - OR (high-volume)", publisher="Elsevier", oa_2yr=5.86, oa_h=407,
    scope="OR incl. financial modelling and portfolio optimisation.", qf_rel=4, ml_rel=5, related="FK2018; KDH2017; BAMS2014",
    methodology="OR/ML methods with finance applications.", empirical="Moderate; transaction costs increasingly expected.", theory="Optional.",
    data="Flexible.", code_policy="Verify.", difficulty=3, fit=7, role="Backup", note="Good for optimisation-heavy variants.")
add(journal="Journal of Banking & Finance", tier="Tier 2 - Field finance", publisher="Elsevier", oa_2yr=4.45, oa_h=309,
    scope="Finance and banking broadly, incl. investments.", qf_rel=4, ml_rel=3, related="MPR2026", methodology="Empirical finance.",
    empirical="High.", theory="Optional.", data="WRDS-standard.", code_policy="Verify.", difficulty=3, fit=8, role="Backup (strong)", note="")
add(journal="Journal of Empirical Finance", tier="Tier 2 - Field finance", publisher="Elsevier", oa_2yr=2.82, oa_h=133,
    scope="Empirical finance and financial econometrics.", qf_rel=4, ml_rel=3, related="LW2008", methodology="Empirical/econometric.",
    empirical="High.", theory="Optional.", data="WRDS-standard.", code_policy="Verify.", difficulty=3, fit=8, role="Backup (strong)", note="")
add(journal="Journal of Financial Markets", tier="Tier 2 - Field finance", publisher="Elsevier", oa_2yr=2.09, oa_h=104,
    scope="Market microstructure, trading, asset pricing.", qf_rel=5, ml_rel=3, related="TH2021; WL2025; AMI2002", methodology="Empirical microstructure / trading.",
    empirical="High for cost modelling.", theory="Optional.", data="TAQ/WRDS.", code_policy="Verify.", difficulty=3, fit=8, role="Backup (strong)",
    note="Natural home if transaction-cost modelling is central.")
add(journal="Journal of Economic Dynamics and Control", tier="Tier 2 - Field", publisher="Elsevier", oa_2yr=2.00, oa_h=168,
    scope="Computational economics and finance.", qf_rel=3, ml_rel=3, related="CFMZ2023; GT2007", methodology="Computational/empirical.",
    empirical="Moderate-high.", theory="Optional.", data="Flexible.", code_policy="Verify.", difficulty=3, fit=6, role="Backup", note="")
add(journal="Critical Finance Review", tier="Tier 2 - Field (replication/critique)", publisher="Now Publishers", oa_2yr=3.74, oa_h=32,
    scope="Critical/replication-oriented finance research.", qf_rel=4, ml_rel=3, related="LEW2015; CZ2022", methodology="Replication, critique, careful re-examination.",
    empirical="High transparency.", theory="Optional.", data="Open where possible.", code_policy="Verify.", difficulty=3, fit=7,
    role="Backup (if results are mainly a critical re-assessment)", note="")
add(journal="Mathematical Finance", tier="Tier 2 - Mathematical finance", publisher="Wiley", oa_2yr=1.60, oa_h=129,
    scope="Mathematical finance theory.", qf_rel=3, ml_rel=2, related="-", methodology="Mathematical theory.", empirical="Low.", theory="Required.",
    data="-", code_policy="Verify.", difficulty=5, fit=2, role="Not recommended", note="Poor fit for empirical signal combination.")
add(journal="Journal of Computational Finance", tier="Tier 2 - Computational finance", publisher="Infopro Digital (Risk.net)", oa_2yr=0.68, oa_h=57,
    scope="Verified (risk.net): numerical and computational techniques in pricing, hedging and risk management; recent issues include ML and portfolio optimisation.",
    qf_rel=3, ml_rel=3, related="BBLZ2017", methodology="Numerical methods.", empirical="Low-moderate.", theory="Numerical analysis.", data="-",
    code_policy="Verify.", difficulty=3, fit=4, role="Not recommended (except optimiser-computation variant)", note="Editor-in-chief: Christoph Reisinger (risk.net).")
add(journal="Annals of Operations Research", tier="Tier 2/3 - OR", publisher="Springer", oa_2yr=3.89, oa_h=186, scope="OR applications incl. finance.",
    qf_rel=3, ml_rel=4, related="ULM2024; SYM2025", methodology="OR/ML.", empirical="Moderate.", theory="Optional.", data="Flexible.", code_policy="Verify.",
    difficulty=2, fit=6, role="Backup", note="")
add(journal="Financial Analysts Journal", tier="Tier 3 - Practitioner (high reputation)", publisher="Taylor & Francis / CFA Institute", oa_2yr=2.74, oa_h=168,
    scope="Practitioner-relevant investment research.", qf_rel=4, ml_rel=4, related="RJ2019; KPT2012; NMV2019; LO2002; BL1992", methodology="Rigorous but accessible.",
    empirical="Practical relevance, costs, capacity.", theory="Not required.", data="Flexible.", code_policy="Verify.", difficulty=3, fit=7,
    role="Backup (practitioner version)", note="Shorter practitioner spin-off of the main paper.")
add(journal="Journal of Portfolio Management", tier="Tier 3 - Practitioner", publisher="With Intelligence (PMR)", oa_2yr=0.80, oa_h=116,
    scope="Practitioner portfolio management.", qf_rel=4, ml_rel=3, related="BLDP2014; LDP2016; HL2015; CSS2012; LS2008", methodology="Practitioner.",
    empirical="Moderate.", theory="No.", data="Flexible.", code_policy="None known.", difficulty=2, fit=6, role="Backup (practitioner)", note="")
add(journal="Journal of Financial Data Science", tier="Tier 3 - Practitioner ML", publisher="With Intelligence (PMR)", oa_2yr=0.68, oa_h=21,
    scope="Data science and ML in finance for practitioners.", qf_rel=4, ml_rel=5, related="BHHH2023; LLMSS2021; ZZR2020; LZR2019; AHM2019",
    methodology="Applied ML.", empirical="Moderate.", theory="No.", data="Flexible.", code_policy="None known.", difficulty=2, fit=6, role="Backup (practitioner ML)", note="")
add(journal="ACM ICAIF (conference)", tier="ML/AI venue - finance-specific", publisher="ACM", oa_2yr=None, oa_h=None,
    scope="Verified: ACM International Conference on AI in Finance, proceedings in ACM DL (2020-2025; 2026 in Milan).",
    qf_rel=3, ml_rel=5, related="-", methodology="AI/ML methods.", empirical="Benchmarks; costs often lighter.", theory="Optional.",
    data="Public benchmarks favoured.", code_policy="Varies.", difficulty=2, fit=5, role="Early dissemination",
    note="Useful for feedback on ML components; limited weight for finance hiring/promotion.")
add(journal="NeurIPS / ICML / KDD (main or workshops)", tier="ML/AI venue - general", publisher="Various", oa_2yr=None, oa_h=None,
    scope="General ML; finance appears in applications and workshops.", qf_rel=2, ml_rel=5, related="DAK2017; AK2017; AAB2019; DA2023", methodology="ML novelty.",
    empirical="ML benchmarks.", theory="Often.", data="Public.", code_policy="Code often expected.", difficulty=4, fit=3, role="Not recommended for main paper",
    note="Finance reviewers discount these unless economic evaluation is rigorous.")
add(journal="Expert Systems with Applications", tier="Tier 3 - Applied AI (high-volume)", publisher="Elsevier", oa_2yr=7.51, oa_h=349,
    scope="Applied intelligent systems.", qf_rel=2, ml_rel=5, related="-", methodology="Applied ML.", empirical="Variable; costs often omitted.", theory="No.",
    data="Flexible.", code_policy="Verify.", difficulty=2, fit=3, role="Not recommended",
    note="High citation counts do not translate into finance-field reputation; illustrates why IF alone is misleading.")
