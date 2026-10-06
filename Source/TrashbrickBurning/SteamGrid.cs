using System.Collections.Generic;
using RimWorld;
using UnityEngine;
using Verse;

namespace TrashbrickBurning
{
    /// <summary>
    /// Visible steam. Vents, Overpressure Tank releases and bleeds, safety valves, leaks and bursts
    /// let steam into the cells they blow into; it spreads like a gas through open cells and open
    /// doors, drifts off fast outdoors, and indoors hangs in the air and slowly condenses - filling a
    /// room as a white fog and keeping it hot, on top of the heat its source already pushed, up to
    /// SteamMaxTemperature. Densities are per cell: 1 is a thick fog.
    /// </summary>
    public class SteamGrid : MapComponent
    {
        private const int StepTicks = 30;
        private const float StepSeconds = StepTicks / 60f;

        /// <summary>Share of the difference that flows to each open neighbour a step (stable below 0.25).</summary>
        private const float SpreadRate = 0.18f;

        /// <summary>Lost a step outdoors: it blows away.</summary>
        private const float OutdoorLoss = 0.2f;

        /// <summary>Lost a step indoors in a hot room; up to three times that in a cold one.</summary>
        private const float IndoorLoss = 0.006f;

        /// <summary>Heat a second from each unit of steam in a room.</summary>
        public const float HeatPerUnitPerSecond = 5f;

        /// <summary>Steam heats a room up to about this: it's water vapour, not fire.</summary>
        public const float SteamMaxTemperature = 100f;

        private const float Gone = 0.005f;

        /// <summary>Density at which a cell puffs most often and most opaque.</summary>
        private const float FullFog = 0.6f;

        /// <summary>Chance a step that a cell at full fog puffs out a steam fleck.</summary>
        private const float PuffChance = 0.45f;

        private static FleckDef puffDef;

        private float[] grid;
        private HashSet<int> active = new HashSet<int>();

        public SteamGrid(Map map) : base(map)
        {
        }

        private float[] Grid => grid ?? (grid = new float[map.cellIndices.NumGridCells]);

        public static bool Enabled => TrashbrickBurningMod.S.steamClouds;

        /// <summary>Lets steam into a cell (or the nearest open cell next to it, if it's walled off).</summary>
        public static void Add(Map map, IntVec3 cell, float amount)
        {
            if (!Enabled || map == null || amount <= 0f || !cell.InBounds(map))
            {
                return;
            }
            SteamGrid steam = map.GetComponent<SteamGrid>();
            if (steam == null)
            {
                return;
            }
            if (!steam.GasCanPass(cell))
            {
                foreach (IntVec3 c in GenAdj.CellsAdjacentCardinal(cell, Rot4.North, IntVec2.One))
                {
                    if (c.InBounds(map) && steam.GasCanPass(c))
                    {
                        cell = c;
                        break;
                    }
                }
            }
            int i = map.cellIndices.CellToIndex(cell);
            steam.Grid[i] += amount;
            steam.active.Add(i);
        }

        /// <summary>Steam from venting heat: a 3000W vent lets out half a unit a second.</summary>
        public static void AddFromWatts(Map map, IntVec3 cell, float watts, float seconds) =>
            Add(map, cell, watts * seconds / 6000f);

        public static float DensityAt(Map map, IntVec3 cell)
        {
            SteamGrid steam = map?.GetComponent<SteamGrid>();
            return steam?.grid == null || !cell.InBounds(map) ? 0f : steam.grid[map.cellIndices.CellToIndex(cell)];
        }

        /// <summary>Gas gets through: no full-height building in the way, or an open door.</summary>
        private bool GasCanPass(IntVec3 c)
        {
            Building edifice = c.GetEdifice(map);
            if (edifice is Building_Door door)
            {
                return door.Open;
            }
            return edifice == null || edifice.def.Fillage != FillCategory.Full;
        }

        public override void MapComponentTick()
        {
            base.MapComponentTick();
            if (active.Count == 0 || Find.TickManager.TicksGame % StepTicks != 0)
            {
                return;
            }
            if (!Enabled)
            {
                Clear();
                return;
            }
            Step();
        }

        private void Clear()
        {
            foreach (int i in active)
            {
                grid[i] = 0f;
            }
            active.Clear();
        }

