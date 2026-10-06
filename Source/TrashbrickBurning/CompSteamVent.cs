using System.Collections.Generic;
using PipeSystem;
using RimWorld;
using UnityEngine;
using Verse;

namespace TrashbrickBurning
{
    public class CompProperties_SteamVent : CompProperties
    {
        /// <summary>The most heat it vents.</summary>
        public float maxWatts = 3000f;

        /// <summary>
        /// Hung on a wall, or standing on the ground: it blows its steam into its own cell. Otherwise
        /// (the old in-wall vent) into the cell it faces.
        /// </summary>
        public bool plumeAtSelf;

        /// <summary>Heat pushed into the plume cell per second for each watt vented: a vanilla heater's rate, twice a radiator's.</summary>
        public float heatPerWattSecond = 0.12f;

        /// <summary>Venting at least this much scalds anyone standing in the plume (hazards on).</summary>
        public float scaldAboveWatts = 500f;

        public CompProperties_SteamVent()
        {
            compClass = typeof(CompSteamVent);
        }
    }

    /// <summary>Shows the plume cell - the one a steam vent or wall exhaust port faces - while placing it.</summary>
    public class PlaceWorker_SteamVent : PlaceWorker
    {
        public static readonly Color PlumeColor = new Color(0.9f, 0.45f, 0.3f);

        public override void DrawGhost(ThingDef def, IntVec3 center, Rot4 rot, Color ghostCol, Thing thing = null)
        {
            GenDraw.DrawFieldEdges(new List<IntVec3> { center + rot.FacingCell }, PlumeColor);
        }
    }

    /// <summary>
    /// A steam vent built into a wall, like a cooler. It takes the heat nobody else on the network
    /// wants - after turbines, radiators and Overpressure Tanks - so the burners don't build
    /// pressure, and it can also drain the tanks above a level you set. It blows the steam out of
    /// its front face: a lot of heat into that cell, and a scald for anyone standing in it.
    /// </summary>
    public class CompSteamVent : ThingComp
    {
        public const int NeverDrain = -1;
        public static readonly float[] DrainLevels = { 0.25f, 0.5f, 0.75f };

        /// <summary>Index into DrainLevels, or NeverDrain: only take heat that would build pressure.</summary>
        public int drainLevel = 1;

        private float venting;

        public CompProperties_SteamVent Props => (CompProperties_SteamVent)props;

        public bool Open
        {
            get
            {
                CompBreakdownable breakdown = parent.GetComp<CompBreakdownable>();
                return parent.Spawned && FlickUtility.WantsToBeOn(parent) && (breakdown == null || !breakdown.BrokenDown);
            }
        }

        /// <summary>What it can take from the network's leftover heat.</summary>
        public float Capacity => Open && TrashbrickBurningMod.Advanced ? Props.maxWatts : 0f;

        public float Venting => venting;

        public IntVec3 PlumeCell => Props.plumeAtSelf ? parent.Position : parent.Position + parent.Rotation.FacingCell;

        public override void PostExposeData()
        {
            base.PostExposeData();
            Scribe_Values.Look(ref drainLevel, "drainLevel", 1);
        }

        private readonly GasJet jet = new GasJet();

        /// <summary>
        /// The jet of steam it blows, scaled to what it's venting: a wall vent straight out from the
        /// wall, a ground vent towards the cell it faces.
        /// </summary>
        private void TickJet()
        {
            if (venting <= 1f || !parent.Spawned || !parent.IsHashIntervalTick(GasJet.TickInterval))
            {
                return;
            }
            Rot4 dir = Props.plumeAtSelf ? parent.Rotation.Opposite : parent.Rotation;
            jet.Tick(parent.Map, parent.DrawPos, dir.AsAngle, venting / Props.maxWatts, GasJet.Steam);
        }

        public override void CompTick()
        {
            base.CompTick();
            TickJet();
            if (!parent.IsHashIntervalTick(60))
            {
                return;
            }
            venting = 0f;
            PipeNet net = HeatNetwork.NetOf(parent);
            if (net == null || Capacity <= 0f)
            {
                return;
            }
            HeatNetwork.Flow f = HeatNetwork.Compute(net);
            if (f.ventCapacity > 0f)
            {
                venting = f.toVents * Capacity / f.ventCapacity;
            }
            // Drain the tanks above the set level with whatever capacity is left.
            if (drainLevel != NeverDrain)
            {
                float level = DrainLevels[Mathf.Clamp(drainLevel, 0, DrainLevels.Length - 1)];
                float room = Props.maxWatts - venting;
                foreach (ThingWithComps thing in HeatNetwork.Members(net))
                {
                    CompHeatAccumulator tank = thing.GetComp<CompHeatAccumulator>();
                    if (tank == null || room <= 0f)
                    {
                        continue;
                    }
                    float above = tank.StoredWattDays - tank.Props.capacityWattDays * level;
                    if (above <= 0.01f)
                    {
                        continue;
                    }
                    float watts = Mathf.Min(room, above * GenDate.TicksPerDay / 60f);
                    tank.AddHeat(-watts * 60f / GenDate.TicksPerDay);
                    venting += watts;
                    room -= watts;
                }
            }
            if (venting > 1f)
            {
                Blow();
            }
        }

