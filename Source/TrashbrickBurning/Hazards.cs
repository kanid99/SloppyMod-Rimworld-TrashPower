using System.Collections.Generic;
using System.Linq;
using PipeSystem;
using RimWorld;
using UnityEngine;
using Verse;
using Verse.Sound;

namespace TrashbrickBurning
{
    /// <summary>
    /// A burner without a safety valve at full pressure: a 1000C steam cloud out to five tiles.
    /// Every room the cloud reaches is pushed towards 1000C by the share of it the cloud fills, so a
    /// small room the cloud fills outright is 1000C and a big hall only warms; outdoors disperses
    /// it. Anyone in the cloud is scalded, worst at the centre. The burner then breaks down and needs
    /// a component to repair, like any breakdown.
    /// </summary>
    public static class SteamBurst
    {
        public const float Radius = 5f;
        public const float CloudTemperature = 1000f;

        public static void Burst(ThingWithComps source)
        {
            Map map = source.Map;
            if (map == null)
            {
                return;
            }
            IntVec3 center = source.OccupiedRect().CenterCell;
            Cloud(center, map, Radius, source);

            source.TakeDamage(new DamageInfo(DamageDefOf.Blunt, source.MaxHitPoints * 0.25f, 0f, -1f, source));
            if (!source.Destroyed)
            {
                source.GetComp<CompBreakdownable>()?.DoBreakdown();
            }
            Find.LetterStack.ReceiveLetter("STB_BurstLabel".Translate(), "STB_BurstText".Translate(source.LabelShort),
                LetterDefOf.NegativeEvent, new TargetInfo(center, map));
        }

        /// <summary>The 1000C cloud itself: rooms it reaches heat by the share it fills, pawns in it are scalded.</summary>
        public static void Cloud(IntVec3 center, Map map, float radius, Thing source)
        {
            List<IntVec3> cells = GenRadial.RadialCellsAround(center, radius, true)
                .Where(c => c.InBounds(map) && GenSight.LineOfSight(center, c, map, true))
                .ToList();

            Dictionary<Room, int> roomCells = new Dictionary<Room, int>();
            foreach (IntVec3 cell in cells)
            {
                Room room = cell.GetRoom(map);
                if (room != null && !room.UsesOutdoorTemperature)
                {
                    roomCells.TryGetValue(room, out int n);
                    roomCells[room] = n + 1;
                }
            }
            foreach (KeyValuePair<Room, int> pair in roomCells)
            {
                float share = Mathf.Clamp01((float)pair.Value / Mathf.Max(1, pair.Key.CellCount));
                pair.Key.Temperature = Mathf.Max(pair.Key.Temperature,
                    Mathf.Lerp(pair.Key.Temperature, CloudTemperature, share));
            }

            HashSet<Pawn> scalded = new HashSet<Pawn>();
            foreach (IntVec3 cell in cells)
            {
                foreach (Thing thing in cell.GetThingList(map).ToList())
                {
                    if (thing is Pawn pawn && scalded.Add(pawn))
                    {
                        float t = cell.DistanceTo(center) / radius;
                        for (int i = 0; i < 2; i++)
                        {
                            pawn.TakeDamage(new DamageInfo(DamageDefOf.Burn, Mathf.Lerp(26f, 7f, t), 0f, -1f, source));
                        }
                    }
                }
                if (Rand.Chance(0.6f))
                {
                    FleckMaker.ThrowSmoke(cell.ToVector3Shifted(), map, Rand.Range(1.4f, 2.6f));
                }
                // The cloud hangs: thick at the centre, thinner at the edge.
                SteamGrid.Add(map, cell, 1.5f * (1f - 0.6f * cell.DistanceTo(center) / radius));
            }
            FleckMaker.ThrowHeatGlow(center, map, 4f);
            (DefDatabase<SoundDef>.GetNamedSilentFail("Explosion_Smoke")
             ?? DefDatabase<SoundDef>.GetNamedSilentFail("Explosion_Flame"))?.PlayOneShot(new TargetInfo(center, map));
        }

        /// <summary>A safety valve lifting: puffs of steam and a little heat, no harm done.</summary>
        public static void Vent(Thing source, Vector3 at)
        {
            Map map = source.Map;
            if (map == null)
            {
                return;
            }
            for (int i = 0; i < 2; i++)
            {
                FleckMaker.ThrowSmoke(at, map, Rand.Range(0.6f, 1.0f));
            }
            GenTemperature.PushHeat(source.Position, map, 8f);
            SteamGrid.Add(map, at.ToIntVec3(), 0.08f);
        }
    }

