#!/usr/bin/env bash
# Rebuild SCM-1 (salt-cell test monitor): project + schematic, ERC, netlist, placement/routing (draft), DRC, fab exports.
set -u
LAB="/Volumes/Aditya ssd/Salt-Battery-Lab"; source "$LAB/tools/env.sh" >/dev/null 2>&1
KPY="$SSD/Applications/KiCad/KiCad.app/Contents/Frameworks/Python.framework/Versions/Current/bin/python3"
[ "$(uname)" = "Linux" ] && KPY=/usr/bin/python3          # EC2 build host: pcbnew in the system python
cd "$LAB/pcb"
python3 tools/gen_project.py scell_monitor design_scm
"$KICAD_CLI" sch erc --format json -o scell_monitor/erc.json scell_monitor/scell_monitor.kicad_sch 2>&1 | grep -v Fontconfig
"$KICAD_CLI" sch export netlist --format kicadsexpr -o scell_monitor/scell_monitor.net scell_monitor/scell_monitor.kicad_sch 2>&1 | grep -v Fontconfig
(cd scell_monitor && "$KPY" ../tools/pcbbuild.py . design_scm scell_monitor.net scell_monitor.kicad_pcb > build.log 2>&1; grep -E "placed|routing" build.log)
# Freerouting (EC2 build host, or any machine with Java 21 + FREEROUTING_JAR): SCM_ROUTER=freerouting pcb/build_scm.sh
if [ "${SCM_ROUTER:-}" = "freerouting" ]; then (cd scell_monitor && "$KPY" ../tools/freeroute.py scell_monitor.kicad_pcb . design_scm "${FR_PASSES:-60}" >> build.log 2>&1; tail -1 build.log); fi
cd scell_monitor && mkdir -p fab && rm -f fab/*
"$KICAD_CLI" pcb drc --refill-zones --save-board --format json -o drc.json scell_monitor.kicad_pcb 2>&1 | grep -v Fontconfig
"$KICAD_CLI" pcb export gerbers -o fab/ scell_monitor.kicad_pcb >/dev/null 2>&1
"$KICAD_CLI" pcb export drill -o fab/ scell_monitor.kicad_pcb >/dev/null 2>&1
"$KICAD_CLI" pcb export pos --format csv --units mm -o fab/scell_monitor-pos.csv scell_monitor.kicad_pcb >/dev/null 2>&1
"$KICAD_CLI" sch export bom --fields 'Reference,Value,Footprint,MPN,Manufacturer,${QUANTITY}' --group-by 'Value,Footprint,MPN' -o fab/scell_monitor-bom.csv scell_monitor.kicad_sch >/dev/null 2>&1
"$KICAD_CLI" sch export pdf -o fab/scell_monitor-schematic.pdf scell_monitor.kicad_sch >/dev/null 2>&1
"$KICAD_CLI" pcb render --side top --width 1600 --height 1100 -o fab/scell_monitor-top.png scell_monitor.kicad_pcb >/dev/null 2>&1
echo "SCM-1 rebuilt (layout is a DRAFT - see PROJECT_SALT/05_ELECTRONICS/README.md)"
