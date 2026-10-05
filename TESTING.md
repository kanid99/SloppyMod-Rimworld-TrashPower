# Playtest checklist

The rework (0.7.0) hasn't run in RimWorld yet: modes, Stirling, gears, the Overpressure Tank and
the new sounds are all first contact. It compiles against the real 1.5 and 1.6 game, VEF and DBH
assemblies. Work top to bottom: each section leans on the one before it.

## Install

1. Put the repo in `RimWorld/Mods/SloppyModTrashPower/` (clone it there, or download the branch
   `claude/trash-brick-fuel-power-f6lia3` as a zip). The repo root *is* the mod folder: `About/`,
   `Defs/`, `1.5/`, `1.6/` and the rest sit directly in it. The compiled DLLs are committed, so
   there's nothing to build.
2. Mod list, in this order: **Harmony**, Core, Biotech, **Vanilla Expanded Framework**,
   **Vanilla Recycling Expanded**, then optionally **Dubs Bad Hygiene** and **VFE - Factory**, then
   **SloppyMod Trash POWER!**.
3. Turn on **Development mode** (Options > General). You'll want the debug log and debug actions.

**First check:** on the main menu, open the debug log (the icon top right). Any red lines
mentioning `STB_`, `TrashbrickBurning`, `PipeSystem` or `STB/` are ours: please copy them to me as-is.
Yellow warnings are worth sending too.

## 1. Loading and settings

- [ ] Options > Mod settings > **SloppyMod Trash POWER!** opens: the play mode checkbox, hazards, other
  fuels, four sliders and a reset button.
- [ ] Start a new colony (or dev quickstart). No red errors in the log.
- [ ] Debug actions > **Research all** (or research Electricity, Microelectronics and VRE complex
  recycling). The **Power** tab has cobbled trash gasifier, trash gasifier, fuel hopper, both
  turbines, Overpressure Tank, pressurised hot water pipe and hidden pipe, and valve. The
  **Temperature** tab has cobbled radiator and hot water radiator.

## 2. A cobbled trash gasifier on its own (advanced mode, the default)

God mode on, then build a **cobbled trash gasifier**. Give it trashbricks (debug spawn
`VRecyclingE_TrashBrick`) or wood.

- [ ] While placing it, a **green outline** shows the two cells in front of its intake (the side
  with the green arrow). Rotate it: the outline and the arrow move together in all four facings.
- [ ] Its **Mode** button cycles eco → normal → high: 600W on 40 a day, 1200W on 100, 1600W on 150.
  The button's tooltip lists all three with Stirling power and leftover heat.
- [ ] Unpiped and lit on normal, it reads *Stirling engine: 150W of power from 450W of heat* and
  *Heat with nowhere to go: 750W*. Its power readout shows **150W**. **Pressure** starts climbing:
  a burner needs an Overpressure Tank or radiators even in Stirling mode.
- [ ] **Smoke** puffs from the flue, the **fire window flickers**, the loose parts **rattle**, and
  you can hear the rattle loop. All of it stops when you switch it off, and freezes when you pause.
- [ ] Refuel from a **fuel hopper** on the intake cells: it pulls fuel as it burns. A hopper on any
  other side does nothing.
- [ ] **Exhaust, unpiped:** in a closed room, the lit gasifier fills the room with **toxic gas** (it
  spreads from the cells around it), pollutes the ground there, reads *EXHAUST: no exhaust pipe...*,
  and the **Burner venting toxic exhaust** alert fires. Colonists in the room build up toxic buildup.
- [ ] **Exhaust, piped:** lay an **exhaust pipe** (Power tab, its own dropdown with the hidden pipe)
  from under the gasifier to an **exhaust port** outdoors. The gas stops, the readout says *piped to 1
  exhaust ports*, the port puffs smoke and the ground around it slowly turns polluted.
- [ ] An exhaust port built **indoors** gasses its room instead, and says so. Its **damper** closes it:
  with no other open port, the exhaust goes back to gassing the burner's room.
- [ ] A trash gasifier makes noticeably less pollution than the cobbled one, and a little less gas.
- [ ] **Port power:** an exhaust port needs 80W for its draught fan. Cut its power (or leave it
  unconnected) and it reads *NO POWER*, the burner reads *EXHAUST: no exhaust pipe to an open, powered
  exhaust port*, and the gas backs up around the burner. Power it again and the gas goes back out the port.
