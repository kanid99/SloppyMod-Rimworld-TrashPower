using System.Collections.Generic;
using HarmonyLib;
using RimWorld;
using UnityEngine;
using Verse;
using Verse.AI;

namespace TrashbrickBurning
{
    [StaticConstructorOnStartup]
    public static class HarmonyInit
    {
        static HarmonyInit()
        {
            Harmony harmony = new Harmony("kanid99.SloppyTrashbrickBurning");
            harmony.PatchAll();
            Patch_CompactorExhaust.Apply(harmony);
        }
    }

    /// <summary>
    /// Vanilla Chemfuel Expanded's chemfuel and deepchem pipes feed a burner through VEF's
    /// CompRefillWithPipes, which counts each pipe unit as one fuel unit and ignores the fuel bill.
    /// On our burners the burner does the refill instead (CompStirlingEngine.RefillFromPipe).
    /// </summary>
    [HarmonyPatch(typeof(PipeSystem.CompRefillWithPipes), nameof(PipeSystem.CompRefillWithPipes.Refill))]
    public static class Patch_RefillWithPipes
    {
        public static bool Prefix(PipeSystem.CompRefillWithPipes __instance, float __0, ref float __result)
        {
            CompStirlingEngine engine = __instance.parent.GetComp<CompStirlingEngine>();
            if (engine == null)
            {
                return true;
            }
            PipeSystem.CompProperties_RefillWithPipes props = __instance.Props;
            __result = engine.RefillFromPipe(props.thing, props.ratio, __0);
            return false;
        }
    }

    /// <summary>
    /// VEF only links the refuelable when its fuel filter allows the pipe's fuel, but the net reads
    /// it unchecked when it sums demand. With the other-fuels setting off, chemfuel isn't in a
    /// burner's filter, so link it anyway: RefillFromPipe still refuses what the filter doesn't allow.
    /// </summary>
    [HarmonyPatch(typeof(PipeSystem.CompRefillWithPipes), nameof(PipeSystem.CompRefillWithPipes.PostSpawnSetup))]
    public static class Patch_RefillWithPipes_Spawn
    {
        private static readonly System.Reflection.FieldInfo Refuelable =
            AccessTools.Field(typeof(PipeSystem.CompRefillWithPipes), "compRefuelable");

        public static void Postfix(PipeSystem.CompRefillWithPipes __instance)
        {
            if (Refuelable != null && Refuelable.GetValue(__instance) == null && __instance.parent.GetComp<CompStirlingEngine>() != null)
            {
                Refuelable.SetValue(__instance, __instance.parent.GetComp<CompRefuelable>());
            }
        }
    }

    /// <summary>
    /// Burners count other fuels at their own values - a wood log is worth less than a trashbrick,
    /// a unit of chemfuel more. CompRefuelable counts every item as one unit, so for our burners
    /// only, this does its item-by-item refuel instead, taking just enough of each stack to fill up.
    /// Everything else still goes through vanilla. Hauled fuel, hopper feed and the fuel gizmo all
    /// come through here; a VFE conveyor refuels by count directly and so counts every item as one.
    /// </summary>
    [HarmonyPatch(typeof(CompRefuelable), nameof(CompRefuelable.Refuel), new[] { typeof(List<Thing>) })]
    public static class Patch_CompRefuelable_Refuel
    {
        public static bool Prefix(CompRefuelable __instance, List<Thing> fuelThings)
        {
            CompStirlingEngine engine = __instance.parent.GetComp<CompStirlingEngine>();
            if (engine == null || fuelThings == null)
            {
                return true;
            }
            float room = __instance.Props.fuelCapacity - __instance.Fuel;
            while (room > 0.01f && fuelThings.Count > 0)
            {
                Thing thing = fuelThings[fuelThings.Count - 1];
                fuelThings.RemoveAt(fuelThings.Count - 1);
                if (!engine.Accepts(thing))
                {
                    continue;
                }
                // A corpse goes in bare: its clothes, weapon and inventory drop where it's fed in.
                if (thing is Corpse corpse && corpse.AnythingToStrip())
                {
                    corpse.Strip();
                }
                float value = Mathf.Max(0.01f, engine.Props.FuelValueOf(thing));
                int count = Mathf.Min(thing.stackCount, Mathf.Max(1, Mathf.CeilToInt(room / value)));
                engine.AddToMix(thing.def, count * value);
                __instance.Refuel(count * value);
                thing.SplitOff(count).Destroy();
                room -= count * value;
            }
            return false;
        }
    }

