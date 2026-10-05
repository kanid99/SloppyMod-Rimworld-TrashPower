using System.Collections.Generic;
using PipeSystem;
using RimWorld;
using UnityEngine;
using Verse;

namespace TrashbrickBurning
{
    /// <summary>
    /// Shares the heat on one pressurised hot water network, once per network per tick, read by
    /// every burner, turbine, radiator and Overpressure Tank on it. The order:
    ///
    ///   1. turbines take burner heat one at a time, each up to its maximum. A turbine short of its
    ///      gear's minimum stalls: it still takes the heat, and wastes it;
    ///   2. radiators take what their rooms need;
    ///   3. Overpressure Tanks charge from what's still left;
    ///   4. steam vents blow off what's left after that (and drain tanks above their set level);
    ///   5. the rest goes back to the burners as surplus - DBH hot water may take it (the bridge
    ///      assembly), and whatever nobody takes builds pressure.
    ///
    /// Then the tanks give back: first to any turbine short of its gear's minimum, topping it up so
    /// it keeps turning (only if they can cover the whole shortfall - a partial top-up would stall
    /// anyway); then to radiators the burners couldn't satisfy.
    ///
    /// Before any of that, a burner's DBH hot water share and its own Stirling engine (when no
    /// turbine is on the network) have taken their part (CompStirlingEngine.NetworkHeatWatts).
    ///
    /// Vanilla Expanded Framework's PipeSystem carries the pipes and networks; the sums are done here.
    /// </summary>
    public static class HeatNetwork
    {
        public class Flow
        {
            public float heat;
            public int burners;
            /// <summary>Burners without a safety valve piped to this network, lit or not.</summary>
            public int cobbledBurners;
            public readonly Dictionary<CompSteamTurbine, float> turbineHeat = new Dictionary<CompSteamTurbine, float>();
            public float toTurbines;
            public float turbineTopUp;
            public float radiatorDemand;
            public float toRadiators;
            public float radiatorsFromTanks;
            public float chargeCapacity;
            public float charge;
            public float dischargeCapacity;
            public float ventCapacity;
            public float toVents;
            public float leftover;
            public bool anyConsumer;
            public bool anyTurbine;

            public float Discharge => turbineTopUp + radiatorsFromTanks;

            public float HeatFor(CompSteamTurbine t) => turbineHeat.TryGetValue(t, out float h) ? h : 0f;
        }

        private static readonly Dictionary<PipeNet, Flow> Cache = new Dictionary<PipeNet, Flow>();
        private static readonly Dictionary<PipeNet, bool> TurbineCache = new Dictionary<PipeNet, bool>();
        private static int cacheTick = -1;

        public const string NetDefName = "STB_HotWaterNet";

        /// <summary>The thing's pressurised hot water network. Burners also sit on the exhaust network.</summary>
        public static PipeNet NetOf(ThingWithComps thing) => ExhaustNetwork.NetOf(thing, NetDefName);

        public static IEnumerable<ThingWithComps> Members(PipeNet net)
        {
            HashSet<Thing> seen = new HashSet<Thing>();
            foreach (CompResource connector in net.connectors)
            {
                if (seen.Add(connector.parent))
                {
                    yield return connector.parent;
                }
            }
        }

        private static void CheckTick()
        {
            int tick = Find.TickManager.TicksGame;
            if (tick != cacheTick)
            {
                Cache.Clear();
                TurbineCache.Clear();
                cacheTick = tick;
            }
        }

        /// <summary>Any steam turbine on the network, running or not: burners' own Stirling engines stand down.</summary>
        public static bool HasTurbine(PipeNet net)
        {
            if (net == null)
            {
                return false;
            }
            CheckTick();
            if (TurbineCache.TryGetValue(net, out bool has))
            {
                return has;
            }
            has = false;
            foreach (ThingWithComps thing in Members(net))
            {
                if (thing.GetComp<CompSteamTurbine>() != null)
                {
                    has = true;
                    break;
                }
            }
            TurbineCache[net] = has;
            return has;
        }

