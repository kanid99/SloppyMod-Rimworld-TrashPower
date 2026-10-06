using System.Collections.Generic;
using PipeSystem;
using RimWorld;
using UnityEngine;
using Verse;

namespace TrashbrickBurning
{
    /// <summary>
    /// The exhaust network: a second Vanilla Expanded Framework pipe network, like Dubs Bad
    /// Hygiene's sewage pipes, carrying burner exhaust to exhaust ports.
    /// </summary>
    public static class ExhaustNetwork
    {
        public const string NetDefName = "STB_ExhaustNet";

        public static PipeNet NetOf(ThingWithComps thing) => NetOf(thing, NetDefName);

        /// <summary>The thing's network of the given PipeNetDef - a building can sit on more than one.</summary>
        public static PipeNet NetOf(ThingWithComps thing, string netDefName)
        {
            List<ThingComp> comps = thing.AllComps;
            for (int i = 0; i < comps.Count; i++)
            {
                if (comps[i] is CompResource res && res.PipeNet != null && res.Props.pipeNet?.defName == netDefName)
                {
                    return res.PipeNet;
                }
            }
            return null;
        }

        public static List<CompExhaustPort> Ports(PipeNet net)
        {
            List<CompExhaustPort> ports = new List<CompExhaustPort>();
            if (net == null)
            {
                return ports;
            }
            foreach (ThingWithComps thing in HeatNetwork.Members(net))
            {
                CompExhaustPort port = thing.GetComp<CompExhaustPort>();
                if (port != null && port.Open)
                {
                    ports.Add(port);
                }
            }
            return ports;
        }

        public static List<CompExhaustTank> Tanks(PipeNet net)
        {
            List<CompExhaustTank> tanks = new List<CompExhaustTank>();
            if (net == null)
            {
                return tanks;
            }
            foreach (ThingWithComps thing in HeatNetwork.Members(net))
            {
                CompExhaustTank tank = thing.GetComp<CompExhaustTank>();
                if (tank != null && tank.parent.Spawned)
                {
                    tanks.Add(tank);
                }
            }
            return tanks;
        }

        /// <summary>
        /// Exhaust with no open port to go to: as much as the expansion tanks on the network have room
        /// for goes into them, and the refs are left holding what didn't fit.
        /// </summary>
        public static void Store(PipeNet net, ref float pollution, ref float gas, ref float rot)
        {
            foreach (CompExhaustTank tank in Tanks(net))
            {
                if (gas + rot <= 0.001f && pollution <= 0.001f)
                {
                    return;
                }
                tank.Take(ref pollution, ref gas, ref rot);
            }
        }

        /// <summary>
        /// Fumes from anything on the network (burner, compactor, factory machine): to the open ports,
        /// else into the expansion tanks. True if all of it went somewhere; the refs keep what's left.
        /// </summary>
        public static bool Route(PipeNet net, ref float pollution, ref float gas, ref float rot, float heat)
        {
            List<CompExhaustPort> open = Ports(net);
            if (open.Count > 0)
            {
                foreach (CompExhaustPort port in open)
                {
                    port.Receive(pollution / open.Count, gas / open.Count, heat / open.Count, rot / open.Count);
                }
                pollution = gas = rot = 0f;
                return true;
            }
            Store(net, ref pollution, ref gas, ref rot);
            return gas + rot < 0.5f;
        }

        /// <summary>
        /// Toxic gas straight into the gas grid, overflowing: a cell holds at most 255, and without
        /// overflow everything past that is thrown away, so a steady stream into one cell never built
        /// up. With it, the excess floods out into the cells around, as a real leak would.
        /// </summary>
        public static void AddToxGas(IntVec3 cell, Map map, int amount) => AddGas(cell, map, GasType.ToxGas, amount);

        public static void AddGas(IntVec3 cell, Map map, GasType type, int amount)
        {
            if (amount > 0 && cell.InBounds(map))
            {
                map.gasGrid.AddGas(cell, type, amount, true);
            }
        }