- [ ] **Garbage compactor:** run exhaust pipe under a Vanilla Recycling Expanded garbage compactor
  to a powered port. While it compacts it reads *its toxic gas goes down the exhaust pipe to 1 exhaust
  ports*, and the gas comes out at the port instead of at its work spot. Without a port it reads *no
  open, powered exhaust port* and gasses its work spot as before.
- [ ] **Factory fumes** (Vanilla Furniture Expanded - Factory): an automated smelter running a job in a
  closed room fills it with toxic gas slowly and reads *Fumes: 20000 toxic gas a day while working*;
  idle, it says *(idle now)* and makes none. Exhaust pipe from it to a powered port: the gas comes out
  at the port and it reads *goes down the exhaust pipe to 1 exhaust ports*. The conveyor crematorium
  adds rot stink. An autoloom has no fumes. The settings checkbox turns it all off, and the
  checkbox only shows with the Factory mod loaded.
- [ ] **Burners are dirtier than the compactor:** a lit burner of any size, even on eco, gasses a
  closed room faster than a working compactor does.
- [ ] **Dirty fuels:** refuel with **loose trash** or **toxic wastepacks**. The burner's readout shows
  *Fuel mix: x0.5 ground pollution, x3 toxic gas* (trash) or x0.25 / x8 (wastepacks),
  and an unpiped burner gasses its room much faster. Refuelling with bricks brings the mix back
  toward x1. The fuel hopper accepts both.
- [ ] **Fuel bill:** a new burner's **Fuel bill** button reads *Fuel bill: N of M* with hay, cloth,
  bioferrite, deepchem and corpses refused. It opens a window with a search radius slider, Anything /
  Trashbricks only, the fuel filter tree (search box, categories, rotten/fresh corpse filters) and a
  list of fuel values. Refuse wastepacks: with wastepacks and bricks both lying around, colonists
  refuel with bricks only, and a hopper full of wastepacks doesn't feed it. Allow hay: it gets fed hay.
- [ ] **Search radius:** set it to 10 with bricks only 20 cells away: nobody refuels it and it reads
  out of fuel. Move bricks within 10 cells, or set the radius back to Unlimited: it gets refuelled.
- [ ] **Corpses:** allow humanlike corpses in the fuel bill. A colonist hauls a raider corpse to the burner; its
  clothes and weapon drop beside it, the fuel goes up about 13, and the readout adds *Burning corpses:
  rot stink x...*. Unpiped, the room fills with rot stink (colonists get the stench thought); piped,
  it comes out of the port. A muffalo corpse adds about its mass / 4.5 (around 30). Rotten corpses can be refused with the bill's rotten filter. Mechanoid corpses aren't
  hauled.
- [ ] **Deepchem** (with Vanilla Chemfuel Expanded): listed and off by default; on, a unit adds 3 fuel
  and the mix reads x4 pollution, x5 toxic gas.
- [ ] A burner from a 0.9.49 save loads with its Fuels menu choices carried into the fuel bill
  (e.g. hay allowed stays allowed, wastepacks refused stay refused).
- [ ] **Chemfuel pipe** (Vanilla Chemfuel Expanded): run a chemfuel pipe from a tank with chemfuel
  in it under an empty burner. It fills up to its target; the tank drops by about 1 for every 2.5
  fuel it gains, and the mix readout moves toward x1.5 pollution / x0.6 gas. Switch chemfuel off on
  its fuel bill: it stops drawing.
- [ ] **Deepchem pipe:** the same with a deepchem pipe and tank. Nothing is drawn until deepchem is
  allowed in the fuel bill; then 1 deepchem per 3 fuel, and a filthy mix (x4 / x5).
- [ ] With the other-fuels setting off (restart), a burner on a chemfuel pipe draws nothing and
  nothing errors.
- [ ] Fuel bill **Anything**: the button reads *Fuel bill: M of M*. **Trashbricks only**: *1 of M*,
  and colonists bring nothing but bricks.
- [ ] Refuel with **wood** only: the readout shows *Fuel mix: x0.3 ground pollution, x0.5 toxic gas*.
  With **chemfuel**: x1.5 / x0.6.
- [ ] **Sync burners** copies the fuel bill (filter and radius). An old save whose burner had *Accept
  wastepacks* off loads with wastepacks refused in its fuel bill.
