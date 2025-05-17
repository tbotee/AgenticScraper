# Configuration 
Make sure to use $OPENAI_API_KEY for the parametric and xref search

# How to use 

## MPN Search
`python main.py mpn LQP02HQ0N2BZ2 --output results_mpn.json`

## Parametric search
`python main.py parametric --category "Capacitors" --subcategory "Single Layer Microchip Capacitors" --parameters '{"details": "the capacitance shuld be between 0.1 and 1 and LxW 0.25x0.25"}' --max-results 10 --output results_parametric.json --api-key $OPENAI_API_KEY`
 
## XREF Search
`python main.py xref 337XMPL002MG28A --category-path '["Capacitors", "Polymer Aluminium Electrolytic Capacitors"]' --output results_xref.json --api-key $OPENAI_API_KEY`