        private void Blow()
        {
            Map map = parent.Map;
            IntVec3 plume = PlumeCell;
            if (!plume.InBounds(map))
            {
                return;
            }
            GenTemperature.PushHeat(plume, map, venting * Props.heatPerWattSecond);
            SteamGrid.AddFromWatts(map, plume, venting, 1f);
            Vector3 at = plume.ToVector3Shifted();
            int puffs = venting > 1500f ? 3 : venting > 400f ? 2 : 1;
            for (int i = 0; i < puffs; i++)
            {
                FleckMaker.ThrowSmoke(at + new Vector3(Rand.Range(-0.3f, 0.3f), 0f, Rand.Range(-0.3f, 0.3f)), map,
                    Rand.Range(0.7f, 1.3f));
            }
            if (TrashbrickBurningMod.Hazards && venting >= Props.scaldAboveWatts)
            {
                foreach (Thing thing in plume.GetThingList(map).ToArray())
                {
                    if (thing is Pawn pawn && Rand.Chance(0.5f))
                    {
                        pawn.TakeDamage(new DamageInfo(DamageDefOf.Burn, Mathf.Lerp(2f, 6f, venting / Props.maxWatts), 0f, -1f, parent));
                    }
                }
            }
        }

        public override IEnumerable<Gizmo> CompGetGizmosExtra()
        {
            foreach (Gizmo g in base.CompGetGizmosExtra())
            {
                yield return g;
            }
            if (parent.Faction != Faction.OfPlayer)
            {
                yield break;
            }
            yield return new Command_VentDrain(this);
        }

        public override void PostDrawExtraSelectionOverlays()
        {
            base.PostDrawExtraSelectionOverlays();
            GenDraw.DrawFieldEdges(new List<IntVec3> { PlumeCell }, PlaceWorker_SteamVent.PlumeColor);
        }

        public string DrainLabel => drainLevel == NeverDrain
            ? "STB_VentDrainNever".Translate().Resolve()
            : "STB_VentDrainAbove".Translate(DrainLevels[Mathf.Clamp(drainLevel, 0, DrainLevels.Length - 1)].ToStringPercent()).Resolve();

        public override string CompInspectStringExtra()
        {
            if (!TrashbrickBurningMod.Advanced)
            {
                return null;
            }
            string s = "STB_VentStatus".Translate(venting.ToString("0"), Props.maxWatts.ToString("0"));
            s += "\n" + "STB_VentMode".Translate(DrainLabel).Resolve();
            if (HeatNetwork.NetOf(parent) == null)
            {
                s += "\n" + "STB_AccIdleNoPipe".Translate();
            }
            return s;
        }
    }

    /// <summary>Left-click steps never → 25% → 50% → 75%; right-click picks one.</summary>
    public class Command_VentDrain : Command_Action
    {
        private readonly CompSteamVent vent;

        public Command_VentDrain(CompSteamVent vent)
        {
            this.vent = vent;
            defaultLabel = vent.DrainLabel;
            defaultDesc = "STB_VentDrainDesc".Translate();
            icon = TexCommand.ForbidOff;
            action = () =>
            {
                int next = vent.drainLevel + 1;
                vent.drainLevel = next >= CompSteamVent.DrainLevels.Length ? CompSteamVent.NeverDrain : next;
            };
        }

        public override IEnumerable<FloatMenuOption> RightClickFloatMenuOptions
        {
            get
            {
                yield return new FloatMenuOption("STB_VentDrainNever".Translate(), () => vent.drainLevel = CompSteamVent.NeverDrain);
                for (int i = 0; i < CompSteamVent.DrainLevels.Length; i++)
                {
                    int level = i;
                    yield return new FloatMenuOption("STB_VentDrainAbove".Translate(CompSteamVent.DrainLevels[i].ToStringPercent()),
                        () => vent.drainLevel = level);
                }
            }
        }
    }
}