        public static Flow Compute(PipeNet net)
        {
            CheckTick();
            if (Cache.TryGetValue(net, out Flow cached))
            {
                return cached;
            }
            Flow f = new Flow();
            List<CompSteamTurbine> turbines = new List<CompSteamTurbine>();
            List<CompHeatAccumulator> tanks = new List<CompHeatAccumulator>();
            foreach (ThingWithComps thing in Members(net))
            {
                CompStirlingEngine engine = thing.GetComp<CompStirlingEngine>();
                if (engine != null && !engine.Props.safetyValve)
                {
                    f.cobbledBurners++;
                }
                if (engine != null && engine.NetworkHeatWatts > 0f)
                {
                    f.heat += engine.NetworkHeatWatts;
                    f.burners++;
                }
                CompSteamTurbine turbine = thing.GetComp<CompSteamTurbine>();
                if (turbine != null)
                {
                    f.anyConsumer = true;
                    f.anyTurbine = true;
                    if (turbine.CanRun)
                    {
                        turbines.Add(turbine);
                    }
                }
                CompHotWaterRadiator radiator = thing.GetComp<CompHotWaterRadiator>();
                if (radiator != null)
                {
                    f.anyConsumer = true;
                    f.radiatorDemand += radiator.Demand;
                }
                CompSteamVent vent = thing.GetComp<CompSteamVent>();
                if (vent != null)
                {
                    f.anyConsumer = true;
                    f.ventCapacity += vent.Capacity;
                }
                CompHeatAccumulator tank = thing.GetComp<CompHeatAccumulator>();
                if (tank != null)
                {
                    f.anyConsumer = true;
                    tanks.Add(tank);
                    f.chargeCapacity += tank.ChargeRoomWatts;
                    f.dischargeCapacity += tank.DischargeAvailableWatts;
                }
            }
            // A stable order, so the same turbine fills first every tick.
            turbines.Sort((x, y) => x.parent.thingIDNumber.CompareTo(y.parent.thingIDNumber));

            float rest = f.heat;
            foreach (CompSteamTurbine t in turbines)
            {
                float take = Mathf.Min(rest, t.MaxHeatWatts);
                f.turbineHeat[t] = take;
                f.toTurbines += take;
                rest -= take;
            }
            f.toRadiators = Mathf.Min(rest, f.radiatorDemand);
            rest -= f.toRadiators;
            f.charge = Mathf.Min(rest, f.chargeCapacity);
            rest -= f.charge;
            f.toVents = Mathf.Min(rest, f.ventCapacity);
            rest -= f.toVents;
            f.leftover = rest;

            // The tanks give back: keep stalling turbines turning first, then the radiators.
            float pool = f.dischargeCapacity;
            foreach (CompSteamTurbine t in turbines)
            {
                float have = f.turbineHeat[t];
                float need = t.GearMinWatts - have;
                if (need > 0f && need <= pool && t.GearMinWatts <= t.MaxHeatWatts)
                {
                    f.turbineHeat[t] = have + need;
                    f.turbineTopUp += need;
                    pool -= need;
                }
            }
            f.radiatorsFromTanks = Mathf.Min(pool, f.radiatorDemand - f.toRadiators);
            Cache[net] = f;
            return f;
        }

        public static void UpdateBurner(CompStirlingEngine engine)
        {
            float heat = engine.NetworkHeatWatts;
            PipeNet net = NetOf(engine.parent);
            if (net == null)
            {
                engine.networkConnected = false;
                engine.toNetworkWatts = 0f;
                engine.surplusWatts = heat;
                return;
            }
            Flow f = Compute(net);
            engine.networkConnected = f.anyConsumer;
            float share = f.heat > 0f ? heat / f.heat : 0f;
            engine.surplusWatts = f.leftover * share;
            engine.toNetworkWatts = heat - engine.surplusWatts;
        }
    }

