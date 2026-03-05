# Dosa Restaurant Order Analyzer

## What it does
Reads a JSON file of customer orders from a Dosa restaurant and produces two summary files:
- `customers.json` — maps phone numbers to customer names
- `items.json` — maps item names to their price and total order count

## Design
The script is broken into small focused functions:
- `load_orders` — reads the input file
- `build_customers` — extracts unique customers
- `build_items` — aggregates item prices and order counts
- `save_json` — writes output files
- `main` — ties everything together and handles CLI arguments via `argparse`

## How to use

```bash
python analyze_orders.py example_orders.json
```

This will generate `customers.json` and `items.json` in the current directory.

## Requirements
- Python 3.x
- No external dependencies (uses only standard library)
