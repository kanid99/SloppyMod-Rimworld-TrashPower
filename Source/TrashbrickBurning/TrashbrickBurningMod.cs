using System.Collections.Generic;
using RimWorld;
using UnityEngine;
using Verse;

namespace TrashbrickBurning
{
    public class TrashbrickSettings : ModSettings
    {
        /// <summary>
        /// Advanced: stoves are burners (250/350/500W of heat) that feed steam turbines, radiators and
        /// heat accumulators; their own engine makes only 100-300W. Simple: stoves are self-contained
        /// generators and the heat network is hidden.
        /// </summary>
        public bool advanced = true;

        /// <summary>Overpressure bursts and steam leaks.</summary>
        public bool hazards = true;

        /// <summary>Burners also take wood and chemfuel, at their own fuel values.</summary>
        public bool otherFuels = true;

        /// <summary>Vanilla Furniture Expanded - Factory machines give off fumes while they work (CompFactoryFumes).</summary>
        public bool factoryFumes = true;

        /// <summary>Steam hangs in the air as a visible cloud that spreads, heats rooms and condenses (SteamGrid).</summary>
        public bool steamClouds = true;

        /// <summary>With Dubs Bad Hygiene in advanced mode, burners only burn with plumbing water flowing.</summary>
        public bool requireWater = true;

        public float fuelUseMultiplier = 1f;
        public float powerMultiplier = 1f;
        public float pollutionMultiplier = 1f;
        public float leakFrequencyMultiplier = 1f;

        public override void ExposeData()
        {
            base.ExposeData();
            Scribe_Values.Look(ref advanced, "advanced", true);
            Scribe_Values.Look(ref hazards, "hazards", true);
            Scribe_Values.Look(ref otherFuels, "otherFuels", true);
            Scribe_Values.Look(ref factoryFumes, "factoryFumes", true);
            Scribe_Values.Look(ref steamClouds, "steamClouds", true);
            Scribe_Values.Look(ref requireWater, "requireWater", true);
            Scribe_Values.Look(ref fuelUseMultiplier, "fuelUseMultiplier", 1f);
            Scribe_Values.Look(ref powerMultiplier, "powerMultiplier", 1f);
            Scribe_Values.Look(ref pollutionMultiplier, "pollutionMultiplier", 1f);
            Scribe_Values.Look(ref leakFrequencyMultiplier, "leakFrequencyMultiplier", 1f);
        }
    }

    public class TrashbrickBurningMod : Mod
    {
        public static TrashbrickSettings Settings;

        public TrashbrickBurningMod(ModContentPack content) : base(content)
        {
            Settings = GetSettings<TrashbrickSettings>();
        }

        public static TrashbrickSettings S => Settings ?? (Settings = new TrashbrickSettings());

        public static bool Advanced => S.advanced;

        public static bool Hazards => S.hazards;

        public override string SettingsCategory() => "STB_SettingsCategory".Translate();

        public override void DoSettingsWindowContents(Rect inRect)
        {
            TrashbrickSettings s = S;
            Listing_Standard list = new Listing_Standard();
            list.Begin(inRect);
            // The installed build, from About.xml (Source/build.sh stamps it), so a bug report can name it.
            list.Label("STB_SettingVersion".Translate(Content.ModMetaData.ModVersion));
            list.GapLine();
            list.CheckboxLabeled("STB_SettingAdvanced".Translate(), ref s.advanced, "STB_SettingAdvancedDesc".Translate());
            list.Label(s.advanced ? "STB_SettingAdvancedExplain".Translate() : "STB_SettingSimpleExplain".Translate());
            list.Gap();
            list.CheckboxLabeled("STB_SettingHazards".Translate(), ref s.hazards, "STB_SettingHazardsDesc".Translate());
            list.CheckboxLabeled("STB_SettingSteamClouds".Translate(), ref s.steamClouds, "STB_SettingSteamCloudsDesc".Translate());
            list.CheckboxLabeled("STB_SettingOtherFuels".Translate(), ref s.otherFuels, "STB_SettingOtherFuelsDesc".Translate());
            // Only with Vanilla Furniture Expanded - Factory loaded (its About.xml has no packageId to check).
            if (DefDatabase<ThingDef>.GetNamedSilentFail("VFEFactory_AutomatedSmelter") != null)
            {
                list.CheckboxLabeled("STB_SettingFactoryFumes".Translate(), ref s.factoryFumes, "STB_SettingFactoryFumesDesc".Translate());
            }
            if (ModsConfig.IsActive(CompStirlingEngine.DubsBadHygieneId))
            {
                list.CheckboxLabeled("STB_SettingRequireWater".Translate(), ref s.requireWater, "STB_SettingRequireWaterDesc".Translate());
            }
            list.Gap();
            Slider(list, "STB_SettingFuelUse", ref s.fuelUseMultiplier);
            Slider(list, "STB_SettingPower", ref s.powerMultiplier);
            Slider(list, "STB_SettingPollution", ref s.pollutionMultiplier, 0f);
            if (s.hazards)
            {
                Slider(list, "STB_SettingLeaks", ref s.leakFrequencyMultiplier, 0.1f, 5f);
            }
            list.Gap();
            if (list.ButtonText("STB_SettingReset".Translate()))
            {
                s.fuelUseMultiplier = s.powerMultiplier = s.pollutionMultiplier = s.leakFrequencyMultiplier = 1f;
            }
            list.Gap();
            list.Label("STB_SettingRestart".Translate());
            list.End();
        }

