"""
Complete Error Catalog - 75 Errors with User-Friendly Messages
Each error includes: code, message, severity, auto_fix, user_action
"""

ERROR_CATALOG = {
    # ============ SKU ERRORS (1-10) ============
    "E001": {
        "code": "E001", "category": "sku",
        "message": "SKU column contains numbers instead of text codes",
        "user_message": "We found numeric codes in your SKU column. We converted these automatically.",
        "severity": "auto_fix",
    },
    "E002": {
        "code": "E002", "category": "sku",
        "message": "SKU column contains decimal numbers",
        "user_message": "Your SKUs appear as decimals (e.g., 123.0). Fixed automatically.",
        "severity": "auto_fix",
    },
    "E003": {
        "code": "E003", "category": "sku",
        "message": "SKU not found in your product catalog",
        "user_message": "{count} SKUs in your file don't exist in your catalog: {skus}",
        "severity": "blocking",
    },
    "E004": {
        "code": "E004", "category": "sku",
        "message": "Duplicate SKU in file",
        "user_message": "The same SKU appears multiple times in your file.",
        "severity": "warning",
    },
    "E005": {
        "code": "E005", "category": "sku",
        "message": "SKU column is empty",
        "user_message": "The SKU column has no data.",
        "severity": "blocking",
    },
    "E006": {
        "code": "E006", "category": "sku",
        "message": "SKU contains special characters",
        "user_message": "Special characters removed from {count} SKUs.",
        "severity": "auto_fix",
    },
    "E007": {
        "code": "E007", "category": "sku",
        "message": "SKU has extra spaces",
        "user_message": "Trimmed spaces from SKU codes.",
        "severity": "auto_fix",
    },
    "E008": {
        "code": "E008", "category": "sku",
        "message": "SKU case mismatch",
        "user_message": "SKU capitalization corrected to match your catalog.",
        "severity": "auto_fix",
    },
    "E009": {
        "code": "E009", "category": "sku",
        "message": "EAN/barcode used instead of SKU",
        "user_message": "Barcode numbers mapped to SKU codes from your catalog.",
        "severity": "auto_fix",
    },
    "E010": {
        "code": "E010", "category": "sku",
        "message": "SKU displayed in scientific notation",
        "user_message": "Excel converted long numbers to scientific format. Restored original SKU.",
        "severity": "auto_fix",
    },

    # ============ STORE ERRORS (11-18) ============
    "E011": {
        "code": "E011", "category": "store",
        "message": "Store code not found",
        "user_message": "{count} store codes don't exist in your store list: {stores}",
        "severity": "blocking",
    },
    "E012": {
        "code": "E012", "category": "store",
        "message": "Store column missing",
        "user_message": "Your file doesn't have a 'store_code' column.",
        "severity": "blocking",
    },
    "E013": {
        "code": "E013", "category": "store",
        "message": "Store code is numeric",
        "user_message": "Store codes converted from numbers to text.",
        "severity": "auto_fix",
    },
    "E014": {
        "code": "E014", "category": "store",
        "message": "Multiple stores in one row",
        "user_message": "Some rows contain multiple stores (comma-separated).",
        "severity": "warning",
    },
    "E015": {
        "code": "E015", "category": "store",
        "message": "Store code case mismatch",
        "user_message": "Store capitalization corrected to match your master list.",
        "severity": "auto_fix",
    },
    "E016": {
        "code": "E016", "category": "store",
        "message": "Inactive store used",
        "user_message": "Store '{code}' is marked as inactive.",
        "severity": "warning",
    },
    "E017": {
        "code": "E017", "category": "store",
        "message": "Store assigned to wrong warehouse",
        "user_message": "Store '{store}' warehouse mismatch.",
        "severity": "warning",
    },
    "E018": {
        "code": "E018", "category": "store",
        "message": "Store not assigned to any warehouse",
        "user_message": "Store '{code}' has no warehouse assigned.",
        "severity": "warning",
    },

    # ============ DATE ERRORS (19-26) ============
    "E019": {
        "code": "E019", "category": "date",
        "message": "Invalid date format",
        "user_message": "{count} dates could not be parsed.",
        "severity": "blocking",
    },
    "E020": {
        "code": "E020", "category": "date",
        "message": "Date is in the future",
        "user_message": "{count} rows have dates in the future.",
        "severity": "warning",
    },
    "E021": {
        "code": "E021", "category": "date",
        "message": "Date is very old",
        "user_message": "{count} rows have dates more than 1 year old.",
        "severity": "warning",
    },
    "E022": {
        "code": "E022", "category": "date",
        "message": "Excel serial date detected",
        "user_message": "Dates converted from Excel serial numbers.",
        "severity": "auto_fix",
    },
    "E023": {
        "code": "E023", "category": "date",
        "message": "Text date detected",
        "user_message": "Relative dates converted to actual dates.",
        "severity": "auto_fix",
    },
    "E024": {
        "code": "E024", "category": "date",
        "message": "Inconsistent date formats",
        "user_message": "Mixed date formats standardized to YYYY-MM-DD.",
        "severity": "auto_fix",
    },
    "E025": {
        "code": "E025", "category": "date",
        "message": "Missing date column",
        "user_message": "Your file doesn't have a date column.",
        "severity": "blocking",
    },
    "E026": {
        "code": "E026", "category": "date",
        "message": "Date includes time",
        "user_message": "Timestamps extracted to date-only format.",
        "severity": "auto_fix",
    },

    # ============ QUANTITY ERRORS (27-34) ============
    "E027": {
        "code": "E027", "category": "quantity",
        "message": "Negative quantity detected",
        "user_message": "{count} rows have negative quantities.",
        "severity": "warning",
    },
    "E028": {
        "code": "E028", "category": "quantity",
        "message": "Zero quantity detected",
        "user_message": "{count} rows have zero quantity.",
        "severity": "warning",
    },
    "E029": {
        "code": "E029", "category": "quantity",
        "message": "Quantity is text",
        "user_message": "Text quantities converted to numbers.",
        "severity": "auto_fix",
    },
    "E030": {
        "code": "E030", "category": "quantity",
        "message": "Decimal quantity detected",
        "user_message": "{count} rows have fractional quantities.",
        "severity": "warning",
    },
    "E031": {
        "code": "E031", "category": "quantity",
        "message": "Missing quantity values",
        "user_message": "{count} rows have blank quantities. Set to 0.",
        "severity": "warning",
    },
    "E032": {
        "code": "E032", "category": "quantity",
        "message": "Unusually large quantity",
        "user_message": "Row {row} has quantity {value} which seems unusually high.",
        "severity": "requires_approval",
    },
    "E033": {
        "code": "E033", "category": "quantity",
        "message": "Quantity exceeds available inventory",
        "user_message": "Selling {sold} units but only {available} available.",
        "severity": "warning",
    },
    "E034": {
        "code": "E034", "category": "quantity",
        "message": "Quantity has commas",
        "user_message": "Commas removed from quantity values.",
        "severity": "auto_fix",
    },

    # ============ REVENUE ERRORS (35-42) ============
    "E035": {
        "code": "E035", "category": "revenue",
        "message": "Negative revenue detected",
        "user_message": "{count} rows have negative revenue.",
        "severity": "warning",
    },
    "E036": {
        "code": "E036", "category": "revenue",
        "message": "Currency symbols detected",
        "user_message": "Currency symbols removed from revenue values.",
        "severity": "auto_fix",
    },
    "E037": {
        "code": "E037", "category": "revenue",
        "message": "Revenue is text",
        "user_message": "Text revenue values converted to numbers.",
        "severity": "auto_fix",
    },
    "E038": {
        "code": "E038", "category": "revenue",
        "message": "Revenue has commas",
        "user_message": "Commas removed from revenue values.",
        "severity": "auto_fix",
    },
    "E039": {
        "code": "E039", "category": "revenue",
        "message": "Revenue doesn't match quantity x price",
        "user_message": "{count} rows have revenue that doesn't match quantity x unit price.",
        "severity": "warning",
    },
    "E040": {
        "code": "E040", "category": "revenue",
        "message": "Unusually large revenue",
        "user_message": "Row {row} has revenue {value} which seems unusually high.",
        "severity": "requires_approval",
    },
    "E041": {
        "code": "E041", "category": "revenue",
        "message": "Zero revenue with positive quantity",
        "user_message": "{count} rows have quantity > 0 but revenue = 0.",
        "severity": "warning",
    },
    "E042": {
        "code": "E042", "category": "revenue",
        "message": "Unit price mismatch with master",
        "user_message": "Unit price differs from catalog by more than 10%.",
        "severity": "warning",
    },

    # ============ FILE STRUCTURE ERRORS (43-50) ============
    "E043": {
        "code": "E043", "category": "file_structure",
        "message": "Missing required columns",
        "user_message": "Your file is missing these columns: {columns}",
        "severity": "blocking",
    },
    "E044": {
        "code": "E044", "category": "file_structure",
        "message": "Extra columns detected",
        "user_message": "Extra columns ignored: {columns}",
        "severity": "info",
    },
    "E045": {
        "code": "E045", "category": "file_structure",
        "message": "Empty file",
        "user_message": "Your file contains no data rows.",
        "severity": "blocking",
    },
    "E046": {
        "code": "E046", "category": "file_structure",
        "message": "No header row detected",
        "user_message": "Your file doesn't have column headers.",
        "severity": "warning",
    },
    "E047": {
        "code": "E047", "category": "file_structure",
        "message": "Wrong file format",
        "user_message": "Please upload a CSV or Excel file.",
        "severity": "blocking",
    },
    "E048": {
        "code": "E048", "category": "file_structure",
        "message": "Character encoding issue",
        "user_message": "Character encoding auto-detected and corrected.",
        "severity": "auto_fix",
    },
    "E049": {
        "code": "E049", "category": "file_structure",
        "message": "File too large",
        "user_message": "Your file is {size}MB. Maximum is 50MB.",
        "severity": "blocking",
    },
    "E050": {
        "code": "E050", "category": "file_structure",
        "message": "Duplicate rows detected",
        "user_message": "{count} rows are exact duplicates. Kept first occurrence.",
        "severity": "warning",
    },

    # ============ DUPLICATE & OVERWRITE ERRORS (51-57) ============
    "E051": {
        "code": "E051", "category": "duplicate",
        "message": "Data for this date already exists",
        "user_message": "You already uploaded data for {date}.",
        "severity": "warning",
    },
    "E052": {
        "code": "E052", "category": "duplicate",
        "message": "Partial duplicate detected",
        "user_message": "Some rows overlap with existing data.",
        "severity": "warning",
    },
    "E053": {
        "code": "E053", "category": "duplicate",
        "message": "Upload contains older data",
        "user_message": "Uploading older data than what already exists.",
        "severity": "warning",
    },
    "E054": {
        "code": "E054", "category": "duplicate",
        "message": "Same file uploaded twice",
        "user_message": "This file was already uploaded on {date} at {time}.",
        "severity": "blocking",
    },
    "E055": {
        "code": "E055", "category": "duplicate",
        "message": "Data gap detected",
        "user_message": "Missing data for {missing_date} before this upload.",
        "severity": "warning",
    },
    "E056": {
        "code": "E056", "category": "duplicate",
        "message": "Weekend/holiday upload",
        "user_message": "{date} is a {day_type}. Store may be closed.",
        "severity": "warning",
    },
    "E057": {
        "code": "E057", "category": "duplicate",
        "message": "Another user is editing this data",
        "user_message": "{user} is currently uploading data for {date}.",
        "severity": "info",
    },

    # ============ CROSS-FILE CONSISTENCY ERRORS (58-63) ============
    "E058": {
        "code": "E058", "category": "consistency",
        "message": "Sales exceed store inventory",
        "user_message": "Selling {sold} units but store only reported {stock} in inventory.",
        "severity": "blocking",
    },
    "E059": {
        "code": "E059", "category": "consistency",
        "message": "Store and warehouse inventory mismatch",
        "user_message": "Store stock + Warehouse stock doesn't match expected total.",
        "severity": "warning",
    },
    "E060": {
        "code": "E060", "category": "consistency",
        "message": "Store has inventory but no sales",
        "user_message": "{count} stores have inventory but no sales reported today.",
        "severity": "warning",
    },
    "E061": {
        "code": "E061", "category": "consistency",
        "message": "Inventory uploaded but sales missing",
        "user_message": "Store inventory uploaded but not daily sales.",
        "severity": "reminder",
    },
    "E062": {
        "code": "E062", "category": "consistency",
        "message": "SKU sold at store where not stocked",
        "user_message": "SKU '{sku}' sold at {store} but not in that store's inventory.",
        "severity": "warning",
    },
    "E063": {
        "code": "E063", "category": "consistency",
        "message": "Warehouse inventory negative after sales",
        "user_message": "After applying sales, warehouse would have negative stock.",
        "severity": "blocking",
    },

    # ============ BUSINESS RULE ERRORS (64-70) ============
    "E064": {
        "code": "E064", "category": "business_rule",
        "message": "Sell-through rate > 100%",
        "user_message": "Sold more than beginning inventory + received.",
        "severity": "blocking",
    },
    "E065": {
        "code": "E065", "category": "business_rule",
        "message": "Revenue per unit outside acceptable range",
        "user_message": "Unit price {price} is outside normal range for this SKU.",
        "severity": "requires_approval",
    },
    "E066": {
        "code": "E066", "category": "business_rule",
        "message": "Inventory below safety stock",
        "user_message": "{count} SKUs will be below minimum stock level.",
        "severity": "warning",
    },
    "E067": {
        "code": "E067", "category": "business_rule",
        "message": "Inventory above max capacity",
        "user_message": "{count} SKUs exceed maximum stock level.",
        "severity": "warning",
    },
    "E068": {
        "code": "E068", "category": "business_rule",
        "message": "Negative inventory at store",
        "user_message": "Store '{store}' would have negative stock for {count} SKUs.",
        "severity": "blocking",
    },
    "E069": {
        "code": "E069", "category": "business_rule",
        "message": "Store reported sales but was closed",
        "user_message": "{store} reported sales on {date} but was closed.",
        "severity": "warning",
    },
    "E070": {
        "code": "E070", "category": "business_rule",
        "message": "Test data detected",
        "user_message": "This file appears to contain test data.",
        "severity": "warning",
    },

    # ============ TIMEZONE ERRORS (71-74) ============
    "E071": {
        "code": "E071", "category": "timezone",
        "message": "Date in wrong timezone",
        "user_message": "Date mismatch between your timezone and store timezone.",
        "severity": "warning",
    },
    "E072": {
        "code": "E072", "category": "timezone",
        "message": "Relative date confusion",
        "user_message": "'today' resolved to {date}.",
        "severity": "info",
    },
    "E073": {
        "code": "E073", "category": "timezone",
        "message": "DST transition day",
        "user_message": "{date} is a Daylight Saving Time transition day.",
        "severity": "warning",
    },
    "E074": {
        "code": "E074", "category": "timezone",
        "message": "Fiscal calendar mismatch",
        "user_message": "File uses fiscal calendar, system uses calendar months.",
        "severity": "info",
    },

    # ============ PERFORMANCE ERRORS (75) ============
    "E075": {
        "code": "E075", "category": "performance",
        "message": "Upload timeout - processing in background",
        "user_message": "Your file is large ({rows} rows). Processing in background.",
        "severity": "info",
    },
}


def get_error(error_code, **kwargs):
    """Get formatted error with user-friendly message."""
    error = ERROR_CATALOG.get(error_code, {})
    if not error:
        return {"code": "UNKNOWN", "message": "Unknown error", "severity": "error"}
    formatted = error.copy()
    if kwargs:
        try:
            formatted["user_message"] = formatted["user_message"].format(**kwargs)
        except (KeyError, IndexError):
            pass
    return formatted


def get_errors_by_severity(severity):
    return [e for e in ERROR_CATALOG.values() if e.get("severity") == severity]


def get_errors_by_category(category):
    return [e for e in ERROR_CATALOG.values() if e.get("category") == category]