        private void Step()
        {
            float[] g = Grid;
            CellIndices indices = map.cellIndices;
            List<int> cells = new List<int>(active);
            Dictionary<int, float> delta = new Dictionary<int, float>();

            // Spread: each cell shares with its open neighbours that have less.
            foreach (int i in cells)
            {
                float d = g[i];
                IntVec3 c = indices.IndexToCell(i);
                for (int k = 0; k < 4; k++)
                {
                    IntVec3 n = c + GenAdj.CardinalDirections[k];
                    if (!n.InBounds(map) || !GasCanPass(n))
                    {
                        continue;
                    }
                    int ni = indices.CellToIndex(n);
                    float flow = (d - g[ni]) * SpreadRate;
                    if (flow <= 0f)
                    {
                        continue;
                    }
                    delta.TryGetValue(i, out float a);
                    delta[i] = a - flow;
                    delta.TryGetValue(ni, out float b);
                    delta[ni] = b + flow;
                }
            }
            foreach (KeyValuePair<int, float> pair in delta)
            {
                g[pair.Key] = Mathf.Max(0f, g[pair.Key] + pair.Value);
                active.Add(pair.Key);
            }

            // Drift off outdoors, condense indoors, and heat the rooms it hangs in.
            Dictionary<Room, float> rooms = new Dictionary<Room, float>();
            Dictionary<Room, IntVec3> roomCell = new Dictionary<Room, IntVec3>();
            cells = new List<int>(active);
            foreach (int i in cells)
            {
                IntVec3 c = indices.IndexToCell(i);
                if (!GasCanPass(c))
                {
                    // A door shut on it, or a wall went up: it condenses on the spot.
                    g[i] = 0f;
                    active.Remove(i);
                    continue;
                }
                Room room = c.GetRoom(map);
                bool outdoors = room == null || room.UsesOutdoorTemperature;
                float loss = OutdoorLoss;
                if (!outdoors)
                {
                    loss = IndoorLoss * (1f + 2f * Mathf.Clamp01((40f - room.Temperature) / 60f));
                    rooms.TryGetValue(room, out float sum);
                    rooms[room] = sum + g[i];
                    roomCell[room] = c;
                }
                g[i] *= 1f - loss;
                if (g[i] < Gone)
                {
                    g[i] = 0f;
                    active.Remove(i);
                }
            }
            foreach (KeyValuePair<Room, float> pair in rooms)
            {
                if (pair.Key.Temperature < SteamMaxTemperature)
                {
                    GenTemperature.PushHeat(roomCell[pair.Key], map, pair.Value * HeatPerUnitPerSecond * StepSeconds);
                }
            }
            ThrowPuffs();
        }

        /// <summary>
        /// The visible steam: vanilla flecks, drawn instanced in batches like fire smoke. Each cell on
        /// screen puffs one out now and then - more often and more opaque the thicker its steam - which
        /// drifts a little, swells and fades over about three seconds. Only for the map being looked
        /// at, and only cells in view.
        /// </summary>
        private void ThrowPuffs()
        {
            if (Find.CurrentMap != map)
            {
                return;
            }
            puffDef = puffDef ?? DefDatabase<FleckDef>.GetNamedSilentFail("STB_SteamPuff");
            if (puffDef == null)
            {
                return;
            }
            CellRect view = Find.CameraDriver.CurrentViewRect.ExpandedBy(2);
            foreach (int i in active)
            {
                float d = grid[i];
                if (d < 0.03f)
                {
                    continue;
                }
                IntVec3 c = map.cellIndices.IndexToCell(i);
                float thick = Mathf.Min(1f, d / FullFog);
                if (!view.Contains(c) || !Rand.Chance(PuffChance * (0.3f + 0.7f * thick)))
                {
                    continue;
                }
                Vector3 pos = c.ToVector3Shifted() + new Vector3(Rand.Range(-0.4f, 0.4f), 0f, Rand.Range(-0.4f, 0.4f));
                FleckCreationData data = FleckMaker.GetDataStatic(pos, map, puffDef, Rand.Range(1.6f, 2.3f));
                data.rotation = Rand.Range(0f, 360f);
                data.rotationRate = Rand.Range(-12f, 12f);
                data.velocityAngle = Rand.Range(0f, 360f);
                data.velocitySpeed = Rand.Range(0.05f, 0.2f);
                data.instanceColor = new Color(0.94f, 0.96f, 1f, 0.12f + 0.38f * thick);
                map.flecks.CreateFleck(data);
            }
        }

        public override void ExposeData()
        {
            base.ExposeData();
            List<int> cells = null;
            List<float> values = null;
            if (Scribe.mode == LoadSaveMode.Saving)
            {
                cells = new List<int>(active);
                values = new List<float>();
                foreach (int i in cells)
                {
                    values.Add(Grid[i]);
                }
            }
            Scribe_Collections.Look(ref cells, "steamCells", LookMode.Value);
            Scribe_Collections.Look(ref values, "steamValues", LookMode.Value);
            if (Scribe.mode == LoadSaveMode.PostLoadInit && cells != null && values != null)
            {
                active = new HashSet<int>();
                for (int k = 0; k < cells.Count && k < values.Count; k++)
                {
                    if (cells[k] >= 0 && cells[k] < Grid.Length)
                    {
                        Grid[cells[k]] = values[k];
                        active.Add(cells[k]);
                    }
                }
            }
        }
    }
}
