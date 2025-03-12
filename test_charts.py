#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Test script for chart fixes in the Total Battle Analyzer application.

This script modifies the chart functionality and runs the application.
"""

import os
import sys
import shutil
import tempfile
from pathlib import Path
import time

def modify_mainwindow_py():
    """Modify the mainwindow.py file to fix chart issues."""
    # Path to the mainwindow.py file
    mainwindow_path = Path('src/modules/mainwindow.py')
    
    # Create backup
    backup_path = Path(f'src/modules/mainwindow_backup_{int(time.time())}.py')
    shutil.copy(mainwindow_path, backup_path)
    print(f"Created backup at {backup_path}")
    
    # Read the entire file
    with open(mainwindow_path, 'r', encoding='utf-8') as f:
        content = f.readlines()
    
    # Find the update_chart method's bar chart section
    bar_chart_idx = None
    line_chart_idx = None
    
    for i, line in enumerate(content):
        if 'def update_chart(self):' in line:
            print(f"Found update_chart method at line {i+1}")
        if 'if chart_type == "Bar Chart":' in line:
            bar_chart_idx = i
            print(f"Found Bar Chart section at line {i+1}")
        if 'elif chart_type == "Line Chart":' in line:
            line_chart_idx = i
            print(f"Found Line Chart section at line {i+1}")
    
    # Fix bar chart labels
    if bar_chart_idx:
        for i in range(bar_chart_idx, bar_chart_idx + 50):
            if "if show_values:" in content[i] and "for bar in bars:" in content[i+1]:
                # Insert code to clear existing labels
                content.insert(i+1, "                    # Clear any existing value texts first to prevent duplicates\n")
                content.insert(i+2, "                    for text in ax.texts:\n")
                content.insert(i+3, "                        text.remove()\n")
                content.insert(i+4, "                    \n")
                print("Added text clearing code for bar chart labels")
                break
    
    # Fix horizontal bar chart labels
    horizontal_bar_idx = None
    for i, line in enumerate(content):
        if 'elif chart_type == "Horizontal Bar":' in line:
            horizontal_bar_idx = i
            print(f"Found Horizontal Bar section at line {i+1}")
            break
    
    if horizontal_bar_idx:
        for i in range(horizontal_bar_idx, horizontal_bar_idx + 50):
            if "if show_values:" in content[i]:
                # Insert code to clear existing labels
                content.insert(i+1, "                    # Clear any existing value texts first to prevent duplicates\n")
                content.insert(i+2, "                    for text in ax.texts:\n")
                content.insert(i+3, "                        text.remove()\n")
                content.insert(i+4, "                    \n")
                print("Added text clearing code for horizontal bar chart labels")
                break
    
    # Fix pie chart labels
    pie_chart_idx = None
    for i, line in enumerate(content):
        if 'elif chart_type == "Pie Chart":' in line:
            pie_chart_idx = i
            print(f"Found Pie Chart section at line {i+1}")
            break
    
    if pie_chart_idx:
        for i in range(pie_chart_idx, pie_chart_idx + 10):
            if "# Calculate smaller data sample" in content[i]:
                # Insert code to clear existing labels
                content.insert(i+1, "                # Clear any existing texts to prevent duplicates\n")
                content.insert(i+2, "                for text in ax.texts:\n")
                content.insert(i+3, "                    text.remove()\n")
                content.insert(i+4, "                \n")
                print("Added text clearing code for pie chart labels")
                break
    
    # Fix line chart functionality
    if line_chart_idx:
        # Find the end of the line chart section
        line_chart_end_idx = None
        for i in range(line_chart_idx + 1, len(content)):
            if "else:" in content[i] and content[i].strip() == "else:":
                line_chart_end_idx = i
                print(f"Found end of Line Chart section at line {i+1}")
                break
        
        if line_chart_end_idx:
            # Replace the entire line chart section
            new_line_chart_section = [
                "                # For date data, a line chart makes sense as a single line\n",
                "                if category_column == 'DATE':\n",
                "                    # Sort data by date for line chart to ensure proper chronological order\n",
                "                    data = data.sort_values(category_column)\n",
                "                    \n",
                "                    line = ax.plot(data[category_column].values, data[measure].values, \n",
                "                                  marker='o', color=TABLEAU_COLORS[2],  # Green\n",
                "                                  linewidth=2, markersize=8)\n",
                "                    \n",
                "                    # Add values at each point if requested\n",
                "                    if show_values:\n",
                "                        # Clear any existing value texts first to prevent duplicates\n",
                "                        for text in ax.texts:\n",
                "                            text.remove()\n",
                "                        \n",
                "                        for i, (x, y) in enumerate(zip(data[category_column].values, data[measure].values)):\n",
                "                            ax.text(x, y, f'{y:,.0f}', ha='center', va='bottom',\n",
                "                                   color=self.chart_canvas.style_presets['default']['text_color'],\n",
                "                                   fontweight='bold')\n",
                "                    \n",
                "                    ax.set_ylabel(f'{measure.replace(\"_\", \" \").title()}')\n",
                "                    ax.set_title(f'{chart_title} Trends')\n",
                "                    plt.setp(ax.get_xticklabels(), rotation=45, ha='right')\n",
                "                else:\n",
                "                    # For non-date categories, create a line chart with points at regular intervals\n",
                "                    x = np.arange(len(data))\n",
                "                    line = ax.plot(x, data[measure].values, \n",
                "                                  marker='o', color=TABLEAU_COLORS[2],  # Green\n",
                "                                  linewidth=2, markersize=8)\n",
                "                    \n",
                "                    # Add values at each point if requested\n",
                "                    if show_values:\n",
                "                        # Clear any existing value texts first to prevent duplicates\n",
                "                        for text in ax.texts:\n",
                "                            text.remove()\n",
                "                        \n",
                "                        for i, y in enumerate(data[measure].values):\n",
                "                            ax.text(i, y, f'{y:,.0f}', ha='center', va='bottom',\n",
                "                                   color=self.chart_canvas.style_presets['default']['text_color'],\n",
                "                                   fontweight='bold')\n",
                "                    \n",
                "                    # Set x-ticks to category names\n",
                "                    ax.set_xticks(x)\n",
                "                    ax.set_xticklabels(data[category_column].values)\n",
                "                    ax.set_ylabel(f'{measure.replace(\"_\", \" \").title()}')\n",
                "                    ax.set_title(f'{chart_title} Trends')\n",
                "                    plt.setp(ax.get_xticklabels(), rotation=45, ha='right')\n"
            ]
            
            # Replace old line chart section with new one
            del content[line_chart_idx + 1:line_chart_end_idx]
            for i, line in enumerate(new_line_chart_section):
                content.insert(line_chart_idx + 1 + i, line)
            
            print("Replaced Line Chart section with enhanced implementation")
    
    # Remove duplicate generate_chart_for_report method
    duplicate_method_idx = None
    for i, line in enumerate(content):
        if i > 2500 and "def generate_chart_for_report(self, chart_type, category_field, title):" in line:
            duplicate_method_idx = i
            print(f"Found duplicate generate_chart_for_report method at line {i+1}")
            break
    
    if duplicate_method_idx:
        # Comment out the duplicate method
        # Find the end of the method (next def or end of file)
        duplicate_method_end_idx = None
        for i in range(duplicate_method_idx + 1, len(content)):
            if "    def " in content[i]:
                duplicate_method_end_idx = i
                print(f"Found end of duplicate method at line {i+1}")
                break
        
        if duplicate_method_end_idx:
            # Comment out all lines in the duplicate method
            comment_prefix = "    # "
            content[duplicate_method_idx] = comment_prefix + content[duplicate_method_idx][4:]
            for i in range(duplicate_method_idx + 1, duplicate_method_end_idx):
                if content[i].strip():  # Only comment non-empty lines
                    content[i] = comment_prefix + content[i][4:]
            
            # Add a comment explaining why this is commented out
            content.insert(duplicate_method_idx, "    # This is a duplicate method - removed to prevent conflicts\n")
            print("Commented out duplicate generate_chart_for_report method")
    
    # Write the modified content back to the file
    with open(mainwindow_path, 'w', encoding='utf-8') as f:
        f.writelines(content)
    
    print("Successfully updated mainwindow.py with fixes for chart issues")

def run_application():
    """Run the Total Battle Analyzer application."""
    # Import and run the main function from the main application file
    sys.path.append('src')
    try:
        from main import main
        main()
    except ImportError:
        print("Error: Could not import main.py. Make sure you're running this script from the project root directory.")
        return 1
    except Exception as e:
        print(f"Error running application: {str(e)}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0

if __name__ == "__main__":
    print("Applying chart fixes and running Total Battle Analyzer...")
    try:
        modify_mainwindow_py()
        sys.exit(run_application())
    except Exception as e:
        print(f"Error: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1) 