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
                'bar_colors': ['#D4AF37', '#345995', '#56A64B', '#A6564B'],  # Gold, Blue, Green, Red
                'pie_colors': ['#D4AF37', '#345995', '#56A64B', '#A6564B', '#8899AA', '#F0C75A'],
                'line_color': '#345995',  # Secondary blue
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