        public static void ReleaseToxGas(Thing source, int amount) => ReleaseGas(source, GasType.ToxGas, amount);

        /// <summary>Gas into a cell next to the source that gas can occupy.</summary>
        public static void ReleaseGas(Thing source, GasType type, int amount)
        {
            Map map = source.Map;
            if (map == null || amount <= 0)
            {
                return;
            }
            List<IntVec3> cells = new List<IntVec3>();
            foreach (IntVec3 c in GenAdj.CellsAdjacent8Way(source))
            {
                if (c.InBounds(map) && !c.Impassable(map))
                {
                    cells.Add(c);
                }
            }
            if (cells.Count == 0)
            {
                return;
            }
            AddGas(cells.RandomElement(), map, type, amount);
        }
    }

    public class CompProperties_Exhaust : CompProperties
    {
        /// <summary>Ground cells polluted per unit of fuel burnt (Biotech pollution).</summary>
        public float pollutionPerFuel = 0.05f;

        /// <summary>Toxic gas released per unit of fuel burnt, wherever the exhaust comes out.</summary>
        public float toxGasPerFuel = 100f;

        /// <summary>Heat the exhaust carries out of a port, per unit of fuel burnt: a mild warmth where it comes out.</summary>
        public float heatPerFuel = 20f;

        public CompProperties_Exhaust()
        {
            compClass = typeof(CompExhaust);
        }
    }

    /// <summary>
    /// Burning trash makes exhaust. Piped to an exhaust port, it comes out there - polluting the
    /// ground around the port, and gassing the room if the port is indoors. Not piped anywhere, it
    /// comes out of the burner itself: toxic gas in the room around it, and pollution on the ground.
    /// </summary>
    public class CompExhaust : ThingComp
    {
        private const int Interval = GenTicks.TickRareInterval;

        private float pollutionBuffer;
        private float gasBuffer;
        private float rotBuffer;
        private int ports;
        private bool ventingLocally;
        private bool holdingInTank;

        public CompProperties_Exhaust Props => (CompProperties_Exhaust)props;

        /// <summary>Burning with nowhere for the exhaust to go but its own room.</summary>
        public bool VentingLocally => ventingLocally;

        private float FuelPerDay => parent.GetComp<CompStirlingEngine>()?.FuelPerDay ?? 0f;

        public float PollutionPerDay => FuelPerDay * Props.pollutionPerFuel * TrashbrickBurningMod.S.pollutionMultiplier
            * (parent.GetComp<CompStirlingEngine>()?.mixPollution ?? 1f);

        public override void PostExposeData()
        {
            base.PostExposeData();
            Scribe_Values.Look(ref pollutionBuffer, "exhaustPollution", 0f);
            Scribe_Values.Look(ref gasBuffer, "exhaustGas", 0f);
            Scribe_Values.Look(ref rotBuffer, "exhaustRot", 0f);
        }

        public override void CompTick()
        {
            base.CompTick();
            if (parent.IsHashIntervalTick(Interval))
            {
                Step(Interval);
            }
        }

        public override void CompTickRare()
        {
            base.CompTickRare();
            Step(Interval);
        }