    /// <summary>One turbine gear: the least heat it turns over on, and how much of the heat it makes power.</summary>
    public class TurbineGear
    {
        public string key;
        public float minWatts;
        public float efficiency;
    }

    public class CompProperties_SteamTurbine : CompProperties_Power
    {
        /// <summary>The most heat this turbine can take: three burners on high.</summary>
        public float maxHeatWatts = 6000f;

        /// <summary>Low, medium and high. Higher gears are more efficient but need more heat to turn at all.</summary>
        public List<TurbineGear> gears = new List<TurbineGear>();

        public CompProperties_SteamTurbine()
        {
            compClass = typeof(CompSteamTurbine);
        }
    }

    /// <summary>
    /// A generator that turns the heat piped to it into power at its gear's efficiency. Below the
    /// gear's minimum it stalls: it still takes its share of the heat, and wastes it.
    /// </summary>
    public class CompSteamTurbine : CompPowerPlant
    {
        private const int RecalcInterval = 60;

        public int gear;

        private float watts;
        private float heatWatts;
        private int feeders;
        private float topUp;

        public new CompProperties_SteamTurbine Props => (CompProperties_SteamTurbine)props;

        protected override float DesiredPowerOutput => watts;

        public float HeatWatts => heatWatts;

        public TurbineGear Gear => Props.gears.Count == 0 ? null : Props.gears[Mathf.Clamp(gear, 0, Props.gears.Count - 1)];

        public float GearMinWatts => Gear?.minWatts ?? 0f;

        public float MaxHeatWatts => Props.maxHeatWatts;

        public bool Stalled => CanRun && TrashbrickBurningMod.Advanced && heatWatts < GearMinWatts;

        public bool Turning => watts > 0f;

        public bool CanRun
        {
            get
            {
                CompBreakdownable breakdown = parent.GetComp<CompBreakdownable>();
                return FlickUtility.WantsToBeOn(parent) && (breakdown == null || !breakdown.BrokenDown);
            }
        }

        public override void PostExposeData()
        {
            base.PostExposeData();
            Scribe_Values.Look(ref gear, "gear", 0);
        }

        public override void CompTick()
        {
            if (parent.IsHashIntervalTick(RecalcInterval))
            {
                Recalculate();
            }
            base.CompTick();
        }

        private void Recalculate()
        {
            watts = heatWatts = topUp = 0f;
            feeders = 0;
            PipeNet net = HeatNetwork.NetOf(parent);
            if (!TrashbrickBurningMod.Advanced || net == null || !CanRun)
            {
                return;
            }
            HeatNetwork.Flow f = HeatNetwork.Compute(net);
            feeders = f.burners;
            heatWatts = f.HeatFor(this);
            topUp = f.turbineTopUp;
            TurbineGear g = Gear;
            if (g != null && heatWatts >= g.minWatts && heatWatts > 0f)
            {
                watts = heatWatts * g.efficiency * TrashbrickBurningMod.S.powerMultiplier;
            }
        }

        /// <summary>The best gear this much heat would turn, or -1 if none.</summary>
        private int BestGearFor(float heat)
        {
            int best = -1;
            for (int i = 0; i < Props.gears.Count; i++)
            {
                if (heat >= Props.gears[i].minWatts)
                {
                    best = i;
                }
            }
            return best;
        }

        public override IEnumerable<Gizmo> CompGetGizmosExtra()
        {
            foreach (Gizmo g in base.CompGetGizmosExtra())
            {
                yield return g;
            }
            if (parent.Faction != Faction.OfPlayer || !TrashbrickBurningMod.Advanced || Props.gears.Count == 0)
            {
                yield break;
            }
            yield return new Command_TurbineGear(this);
        }

        public string GearLabel(int i)
        {
            TurbineGear g = Props.gears[i];
            return "STB_GearLine".Translate(("STB_Gear_" + g.key).Translate(), g.minWatts.ToString("0"),
                g.efficiency.ToStringPercent());
        }

