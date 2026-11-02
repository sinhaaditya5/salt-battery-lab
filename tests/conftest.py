import sys, pathlib
LAB = pathlib.Path("/Volumes/Aditya ssd/Salt-Battery-Lab")
for p in (LAB, LAB / "tools", LAB / "docs"):
    sys.path.insert(0, str(p))
