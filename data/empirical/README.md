# Hudson Bay lynx–hare historical index (1900–1920)

This repository includes a small, semicolon-delimited transcription of the public
`Lynx_Hare.csv` dataset distributed with Richard McElreath's *rethinking* teaching
repository. Source: https://github.com/rmcelreath/rethinking/blob/master/data/Lynx_Hare.csv

The file records annual Lynx and Hare values from 1900 through 1920. These are
historical pelt/trapping-index observations, not standardized direct population
censuses. They are included as an empirical *pattern-check* dataset only. The
21-year window is short and does not support strong inference about long-term
population cycles, nor does it represent all historical Hudson Bay observations.

The TSA `hare` documentation identifies the historical hare series as based on
trapper questionnaires and cites MacLulich (1937) and Stenseth et al. (1997):
https://search.r-project.org/CRAN/refmans/TSA/html/hare.html

Do not treat these data as ground truth for animal abundance. Any model fit must
use the documented chronological split, with the final 30% held out from tuning.
