using RimWorld;
using UnityEngine;
using Verse;

namespace TrashbrickBurning
{
    /// <summary>
    /// A visible jet out of a steam vent or exhaust port: a stream of STB_JetPuff flecks shot out in
    /// the outlet's direction, more of them, faster and bigger the harder it's blowing (strength 0
    /// to 1). Vanilla's fleck system draws them instanced, like fire smoke. Each outlet keeps its
    /// own accumulator, so the stream is steady rather than lumpy.
    /// </summary>
    public class GasJet
    {
        public static readonly Color Steam = new Color(0.94f, 0.96f, 1f);
        public static readonly Color ToxGas = new Color(0.74f, 0.8f, 0.36f);
        public static readonly Color RotStink = new Color(0.56f, 0.47f, 0.33f);

        /// <summary>Ticks between calls of Tick; the accumulator carries the fractions over.</summary>
        public const int TickInterval = 3;

        private static FleckDef def;
        private float accumulator;

        /// <summary>
        /// Call every TickInterval ticks while blowing. angle is the jet's direction (Rot4.AsAngle:
        /// 0 = north, 90 = east), spread how far the puffs scatter either side of it, in degrees.
        /// </summary>
        public void Tick(Map map, Vector3 origin, float angle, float strength, Color color, float spread = 10f)
        {
            strength = Mathf.Clamp01(strength);
            if (map == null || strength <= 0.01f || Find.CurrentMap != map)
            {
                accumulator = 0f;
                return;
            }
            def = def ?? DefDatabase<FleckDef>.GetNamedSilentFail("STB_JetPuff");
            if (def == null || !Find.CameraDriver.CurrentViewRect.ExpandedBy(4).Contains(origin.ToIntVec3()))
            {
                return;
            }
            accumulator += (2f + 12f * strength) * TickInterval / 60f;
            while (accumulator >= 1f)
            {
                accumulator -= 1f;
                FleckCreationData data = FleckMaker.GetDataStatic(origin, map, def, Rand.Range(0.3f, 0.45f) + 0.35f * strength);
                data.velocityAngle = angle + Rand.Range(-spread, spread);
                data.velocitySpeed = (0.6f + 2.4f * strength) * Rand.Range(0.8f, 1.2f);
                data.rotation = Rand.Range(0f, 360f);
                data.rotationRate = Rand.Range(-30f, 30f);
                data.instanceColor = new Color(color.r, color.g, color.b, 0.35f + 0.35f * strength);
                map.flecks.CreateFleck(data);
            }
        }
    }
}
