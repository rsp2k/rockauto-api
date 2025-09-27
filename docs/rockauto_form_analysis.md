# RockAuto Parts Search Form Analysis

## Summary

This document provides a comprehensive analysis of the RockAuto parts search page at https://www.rockauto.com/en/partsearch/ including form structure, field names, dropdown options, and implementation details for web scraping.

## 1. Main Part Number Search Form

### Form Details
- **Form ID**: `frm_partsearch`
- **Action**: `/en/partsearch/`
- **Method**: `POST`
- **Name**: `frm_partsearch`

### Form Fields

#### 1. Part Number Field
- **Element**: `<input type="text">`
- **Name**: `partsearch[partnum][partsearch_007]`
- **ID**: `partnum_partsearch_007`
- **Purpose**: Enter part number with wildcard support (use * for wildcards)

#### 2. Manufacturer Dropdown
- **Element**: `<select>`
- **Name**: `partsearch[manufacturer][partsearch_007]`
- **ID**: `manufacturer_partsearch_007`
- **Options**: 570 total manufacturers
- **Default**: "All" (empty value)
- **OnChange Handler**: `clb.PartSearchChangeMfrOption(this, "partsearch_007");`

#### 3. Part Group Dropdown
- **Element**: `<select>`
- **Name**: `partsearch[partgroup][partsearch_007]`
- **ID**: `partgroup_partsearch_007`
- **Options**: 27 part groups (see complete list below)
- **Default**: "All" (empty value)

#### 4. Part Type Dropdown
- **Element**: `<select>`
- **Name**: `partsearch[parttype][partsearch_007]`
- **ID**: `parttype_partsearch_007`
- **Options**: 5,314 part types
- **Default**: "All" (empty value)

#### 5. Part Name Field
- **Element**: `<input type="text">`
- **Name**: `partsearch[partname][partsearch_007]`
- **ID**: `partname_partsearch_007`
- **Purpose**: Additional text search for part names

#### 6. Submit Button
- **Element**: `<input type="submit">`
- **Name**: `partsearch[do][partsearch_007]`
- **ID**: `partsearch[do][partsearch_007]`
- **Value**: "Search"

#### 7. Reset Button
- **Element**: `<input type="button">`
- **Name**: `resetpartsearch`
- **ID**: `resetpartsearch`

#### 8. Hidden Fields
- **_nck**: Security token (required for form submission)
- **dopartsearch**: Set to "1" (indicates part search operation)

## 2. Part Group Options (Complete List)

| Value | Display Text |
|-------|--------------|
| "" | All |
| "Apparel & Gifts" | Apparel & Gifts |
| "Belt Drive" | Belt Drive |
| "Body & Lamp Assembly" | Body & Lamp Assembly |
| "Brake & Wheel Hub" | Brake & Wheel Hub |
| "Cooling System" | Cooling System |
| "Drivetrain" | Drivetrain |
| "Electrical" | Electrical |
| "Electrical-Bulb & Socket" | Electrical-Bulb & Socket |
| "Electrical-Connector" | Electrical-Connector |
| "Electrical-Switch & Relay" | Electrical-Switch & Relay |
| "Engine" | Engine |
| "Exhaust & Emission" | Exhaust & Emission |
| "Fuel & Air" | Fuel & Air |
| "Garage Equipment" | Garage Equipment |
| "Hardware" | Hardware |
| "Heat & Air Conditioning" | Heat & Air Conditioning |
| "Hoses/Lines & Clamps" | Hoses/Lines & Clamps |
| "Ignition" | Ignition |
| "Interior" | Interior |
| "Literature" | Literature |
| "Steering" | Steering |
| "Suspension" | Suspension |
| "Transmission-Automatic" | Transmission-Automatic |
| "Transmission-Manual" | Transmission-Manual |
| "Wheel" | Wheel |
| "Wiper & Washer" | Wiper & Washer |

## 3. Top Search Bar ("What is part called" search)

### Form Details
- **Class**: `catalog-search-bar-form`
- **Action**: Empty (submits to current page)
- **Method**: `POST`

### Form Fields

#### 1. Search Input
- **Element**: `<input type="text">`
- **Name**: `topsearchinput[input]`
- **ID**: `topsearchinput[input]`
- **Placeholder**: "year make model part type or part number or question"
- **Max Length**: 100 characters
- **Classes**: `topsearchinput topsearchwidth`

#### 2. Submit Button
- **Element**: `<input type="submit">`
- **Name**: `btntabsearch`
- **ID**: `btntabsearch`
- **Value**: "Search"

#### 3. Hidden Fields
- **_nck**: Security token (same format as main form)
- **topsearchinput[submit]**: Set to "1"

## 4. Manufacturer Options (Sample)

The manufacturer dropdown contains 570 options. Here are the first 20:

