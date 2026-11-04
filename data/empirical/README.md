# Empirical dataset registry and provenance

The checked-in Hudson Bay 1900–1920 pelt-index series remains the only raw
empirical series in the current campaign. The following longer independent
sources are registered for controlled ingestion; they are not pooled or
silently converted into abundance counts.

| Dataset | Coverage | Sampling method / observation | Role and caveat |
|---|---|---|---|
| Tetlin National Wildlife Refuge, Alaska | 1990–2024 | Snowshoe hare pellet counts across quadrats and sites | Hare-only series; raw CSV and ServCat processing record are linked in Data.gov metadata. Not paired predator abundance. |
| Kluane hare grids, Yukon | Multi-decade monitoring; Dryad release includes monitoring, live-trap and experimental records | Live trapping / capture-mark-recapture, experimental grids and small-mammal monitoring | Valuable independent hare demographic and experimental evidence; inspect individual workbook metadata and use a clearly specified subset. |
| Wood Buffalo National Park, Canada | 2006–2017 | Annual June fecal-pellet counts on four permanent transects; plots cleared after counting | Hare-only transect series; methodology and data dictionary are published separately. |
| Yukon boreal community monitoring | 1973–2022 | Annual permanent hare pellet plots; predator snow-track counts on fixed routes after fresh snowfall; site-specific protocols | Potential paired multi-species pattern series, but predator tracks are an index and survey effort/weather/site differences must be retained. |

## Source links

- Tetlin FWS / Data.gov metadata:
  https://catalog.data.gov/dataset/snowshoe-hare-population-monitoring-at-tetlin-national-wildlife-refuge-raw-datas-1990-2024
- Kluane monitoring and experiment data (Dryad, DOI 10.5061/dryad.684s1):
  https://datadryad.org/dataset/doi:10.5061/dryad.684s1
- Wood Buffalo hare pellet survey and data dictionary:
  https://open.canada.ca/data/en/dataset/045239c3-f835-4be8-921a-f17caf264097
- Yukon boreal community monitoring methods and long-term series:
  https://www.frontiersin.org/journals/ecology-and-evolution/articles/10.3389/fevo.2023.1187222/full
- Kluane 1977–2020 capture-mark-recapture demographic study:
  https://www.usgs.gov/publications/demographic-mechanisms-snowshoe-hare-population-cycles-yukon-canada

## Ingestion policy

Before a dataset becomes a model input, preserve the original downloaded file
and record its SHA-256, retrieval date, license/terms, publisher, citation,
data dictionary, site and transect identifiers, temporal resolution, units,
sampling effort, missingness and any transformations. Keep raw observations
separate from derived summaries. Do not treat pellet counts, live-trap
abundance estimates, capture rates, camera hit rates and snow tracks as the
same measurement. Do not join hare and predator observations across sites or
years without a defensible temporal/spatial matching rule.

The Tetlin and Wood Buffalo sources are hare-only and can test prey/resource
dynamics, not a two-species predator-prey model by themselves. The Yukon
community monitoring source may support a paired-pattern analysis only after
recovering the underlying site-year tables and validating the overlap of
hare and predator survey effort. Kluane individual-level capture histories
require a dedicated observation model; do not reduce them to arbitrary annual
counts.

At this milestone, the dataset registry is metadata/provenance work. The raw
files have not yet been downloaded, checksum-verified, harmonized or used to
fit the model. No results are claimed from these additional sources.

---

## Original Hudson Bay historical index (1900–1920)

The repository includes a semicolon-delimited transcription of the public
`Lynx_Hare.csv` dataset distributed with Richard McElreath's *rethinking*
teaching repository:
https://github.com/rmcelreath/rethinking/blob/master/data/Lynx_Hare.csv

These are historical pelt/trapping-index observations, not standardized direct
population censuses. The TSA `hare` documentation identifies the historical
hare series as based on trapper questionnaires:
https://search.r-project.org/CRAN/refmans/TSA/html/hare.html

Use the first 70% chronologically for calibration and the final 30% as a
strictly untouched holdout. This short series is an empirical pattern check,
not a ground-truth abundance record.
