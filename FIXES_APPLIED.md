# Fixes Applied - TUI Duplicate Key Issue

## Problem
The TUI was throwing a `DuplicateKey` error because multiple comments from different files could have the same line number, causing duplicate row keys in the DataTable.

## Fixes Applied

### 1. Fixed Duplicate Key Issue in TUI (`codeatlas/tui.py`)
- **Changed**: Row keys now use a unique format: `"{file_path}:{line_number}:{index}"`
- **Location**: `CommentList.on_mount()` method
- **Impact**: Each comment now has a unique key, preventing duplicate key errors

### 2. Updated Row Selection Handler (`codeatlas/tui.py`)
- **Changed**: `on_data_table_row_selected()` now properly parses the unique key format
- **Location**: `CommentTUI.on_data_table_row_selected()` method
- **Impact**: Comment selection now correctly identifies and displays the right comment

### 3. Improved Comment Line Counting (`codeatlas/scanner.py`)
- **Changed**: Comment line counting now properly handles block comments that span multiple lines
- **Location**: `CodebaseScanner._scan_file()` method
- **Impact**: More accurate statistics for files with multi-line block comments

### 4. Enhanced Filter Support in CLI (`codeatlas/cli.py`)
- **Changed**: CLI now properly filters comments before passing to TUI
- **Location**: `comments()` command function
- **Impact**: TUI now shows only filtered comments when filters are applied

### 5. Added Missing Import (`codeatlas/cli.py`)
- **Changed**: Added `Dict` to imports from `typing`
- **Impact**: Fixed type annotation issues

## Testing Recommendations

1. Test TUI with multiple comments on the same line number from different files
2. Test TUI with filtered comments (--file, --language, --text filters)
3. Test comment line counting with block comments spanning multiple lines
4. Verify row selection works correctly in TUI

## Files Modified
- `codeatlas/tui.py` - Fixed duplicate keys and row selection
- `codeatlas/scanner.py` - Improved comment line counting
- `codeatlas/cli.py` - Enhanced filtering and added import