| Value | Display Text |
|-------|--------------|
| "" | All |
| "3D" | 3D |
| "3M" | 3M |
| "AAE" | AAE |
| "ACC" | ACC |
| "ACCEL" | ACCEL |
| "ACDELCO" | ACDELCO |
| "ACE" | ACE |
| "ACI" | ACI |
| "ACKOJA" | ACKOJA |
| "ACME AUTO" | ACME AUTO |
| "ADVAN-TECH" | ADVAN-TECH |
| "ADVICS" | ADVICS |
| "AEM INDUCTION" | AEM INDUCTION |
| "AGILITY" | AGILITY |
| "AGS" | AGS |
| "AIMCO" | AIMCO |
| "AIRAID" | AIRAID |
| "AIRQUALITEE" | AIRQUALITEE |
| "AIRTEX" | AIRTEX |

## 5. Part Type Options (Sample)

The part type dropdown contains 5,314 options. Here are the first 20:

| Value | Display Text |
|-------|--------------|
| "" | All |
| "1001839" | SAE 0W-20 |
| "1000865" | 1/4" (6.4mm) Belt |
| "1001846" | SAE 5W-40 |
| "1000578" | 3/8" (9.5mm) Belt |
| "1000783" | 3/8" (9.5mm) Belt |
| "1000581" | 1/2" (12.7mm) Belt |
| "1000864" | 13/32" (10.3mm) Belt |
| "1001208" | 17/32" (13.5mm) Belt |
| "1000584" | 5/8" (15.9mm) Belt |
| "1001207" | 7/16" (11.1mm) Belt |
| "1000582" | 21/32" (16.7mm) Belt |
| "1000866" | 3/4" (19.1mm) Belt |
| "1001850" | SAE 10W-30 |
| "1001851" | SAE 10W-40 |
| "1001852" | SAE 10W-50 |
| "1000778" | 1/2" (12.7mm) Belt |
| "1000780" | 17/32" (13.5mm) Belt |
| "1001541" | 27/32" (21.4mm) Belt |
| "1000585" | 7/8" (22.2mm) Belt |

## 6. Security & Session Management

### CSRF Protection
- All forms include a hidden `_nck` field containing a security token
- This token appears to be required for form submission
- Token format: Base64-encoded string, approximately 200+ characters

### Session State
- The page uses JavaScript for dynamic behavior
- Form elements have JavaScript event handlers for enhanced functionality
- The manufacturer dropdown has an onChange handler that may update other fields

## 7. JavaScript Functionality

### Dynamic Form Behavior
- Manufacturer selection triggers: `clb.PartSearchChangeMfrOption(this, "partsearch_007")`
- Top search has autocomplete functionality with these handlers:
  - `onkeydown="akhandler(event)"`
  - `onkeyup="acmp_keyup(event)"`
  - `onfocus="acmp_partcategory = null"`
  - Auto-suggestion system

### Search Suggestions
- The top search includes an auto-suggest feature
- Suggestion container: `<table id="autosuggestions[topsearchinput]">`
- Results message area: `<span id="searchresultmessage[topsearchinput]">`

## 8. Implementation Notes for Web Scraping

### Required Headers
```python
headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
    'Content-Type': 'application/x-www-form-urlencoded',
    'Referer': 'https://www.rockauto.com/en/partsearch/'
}
```

### Form Data Structure for Main Search
```python
form_data = {
    '_nck': '[EXTRACTED_TOKEN]',
    'dopartsearch': '1',
    'partsearch[partnum][partsearch_007]': 'PART_NUMBER',
    'partsearch[manufacturer][partsearch_007]': 'MANUFACTURER_VALUE',
    'partsearch[partgroup][partsearch_007]': 'PART_GROUP_VALUE',
    'partsearch[parttype][partsearch_007]': 'PART_TYPE_VALUE',
    'partsearch[partname][partsearch_007]': 'PART_NAME',
    'partsearch[do][partsearch_007]': 'Search'
}
```

### Form Data Structure for Top Search
```python
form_data = {
    '_nck': '[EXTRACTED_TOKEN]',
    'topsearchinput[submit]': '1',
    'topsearchinput[input]': 'SEARCH_QUERY',
    'btntabsearch': 'Search'
}
```

### Token Extraction
The security token (`_nck`) must be extracted from the initial page load and included in all subsequent requests.

### Search Result Structure
Based on the form analysis, search results would be returned as a new page load. The results structure would need to be analyzed from actual search responses.

## 9. Recommended Scraping Approach

1. **Initial Page Load**: GET https://www.rockauto.com/en/partsearch/
2. **Extract Token**: Parse the `_nck` hidden input value
3. **Form Submission**: POST to /en/partsearch/ with appropriate form data
4. **Result Parsing**: Parse the returned HTML for search results

### Session Management
- Maintain cookies across requests to preserve session state
- The `_nck` token may change between requests, so extract it fresh for each form submission

### Rate Limiting
- Implement appropriate delays between requests
- Consider rotating User-Agent strings and IP addresses for large-scale scraping

This analysis provides all the necessary information to implement robust web scraping for RockAuto's parts search functionality.