        public override string CompInspectStringExtra()
        {
            string baseString = base.CompInspectStringExtra();
            List<string> lines = new List<string>();
            if (TrashbrickBurningMod.Advanced && Gear != null)
            {
                lines.Add("STB_TurbineGearStatus".Translate(("STB_Gear_" + Gear.key).Translate(),
                    Gear.minWatts.ToString("0"), Gear.efficiency.ToStringPercent()));
                lines.Add("STB_TurbineLoad".Translate(heatWatts.ToString("0"), Props.maxHeatWatts.ToString("0")));
                if (Stalled && heatWatts > 0f)
                {
                    int best = BestGearFor(heatWatts);
                    string stall = "STB_TurbineStalled".Translate(heatWatts.ToString("0"), Gear.minWatts.ToString("0"));
                    if (best >= 0)
                    {
                        stall += " " + "STB_TurbineTryGear".Translate(("STB_Gear_" + Props.gears[best].key).Translate());
                    }
                    lines.Add(stall);
                }
                if (topUp > 0f)
                {
                    lines.Add("STB_TurbineFromTank".Translate());
                }
                lines.Add("STB_TurbineFeeders".Translate(feeders));
            }
            string line = string.Join("\n", lines);
            if (line.NullOrEmpty())
            {
                return baseString;
            }
            return baseString.NullOrEmpty() ? line : baseString + "\n" + line;
        }
    }

    /// <summary>Left-click steps low → medium → high; right-click picks one.</summary>
    public class Command_TurbineGear : Command_Action
    {
        private readonly CompSteamTurbine turbine;

        public Command_TurbineGear(CompSteamTurbine turbine)
        {
            this.turbine = turbine;
            defaultLabel = "STB_TurbineGear".Translate(("STB_Gear_" + turbine.Gear.key).Translate());
            defaultDesc = "STB_TurbineGearDesc".Translate(GearTable());
            icon = TexCommand.DesirePower;
            action = () => turbine.gear = (turbine.gear + 1) % turbine.Props.gears.Count;
        }

        private string GearTable()
        {
            string s = "";
            for (int i = 0; i < turbine.Props.gears.Count; i++)
            {
                s += "\n" + turbine.GearLabel(i);
            }
            return s;
        }

        public override IEnumerable<FloatMenuOption> RightClickFloatMenuOptions
        {
            get
            {
                for (int i = 0; i < turbine.Props.gears.Count; i++)
                {
                    int g = i;
                    yield return new FloatMenuOption(turbine.GearLabel(g), () => turbine.gear = g);
                }
            }
        }
    }

    public class CompProperties_HotWaterRadiator : CompProperties
    {
        /// <summary>The most heat it takes from the network.</summary>
        public float maxWatts = 250f;

        /// <summary>Room heat pushed per second for each watt received. Vanilla's heater is about 0.12.</summary>
        public float heatPerWattSecond = 0.06f;

        public CompProperties_HotWaterRadiator()
        {
            compClass = typeof(CompHotWaterRadiator);
        }
    }

    /// <summary>
    /// Heats its room from the network, up to the target temperature set on its CompTempControl, with
    /// vanilla's own temperature system - so it sits alongside Vanilla Temperature Expanded or any
    /// other heater. Radiators come after turbines in the network's order.
    /// </summary>
    public class CompHotWaterRadiator : ThingComp
    {
        private float received;

        public CompProperties_HotWaterRadiator Props => (CompProperties_HotWaterRadiator)props;

        public float Demand
        {
            get
            {
                CompBreakdownable breakdown = parent.GetComp<CompBreakdownable>();
                if (!parent.Spawned || !FlickUtility.WantsToBeOn(parent) || (breakdown != null && breakdown.BrokenDown))
                {
                    return 0f;
                }
                CompTempControl temp = parent.GetComp<CompTempControl>();
                Room room = parent.GetRoom();
                if (room == null || room.UsesOutdoorTemperature)
                {
                    return 0f;
                }
                float target = temp?.targetTemperature ?? 21f;
                return room.Temperature < target ? Props.maxWatts : 0f;
            }
        }

