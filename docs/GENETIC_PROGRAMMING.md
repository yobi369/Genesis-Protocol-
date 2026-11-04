# Structured Genetic Programming

Genesis Protocol now supports a typed program representation that compiles into a constrained instruction genome.

## Node types

- `Action`: move, gather, rest or cooperate.
- `IfEnergyBelow`: execute one action only when current energy is below a threshold.
- `IfResourcesBelow`: execute one action only when remaining shared resources are below a threshold.
- `RepeatAction`: execute an action, then repeat it a bounded number of additional times.

## Safety and execution

The compiler emits only the Genesis opcode set. The interpreter does not evaluate Python, import modules, access files or open network connections. Conditional branches and repeats are bounded by the genome length and instruction budget.

Conditional nodes intentionally contain one primitive action. This keeps the compiler semantics exact with the current bytecode format. Nested blocks, typed arithmetic, registers, loops with explicit control-flow graphs and grammar-constrained tree evolution are future extensions.

## Operators

Programs support seeded random generation, node mutation, and sequence crossover. The compiled genome remains subject to the 64-instruction limit. Program mutation is a research operator; its effectiveness must be evaluated against matched baselines rather than assumed.