- [ ] **Visible steam:** in a closed room, set a steam vent (or an Overpressure Tank's auto-release) blowing.
  A white fog spreads out from it and fills the room within a minute or two, churning slowly; the
  room heats much faster than before and levels off around 100°C. Open a door: the fog drifts
  through. Outdoors the steam blows away within seconds. Stop the vent: the fog thins and clears over
  a game hour or so. Bleed a full tank: a big cloud. Save and reload with fog in a room: it's still
  there. Setting *Visible steam clouds* off: the fog clears and only puffs remain.
- [ ] **Wall exhaust port:** hangs on a wall (it won't place away from one) without replacing it,
  drawn on the wall's face. Hung outside, gas drifts off and the ground below slowly pollutes. Hung
  inside a closed room, toxic gas builds up quickly and the room warms a little.
- [ ] **Shared cells:** lay exhaust pipe along the same cells as pressurised hot water pipe. Both
  build, and each links only to its own kind.
- [ ] It (and the cobbled turbine and radiator) breaks down noticeably more often than vanilla
  machines.

## 3. The trash gasifier

- [ ] Modes: 750W on 30 a day, 1500W on 75, 2000W on 112.5. Stirling 100 / 250 / 500W.
- [ ] Smoke and steam wisps from its stack, and a **chuffing steam engine** sound while it runs.
- [ ] Unpiped on normal: 250W of power, 750W of leftover heat. Pressure climbs to 85%, then the
  safety valve **vents** puffs of steam. It never bursts.

## 4. Pipes, the Overpressure Tank and radiators (no turbine yet)

Lay **pressurised hot water pipe** from a trash gasifier to an **Overpressure Tank**.

- [ ] The tank fills by the burner's leftover heat (*Stored: x of 36 kWh (+750W)* on normal), and
  the burner's pressure stops climbing. The Stirling engine keeps making power.
- [ ] A **radiator** on the same pipe in a cold, enclosed room takes heat first and warms the room
  to its target. With the burner off, the radiator keeps drawing from the tank.
- [ ] The radiator's **Radiator valve** closes it off.
- [ ] Tank hazards (hazards on): the readout shows **Explosion risk** (none below 20% full), days
  since it was last bled, and *risk x4* with a cobbled gasifier on the network. The bar reddens as
  the risk climbs; above 2% a day the **Overpressure Tank at risk** alert fires.
- [ ] **Bleed to 25%**: a colonist walks over, works a few seconds with steam puffs, the stored heat
  drops, the room warms, and the wear resets.
- [ ] **Auto-release** on, **Release above: 50%**: once the tank is over half full it vents on its
  own (*venting xW*), puffs steam, and its room heats up fast.

## 5. Steam turbines and gears

Add a **steam turbine** to the network.

- [ ] Every burner on the network now reads *Stirling engine off: a steam turbine is on its network*,
  and its power drops to 0.
- [ ] The turbine has a **Gear** button: low / medium / high, turning over on 500 / 1500 / 3000W at
  60% / 70% / 80%.
- [ ] One gasifier on normal (1500W), turbine in **medium**: about **1050W** of power.
- [ ] Shift to **high** with that one gasifier: the turbine **stalls** - *STALLED: 1500W is under the
  3000W this gear needs* and *medium gear would turn* - makes 0W, and the **Steam turbine stalled**
  alert fires. The heat is wasted: the tank doesn't charge from it.
- [ ] Two gasifiers on normal in high gear: about **2400W**.
- [ ] The turbine's **cooling fan spins** while it makes power, spins down when it stops, and freezes
  when you pause.
- [ ] **Moving parts:** the steam turbine's governor weights whirl, the coupling's bolts roll and the
  blades stream past the hatch; the cobbled turbine's flywheel weights roll and its belt runs to the
  side dynamo. All of it speeds up and coasts down with the fan, and looks right in all four facings. The steam turbine has a **whine** running loop.
- [ ] Reserve steam: with a charged tank, switch the burners off. The tank tops the turbine up to its
  gear's minimum (*Kept turning by the Overpressure Tank*) until it runs dry.
- [ ] The **cobbled steam turbine** is one step worse (50 / 60 / 70%), takes up to 4800W, rattles,
  and breaks down more.
- [ ] Rotate the turbines through all four facings: the art and the fan look right each way.

## 5b. Burst (hazards on)

- [ ] A **cobbled gasifier on high** with nowhere for its heat to go climbs to 70% (the red **Burner
  overpressure** alert) and at 100% **bursts**: a letter, a steam cloud, burns within 5 tiles, a hot
  room, and the gasifier broken down.
- [ ] Hazards off: it vents like the trash gasifier instead.

## 5b2. Steam vent and room heat

- [ ] **Steam vents** (Temperature tab, one button): the **wall steam vent** hangs on a wall without replacing it and blows on the side it hangs on; the ground **steam vent** stands anywhere and blows into its own cell. Pipe to the cell each sits in.
- [ ] With a burner whose heat has nowhere else to go, the vent reads *Venting xW*, puffs steam out of its front, and the burner's pressure stops climbing.
- [ ] **Drain tanks above 50%**: a fuller Overpressure Tank on the network is bled down to half. *Tanks: leave alone* stops that.
- [ ] Facing into a room, the room heats fast; a pawn standing in the plume gets burns (hazards on). Its valve shuts it.
- [ ] **Room heat:** in closed rooms, a lit cobbled gasifier warms its room clearly, a trash gasifier less, and a charged Overpressure Tank only slightly (and loses a little charge doing it).

## 5c. Large and industrial burners

- [ ] They're in the Power tab as **large cobbled trash gasifier**, **large trash gasifier** (3x4) and
  **industrial trash gasifier** (3x6). The green outline covers the whole 3-cell front.
- [ ] No power readout; they need a turbine. Unpiped, their heat builds pressure.
- [ ] Selecting any building from the mod shows **build buttons for all the others**.

## 6. Steam leaks

Settings: slide **Steam leak frequency** to the maximum to see one sooner, or damage a pipe with a
debug action (take damage).

- [ ] A pipe below half its hit points while hot water flows **leaks**: a message, smoke puffs, and
  pawns walking past get small burns.
- [ ] A colonist repairs it and the leak stops.
- [ ] Nothing leaks while no burner is lit.

## 7. Simple play mode

Switch to simple mode in settings and **restart**.

- [ ] Turbines, pipes, valve, radiators, the Overpressure Tank and the large and industrial burners are gone from the build menu.
- [ ] A cobbled trash gasifier makes **1000W** on 20 fuel a day; a trash gasifier **1200W** on 12.

## 8. With Dubs Bad Hygiene

- [ ] Sludge pellets: a biofuel refinery has **Make sludge pellets** (75 sludge → 100); every burner
  and the fuel hopper take them.
- [ ] **Advanced:** a burner on DBH plumbing with a hot water tank shows a **Hot water: 0%** button
  (left-click steps 10%, right-click picks). No **Power Mode** stepper.
- [ ] At 0% with a turbine taking all its heat, the tank gets nothing. Raise it to 50%: the burner
  reads *Hot water share: 50% (125W offered first), drawn: xW*, the tank heats, and the turbine's
  heat drops by the amount drawn. Once the tank is hot and draws nothing, the turbine gets it all back.
- [ ] With no turbine, a hot water share the plumbing draws comes before the Stirling engine, so its power drops.
- [ ] **Simple:** the engine mode button cycles power / water-cooled / heat recovery. Water-cooled
  reads *(no water)* without plumbing water, and makes 120% with it.

- [ ] **Tank as a DBH boiler:** pipe an Overpressure Tank into DBH plumbing with a DBH hot water tank or radiator. Its readout shows *To DBH hot water and heating: xW* while they're short of heat, and nothing once they're hot. The tank's charge drops by what it gives.
- [ ] **Water needed:** with DBH, a fuelled, switched-on burner with **no plumbing** under it doesn't burn: its readout says *NO WATER* and the **Burner has no water** alert fires. On plumbing with no water supply: the same. Connect a well/pump and water tower: it lights within a few seconds and reads *Water: 40 a day* on normal (20 eco, 53 high).
- [ ] Mod settings, **Burners need plumbing water** off: it burns without water again.

## 9. With VFE - Factory

- [ ] Our fuel hopper is gone from the build menu. A **factory hopper** on the intake feeds the gasifier.
- [ ] A conveyor into that factory hopper keeps the gasifier fed (belt → hopper → gasifier).

## What to send me

- Any red or yellow log lines, copied as-is. `Player.log` has everything: on Windows it's in
  `%USERPROFILE%\AppData\LocalLow\Ludeon Studios\RimWorld by Ludeon Studios\`.
- Numbers that come out different from the ones above.
- Anything that looks wrong in a particular facing, with the facing named.
- How the balance *feels*: fuel use, burst timing, leak frequency and the rattle volume are all
  first guesses.