        public override void CompTick()
        {
            base.CompTick();
            if (!parent.IsHashIntervalTick(60))
            {
                return;
            }
            received = 0f;
            PipeNet net = HeatNetwork.NetOf(parent);
            if (!TrashbrickBurningMod.Advanced || net == null)
            {
                return;
            }
            HeatNetwork.Flow f = HeatNetwork.Compute(net);
            float demand = Demand;
            if (demand > 0f && f.radiatorDemand > 0f)
            {
                received = (f.toRadiators + f.radiatorsFromTanks) * demand / f.radiatorDemand;
                GenTemperature.PushHeat(parent, received * Props.heatPerWattSecond);
            }
        }

        public override string CompInspectStringExtra()
        {
            return "STB_RadiatorStatus".Translate(received.ToString("0"), Props.maxWatts.ToString("0"));
        }
    }

    /// <summary>
    /// The radiators' thermostat. Vanilla's readout ends in a line break meant for the power line
    /// that follows on a heater; a radiator has no power comp, so RimWorld logs it as an error.
    /// </summary>
    public class CompRadiatorTempControl : CompTempControl
    {
        public override string CompInspectStringExtra()
        {
            return base.CompInspectStringExtra()?.TrimEnd();
        }
    }

    public class CompProperties_HeatAccumulator : CompProperties
    {
        /// <summary>Stored heat, in watt-days.</summary>
        public float capacityWattDays = 1500f;

        /// <summary>How fast it charges and discharges: enough to hold a turbine in high gear.</summary>
        public float rateWatts = 3000f;

        /// <summary>Auto-release: how fast it vents above its set level.</summary>
        public float ventWatts = 3000f;

        /// <summary>Auto-release: room heat pushed per second for each watt vented. Radiators give 0.06.</summary>
        public float ventHeatPerWattSecond = 0.03f;

        /// <summary>Mean days between explosions when full, freshly bled, on a network of gasifiers only.</summary>
        public float explosionMtbDaysWhenFull = 60f;

        /// <summary>Risk multiplier while any burner without a safety valve is piped to the network.</summary>
        public float cobbledRiskFactor = 4f;

        /// <summary>Wear adds this much risk (x1) every this many days since the tank was last bled, up to x3.</summary>
        public float wearDays = 20f;

        /// <summary>Below this fill the tank can't explode.</summary>
        public float safeFill = 0.2f;

        /// <summary>Blast radius from empty to full.</summary>
        public FloatRange explosionRadius = new FloatRange(2.9f, 6.9f);

        /// <summary>Room heat pushed per watt-day bled off.</summary>
        public float bleedHeatPerWattDay = 0.5f;

        /// <summary>
        /// Heat it leaks through its lagging when full, in watts, scaling with how full it is. It
        /// warms its room a little - a small fraction of what a burner does - and loses that heat.
        /// </summary>
        public float leakWattsWhenFull = 20f;

        /// <summary>Room heat pushed per second for each watt leaked, as radiators.</summary>
        public float leakHeatPerWattSecond = 0.06f;

        public CompProperties_HeatAccumulator()
        {
            compClass = typeof(CompHeatAccumulator);
        }
    }

    /// <summary>
    /// The Overpressure Tank. One mode, three jobs, in order:
    ///
    ///   1. relieve pressure: it takes whatever heat the turbines and radiators don't use;
    ///   2. heat radiators the burners can't satisfy (ours, and DBH's through the bridge assembly);
    ///   3. reserve steam: it tops a turbine up to its gear's minimum when the burners fall short,
    ///      so it keeps turning through a breakdown or a refuel.
    ///
    /// The fuller it is, the likelier it is to let go. Pawns bleed it (the bleed job), or it can be
    /// set to auto-release above a level, venting the heat into its room.
    /// </summary>
    public class CompHeatAccumulator : ThingComp
    {
        public bool bleedRequested;
        public float bleedTo = 0.25f;
        public bool autoRelease;
        public float releaseAbove = 0.5f;

