# Ecological Evolution Model

## Population and species

The ecosystem starts with one or more configured species. Each organism has a stable ID, species assignment, immutable genome, parent IDs and birth generation. Reproduction is species-local; a species with no surviving members becomes extinct. A species split is recorded when offspring genome distance from its parent crosses the configured threshold.

The current speciation rule is deliberately simple and should be treated as an operational heuristic, not a validated biological species concept. It does not yet use reproductive isolation, multi-generation clustering or a calibrated phylogenetic threshold.

## Shared-resource competition

Organisms are evaluated in a seeded shuffled order against a shared finite resource pool. Gathering depletes that pool, so earlier successful foragers can reduce what remains for later organisms. Resource supply and action costs can change at scheduled generation boundaries.

This makes the competition outcome order-dependent by design. The random seed and phase schedule are therefore part of the experiment manifest.

## Partner-dependent cooperation

Organisms are paired for an interaction round. A cooperation payoff is granted only when both paired organisms actually execute a cooperation instruction. Unreciprocated attempts incur the configured cost. This is a minimal reciprocal-interaction model; spatial neighborhoods, repeated-game memory, kin selection and networked partnerships remain future work.

## Multi-objective selection

Fitness is represented as three objectives:
1. Resources acquired.
2. Remaining energy (survival proxy).
3. Reciprocal cooperation achieved.

The engine applies nondominated sorting and crowding distance to preserve trade-offs. This is an NSGA-II-inspired selection mechanism, not a full reference implementation of every NSGA-II operator.

## Dynamic environments

Environmental phases are ordered by start generation. Each phase defines resource supply, movement cost, gather reward, cooperation reward and unreciprocated cooperation cost. The active phase is recorded in each generation report.

## Limitations

- No spatial grid, metabolism over continuous time or explicit trophic levels yet.
- Pairing is random and one-round, not persistent social networks.
- Species splitting uses parent-child genome distance and can over-split under aggressive mutation.
- Survival is an energy threshold; there is no stochastic mortality or age structure.
- Population capacity is species-local; resource pressure is the primary shared ecological constraint.
- Fitness objectives are proxies defined by this simulator, not universal measures of organismal fitness.
