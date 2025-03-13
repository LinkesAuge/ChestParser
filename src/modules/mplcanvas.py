# mplcanvas.py - MplCanvas class implementation
from modules.utils import *
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
import matplotlib.pyplot as plt
import numpy as np
from pathlib import Path
import os

class MplCanvas(FigureCanvas):
    """Matplotlib canvas for embedding in Qt applications with consistent styling."""
    
    def __init__(self, width=5, height=4, dpi=100):
        """Initialize the canvas with dark theme styling."""
        # Define style settings first
        self.define_style_presets()
        
        # Create figure with dark background
        self.fig = Figure(figsize=(width, height), dpi=dpi)
        self.axes = self.fig.add_subplot(111)
        
        # Initialize parent
        super().__init__(self.fig)
        
        # Apply dark theme
        self.apply_default_style()
    
    def define_style_presets(self):
        """Define style presets for the application."""
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
    
    def apply_default_style(self):
        """Apply the default style to the chart."""
        self.apply_style('default')
    
    def apply_style(self, style_name='default'):
        """
        Apply the specified style to the chart.
        
        Args:
            style_name (str): The name of the style preset to use
        """
        if style_name not in self.style_presets:
            print(f"Warning: Style '{style_name}' not found, using default")
            style_name = 'default'
            
        style = self.style_presets[style_name]
        
        # Set figure and axes colors
        self.fig.patch.set_facecolor(style['bg_color'])
        self.axes.set_facecolor(style['bg_color'])
        
        # Set text colors
        self.axes.xaxis.label.set_color(style['text_color'])
        self.axes.yaxis.label.set_color(style['text_color'])
        self.axes.title.set_color(style['title_color'])
        self.axes.title.set_fontsize(style['title_size'])
        
        # Set tick colors
        self.axes.tick_params(axis='both', colors=style['tick_color'], labelcolor=style['text_color'])
        
        # Set grid
        self.axes.grid(True, color=style['grid_color'], linestyle='--', alpha=0.3)
        
        # Set spine colors
        for spine in self.axes.spines.values():
            spine.set_color(style['grid_color'])
        
        # Update the display
        self.draw()
    
    def reset_figure(self):
        """
        Reset the figure by clearing it and creating new axes with default styling.
        Use this before drawing a new chart.
        
        Returns:
            matplotlib.axes.Axes: The new axes object
        """
        # Reset matplotlib's global parameters to defaults
        plt.rcdefaults()
        
        # Clear the figure
        self.fig.clear()
        
        # Create new axes
        self.axes = self.fig.add_subplot(111)
        
        # Apply styling
        self.apply_default_style()
        
        # Make sure existing text objects are cleared
        for text in self.axes.texts:
            text.remove()
            
        return self.axes
    
    def add_text(self, x, y, text, ha='center', va='bottom', fontweight='bold', size=None):
        """
        Add text to the chart with consistent styling.
        
        Args:
            x (float): X-coordinate
            y (float): Y-coordinate
            text (str): Text to display
            ha (str, optional): Horizontal alignment. Defaults to 'center'.
            va (str, optional): Vertical alignment. Defaults to 'bottom'.
            fontweight (str, optional): Font weight. Defaults to 'bold'.
            size (int, optional): Font size. Defaults to None.
            
        Returns:
            matplotlib.text.Text: The text object
        """
        style = self.style_presets['default']
        
        # Create text with consistent styling
        text_obj = self.axes.text(x, y, text, 
                                 ha=ha, 
                                 va=va, 
                                 color=style['text_color'],
                                 fontweight=fontweight)
        
        # Set size if specified
        if size is not None:
            text_obj.set_size(size)
            
        return text_obj
    
    def add_text_to_axes(self, ax, x, y, text, ha='center', va='bottom', fontweight='bold', size=None):
        """
        Add text to specific axes with consistent styling.
        
        Args:
            ax (matplotlib.axes.Axes): The axes to add text to
            x (float): X-coordinate
            y (float): Y-coordinate
            text (str): Text to display
            ha (str, optional): Horizontal alignment. Defaults to 'center'.
            va (str, optional): Vertical alignment. Defaults to 'bottom'.
            fontweight (str, optional): Font weight. Defaults to 'bold'.
            size (int, optional): Font size. Defaults to None.
            
        Returns:
            matplotlib.text.Text: The text object
        """
        style = self.style_presets['default']
        
        # Create text with consistent styling
        text_obj = ax.text(x, y, text, 
                          ha=ha, 
                          va=va, 
                          color=style['text_color'],
                          fontweight=fontweight)
        
        # Set size if specified
        if size is not None:
            text_obj.set_size(size)
            
        return text_obj
    
    def get_colors(self):
        """
        Get the color palette used in the application.
        
        Returns:
            list: List of hex color codes for charts
        """
        return self.style_presets['default']['bar_colors']
    
    def apply_style_to_axes(self, ax):
        """
        Apply the default style to external axes.
        Useful for report charts or manually created subplots.
        
        Args:
            ax (matplotlib.axes.Axes): The axes to style
            
        Returns:
            matplotlib.axes.Axes: The styled axes
        """
        style = self.style_presets['default']
        
        # Set axes background
        ax.set_facecolor(style['bg_color'])
        
        # Set text colors
        ax.xaxis.label.set_color(style['text_color'])
        ax.yaxis.label.set_color(style['text_color'])
        ax.title.set_color(style['title_color'])
        ax.title.set_fontsize(style['title_size'])
        
        # Set tick colors
        ax.tick_params(axis='both', colors=style['tick_color'], labelcolor=style['text_color'])
        
        # Set grid
        ax.grid(True, color=style['grid_color'], linestyle='--', alpha=0.3)
        
        # Set spine colors
        for spine in ax.spines.values():
            spine.set_color(style['grid_color'])
            
        # Clear any existing text objects
        for text in ax.texts:
            text.remove()
            
        return ax
    
    def save_figure(self, filepath, dpi=300):
        """
        Save the figure to a file.
        
        Args:
            filepath (str): The path to save the figure to.
            dpi (int, optional): The resolution of the saved figure in dots per inch. Defaults to 300.
            
        Returns:
            str: The path the figure was saved to.
        """
        style = self.style_presets['default']
        self.fig.savefig(
            filepath, 
            dpi=dpi, 
            bbox_inches='tight', 
            facecolor=style['bg_color'], 
            edgecolor='none'
        )
        return filepath


