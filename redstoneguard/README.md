# CraftedHorizons RedstoneGuard

Minecraft Paper 1.21.11 (Java 21+) protection against high-frequency redstone clocks.

* Detects at least five distinct rising-signal game ticks within one second
  in an 8 × 8 × 8 block region, spanning at least half a second.
* Blocks redstone-current changes in that local region for 60 seconds using
  `BlockRedstoneEvent.setNewCurrent(oldCurrent)`.
* A second detection in the same region triggers a lightning **visual effect**
  at the detected Y level, even underground, and removes only directly
  connected redstone wire, comparators, repeaters, observers and torches.
* Caps deletion to 96 redstone blocks inside six blocks of the trigger.
* Excludes spawn/tournament worlds by default. Stores repeat-offense counts
  in `plugins/CraftedHorizonsRedstoneGuard/config.yml` across restarts.
* `/redstoneguard` and `/redstoneguard reload` require `redstoneguard.admin`.
  Staff warnings require `redstoneguard.alerts`.

## Installation

Put `CraftedHorizonsRedstoneGuard-1.0.0.jar` in `/plugins/` and restart Paper.
Review and edit `plugins/CraftedHorizonsRedstoneGuard/config.yml` as needed.

## Operational caveats

The Bukkit redstone-change event does not cover every possible redstone-driven
action (e.g. some direct pistons/observers behavior); not all infinite clocks can
be proven from events alone. A 5/s threshold can still catch intentional fast
mechanisms. The freeze may leave power frozen until a neighboring block update
occurs. This plugin never sets real damaging lightning or causes explosions.
Test on a staging world before enabling automatic destruction in production.
