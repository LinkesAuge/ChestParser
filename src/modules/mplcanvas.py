# mplcanvas.py - MplCanvas class implementation
from modules.utils import *
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
import matplotlib.pyplot as plt
import numpy as np
from pathlib import Path
import os

class MplCanvas(FigureCanvas):
    """Matplotlib canvas for embedding in Qt applications."""
    
    def __init__(self, width=5, height=4, dpi=100):
        """Initialize the canvas with dark theme styling."""
        # Create figure with dark background
        self.fig = Figure(figsize=(width, height), dpi=dpi, facecolor='#1A2742')
        self.axes = self.fig.add_subplot(111)
        
        # Initialize parent
        super().__init__(self.fig)
        
        # Set up style presets
        self.style_presets = {
            'default': {
                'bg_color': '#1A2742',  # Dark blue background
                'text_color': '#FFFFFF',  # White text
                'grid_color': '#2A3F5F',  # Medium blue grid
                'tick_color': '#FFFFFF',  # White ticks
                'title_color': '#D4AF37',  # Gold title
                'title_size': 14,
                'label_size': 12,
                'bar_colors': ['#D4AF37', '#5991C4', '#6EC1A7', '#D46A5F'],  # Gold, Blue, Green, Red
                'pie_colors': ['#D4AF37', '#5991C4', '#6EC1A7', '#D46A5F', '#8899AA', '#F0C75A'],
                'line_color': '#5991C4',  # Blue
                'line_width': 2.5,
                'marker_size': 8,
                'marker_color': '#D4AF37',  # Gold markers
                'edge_color': '#1A2742'  # Dark blue edges
            }
        }
        
        # Apply dark theme
        self.apply_style('default')
    
    def apply_style(self, style_name='default'):
        """Apply the dark theme style to the chart."""
        if style_name not in self.style_presets:
            return
            
        style = self.style_presets[style_name]
        
        # Set figure and axes colors
        self.fig.patch.set_facecolor(style['bg_color'])
        self.axes.set_facecolor(style['bg_color'])
        
        # Set text colors
        self.axes.title.set_color(style['title_color'])
        self.axes.xaxis.label.set_color(style['text_color'])
        self.axes.yaxis.label.set_color(style['text_color'])
        
        # Set tick colors
        self.axes.tick_params(colors=style['tick_color'])
        
        # Set grid
        self.axes.grid(True, color=style['grid_color'], linestyle='--', alpha=0.3)
        
        # Set spine colors
        for spine in self.axes.spines.values():
            spine.set_color(style['grid_color'])
        
        # Update the display
        self.draw()
    
    def apply_style_to_axes(self, ax, style_name='default'):
        """
        Apply the dark theme style to the specified axes object.
        Useful when creating new subplots manually.
        
        Args:
            ax (matplotlib.axes.Axes): The axes object to style
            style_name (str, optional): The style preset to use. Defaults to 'default'.
        """
        if style_name not in self.style_presets:
            return
            
        style = self.style_presets[style_name]
        
        # Set axes colors
        ax.set_facecolor(style['bg_color'])
        
        # Set text colors
        ax.title.set_color(style['title_color'])
        ax.xaxis.label.set_color(style['text_color'])
        ax.yaxis.label.set_color(style['text_color'])
        
        # Set tick colors
        ax.tick_params(colors=style['tick_color'])
        
        # Set grid
        ax.grid(True, color=style['grid_color'], linestyle='--', alpha=0.3)
        
        # Set spine colors
        for spine in ax.spines.values():
            spine.set_color(style['grid_color'])
            
        # Set title font size
        ax.title.set_fontsize(style['title_size'])
        
        # Update the display
        self.draw()
        
        return ax
    
    def get_tableau_colors(self):
        """
        Get the Tableau-like color palette used in the application.
        
        Returns:
            list: List of hex color codes for charts
        """
        return [
            '#D4AF37',  # Gold
            '#5991C4',  # Blue
            '#6EC1A7',  # Green
            '#D46A5F',  # Red
            '#A073D1',  # Purple
            '#F49E5D',  # Orange
            '#9DC375',  # Light Green
            '#C4908F',  # Rose
            '#8595A8',  # Gray Blue
            '#D9A471',  # Tan
        ]
    
    def save_figure(self, filepath, dpi=300):
        """
        Save the figure to a file.
        
        Args:
            filepath (str): The path to save the figure to.
            dpi (int, optional): The resolution of the saved figure in dots per inch. Defaults to 300.
            
        Returns:
            str: The path the figure was saved to.
        """
        self.fig.savefig(filepath, dpi=dpi, bbox_inches='tight', facecolor=self.fig.get_facecolor())
        return filepath