        public static readonly float[] ReleaseLevels = { 0.25f, 0.5f, 0.75f, 1f };

        private int lastBledTick = -1;
        private int cobbledOnNet;

        private float stored;
        private float lastFlow;
        private float lastVent;
        private string idleReason;

        public CompProperties_HeatAccumulator Props => (CompProperties_HeatAccumulator)props;

        public float Fraction => Props.capacityWattDays > 0f ? stored / Props.capacityWattDays : 0f;

        public float ChargeRoomWatts => stored < Props.capacityWattDays - 0.01f ? Props.rateWatts : 0f;

        public float DischargeAvailableWatts => stored > 0.01f ? Mathf.Min(Props.rateWatts, stored * GenDate.TicksPerDay / 60f) : 0f;

        public override void PostExposeData()
        {
            base.PostExposeData();
            Scribe_Values.Look(ref stored, "storedHeat", 0f);
            Scribe_Values.Look(ref bleedRequested, "bleedRequested", false);
            Scribe_Values.Look(ref bleedTo, "bleedTo", 0.25f);
            Scribe_Values.Look(ref lastBledTick, "lastBledTick", -1);
            Scribe_Values.Look(ref autoRelease, "autoRelease", false);
            Scribe_Values.Look(ref releaseAbove, "releaseAbove", 0.5f);
        }

        public override void CompTick()
        {
            base.CompTick();
            if (!parent.IsHashIntervalTick(60))
            {
                return;
            }
            lastFlow = 0f;
            lastVent = 0f;
            idleReason = null;
            if (lastBledTick < 0)
            {
                lastBledTick = Find.TickManager.TicksGame;
            }
            AutoRelease();
            LeakHeat();
            PipeNet net = HeatNetwork.NetOf(parent);
            cobbledOnNet = 0;
            if (!TrashbrickBurningMod.Advanced || net == null)
            {
                idleReason = "STB_AccIdleNoPipe";
                return;
            }
            HeatNetwork.Flow f = HeatNetwork.Compute(net);
            cobbledOnNet = f.cobbledBurners;
            if (Rand.Chance(ExplosionChancePerDay * 60f / GenDate.TicksPerDay))
            {
                AccumulatorExplosion.Explode(this);
                return;
            }
            float charge = Share(f.charge, ChargeRoomWatts, f.chargeCapacity);
            float discharge = Share(f.Discharge, DischargeAvailableWatts, f.dischargeCapacity);
            lastFlow = charge - discharge;
            stored = Mathf.Clamp(stored + lastFlow * 60f / GenDate.TicksPerDay, 0f, Props.capacityWattDays);
            if (Mathf.Abs(lastFlow) < 0.5f)
            {
                if (f.heat <= 0f && stored <= 0.01f)
                {
                    idleReason = "STB_AccIdleNoHeat";
                }
                else if (ChargeRoomWatts <= 0f && f.heat > 0f)
                {
                    idleReason = "STB_AccIdleFull";
                }
                else if (f.heat > 0f)
                {
                    idleReason = "STB_AccIdleTurbinesTakeAll";
                }
            }
        }

        /// <summary>Even lagged, a tank of hot water warms its room a little, losing that heat.</summary>
        private void LeakHeat()
        {
            if (!parent.Spawned || stored <= 0.01f)
            {
                return;
            }
            float watts = Props.leakWattsWhenFull * Fraction;
            stored = Mathf.Max(0f, stored - watts * 60f / GenDate.TicksPerDay);
            GenTemperature.PushHeat(parent, watts * Props.leakHeatPerWattSecond);
        }

