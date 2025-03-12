#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Script to fix chart issues in the Total Battle Analyzer application.

This script corrects two specific issues:
1. Bar chart duplicate number labels
2. Line chart functionality not working properly
"""

import os
import sys
import shutil
import time
from pathlib import Path

def fix_chart_issues():
    """Fix chart issues in the mainwindow.py file."""
    # Path to the mainwindow.py file
    mainwindow_path = Path('src/modules/mainwindow.py')
    
    # Create backup
    backup_path = Path(f'src/modules/mainwindow_backup_{int(time.time())}.py')
    shutil.copy(mainwindow_path, backup_path)
    print(f"Created backup at {backup_path}")
    
    # Read the file content
    with open(mainwindow_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Fix 1: Add code to clear existing labels in Bar Chart section
    bar_chart_fix = """                # Add values on top of each bar if requested
                if show_values:
                    # Clear any existing value texts first to prevent duplicates
                    for text in ax.texts:
                        text.remove()
                    
                    for bar in bars:"""
    
    original_bar_chart = """                # Add values on top of each bar if requested
                if show_values:
                    for bar in bars:"""
    
    content = content.replace(original_bar_chart, bar_chart_fix)
    
    # Fix 2: Add code to clear existing labels in Horizontal Bar section
    horizontal_bar_fix = """                # Add values at the end of each bar if requested
                if show_values:
                    # Clear any existing value texts first to prevent duplicates
                    for text in ax.texts:
                        text.remove()
                        
                    for i, bar in enumerate(bars):"""
    
    original_horizontal_bar = """                # Add values at the end of each bar if requested
                if show_values:
                    for i, bar in enumerate(bars):"""
    
    content = content.replace(original_horizontal_bar, horizontal_bar_fix)
    
    # Fix 3: Add code to clear existing texts in Pie Chart section
    pie_chart_fix = """                # Calculate smaller data sample if too many slices would make pie chart unreadable
                pie_data = data
                if len(data) > 10:
                    # Limit to top 9 + "Others"
                    top_items = data.iloc[:9].copy()
                    others_sum = data.iloc[9:][measure].sum()
                    others_row = pd.DataFrame({
                        category_column: ['Others'],
                        measure: [others_sum]
                    })
                    pie_data = pd.concat([top_items, others_row]).reset_index(drop=True)
                
                # Clear any existing texts to prevent duplicates
                for text in ax.texts:
                    text.remove()
                
                # Use multiple colors"""
    
    original_pie_chart = """                # Calculate smaller data sample if too many slices would make pie chart unreadable
                pie_data = data
                if len(data) > 10:
                    # Limit to top 9 + "Others"
                    top_items = data.iloc[:9].copy()
                    others_sum = data.iloc[9:][measure].sum()
                    others_row = pd.DataFrame({
                        category_column: ['Others'],
                        measure: [others_sum]
                    })
                    pie_data = pd.concat([top_items, others_row]).reset_index(drop=True)
                
                # Use multiple colors"""
    
    content = content.replace(original_pie_chart, pie_chart_fix)
    
    # Fix 4: Completely replace the Line Chart section
    # First, find the start and end of the Line Chart section
    line_chart_start = "            elif chart_type == \"Line Chart\":"
    line_chart_end = "                    # For non-date categories, use a scatter plot with different colors"
    
    # Get the position of the start and end markers
    start_pos = content.find(line_chart_start)
    end_pos = content.find(line_chart_end)
    
    if start_pos != -1 and end_pos != -1:
        # Extract the part to replace
        line_chart_section = content[start_pos:end_pos]
        
        # Create the new line chart section
        new_line_chart_section = """            elif chart_type == "Line Chart":
                # For date data, a line chart makes sense as a single line
                if category_column == 'DATE':
                    # Sort data by date for line chart to ensure proper chronological order
                    data = data.sort_values(category_column)
                    
                    line = ax.plot(data[category_column].values, data[measure].values, 
                                  marker='o', color=TABLEAU_COLORS[2],  # Green
                                  linewidth=2, markersize=8)
                    
                    # Add values at each point if requested
                    if show_values:
                        # Clear any existing value texts first to prevent duplicates
                        for text in ax.texts:
                            text.remove()
                        
                        for i, (x, y) in enumerate(zip(data[category_column].values, data[measure].values)):
                            ax.text(x, y, f'{y:,.0f}', ha='center', va='bottom',
                                   color=self.chart_canvas.style_presets['default']['text_color'],
                                   fontweight='bold')
                    
                    ax.set_ylabel(f'{measure.replace("_", " ").title()}')
                    ax.set_title(f'{chart_title} Trends')
                    plt.setp(ax.get_xticklabels(), rotation=45, ha='right')
                else:
                    # For non-date categories, create a line chart with points at regular intervals
                    x = np.arange(len(data))
                    line = ax.plot(x, data[measure].values, 
                                  marker='o', color=TABLEAU_COLORS[2],  # Green
                                  linewidth=2, markersize=8)
                    
                    # Add values at each point if requested
                    if show_values:
                        # Clear any existing value texts first to prevent duplicates
                        for text in ax.texts:
                            text.remove()
                        
                        for i, y in enumerate(data[measure].values):
                            ax.text(i, y, f'{y:,.0f}', ha='center', va='bottom',
                                   color=self.chart_canvas.style_presets['default']['text_color'],
                                   fontweight='bold')
                    
                    # Set x-ticks to category names
                    ax.set_xticks(x)
                    ax.set_xticklabels(data[category_column].values)
                    ax.set_ylabel(f'{measure.replace("_", " ").title()}')
                    ax.set_title(f'{chart_title} Trends')
                    plt.setp(ax.get_xticklabels(), rotation=45, ha='right')
            
            """
        
        # Replace the line chart section
        content = content.replace(line_chart_section, new_line_chart_section)
    
    # Fix 5: Comment out duplicate generate_chart_for_report method
    # Find the start of the duplicate method
    duplicate_method_marker = "    def generate_chart_for_report(self, chart_type, category_field, title):"
    
    # Count how many times this method appears
    method_count = content.count(duplicate_method_marker)
    
    if method_count > 1:
        # Find the position of the second occurrence
        first_pos = content.find(duplicate_method_marker)
        second_pos = content.find(duplicate_method_marker, first_pos + 1)
        
        if second_pos != -1:
            # Find the next method definition after the duplicate method
            next_method_marker = "    def "
            next_method_pos = content.find(next_method_marker, second_pos + 1)
            
            # If we found the next method, extract the duplicate method
            if next_method_pos != -1:
                duplicate_method = content[second_pos:next_method_pos]
                
                # Create commented version
                commented_method = "    # This is a duplicate method - removed to prevent conflicts\n"
                for line in duplicate_method.split('\n'):
                    if line.strip():
                        commented_method += "    # " + line[4:] + "\n"
                    else:
                        commented_method += "\n"
                
                # Replace the duplicate method with the commented version
                content = content.replace(duplicate_method, commented_method)
                
                print("Successfully commented out duplicate generate_chart_for_report method")
    
    # Write the modified content back to the file
    with open(mainwindow_path, 'w', encoding='utf-8') as f:
        f.write(content)
    
    print("Successfully updated mainwindow.py with fixes for chart issues")

def main():
    """Main function to fix chart issues and run the application."""
    try:
        fix_chart_issues()
        print("Chart fixes applied successfully. You can now run the application.")
        return 0
    except Exception as e:
        print(f"Error: {str(e)}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    sys.exit(main()) 