    /// <summary>
    /// The burner's fuel bill: colonists only bring fuel it allows, from within its search radius.
    /// Vanilla's fuel search only knows the def's filter, so a fuel it picks that the bill rules out
    /// is swapped for the nearest one the bill allows.
    /// </summary>
    [HarmonyPatch(typeof(RefuelWorkGiverUtility), "FindBestFuel")]
    public static class Patch_RefuelWorkGiverUtility_FindBestFuel
    {
        public static void Postfix(Pawn pawn, Thing refuelable, ref Thing __result)
        {
            CompStirlingEngine engine = (refuelable as ThingWithComps)?.GetComp<CompStirlingEngine>();
            CompRefuelable fuel = (refuelable as ThingWithComps)?.GetComp<CompRefuelable>();
            if (engine == null || fuel == null || __result == null || engine.Accepts(__result) && engine.InRange(__result))
            {
                return;
            }
            ThingFilter filter = fuel.Props.fuelFilter;
            __result = GenClosest.ClosestThingReachable(pawn.Position, pawn.Map, filter.BestThingRequest,
                PathEndMode.ClosestTouch, TraverseParms.For(pawn), 9999f,
                t => !t.IsForbidden(pawn) && pawn.CanReserve(t) && filter.Allows(t) && engine.Accepts(t) && engine.InRange(t));
        }
    }

    /// <summary>The same, for the fuel list a multi-item refuel gathers.</summary>
    [HarmonyPatch(typeof(RefuelWorkGiverUtility), "FindAllFuel")]
    public static class Patch_RefuelWorkGiverUtility_FindAllFuel
    {
        public static void Postfix(Thing refuelable, ref List<Thing> __result)
        {
            CompStirlingEngine engine = (refuelable as ThingWithComps)?.GetComp<CompStirlingEngine>();
            if (engine != null && __result != null)
            {
                __result.RemoveAll(t => !engine.Accepts(t) || !engine.InRange(t));
                if (__result.Count == 0)
                {
                    __result = null;
                }
            }
        }
    }

    /// <summary>
    /// Vanilla Recycling Expanded's garbage compactor lets out toxic gas at its interaction spot while
    /// it works (Building_Compactor.Tick calls GasUtility.AddGas). While a compactor is ticking, any
    /// toxic gas it adds is offered to its exhaust network; if a powered port takes it, it isn't
    /// let out at the compactor. Patched by name, so nothing here depends on VRE's assembly.
    /// </summary>
    public static class Patch_CompactorExhaust
    {
        [System.ThreadStatic]
        private static CompExhaustSource ticking;

        public static void Apply(Harmony harmony)
        {
            System.Type compactor = AccessTools.TypeByName("VanillaRecyclingExpanded.Building_Compactor");
            System.Reflection.MethodInfo tick = compactor == null ? null : AccessTools.Method(compactor, "Tick");
            System.Reflection.MethodInfo addGas = AccessTools.Method(typeof(GasUtility), nameof(GasUtility.AddGas),
                new[] { typeof(IntVec3), typeof(Map), typeof(GasType), typeof(int) });
            if (tick == null || addGas == null)
            {
                return;
            }
            harmony.Patch(tick, new HarmonyMethod(typeof(Patch_CompactorExhaust), nameof(TickPrefix)),
                finalizer: new HarmonyMethod(typeof(Patch_CompactorExhaust), nameof(TickFinalizer)));
            harmony.Patch(addGas, new HarmonyMethod(typeof(Patch_CompactorExhaust), nameof(AddGasPrefix)));
        }

        public static void TickPrefix(Thing __instance)
        {
            ticking = (__instance as ThingWithComps)?.GetComp<CompExhaustSource>();
        }

        public static System.Exception TickFinalizer(System.Exception __exception)
        {
            ticking = null;
            return __exception;
        }

        public static bool AddGasPrefix(GasType gasType, ref int amount)
        {
            if (ticking == null || gasType != GasType.ToxGas)
            {
                return true;
            }
            amount = ticking.RouteGas(amount);
            // What the ports and expansion tanks couldn't take still comes out at the compactor.
            return amount > 0;
        }
    }
}