        private void Step(int ticks)
        {
            CompStirlingEngine engine = parent.GetComp<CompStirlingEngine>();
            List<CompExhaustPort> open = ExhaustNetwork.Ports(ExhaustNetwork.NetOf(parent));
            ports = open.Count;
            ventingLocally = false;
            if (engine == null || !engine.Burning || !parent.Spawned)
            {
                return;
            }
            float mult = TrashbrickBurningMod.S.pollutionMultiplier;
            float fuel = engine.FuelPerDay * ticks / GenDate.TicksPerDay;
            // Dirtier fuel mixes (wastepacks, loose trash) make more gas and less ground pollution.
            float pollution = fuel * Props.pollutionPerFuel * mult * engine.mixPollution;
            float gas = fuel * Props.toxGasPerFuel * mult * engine.mixToxGas;
            // Burnt corpses: rot stink, scaled off the same toxic gas figure.
            float rot = fuel * Props.toxGasPerFuel * mult * engine.mixRotStink;
            holdingInTank = false;
            if (ExhaustNetwork.Route(ExhaustNetwork.NetOf(parent), ref pollution, ref gas, ref rot, fuel * Props.heatPerFuel))
            {
                holdingInTank = open.Count == 0;
                return;
            }
            ventingLocally = true;
            pollutionBuffer += pollution;
            gasBuffer += gas;
            rotBuffer += rot;
            Emit(parent, null, ref pollutionBuffer, ref gasBuffer, ref rotBuffer, true);
        }

        /// <summary>
        /// Lets out whole units. With an outlet cell (a wall-mounted port's own cell), everything
        /// comes out there; otherwise into the cells around the thing. Ground pollution, toxic gas and rot stink
        /// wherever it is - outdoors the gas drifts off on its own, in a room it builds up.
        /// </summary>
        public static void Emit(Thing at, IntVec3? outlet, ref float pollution, ref float gas, ref float rot, bool alwaysGas = true)
        {
            Map map = at.Map;
            if (map == null)
            {
                return;
            }
            IntVec3 cell = outlet ?? at.Position;
            if (!cell.InBounds(map))
            {
                return;
            }
            if (pollution >= 1f && ModsConfig.BiotechActive)
            {
                int cells = (int)pollution;
                pollution -= cells;
                PollutionUtility.GrowPollutionAt(cell, map, cells);
            }
            EmitGas(at, outlet, cell, map, GasType.ToxGas, ref gas, alwaysGas);
            EmitGas(at, outlet, cell, map, GasType.RotStink, ref rot, alwaysGas);
            if (Rand.Chance(0.7f))
            {
                Vector3 smoke = outlet.HasValue ? cell.ToVector3Shifted() : at.TrueCenter();
                FleckMaker.ThrowSmoke(smoke, map, Rand.Range(0.8f, 1.4f));
            }
        }

        private static void EmitGas(Thing at, IntVec3? outlet, IntVec3 cell, Map map, GasType type, ref float gas, bool alwaysGas)
        {
            if (gas < 1f)
            {
                return;
            }
            int amount = (int)gas;
            gas -= amount;
            Room room = outlet.HasValue ? cell.GetRoom(map) : at.GetRoom();
            bool indoors = room != null && !room.PsychologicallyOutdoors;
            if (!alwaysGas && !indoors)
            {
                return;
            }
            if (outlet.HasValue && !cell.Impassable(map))
            {
                ExhaustNetwork.AddGas(cell, map, type, amount);
            }
            else
            {
                ExhaustNetwork.ReleaseGas(at, type, amount);
            }
        }

        public override string CompInspectStringExtra()
        {
            CompStirlingEngine engine = parent.GetComp<CompStirlingEngine>();
            if (engine == null || !engine.Burning)
            {
                return ports > 0 ? "STB_ExhaustPiped".Translate(ports).Resolve() : null;
            }
            if (ventingLocally)
            {
                return "STB_ExhaustLocal".Translate(PollutionPerDay.ToString("0.#")).Resolve();
            }
            if (holdingInTank)
            {
                return "STB_ExhaustToTank".Translate().Resolve();
            }
            return "STB_ExhaustToPorts".Translate(ports, PollutionPerDay.ToString("0.#")).Resolve();
        }
    }

    public class CompProperties_ExhaustPort : CompProperties
    {
        /// <summary>
        /// Wall-mounted: hung on a wall, it lets the exhaust out into its own cell, on the side of the
        /// wall it's hung on. Otherwise (the stack) into the cells around it.
        /// </summary>
        public bool outletAtSelf;