    public class CompProperties_SteamLeak : CompProperties
    {
        /// <summary>
        /// Mean days between leaks on one network while hot water flows through it. Each connected
        /// piece rolls, scaled by how many pieces the network has, so a long network leaks no more
        /// often than a short one - it just has more places to do it.
        /// </summary>
        public float mtbDaysPerNetwork = 20f;

        /// <summary>A leak knocks off this much of the part's hit points; it leaks until repaired.</summary>
        public float damageFraction = 0.3f;

        public CompProperties_SteamLeak()
        {
            compClass = typeof(CompSteamLeak);
        }
    }

    /// <summary>
    /// Pressurised hot water pipes and turbines spring leaks now and then. A leak damages the part,
    /// and while it's damaged and hot water flows it sprays scalding steam over the cells around it,
    /// burning anyone passing. Repairing it stops the leak. A part badly damaged some other way -
    /// a raid, a fire - starts leaking too.
    /// </summary>
    public class CompSteamLeak : ThingComp
    {
        private const float StopLeakingAt = 0.9f;
        private const float LeakWhenBelow = 0.5f;

        private bool leaking;

        private CompProperties_SteamLeak Props => (CompProperties_SteamLeak)props;

        public bool Leaking => leaking;

        public override void PostExposeData()
        {
            base.PostExposeData();
            Scribe_Values.Look(ref leaking, "leaking", false);
        }

        public override void CompTick()
        {
            base.CompTick();
            if (parent.IsHashIntervalTick(GenTicks.TickRareInterval))
            {
                Check();
            }
        }

        public override void CompTickRare()
        {
            base.CompTickRare();
            Check();
        }

        private void Check()
        {
            if (!parent.Spawned || !TrashbrickBurningMod.Advanced || !TrashbrickBurningMod.Hazards)
            {
                leaking = false;
                return;
            }
            if (leaking && parent.HitPoints >= parent.MaxHitPoints * StopLeakingAt)
            {
                leaking = false;
            }
            PipeNet net = HeatNetwork.NetOf(parent);
            if (net == null)
            {
                return;
            }
            HeatNetwork.Flow f = HeatNetwork.Compute(net);
            bool hot = f.heat > 0f || f.Discharge > 0f;
            if (!hot)
            {
                return;
            }
            if (!leaking)
            {
                float mult = Mathf.Max(0.01f, TrashbrickBurningMod.S.leakFrequencyMultiplier);
                float mtb = Props.mtbDaysPerNetwork * Mathf.Max(1, net.connectors.Count) / mult;
                if (parent.HitPoints < parent.MaxHitPoints * LeakWhenBelow)
                {
                    leaking = true;
                }
                else if (Rand.MTBEventOccurs(mtb, GenDate.TicksPerDay, GenTicks.TickRareInterval))
                {
                    StartLeak();
                }
            }
            if (leaking)
            {
                Spray();
            }
        }

        private void StartLeak()
        {
            leaking = true;
            parent.TakeDamage(new DamageInfo(DamageDefOf.Deterioration, parent.MaxHitPoints * Props.damageFraction));
            Messages.Message("STB_LeakMessage".Translate(parent.LabelShort), parent, MessageTypeDefOf.NegativeEvent);
        }

        private void Spray()
        {
            Map map = parent.Map;
            IntVec3 pos = parent.Position;
            FleckMaker.ThrowSmoke(parent.TrueCenter(), map, Rand.Range(0.8f, 1.3f));
            GenTemperature.PushHeat(pos, map, 30f);
            SteamGrid.Add(map, pos, 0.8f);
            foreach (IntVec3 cell in GenAdj.CellsAdjacent8Way(parent).Concat(parent.OccupiedRect().Cells))
            {
                if (!cell.InBounds(map))
                {
                    continue;
                }
                foreach (Thing thing in cell.GetThingList(map).ToList())
                {
                    if (thing is Pawn pawn && Rand.Chance(0.5f))
                    {
                        pawn.TakeDamage(new DamageInfo(DamageDefOf.Burn, Rand.Range(2f, 5f), 0f, -1f, parent));
                    }
                }
            }
        }

        public override string CompInspectStringExtra()
        {
            return leaking ? "STB_Leaking".Translate().ToString() : null;
        }
    }
}
