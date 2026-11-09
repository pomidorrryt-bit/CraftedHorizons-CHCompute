package net.craftedhorizons.redstoneguard;

import java.util.ArrayDeque;
import java.util.ArrayList;
import java.util.Collection;
import java.util.Deque;
import java.util.HashMap;
import java.util.HashSet;
import java.util.Iterator;
import java.util.List;
import java.util.Map;
import java.util.Set;
import java.util.UUID;
import java.util.logging.Level;
import org.bukkit.Bukkit;
import org.bukkit.Location;
import org.bukkit.Material;
import org.bukkit.World;
import org.bukkit.block.Block;
import org.bukkit.block.BlockFace;
import org.bukkit.command.Command;
import org.bukkit.command.CommandSender;
import org.bukkit.entity.Player;
import org.bukkit.event.EventHandler;
import org.bukkit.event.EventPriority;
import org.bukkit.event.Listener;
import org.bukkit.event.block.BlockRedstoneEvent;
import org.bukkit.plugin.java.JavaPlugin;

/** Protects individual 8x8x8 redstone sectors from sustained clock loops. */
public final class RedstoneGuardPlugin extends JavaPlugin implements Listener {
    private static final BlockFace[] FACES = {
        BlockFace.UP, BlockFace.DOWN, BlockFace.NORTH,
        BlockFace.SOUTH, BlockFace.EAST, BlockFace.WEST
    };
    private final Map<Sector, Circuit> circuits = new HashMap<>();
    private long tick;
    private boolean removing;
    private int threshold;
    private int cooldownTicks;
    private int radius;
    private int destructionLimit;
    private boolean destroyOnRepeat;
    private Set<String> excludedWorlds = new HashSet<>();

    @Override
    public void onEnable() {
        saveDefaultConfig();
        loadSettings();
        Bukkit.getPluginManager().registerEvents(this, this);
        Bukkit.getScheduler().runTaskTimer(this, () -> {
            tick++;
            if (tick % 20 == 0) sweep();
        }, 1L, 1L);
        getLogger().info("RedstoneGuard enabled: " + threshold
                + " distinct rising ticks per second per local sector; "
                + (cooldownTicks / 20) + "s cooldown.");
    }

    private void loadSettings() {
        reloadConfig();
        threshold = Math.max(2, Math.min(20, getConfig().getInt("signals-per-second", 5)));
        cooldownTicks = Math.max(20, getConfig().getInt("cooldown-seconds", 60) * 20);
        radius = Math.max(1, Math.min(12, getConfig().getInt("destroy-radius", 6)));
        destructionLimit = Math.max(1, Math.min(256, getConfig().getInt("max-destroy-blocks", 96)));
        destroyOnRepeat = getConfig().getBoolean("destroy-on-repeat", true);
        excludedWorlds = new HashSet<>(getConfig().getStringList("excluded-worlds"));
    }

    @EventHandler(priority = EventPriority.HIGHEST)
    public void onRedstone(BlockRedstoneEvent event) {
        if (removing || event.getOldCurrent() == event.getNewCurrent()) return;
        Block block = event.getBlock();
        if (excludedWorlds.contains(block.getWorld().getName())) return;
        if (!isWireOrClock(block.getType())) return;

        Sector key = Sector.of(block);
        Circuit state = circuits.computeIfAbsent(key, unused -> new Circuit());

        if (tick < state.frozenUntil) {
            // BlockRedstoneEvent is NOT cancellable. Retaining old power is the
            // supported way to suppress this particular current transition.
            event.setNewCurrent(event.getOldCurrent());
            return;
        }

        if (event.getNewCurrent() <= event.getOldCurrent()) return;

        // Count one rising signal per GAME TICK within an 8x8x8 sector.
        // One lever energizing 30 dust blocks in a tick counts as ONE signal.
        if (state.lastSampleTick == tick) return;
        state.lastSampleTick = tick;
        state.risingTicks.addLast(tick);
        while (!state.risingTicks.isEmpty() && tick - state.risingTicks.peekFirst() > 20) {
            state.risingTicks.removeFirst();
        }
        BlockPoint point = BlockPoint.of(block);
        state.recent.put(point, tick);
        if (state.risingTicks.size() < threshold) return;

        // Reject a fast burst of neighbor updates; the signal must repeat
        // for at least 0.5 seconds to look like an actual clock.
        if (tick - state.risingTicks.peekFirst() < 10) return;

        state.risingTicks.clear();
        state.frozenUntil = tick + cooldownTicks;
        event.setNewCurrent(event.getOldCurrent());

        String persisted = "offenses." + key.worldId + ".s_"
                + key.x + "_" + key.y + "_" + key.z;
        int offenses = getConfig().getInt(persisted, 0) + 1;
        getConfig().set(persisted, offenses);
        saveConfig();

        if (offenses == 1 || !destroyOnRepeat) {
            notifyStaff("§eRedstone clock detected at §f" + key.display(block.getWorld())
                    + "§e. Suspended for " + cooldownTicks / 20 + "s (offense " + offenses + ").");
            return;
        }

        // The second sustained clock in the same local sector is destructive.
        // Destruction is postponed to the following tick, outside the event.
        List<BlockPoint> seeds = new ArrayList<>(state.recent.keySet());
        notifyStaff("§cRepeated redstone clock at §f" + key.display(block.getWorld())
                + "§c. Removing the looping circuit with underground lightning.");
        Bukkit.getScheduler().runTask(this, () -> removeClock(block.getWorld(), point, seeds));
    }