        public CompProperties_ExhaustPort()
        {
            compClass = typeof(CompExhaustPort);
        }
    }

    /// <summary>
    /// Where the exhaust network comes out: it pollutes the ground around the port and, if the
    /// port is indoors, gasses the room. Build it outside, somewhere you don't mind polluting.
    /// </summary>
    public class CompExhaustPort : ThingComp
    {
        private float pollutionBuffer;
        private float gasBuffer;
        private float rotBuffer;
        private float receivedToday;
        private int lastReceiveTick = -1;

        // The jet: gas and rot stink received this window, and the rate over the last one.
        private float windowGas;
        private float windowRot;
        private float gasPerDay;
        private float rotShare;
        private readonly GasJet jet = new GasJet();

        /// <summary>Toxic gas a day at which the jet blows full: about a cobbled gasifier on high.</summary>
        private const float FullJetGasPerDay = 150000f;

        /// <summary>
        /// Its fan has to run to draw the exhaust: switched on and powered. With no open port, the
        /// exhaust backs up and comes out of the burners (and compactors) that make it.
        /// </summary>
        public bool Open
        {
            get
            {
                if (!parent.Spawned || !FlickUtility.WantsToBeOn(parent))
                {
                    return false;
                }
                CompPowerTrader power = parent.GetComp<CompPowerTrader>();
                return power == null || power.PowerOn;
            }
        }

        private CompProperties_ExhaustPort Props => (CompProperties_ExhaustPort)props;

        /// <summary>Where the exhaust comes out: the cell in front of a wall port, or null for around the stack.</summary>
        public IntVec3? Outlet => Props.outletAtSelf ? parent.Position : (IntVec3?)null;

        public bool Active => lastReceiveTick >= 0 && Find.TickManager.TicksGame - lastReceiveTick < GenTicks.TickRareInterval * 2;

        public override void PostExposeData()
        {
            base.PostExposeData();
            Scribe_Values.Look(ref pollutionBuffer, "exhaustPollution", 0f);
            Scribe_Values.Look(ref gasBuffer, "exhaustGas", 0f);
            Scribe_Values.Look(ref rotBuffer, "exhaustRot", 0f);
        }

        /// <summary>Exhaust from the burners: pollution, gas and rot stink out where it comes out, and a little heat.</summary>
        public void Receive(float pollution, float gas, float heat, float rot = 0f)
        {
            pollutionBuffer += pollution;
            gasBuffer += gas;
            rotBuffer += rot;
            windowGas += gas;
            windowRot += rot;
            receivedToday = pollution * GenDate.TicksPerDay / GenTicks.TickRareInterval;
            lastReceiveTick = Find.TickManager.TicksGame;
            IntVec3 cell = Outlet ?? parent.Position;
            if (heat > 0f && cell.InBounds(parent.Map))
            {
                GenTemperature.PushHeat(cell, parent.Map, heat);
            }
            CompExhaust.Emit(parent, Outlet, ref pollutionBuffer, ref gasBuffer, ref rotBuffer);
        }

        /// <summary>
        /// A jet of fumes out of the port, scaled to how much is coming through: yellow-green toxic
        /// exhaust, browner the more rot stink is in it. A wall port blows straight out from the wall;
        /// the stack sends a plume up from its top.
        /// </summary>
        public override void CompTick()
        {
            base.CompTick();
            if (parent.IsHashIntervalTick(GenTicks.TickRareInterval))
            {
                float total = windowGas + windowRot;
                gasPerDay = total * GenDate.TicksPerDay / GenTicks.TickRareInterval;
                rotShare = total > 0f ? windowRot / total : 0f;
                windowGas = windowRot = 0f;
            }
            if (!parent.Spawned || gasPerDay <= 0f || !parent.IsHashIntervalTick(GasJet.TickInterval))
            {
                return;
            }
            Color color = Color.Lerp(GasJet.ToxGas, GasJet.RotStink, rotShare);
            float strength = gasPerDay / FullJetGasPerDay;
            if (Props.outletAtSelf)
            {
                jet.Tick(parent.Map, parent.DrawPos, parent.Rotation.Opposite.AsAngle, strength, color);
            }
            else
            {
                Vector3 top = parent.DrawPos + new Vector3(0f, 0f, 0.45f);
                jet.Tick(parent.Map, top, 0f, strength, color, 18f);
            }
        }

