# SloppyMod Trash POWER!
A RimWorld mod (1.5 / 1.6) for burning trash bricks, and maybe more, for power.

## Requirements
- **Required:** Vanilla Expanded Framework (VRE already needs it; its PipeSystem runs the hot water network) and Harmony (VEF needs it too)
- **Required:** [Vanilla Recycling Expanded](https://steamcommunity.com/sharedfiles/filedetails/?id=3155781848) (and what it needs: Vanilla Expanded Framework, Biotech)
- **Optional:** Dubs Bad Hygiene (in full or Lite mode). If it's loaded, sludge pellets and the plumbing modes switch on.
- **Optional:** Vanilla Furniture Expanded - Factory. If it's loaded, conveyor compatibility switches on (see below).

## What it adds
### Play modes (Mod settings)
**Advanced** (default): gasifiers are **burners** that feed **steam turbines** through pressurised hot water pipes.
**Simple**: gasifiers are self-contained generators, and the turbines and pipes aren't in the build menu.
Modes and power switch over straight away; the build menu updates after a restart.

### Trash gasifiers (Power tab)
The whole system is **trash gasification**. The **cobbled trash gasifier** is the early, jerry-rigged one. The **trash gasifier** is the baseline unit: cleaner, more efficient and safer.

| | Cobbled trash gasifier | Trash gasifier |
|---|---|---|
| Size | 2x2 | 2x2 |
| Research | Electricity + VRE complex recycling | Microelectronics + VRE complex recycling |
| Cost | 120 steel, 2 components | 150 steel, 25 plasteel, 4 components |
| Pressure safety | **no safety valve**: at full pressure it bursts | safety valve vents |
| Exhaust | heavy: 0.06 polluted cells and 1000 toxic gas per brick | filtered: 0.02 and 1200 per brick (it burns fewer) |
| Breakdowns | twice as often | normal |

**Advanced mode:** each burner has a **mode** button: eco, normal or high. Eco gets the most heat from each brick but makes the least; high makes the most, wastes the most fuel and heats the room most.

| Mode | Cobbled: heat on fuel/day | Trash gasifier: heat on fuel/day | Stirling power (cobbled / gasifier) | Water with DBH (cobbled / gasifier) |
|---|---|---|---|---|
| Eco | 600W on 40 (15W per brick) | 750W on 30 (**25W per brick**) | 75W / 100W | 16 / 20 a day |
| Normal | 1200W on 100 (12W) | **1500W on 75** (20W) | 150W / 250W | 32 / 40 a day |
| High | 1600W on 150 (10.7W) | 2000W on 112.5 (17.8W) | 300W / 500W | 43 / 53 a day |

- **Stirling engine:** with **no steam turbine on its network**, a burner's own Stirling engine makes a little power, using **three times its output in heat**. The rest of the heat still goes out on the pipe, so even in Stirling mode a burner needs an Overpressure Tank or radiators, or its pressure builds. As soon as a turbine is on the network, the Stirling engines stand down.
- **Sync burners** copies a burner's mode, hot water share and fuel choices to the other burners on its network, or on the map.

**Simple mode:** the cobbled gasifier makes **1000W** on 20 bricks a day; the trash gasifier makes **1200W** on 12.

### Large and industrial burners (advanced mode, Power tab)
Bigger burners with **no engine of their own**, so they need steam turbines. They scale with their size: the large ones make **three times** the heat of their small counterpart, the industrial one **six times** a trash gasifier's, and each gets more out of every brick than the small ones - the large tier burns 10% less fuel per watt, the industrial 20% less.

| | Large cobbled trash gasifier | Large trash gasifier | Industrial trash gasifier |
|---|---|---|---|
| Size | 3x4 | 3x4 | 3x6 |
| Heat, eco / normal / high | 1800 / 3600 / 4800W | 2250 / 4500 / 6000W | 4500 / 9000 / 12000W |
| Fuel a day | 108 / 270 / 405 | 81 / 202.5 / 304 | 144 / 360 / 540 |
| Heat per brick a day (normal) | 13.3W (small: 12W) | 22.2W (small: 20W) | 25W |
| Holds | 450 bricks | 300 bricks | 600 bricks |
| Turbines it runs at full burn | one (high gear on normal) | one flat out | two flat out |
| Safety valve | no, it bursts | yes | yes |

They eat trash fast: an industrial gasifier on normal burns what 14 garbage compactors make. Feed them from hoppers or, with Vanilla Chemfuel Expanded, a chemfuel pipe.

### Steam turbines (advanced mode)
Two tiers, both 2x3, with **three gears**. A higher gear turns more of the heat into power but needs more heat to turn at all. **Below its gear's minimum a turbine stalls**: it still takes its share of the heat, wastes it, and makes nothing.

| Gear | Minimum heat | Steam turbine | Cobbled steam turbine |
|---|---|---|---|
| Low | 500W | 60% | 50% |
| Medium | 1500W | 70% | 60% |
| High | 3000W | 80% | 70% |

| | Cobbled steam turbine | Steam turbine |
|---|---|---|
| Research | Electricity + VRE complex recycling | Microelectronics + VRE complex recycling |
| Most heat it takes | 4800W (3 cobbled on high) | 6000W (3 gasifiers on high) |
| Breakdowns | twice as often | normal |

One trash gasifier on normal (1500W) runs a turbine in medium gear. High gear takes two. Several turbines on one network fill one at a time. The turbine's readout says when it has stalled and which gear would turn; a **Steam turbine stalled** alert warns you too. While they make power, turbines show their moving parts, spinning up and coasting down: the steam turbine a **flyball governor** whirling on its steam chest, its **shaft coupling** rolling and its **blades** streaming past an inspection hatch; the cobbled turbine its **flywheel** rim rolling and a **flat belt** driving a salvaged dynamo. Both have a spinning cooling fan and their own running sound.

- **Pipes:** our own network on Vanilla Expanded Framework's PipeSystem, the same system VE's chemfuel pipes use. That gives the usual overlay, plus a visible pipe, a **hidden pipe** and a **valve**, all at the Electricity tier. The visible and hidden pipe share **one architect button** (a dropdown). They sit in the Power tab, or in VE's **pipe networks** tab when a mod adds it (Vanilla Chemfuel Expanded). A building joins the network where a pipe runs under it.

### The heat network (advanced mode)
A burner's heat goes, in order:
1. With Dubs Bad Hygiene, its **hot water share** to the plumbing (see below).
2. Its own **Stirling engine**, only if no turbine is on the network.
3. **Steam turbines**, one at a time, each up to its maximum.
4. **Radiators**: 1x1, heating their room to the target temperature you set through vanilla's own temperature system. The **cobbled radiator** (Electricity: 20 steel, 10 wood) takes up to 150W, leaks about three times as often and breaks down; the **cast-iron radiator** (Microelectronics: 45 steel) takes up to 250W. Each has a valve to shut it off.
5. **Overpressure Tanks**: 2x2, hold 36 kWh, charging and discharging at up to 3000W. A tank takes whatever the turbines and radiators don't. It gives it back to **radiators** the burners can't satisfy, and **tops a stalling turbine up** to its gear's minimum when the burners fall short, through a breakdown or a refuel. With Dubs it also feeds the plumbing's hot water tanks and radiators.
6. **Steam vents**: 1x1, two kinds under one architect button (Electricity): a **wall steam vent** hung on a wall like the wall exhaust port, blowing on the side it hangs on, and a free-standing **steam vent** standpipe. A vent blows off whatever nothing else takes, up to 3000W, as scalding steam. Set it to also **drain the tanks above 25/50/75%** to keep their explosion risk down. Put it outdoors: indoors it heats the room fast, and anyone in the steam is burned. For players who'd rather not build DBH heating to let off steam.
7. **Dubs Bad Hygiene hot water and heating**, from what's left.
8. Whatever's left **builds pressure**.

### Hazards (can be switched off)
- **Overpressure:** heat with nowhere to go builds pressure over about half a day at 500W. The **trash gasifier's safety valve** vents it harmlessly in puffs of steam. The **cobbled gasifier has no working safety valve**: at full pressure it **bursts**. A **1000°C steam cloud** fills everything within 5 tiles in line of sight: rooms are heated by the share of them the cloud fills, and anyone caught in it is scalded, worst at the centre. The gasifier then breaks down and needs repairing. A critical alert warns you from 70% pressure.
- **Overpressure Tank explosions:** a tank more than 20% full can let go, with a blast and a 1000°C steam cloud out to 3-7 tiles depending on how full it is. The risk rises with the square of the fill, with the days since it was last bled (up to x3), and four times over while a cobbled gasifier (no safety valve) is piped to its network. When full and freshly bled on a gasifier-only network it averages one explosion in 60 days. Its readout shows the risk a day, and an **Overpressure Tank at risk** alert fires above 2% a day. **Bleed** (right-click to choose 0/25/50/75%) has a colonist (basic work) open the blow-off valve: the heat goes into the room and the wear resets. Or turn on **Auto-release** and pick a level (25/50/75/100%): above it the tank vents on its own, up to 3000W, straight into its room - safe, but it gets hot fast indoors.
- **Steam leaks:** pipes, turbines, radiators and Overpressure Tanks spring a leak now and then while hot water flows. On average once every 20 days per network, whatever its size, and adjustable in settings. A leaking part is damaged and sprays scalding steam on the cells around it until a colonist repairs it. Parts badly damaged some other way (raids, fire) leak too.
- **Visible steam:** steam from vents, Overpressure Tank releases and bleeds, safety valves, leaks and bursts hangs in the air as a white **steam cloud**. It spreads cell to cell through open space and open doors, drifts away quickly outdoors, and indoors **fills the room** and slowly condenses (faster in a cold room). While it hangs there it **keeps the room hot** - 5 heat a second per unit of steam, on top of the heat its source already gave off - up to about 100°C. A 3000W vent left blowing into a closed room fogs it within a minute or two and turns it into a sauna. A steam burst leaves a thick cloud over its whole blast. It's drawn with vanilla's particle system (batched like fire smoke): each steamy cell on screen puffs out drifting steam now and then, more often and thicker the denser the steam, so it stays cheap. Switch it off in settings (*Visible steam clouds*) to go back to puffs only.

### Exhaust and pollution
Burning trash makes exhaust, in both play modes. It has to go somewhere:
- **Exhaust pipe** (visible and hidden, one architect button) carries it to an **exhaust port**: a 1x1 soot-black stack (Electricity: 30 steel). Build the port outdoors; the ground around it slowly fills with pollution (Biotech's pollution). A port indoors gasses its room. Several ports on one network share the exhaust; a port's **damper** closes it. The stack and a **wall exhaust port** share one architect button. The wall port (35 steel) hangs on a wall like a wall lamp or an over-the-wall unit and blows the exhaust out on the side it hangs on: hang it on the outside of a wall and pipe to it under the wall. Exhaust pipe and pressurised hot water pipe are separate networks and can share a cell.
- **Ports need power:** each port's draught fan draws 80W. Without power (or with its damper shut) a port is closed, and with no open port the exhaust **backs up into the burners** and comes out around them.
- **Exhaust expansion tank** (2x2, Electricity: 120 steel, 1 component): a buffer for short power cuts. While no open, powered port can take the exhaust, everything on the network - burners, garbage compactors, factory machines - fills the tank instead of gassing its room. It holds 30,000 toxic gas (about eight hours of a trash gasifier on normal) and drains into the ports over about two hours once one is working again. Full, the exhaust backs up as before. Destroyed or deconstructed, it lets out everything it holds on the spot - empty it before taking it down.
- **Garbage compactor:** Vanilla Recycling Expanded's garbage compactor joins the exhaust network too. Run exhaust pipe under it to a powered port and the toxic gas it makes while compacting (300 every 10 seconds, about 30,000 a day) goes out of the port instead of around its work spot. Unpiped, it gasses its surroundings as usual.
- **Factory fumes (Vanilla Furniture Expanded - Factory):** the dirty factory machines give off fumes while they're running a process, and join the exhaust network the same way. Pipe them to a powered port to send the fumes outside; unpiped, they come out around the machine. A settings checkbox switches it off, and the pollution slider scales it.

| Machine | Toxic gas a day while working | Ground pollution a day |
|---|---|---|
| Automated smelter | 20,000 | 1 cell |
| Automated alloy forge | 25,000 | 1.5 cells |
| Automated biofuel refinery | 15,000 | 0.5 cells |
| Neutroamine synthesizer | 30,000 | 1 cell |
| Automated ammunition press | 10,000 | 0.5 cells |
| Medicine granulator | 8,000 | - |
| Conveyor crematorium | 10,000, plus 20,000 rot stink | 0.5 cells |

The clean machines (autoloom, masonry saw, mincer, conveyor oven, assembler, distillery, machining bay) make none.
- **At the port:** exhaust comes out as toxic gas (it drifts off outdoors, and builds up fast in a closed room), a little heat, and ground pollution.
- **No exhaust pipe to an open port:** the burner lets its exhaust out around itself - **toxic gas** into the cells around it, and pollution on the ground there. Its readout says *EXHAUST* in capitals and a **Burner venting toxic exhaust** alert fires.
- **How much:** by fuel burnt. Every burner, on every mode, makes more toxic gas than a working garbage compactor - burning trash is dirtier than crushing it. The trash gasifier's filters cut the ground pollution to a third; the gas only a little. A settings slider scales it.

| Burner | Pollution per brick | Toxic gas per brick | Toxic gas a day (eco / normal / high) |
|---|---|---|---|
| Cobbled trash gasifier | 0.06 | 1000 | 40,000 / 100,000 / 150,000 |
| Trash gasifier | 0.02 | 1200 | 36,000 / 90,000 / 135,000 |
| Large cobbled trash gasifier | 0.06 | 1000 | 108,000 / 270,000 / 405,000 |
| Large trash gasifier | 0.02 | 1200 | 97,200 / 243,000 / 364,500 |
| Industrial trash gasifier | 0.02 | 1000 | 144,000 / 360,000 / 540,000 |
| *(VRE garbage compactor)* | - | - | *about 30,000 while working* |

On trashbricks; loose trash and wastepacks multiply the gas (below).

### Other fuels
Burners take more than trashbricks. Each fuel is counted at its own value (a Harmony patch on refuelling) and burns with its own exhaust, against a trashbrick:

| Fuel | Worth (bricks) | Ground pollution | Toxic gas | New burners |
|---|---|---|---|---|
| Trashbrick | 1 | x1 | x1 | take it |
| Wood log | 0.4 | x0.3 | x0.5 | take it |
| Chemfuel | 2.5 | x1.5 | x0.6 | take it |
| Loose trash (VRE) | 1.5 | x0.5 | x3 | take it |
| Toxic wastepack (Biotech) | 0.5 | x0.25 | x8 | take it |
| Hay | 0.15 | x0.2 | x0.4 | refuse it |
| Cloth | 0.25 | x0.5 | x1.5 | refuse it |
| Bioferrite (Anomaly) | 4 | x1 | x2 | refuse it |
| Deepchem (Vanilla Chemfuel Expanded) | 3 | x4 | x5 | refuse it |
| Corpses (humanlike, animal, insect) | 1 per 4.5 kg of body (a human about 13) | x0.3 | x0.3, plus **rot stink x6** | refuse them |
| Sludge pellets (with DBH) | 1 | x1 | x1 | take it |

- **Fuel bill:** every burner has a **Fuel bill** button. It opens a window laid out like a vanilla bill: a **fuel search radius** (how far colonists will go to fetch fuel, like a bill's ingredient search radius) and the **fuel filter** tree, with its search box, categories and special filters (fresh or rotten corpses, colonist or stranger corpses...). Colonists and hoppers only bring it what the filter allows, and colonists only from within the radius. **Anything** allows every fuel, **Trashbricks only** the bricks alone; down the right, each fuel's worth and exhaust. Hay, cloth, bioferrite, deepchem and corpses start refused, so nobody burns your fodder, tailoring stock, bioferrite, refinery feedstock or dead unasked. Fuels added by a later version, or by a mod you switch on later, start refused on burners you've already built too. **Sync burners** copies the bill.
- **Fuel pipes (Vanilla Chemfuel Expanded):** burners connect to VCE's **chemfuel** and **deepchem** pipe networks: run a pipe under a burner and it tops itself up to its refuel target from the network's tanks, like VCE's own generators. Piped fuel counts at its own value and goes into the fuel mix like hauled fuel, and a fuel the burner's fuel bill refuses isn't drawn - deepchem starts off, so switch it on to burn piped deepchem.
- **Deepchem** refines 1:2 into chemfuel (5 bricks' worth), so burning it raw wastes some - and it's the filthiest fuel there is.
- **Corpses** are stripped as they go in (clothes, weapon and inventory drop at the burner) and are worth their **mass**: a trashbrick is compressed matter, so it takes 5 kg of corpse to match 1 kg of brick - with VRE's 0.9 kg bricks, 1 brick per 4.5 kg of body. A 60 kg human is about 13 bricks, a muffalo about 30. A corpse worth more than the burner has room for still goes in whole, and the excess is lost. They burn with a huge cloud of **rot stink** on top of a little toxic gas. It goes down the exhaust like the rest, so pipe it to a port somewhere downwind. Mechanoid corpses don't burn.
- **Setting:** *Burners also take wood, chemfuel, deepchem, hay, cloth and bioferrite* (on by default, restart to apply) removes those from every burner. Loose trash and wastepacks always burn.
- The fuel hopper holds all of them; hay, cloth and bioferrite are off in a new hopper's storage settings.

Cleaning about 6 polluted cells makes one wastepack; burning it puts back a tiny fraction of a cell (about 0.008 in a cobbled gasifier) and a burst of toxic gas, so burning cleaned-up pollution can't loop. The fuel in a burner is a mix: its readout says how dirty the current mix burns. The fuel hopper takes them too.

### Polish
- **Effects:** smoke from the cobbled flue and the gasifier's stack, a flickering firebox glow, steam wisps from turbines, the gasifier's safety valve visibly venting, and a spinning cooling fan on each turbine while it makes power.
- **Sound:** synthesised running loops: the cobbled machines rattle (`Source/Audio/make_rattle.py`), the trash gasifier chuffs like a steam engine and the steam turbine whines (`Source/Audio/make_steam.py`).
- **Alerts:** burner overpressure (critical), steam turbine getting no heat, steam turbine stalled, burner out of fuel, Overpressure Tank at risk.
- **Room heat:** burners heat the room they're in (cobbled 5 / 10 / 14 by mode, trash gasifier 1.5 / 3 / 4 - it's insulated). An Overpressure Tank warms its room a little too, leaking up to 20W of its stored heat when full: a fraction of a burner.
- **Status:** burners show their mode, Stirling output and any heat with nowhere to go; turbines their gear, heat and whether they've stalled; tanks a charge bar, kWh stored, explosion risk and auto-release.

### Build shortcuts
Selecting any building from this mod shows build buttons for **every other one**: hopper, gasifiers, exhaust pipes and port, hot water pipes, valve, turbines, Overpressure Tank, steam vent and radiators, in that order, from fuel to power. You can lay out a whole chain without going back to the architect menu. They're the architect's own buttons, so each appears only once researched, and the heat network's stay hidden in simple mode.

### Settings
Play mode, hazards on/off, other fuels on/off, and sliders for fuel use, power output, pollution and leak frequency.

### One intake, no output
Each machine has a single intake, marked with a green in-arrow on the edge it faces. The gasifier only takes fuel from a hopper on the cells in front of that intake. Those cells are outlined in green while you place or select it.

- **Hoppers:** any building with `isHopper` works on the intake: the vanilla hopper, the VFE Factory hopper, or this mod's fuel hopper. Each machine has a **Draw from hoppers** toggle.
- **Fuel hopper:** 1x1, 25 steel, holds 3 stacks. Its filter is locked to gasifier fuels at Important priority, so haulers keep it full. Point its spout at the machine.
- **With VFE Factory:** VFE's factory hopper is used and ours leaves the build menu; hoppers already built keep working. A belt pushes into the hopper and the gasifier pulls from it, so **belt -> hopper -> gasifier** buffers the fuel. Set the factory hopper's filter to allow trashbricks, since it starts empty. A belt pointed straight at a gasifier also refuels it, from any side; that's VFE's own behavior.

### With Dubs Bad Hygiene
**Sludge pellets:** a biofuel refinery recipe turns 75 fecal sludge into 100 sludge pellets, and every burner burns them. That's less energy than DBH's sludge-to-chemfuel recipe (35 chemfuel, about 7.8 generator-days), but pellets don't explode when damaged, catch fire less easily, and don't rot.

**Plumbing:** every burner connects to DBH plumbing.
- **Advanced mode:** a burner on the plumbing is also a DBH boiler. Each burner has a **Hot water** share (0–100% in 10% steps; left-click steps, right-click picks). That share of its heat is offered to the plumbing's hot-water tanks and radiators **first**, one boiler unit per watt. Whatever the plumbing doesn't actually draw goes on to the turbines, so a high share only costs power when the tanks and radiators really want the heat. Anything the network leaves over is offered to the plumbing too. What the plumbing draws of the share comes before the Stirling engine, so it can cut the Stirling's power.
- **Simple mode:** an engine mode gizmo adds **water-cooled** (120% power while water flows, drawing 50 or 40 water a day) and **heat recovery** (a 1600-unit boiler for hot water and heating, at 50% power for the cobbled gasifier or 60% for the trash gasifier).

**Overpressure Tank as a boiler:** on DBH plumbing, the Overpressure Tank is also a DBH boiler. It feeds the plumbing's hot water tanks and radiators from the heat it holds, offering only what they're short of, so a satisfied plumbing network doesn't drain it. 1 DBH heating unit = 1W, as DBH's own electric boiler.

**Water (advanced mode):** a burner **needs** water from DBH plumbing to burn, by its mode (see the table above). With no plumbing, or no water on it, it won't light: its readout says *NO WATER* and a **Burner has no water** alert fires. A mod setting turns the requirement off.

The large and industrial burners join DBH plumbing too, with boilers of 4800 and 9600 units.

Works with DBH's Lite mode too: that's a setting inside DBH, not a separate mod.

## Layout
```
About/                                   metadata, preview, icon
LoadFolders.xml                          loads Mods/<mod> only when that mod is active
Defs/ThingDefs_Buildings/                both machines, the fuel hopper, the hot water network, pipes, valve and turbine
1.5/, 1.6/Assemblies/                    TrashbrickBurning.dll
Mods/DubsBadHygiene/Defs, Patches/       sludge pellets, plumbing and engine modes
Mods/DubsBadHygiene/1.5, 1.6/Assemblies/ TrashbrickBurning.DBH.dll (references BadHygiene.dll)
Mods/VFEFactory/Patches/                 factory-hopper tag, hides our hopper
Source/TrashbrickBurning/                mod settings, CompBuildShortcuts, CompStirlingEngine (burner, pressure, Stirling), HeatNetwork + turbine/radiator/accumulator, AccumulatorRisk (explosion, bleed job), Hazards (burst, leaks), CompExhaust (exhaust network, ports), CompSteamVent, CompExtraBreakdowns, CompMachineEffects, CompLooseParts, Alerts, HarmonyPatches (fuel values), CompHopperFeed, PlaceWorker_ShowIntake, CompPowerPlantStirling
Source/TrashbrickBurning.DBH/            CompStirlingWater, CompStirlingBoiler
Source/Art/                              draws, verifies and measures every texture
Source/Audio/make_rattle.py              synthesises the rattle loop
Sounds/STB/                              the rattle loop
```

## Building
```sh
Source/build.sh   # needs mono's mcs, curl, unzip and git
```
This compiles against the Krafs.Rimworld.Ref reference assemblies from NuGet, VEF's `PipeSystem.dll`, and (for the DBH bridge) DBH's own `BadHygiene.dll`, the last two from their public repos. The game doesn't need to be installed.

## Art
Every sprite is drawn by `Source/Art/draw_sprites.py`, following the rules the SloppyMods mending and Riimba art settled on: four real views per machine, black only on the silhouette, height from walls and shadows, one meaningful accent colour, and straight pipe runs. The low-tech machines share a home-brew, jerry-rigged look (scrap-plate decks, timber chocks, bolted-on salvage, a car battery, tape, a drip bucket), and their loose parts (dangling cables, a pipe on one clamp, gauges on wobbly stalks, loose nuts) **rattle while they run**, drawn and shaken by `CompLooseParts`. The high-tech ones are neat and bolted. `verify_art.py` checks the art against the C#. See [`Source/Art/README.md`](Source/Art/README.md).