        /// <summary>Above its set level, vents on its own: safe, but it heats its room hard.</summary>
        private void AutoRelease()
        {
            if (!autoRelease || !parent.Spawned)
            {
                return;
            }
            float above = stored - Props.capacityWattDays * releaseAbove;
            if (above <= 0.01f)
            {
                return;
            }
            float vented = Mathf.Min(above, Props.ventWatts * 60f / GenDate.TicksPerDay);
            stored -= vented;
            lastVent = vented * GenDate.TicksPerDay / 60f;
            GenTemperature.PushHeat(parent, lastVent * Props.ventHeatPerWattSecond);
            SteamGrid.AddFromWatts(parent.Map, parent.Position, lastVent, 1f);
            if (Rand.Chance(0.5f))
            {
                FleckMaker.ThrowSmoke(parent.TrueCenter(), parent.Map, Rand.Range(0.6f, 1.1f));
            }
        }

        public float DaysSinceBled => lastBledTick < 0 ? 0f : (Find.TickManager.TicksGame - lastBledTick) / (float)GenDate.TicksPerDay;

        /// <summary>1 when freshly bled, rising to 3 as the seals and valves wear.</summary>
        public float WearFactor => Mathf.Min(3f, 1f + DaysSinceBled / Props.wearDays);

        /// <summary>
        /// Chance a day of the tank letting go. Zero below the safe fill, then rising with the square of
        /// how full it is, times wear, times four with a cobbled burner (no safety valve) on the network.
        /// </summary>
        public float ExplosionChancePerDay
        {
            get
            {
                if (!TrashbrickBurningMod.Advanced || !TrashbrickBurningMod.Hazards || Fraction <= Props.safeFill)
                {
                    return 0f;
                }
                float p = Mathf.InverseLerp(Props.safeFill, 1f, Fraction);
                float risk = p * p * WearFactor / Props.explosionMtbDaysWhenFull;
                if (cobbledOnNet > 0)
                {
                    risk *= Props.cobbledRiskFactor;
                }
                return Mathf.Min(risk, 1f);
            }
        }

        public float BlastRadius => Props.explosionRadius.LerpThroughRange(Fraction);

        public float StoredWattDays => stored;

        public bool NeedsBleed => bleedRequested && Fraction > bleedTo + 0.01f;

        /// <summary>A pawn opens the blow-off valve: the heat goes into the room, the wear resets.</summary>
        public void Bleed()
        {
            float target = Props.capacityWattDays * bleedTo;
            float bled = Mathf.Max(0f, stored - target);
            stored -= bled;
            lastBledTick = Find.TickManager.TicksGame;
            bleedRequested = false;
            if (parent.Spawned)
            {
                GenTemperature.PushHeat(parent.Position, parent.Map, bled * Props.bleedHeatPerWattDay);
                // Bleeding a full tank fills its room with steam.
                SteamGrid.Add(parent.Map, parent.Position, bled / 100f);
                for (int i = 0; i < 6; i++)
                {
                    FleckMaker.ThrowSmoke(parent.TrueCenter(), parent.Map, Rand.Range(1f, 1.8f));
                }
            }
        }

        /// <summary>Heat in or out from outside the steam network: Dubs Bad Hygiene, through the bridge assembly.</summary>
        public void AddHeat(float wattDays)
        {
            stored = Mathf.Clamp(stored + wattDays, 0f, Props.capacityWattDays);
        }

        public void Emptied()
        {
            stored = 0f;
            bleedRequested = false;
            lastBledTick = Find.TickManager.TicksGame;
        }

        private static float Share(float flow, float mine, float pool) => pool > 0f ? flow * mine / pool : 0f;

        public override IEnumerable<Gizmo> CompGetGizmosExtra()
        {
            foreach (Gizmo gizmo in base.CompGetGizmosExtra())
            {
                yield return gizmo;
            }
            if (parent.Faction != Faction.OfPlayer)
            {
                yield break;
            }
            yield return new Command_Toggle
            {
                defaultLabel = "STB_AutoRelease".Translate(),
                defaultDesc = "STB_AutoReleaseDesc".Translate(),
                icon = TexCommand.ForbidOff,
                isActive = () => autoRelease,
                toggleAction = () => autoRelease = !autoRelease
            };
            if (autoRelease)
            {
                yield return new Command_ReleaseLevel(this);
            }
            if (TrashbrickBurningMod.Hazards)
            {
                yield return new Command_BleedAccumulator(this);
            }
        }