        public override void PostDrawExtraSelectionOverlays()
        {
            base.PostDrawExtraSelectionOverlays();
            if (Outlet.HasValue)
            {
                GenDraw.DrawFieldEdges(new List<IntVec3> { Outlet.Value }, PlaceWorker_SteamVent.PlumeColor);
            }
        }

        public override string CompInspectStringExtra()
        {
            CompPowerTrader power = parent.GetComp<CompPowerTrader>();
            if (power != null && !power.PowerOn && FlickUtility.WantsToBeOn(parent))
            {
                return "STB_PortNoPower".Translate();
            }
            if (!Active)
            {
                return "STB_PortIdle".Translate();
            }
            Room room = Outlet.HasValue ? Outlet.Value.GetRoom(parent.Map) : parent.GetRoom();
            string s = "STB_PortActive".Translate(receivedToday.ToString("0.#"));
            if (room != null && !room.PsychologicallyOutdoors)
            {
                s += "\n" + "STB_PortIndoors".Translate();
            }
            return s;
        }
    }

    public class CompProperties_ExhaustSource : CompProperties
    {
        public CompProperties_ExhaustSource()
        {
            compClass = typeof(CompExhaustSource);
        }
    }

    /// <summary>
    /// On something else that makes fumes - Vanilla Recycling Expanded's garbage compactor, or a
    /// Vanilla Furniture Expanded - Factory machine (CompFactoryFumes). Piped to a powered exhaust
    /// port, its fumes go down the exhaust instead (Patch_CompactorExhaust for the compactor);
    /// otherwise they come out as usual.
    /// </summary>
    public class CompExhaustSource : ThingComp
    {
        /// <summary>
        /// Takes what toxic gas it can down the exhaust - to an open port, or into an expansion tank -
        /// and returns what's left over to come out here.
        /// </summary>
        public int RouteGas(int amount)
        {
            float pollution = 0f, gas = amount, rot = 0f;
            ExhaustNetwork.Route(ExhaustNetwork.NetOf(parent), ref pollution, ref gas, ref rot, 0f);
            return Mathf.CeilToInt(gas - 0.001f);
        }

        /// <summary>Sends fumes down the exhaust: true if all of it went; the refs keep what's left.</summary>
        public bool TryRoute(ref float toxGas, ref float rotStink, ref float pollution) =>
            ExhaustNetwork.Route(ExhaustNetwork.NetOf(parent), ref pollution, ref toxGas, ref rotStink, 0f);

        public override string CompInspectStringExtra()
        {
            int ports = ExhaustNetwork.Ports(ExhaustNetwork.NetOf(parent)).Count;
            if (ports > 0)
            {
                return "STB_SourceToPorts".Translate(ports);
            }
            return ExhaustNetwork.NetOf(parent) != null ? "STB_SourceNoPort".Translate().Resolve() : null;
        }
    }

    public class CompProperties_FactoryFumes : CompProperties_ExhaustSource
    {
        /// <summary>Toxic gas a day while the machine is working (a garbage compactor makes about 30000).</summary>
        public float toxGasPerDay;

        /// <summary>Rot stink a day while working: the crematorium.</summary>
        public float rotStinkPerDay;

        /// <summary>Ground cells polluted a day while working (Biotech).</summary>
        public float pollutionPerDay;

        public CompProperties_FactoryFumes()
        {
            compClass = typeof(CompFactoryFumes);
        }
    }

