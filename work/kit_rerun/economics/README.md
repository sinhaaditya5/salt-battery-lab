# Prototype cost model

The JSON input file intentionally contains null values. The model refuses to run until actual supplier quotes, accepted powder yield, process costs and experimentally measured cell performance are supplied.

```bash
python economics/cost_model.py economics/cost_inputs_template.json
```

That command is expected to stop and list missing actual inputs. Copy the template, fill it from invoices, batch logs and measured tests, then run the copy.

This is a prototype-cell cost model only. It excludes commercial factory COGS: factory CAPEX and depreciation, BMS, module/pack enclosure, thermal management, certification, warranty, logistics, working capital, taxes and manufacturing yield learning.