        public override void PostDraw()
        {
            base.PostDraw();
            GenDraw.FillableBarRequest bar = default(GenDraw.FillableBarRequest);
            bar.center = parent.DrawPos + Vector3.up * 0.1f + new Vector3(0f, 0f, -0.6f);
            bar.size = new Vector2(1.4f, 0.16f);
            bar.fillPercent = Fraction;
            bar.filledMat = SolidColorMaterials.SimpleSolidColorMaterial(
                Color.Lerp(new Color(0.8f, 0.4f, 0.26f), new Color(0.95f, 0.1f, 0.1f), Mathf.Clamp01(ExplosionChancePerDay * 5f)));
            bar.unfilledMat = SolidColorMaterials.SimpleSolidColorMaterial(new Color(0.15f, 0.15f, 0.15f));
            bar.margin = 0.12f;
            GenDraw.DrawFillableBar(bar);
        }

        public override string CompInspectStringExtra()
        {
            // Watt-days to kilowatt-hours, which players read more easily.
            string s = "STB_AccumulatorStatus".Translate((stored * 24f / 1000f).ToString("0.0"),
                (Props.capacityWattDays * 24f / 1000f).ToString("0.0"), lastFlow.ToString("+0;-0;0"));
            if (autoRelease)
            {
                s += "\n" + "STB_AutoReleaseStatus".Translate(releaseAbove.ToStringPercent()).Resolve();
                if (lastVent > 0f)
                {
                    s += " " + "STB_AutoReleaseVenting".Translate(lastVent.ToString("0")).Resolve();
                }
            }
            if (idleReason != null)
            {
                s += "\n" + idleReason.Translate();
            }
            if (TrashbrickBurningMod.Advanced && TrashbrickBurningMod.Hazards)
            {
                float risk = ExplosionChancePerDay;
                s += "\n" + (risk > 0f
                    ? "STB_AccRisk".Translate(risk.ToStringPercent("0.#"), BlastRadius.ToString("0"))
                    : "STB_AccRiskNone".Translate(Props.safeFill.ToStringPercent())).Resolve();
                s += "\n" + "STB_AccWear".Translate(DaysSinceBled.ToString("0.0"), WearFactor.ToString("0.0")).Resolve();
                if (cobbledOnNet > 0)
                {
                    s += " " + "STB_AccCobbled".Translate(Props.cobbledRiskFactor.ToString("0")).Resolve();
                }
                if (bleedRequested)
                {
                    s += "\n" + "STB_AccBleedPending".Translate(bleedTo.ToStringPercent()).Resolve();
                }
            }
            return s;
        }
    }

    /// <summary>Left-click steps the auto-release level 25 → 50 → 75 → 100%; right-click picks one.</summary>
    public class Command_ReleaseLevel : Command_Action
    {
        private readonly CompHeatAccumulator acc;

        public Command_ReleaseLevel(CompHeatAccumulator acc)
        {
            this.acc = acc;
            defaultLabel = "STB_ReleaseLevel".Translate(acc.releaseAbove.ToStringPercent());
            defaultDesc = "STB_ReleaseLevelDesc".Translate();
            icon = TexCommand.ForbidOff;
            action = () =>
            {
                int i = System.Array.IndexOf(CompHeatAccumulator.ReleaseLevels, acc.releaseAbove);
                acc.releaseAbove = CompHeatAccumulator.ReleaseLevels[(i + 1) % CompHeatAccumulator.ReleaseLevels.Length];
            };
        }

        public override IEnumerable<FloatMenuOption> RightClickFloatMenuOptions
        {
            get
            {
                foreach (float level in CompHeatAccumulator.ReleaseLevels)
                {
                    float l = level;
                    yield return new FloatMenuOption(l.ToStringPercent(), () => acc.releaseAbove = l);
                }
            }
        }
    }
}
