"""dev helper (KiCad python): print courtyard bbox + pads of footprints. args: Lib:Name ..."""
import sys, pcbnew
FP = "/Volumes/Aditya ssd/Applications/KiCad/KiCad.app/Contents/SharedSupport/footprints"
for a in sys.argv[1:]:
    lib, name = a.split(":")
    fp = pcbnew.FootprintLoad(FP + "/" + lib + ".pretty", name)
    cy = fp.GetCourtyard(pcbnew.F_CrtYd).BBox() if fp.GetCourtyard(pcbnew.F_CrtYd).OutlineCount() else fp.GetBoundingBox()
    mm = pcbnew.ToMM
    pads = [(p.GetNumber(), round(mm(p.GetPosition().x),3), round(mm(p.GetPosition().y),3)) for p in fp.Pads()]
    print("%-70s crt x[%.2f,%.2f] y[%.2f,%.2f] npads=%d" % (a, mm(cy.GetLeft()), mm(cy.GetRight()), mm(cy.GetTop()), mm(cy.GetBottom()), len(pads)))
    if len(sys.argv) < 4 or "-v" in a: print("    ", pads[:24])