    /// <summary>
    /// A Vanilla Furniture Expanded - Factory machine's fumes: while its VEF processor is running a
    /// process, it makes toxic gas (or rot stink) and a little ground pollution. Piped to a powered
    /// exhaust port they come out there; otherwise around the machine. Scaled by the pollution
    /// setting, and off with the factory fumes setting.
    /// </summary>
    public class CompFactoryFumes : CompExhaustSource
    {
        private const int Interval = GenTicks.TickRareInterval;

        private float gasBuffer;
        private float rotBuffer;
        private float pollutionBuffer;
        private bool working;

        private CompProperties_FactoryFumes Props => (CompProperties_FactoryFumes)props;

        public override void PostExposeData()
        {
            base.PostExposeData();
            Scribe_Values.Look(ref gasBuffer, "fumesGas", 0f);
            Scribe_Values.Look(ref rotBuffer, "fumesRot", 0f);
            Scribe_Values.Look(ref pollutionBuffer, "fumesPollution", 0f);
        }

        public override void CompTick()
        {
            base.CompTick();
            if (parent.IsHashIntervalTick(Interval))
            {
                Step();
            }
        }

        public override void CompTickRare()
        {
            base.CompTickRare();
            Step();
        }

        /// <summary>Running a process right now: VEF's processor has one under way with its ingredients in.</summary>
        private bool Working
        {
            get
            {
                PipeSystem.CompAdvancedResourceProcessor processor = parent.GetComp<PipeSystem.CompAdvancedResourceProcessor>();
                if (processor?.Process == null || !processor.Process.IsRunning)
                {
                    return false;
                }
                CompPowerTrader power = parent.GetComp<CompPowerTrader>();
                return power == null || power.PowerOn;
            }
        }

        private void Step()
        {
            working = parent.Spawned && TrashbrickBurningMod.S.factoryFumes && Working;
            if (!working)
            {
                return;
            }
            float f = (float)Interval / GenDate.TicksPerDay * TrashbrickBurningMod.S.pollutionMultiplier;
            float gas = Props.toxGasPerDay * f, rot = Props.rotStinkPerDay * f, pollution = Props.pollutionPerDay * f;
            if (TryRoute(ref gas, ref rot, ref pollution))
            {
                return;
            }
            gasBuffer += gas;
            rotBuffer += rot;
            pollutionBuffer += pollution;
            CompExhaust.Emit(parent, null, ref pollutionBuffer, ref gasBuffer, ref rotBuffer);
        }

        public override string CompInspectStringExtra()
        {
            if (!TrashbrickBurningMod.S.factoryFumes)
            {
                return null;
            }
            float mult = TrashbrickBurningMod.S.pollutionMultiplier;
            string what = Props.rotStinkPerDay > 0f
                ? "STB_FumesRot".Translate((Props.toxGasPerDay * mult).ToString("0"), (Props.rotStinkPerDay * mult).ToString("0"))
                : "STB_FumesGas".Translate((Props.toxGasPerDay * mult).ToString("0"));
            string line = (working ? "STB_FumesWorking" : "STB_FumesIdle").Translate(what);
            string route = base.CompInspectStringExtra();
            return route.NullOrEmpty() ? line : line + "\n" + route;
        }
    }

    public class CompProperties_ExhaustTank : CompProperties
    {
        /// <summary>Toxic gas (and rot stink) it holds: about eight hours of a trash gasifier on normal.</summary>
        public float capacity = 30000f;

        /// <summary>How fast it empties into open ports, a day: a full tank drains in about two hours.</summary>
        public float drainPerDay = 360000f;

        public CompProperties_ExhaustTank()
        {
            compClass = typeof(CompExhaustTank);
        }
    }