    private void removeClock(World world, BlockPoint trigger, List<BlockPoint> seeds) {
        if (!world.isChunkLoaded(trigger.x >> 4, trigger.z >> 4)) return;
        Deque<BlockPoint> pending = new ArrayDeque<>();
        pending.add(trigger);
        for (BlockPoint p : seeds) if (distance(p, trigger) <= radius) pending.add(p);
        Set<BlockPoint> seen = new HashSet<>();
        List<Block> toRemove = new ArrayList<>();
        while (!pending.isEmpty() && toRemove.size() < destructionLimit) {
            BlockPoint current = pending.removeFirst();
            if (!seen.add(current) || distance(current, trigger) > radius) continue;
            if (!world.isChunkLoaded(current.x >> 4, current.z >> 4)) continue;
            Block b = world.getBlockAt(current.x, current.y, current.z);
            if (!isWireOrClock(b.getType())) continue;
            toRemove.add(b);
            for (BlockFace face : FACES) pending.add(BlockPoint.of(b.getRelative(face)));
        }
        if (toRemove.isEmpty()) return;

        removing = true;
        try {
            // Effect is created at underground coordinates; it does not create
            // a fire, damage players or depend on sky access for destruction.
            Location where = new Location(world, trigger.x + .5, trigger.y, trigger.z + .5);
            world.strikeLightningEffect(where);
            for (Block b : toRemove) b.setType(Material.AIR, true);
            getLogger().warning("Destroyed " + toRemove.size()
                    + " redstone-only blocks at " + world.getName() + " " + trigger);
        } catch (RuntimeException error) {
            getLogger().log(Level.SEVERE, "Failed to remove redstone clock", error);
        } finally {
            removing = false;
        }
    }

    private static int distance(BlockPoint a, BlockPoint b) {
        return Math.max(Math.max(Math.abs(a.x - b.x), Math.abs(a.y - b.y)), Math.abs(a.z - b.z));
    }

    private static boolean isWireOrClock(Material type) {
        return switch (type) {
            case REDSTONE_WIRE, REPEATER, COMPARATOR, OBSERVER,
                    REDSTONE_TORCH, REDSTONE_WALL_TORCH -> true;
            default -> false;
        };
    }

    private void sweep() {
        Iterator<Map.Entry<Sector, Circuit>> iterator = circuits.entrySet().iterator();
        while (iterator.hasNext()) {
            Circuit state = iterator.next().getValue();
            state.recent.entrySet().removeIf(e -> tick - e.getValue() > 40);
            while (!state.risingTicks.isEmpty() && tick - state.risingTicks.peekFirst() > 20) {
                state.risingTicks.removeFirst();
            }
            if (state.frozenUntil > 0 && tick >= state.frozenUntil) {
                state.frozenUntil = 0;
                state.risingTicks.clear();
                // Current changes can resume on the next vanilla block update.
            }
            if (state.frozenUntil == 0 && state.risingTicks.isEmpty()
                    && state.recent.isEmpty()) iterator.remove();
        }
    }

    private void notifyStaff(String message) {
        getLogger().info(message.replaceAll("§[0-9a-fk-or]", ""));
        Collection<? extends Player> online = Bukkit.getOnlinePlayers();
        for (Player player : online) {
            if (player.hasPermission("redstoneguard.alerts")) player.sendMessage("§8[§cRedstoneGuard§8] " + message);
        }
    }

    @Override
    public boolean onCommand(CommandSender sender, Command command, String label, String[] args) {
        if (!sender.hasPermission("redstoneguard.admin")) {
            sender.sendMessage("§cNo permission.");
            return true;
        }
        if (args.length == 1 && args[0].equalsIgnoreCase("reload")) {
            loadSettings();
            sender.sendMessage("§aRedstoneGuard settings reloaded.");
        } else {
            long frozen = circuits.values().stream().filter(c -> tick < c.frozenUntil).count();
            sender.sendMessage("§aRedstoneGuard: §f" + threshold
                    + " signals/s, " + cooldownTicks / 20 + "s cooldown, "
                    + frozen + " local sectors suspended. /redstoneguard reload");
        }
        return true;
    }

    private static final class Circuit {
        final Deque<Long> risingTicks = new ArrayDeque<>();
        final Map<BlockPoint, Long> recent = new HashMap<>();
        long frozenUntil;
        long lastSampleTick = Long.MIN_VALUE;
    }

    private record BlockPoint(int x, int y, int z) {
        static BlockPoint of(Block b) { return new BlockPoint(b.getX(), b.getY(), b.getZ()); }
    }

    private record Sector(UUID worldId, int x, int y, int z) {
        static Sector of(Block b) {
            return new Sector(b.getWorld().getUID(), Math.floorDiv(b.getX(), 8),
                    Math.floorDiv(b.getY(), 8), Math.floorDiv(b.getZ(), 8));
        }
        String display(World w) {
            return w.getName() + " [" + (x * 8) + "," + (y * 8) + "," + (z * 8) + "]";
        }
    }
}