        private static void Slider(Listing_Standard list, string key, ref float value, float min = 0.25f, float max = 3f)
        {
            list.Label(key.Translate(value.ToStringPercent()));
            value = Mathf.Round(list.Slider(value, min, max) * 20f) / 20f;
        }
    }

    /// <summary>
    /// Applies the settings that change defs, once at startup: in simple play mode the heat network
    /// comes off the build menu, and with other fuels switched off the burners and fuel hopper stop
    /// taking wood and chemfuel.
    /// </summary>
    [StaticConstructorOnStartup]
    public static class ApplyPlayMode
    {
        private static readonly string[] AdvancedOnly =
        {
            "STB_SteamTurbine", "STB_CobbledTurbine", "STB_HotWaterPipe", "STB_HotWaterPipeHidden",
            "STB_HotWaterValve", "STB_HotWaterRadiator", "STB_CobbledRadiator", "STB_HeatAccumulator", "STB_SteamVent", "STB_SteamVentGround",
            // All heat and no engine: useless without turbines.
            "STB_LargeCobbledStove", "STB_LargeGasifier", "STB_IndustrialGasifier"
        };

        static ApplyPlayMode()
        {
            if (!TrashbrickBurningMod.S.otherFuels)
            {
                RemoveOtherFuels();
            }
            if (TrashbrickBurningMod.Advanced)
            {
                return;
            }
            // They may sit in more than one architect tab (the pipes move to VE's pipe networks tab
            // when it exists), so every tab they came from has its designator list rebuilt.
            HashSet<DesignationCategoryDef> categories = new HashSet<DesignationCategoryDef>();
            foreach (string name in AdvancedOnly)
            {
                ThingDef def = DefDatabase<ThingDef>.GetNamedSilentFail(name);
                if (def?.designationCategory == null)
                {
                    continue;
                }
                categories.Add(def.designationCategory);
                def.designationCategory = null;
            }
            foreach (DesignationCategoryDef category in categories)
            {
                category.ResolveReferences();
            }
        }

        private static void RemoveOtherFuels()
        {
            foreach (ThingDef def in DefDatabase<ThingDef>.AllDefsListForReading)
            {
                CompProperties_StirlingEngine engine = def.GetCompProperties<CompProperties_StirlingEngine>();
                if (engine == null || engine.otherFuels.NullOrEmpty())
                {
                    continue;
                }
                CompProperties_Refuelable fuel = def.GetCompProperties<CompProperties_Refuelable>();
                foreach (FuelValue other in engine.otherFuels)
                {
                    if (other.optional)
                    {
                        fuel?.fuelFilter.SetAllow(other.thing, false);
                    }
                }
            }
            ThingDef hopper = DefDatabase<ThingDef>.GetNamedSilentFail("STB_FuelHopper");
            if (hopper?.building != null)
            {
                foreach (string name in new[] { "WoodLog", "Chemfuel", "Hay", "Cloth", "Bioferrite", "VCHE_Deepchem" })
                {
                    ThingDef other = DefDatabase<ThingDef>.GetNamedSilentFail(name);
                    if (other != null)
                    {
                        hopper.building.fixedStorageSettings?.filter.SetAllow(other, false);
                        hopper.building.defaultStorageSettings?.filter.SetAllow(other, false);
                    }
                }
            }
        }
    }
}