    /// <summary>
    /// The exhaust expansion tank: a buffer on the exhaust network. While no open, powered port can
    /// take the exhaust - a power cut, every damper shut - the burners, compactors and factory
    /// machines on the network fill it instead of gassing their rooms. Once a port is working again it
    /// drains into the ports at a steady rate. Full, the exhaust backs up as before. Destroyed (or
    /// deconstructed), it lets out everything it holds where it stood.
    /// </summary>
    public class CompExhaustTank : ThingComp
    {
        private const int Interval = GenTicks.TickRareInterval;

        private float gas;
        private float rot;
        private float pollution;
        private int draining;

        public CompProperties_ExhaustTank Props => (CompProperties_ExhaustTank)props;

        public float Held => gas + rot;

        public float Room => Mathf.Max(0f, Props.capacity - Held);

        public float Fraction => Props.capacity > 0f ? Held / Props.capacity : 0f;

        public override void PostExposeData()
        {
            base.PostExposeData();
            Scribe_Values.Look(ref gas, "heldGas", 0f);
            Scribe_Values.Look(ref rot, "heldRot", 0f);
            Scribe_Values.Look(ref pollution, "heldPollution", 0f);
        }

        /// <summary>Takes what it has room for, in proportion; the refs keep the rest.</summary>
        public void Take(ref float p, ref float g, ref float r)
        {
            float incoming = g + r;
            float share = incoming <= 0.001f ? 1f : Mathf.Min(1f, Room / incoming);
            if (share <= 0f)
            {
                return;
            }
            gas += g * share;
            rot += r * share;
            pollution += p * share;
            g -= g * share;
            r -= r * share;
            p -= p * share;
        }

        public override void CompTick()
        {
            base.CompTick();
            if (parent.IsHashIntervalTick(Interval))
            {
                Drain();
            }
        }

        public override void CompTickRare()
        {
            base.CompTickRare();
            Drain();
        }

        private void Drain()
        {
            draining = 0;
            if (!parent.Spawned || Held <= 0.5f && pollution <= 0.01f)
            {
                return;
            }
            List<CompExhaustPort> open = ExhaustNetwork.Ports(ExhaustNetwork.NetOf(parent));
            if (open.Count == 0)
            {
                return;
            }
            draining = open.Count;
            float share = Held <= 0.5f ? 1f : Mathf.Min(1f, Props.drainPerDay * Interval / GenDate.TicksPerDay / Held);
            float g = gas * share, r = rot * share, p = pollution * share;
            gas -= g;
            rot -= r;
            pollution -= p;
            foreach (CompExhaustPort port in open)
            {
                port.Receive(p / open.Count, g / open.Count, 0f, r / open.Count);
            }
        }

        public override void PostDestroy(DestroyMode mode, Map previousMap)
        {
            base.PostDestroy(mode, previousMap);
            if (previousMap == null || Held <= 0.5f)
            {
                return;
            }
            // Burst or taken apart: everything in it comes out at once.
            IntVec3 cell = parent.Position;
            ExhaustNetwork.AddGas(cell, previousMap, GasType.ToxGas, (int)gas);
            ExhaustNetwork.AddGas(cell, previousMap, GasType.RotStink, (int)rot);
            if (pollution >= 1f && ModsConfig.BiotechActive && cell.InBounds(previousMap))
            {
                PollutionUtility.GrowPollutionAt(cell, previousMap, (int)pollution);
            }
            gas = rot = pollution = 0f;
        }

        public override string CompInspectStringExtra()
        {
            string s = "STB_TankHeld".Translate(Held.ToString("0"), Props.capacity.ToString("0"), Fraction.ToStringPercent());
            if (ExhaustNetwork.NetOf(parent) == null)
            {
                return s + "\n" + "STB_TankNoPipe".Translate();
            }
            if (draining > 0)
            {
                return s + "\n" + "STB_TankDraining".Translate(draining);
            }
            if (Held > 0.5f)
            {
                return s + "\n" + (Room <= 1f ? "STB_TankFull" : "STB_TankHolding").Translate();
            }
            return s;
        }
    }
}
