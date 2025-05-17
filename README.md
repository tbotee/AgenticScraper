# Configuration 
Make sure to use $OPENAI_API_KEY for the parametric and xref search

# How to use 

## MPN Search
`python main.py mpn LQP02HQ0N2BZ2 --output results_mpn.json`

## Parametric search
`python main.py parametric --category "Capacitors" --subcategory "Single Layer Microchip Capacitors" --parameters '{"details": "the capacitance shuld be between 0.1 and 1 and LxW 0.25x0.25"}' --max-results 10 --output results_parametric.json --api-key $OPENAI_API_KEY`
 
## XREF Search
`python main.py xref 337XMPL002MG28A --category-path '["Capacitors", "Polymer Aluminium Electrolytic Capacitors"]' --output results_xref.json --api-key $OPENAI_API_KEY`

# Scope of Work: Electronic Component Agentic Scraper Development

# Enhancements
- better llm
- more specific llm prompts
- better caching for debugging purpose

## Project Background and Purpose

Electronic component sourcing is a critical challenge for hardware companies. Engineers and operations teams frequently need to find alternative components that meet specific technical requirements for various reasons:

- **Supply Chain Resilience**: When primary components become unavailable or have extended lead times
- **Cost Optimization**: Finding functionally equivalent parts at lower prices
- **Compliance Requirements**: Meeting regulatory standards that may affect component selection
- **Design Optimization**: Exploring alternatives with better performance characteristics

However, searching across multiple vendor catalogs is time-consuming and complex. Each manufacturer organizes their product data differently, uses proprietary terminology, and implements unique search interfaces, making cross-referencing difficult.

This project aims to develop intelligent scraping agents that can navigate electronic component vendor websites, interpret search interfaces, and return standardized results. The goal is to enable hardware companies to quickly identify alternative components that meet their specifications regardless of which vendor's catalog they are exploring.

## Project Overview

The objective is to design and implement an agentic scraper for electronic component vendor websites, capable of performing three types of searches:

1. **MPN Search**: Finding a specific manufacturer part number
2. **Parametric Search**: Finding components that match specific technical parameters
3. **Cross-Reference Search**: Finding equivalent components to a specified part number from another manufacturer

The scraper should be able to:
- Navigate through the vendor's website structure
- Process search forms and filter interfaces
- Extract component data in a standardized format
- Handle decision points where domain knowledge is required

## Technical Requirements

### Core Functionality

The scraper must support the following search modes if they are available on the vendor website:

1. **MPN Search**
   - Input: Manufacturer part number
   - Output: Matching component details and URL

2. **Parametric Search**
   - Input: Component category, subcategory, and technical parameters
   - Output: List of components meeting the specifications

3. **Cross-Reference Search**
   - Input: Competitor's part number, optional category path
   - Output: List of equivalent components

### Input/Output Specifications

**Input Format**:
The system should accept command-line arguments similar to the following examples:

```bash
# MPN Search
python main.py mpn GRM0115C1C100GE01 --visible --output results_mpn.json

# Parametric Search
python main.py parametric --category "Capacitors" --subcategory "Ceramic Capacitors(SMD)" --parameters "{\"Capacitance\": {\"min\": 1, \"max\": 1.1}}" --max-results 10 --visible --output results_parametric.json --api-key $OPENAI_API_KEY

# Cross-Reference Search
python main.py xref A700D107M004ATE018 --category-path "[\"Capacitors\", \"Polymer Aluminium Electrolytic Capacitors\"]" --visible --output results_xref.json --api-key $OPENAI_API_KEY
```

**Output Format**:
Results should be returned in JSON format, with at minimum the following fields:
- MPN (manufacturer part number)
- URL (to the component detail page)
- Technical specifications (when available)

### Technical Approaches

1. **Web Automation**
   - You may use Selenium, Playwright, Puppeteer, or any other web automation tool of your choice
   - The solution should handle common web challenges (loading delays, dynamic content, etc.)

2. **Decision Intelligence**
   - You may optionally use Large Language Models (e.g., OpenAI API) to help with decision-making at complex points
   - LLM assistance is not required, but can be useful for tasks like:
     - Mapping between different vendors' category structures
     - Interpreting complex form fields and filters
     - Understanding specifications across different naming conventions

3. **Error Handling and Resilience**
   - Implement robust error handling for common scenarios
   - Provide detailed logging for troubleshooting
   - Implement strategies to handle anti-scraping measures if encountered

## Deliverables

1. **Functional Scraper Implementation**
   - Complete code for the scraping agent
   - Support for all three search types if applicable to the chosen vendor
   - Command-line interface following the specified input format

2. **Documentation**
   - README file with installation and usage instructions
   - Code comments explaining the approach and critical decision points
   - Description of any vendor-specific features implemented

3. **Sample Results**
   - Example outputs from each search type
   - Brief analysis of the results quality

## Timeline

The project should be completed within 10 days of starting.

## Evaluation Criteria

Your implementation will be evaluated based on:

1. **Functionality**: Does it successfully perform all three types of searches?
2. **Robustness**: How well does it handle errors, delays, and unexpected website behavior?
3. **Code Quality**: Is the code well-structured, documented, and maintainable?
4. **Innovation**: Any creative solutions for challenging aspects of the scraping process?
5. **Technical Specifications**: Does it successfully extract detailed component specifications?

## Additional Considerations

- **Vendor Selection**: Focus on manufacturers of passive components with large catalogs
- **Batch Processing**: While not required, ability to process multiple MPNs is a plus
- **Vendor-Specific Features**: If you discover unique features in your chosen vendor's website, document and implement them if valuable
- **Anti-Scraping Measures**: Document any challenges encountered with rate limiting, CAPTCHAs, etc., and your approach to addressing them

## Follow-up

After completion, be prepared to discuss:
1. The decision points where domain knowledge was required
2. Your approach to mapping between different vendors' classification systems
3. How your solution might be extended to additional vendors
4. Any challenges unique to your chosen vendor and how you addressed them