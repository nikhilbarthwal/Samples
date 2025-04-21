import numpy as np
import matplotlib.pyplot as plt
from matplotlib.widgets import Slider

# Set up the figure and axis
fig, ax = plt.subplots(figsize=(10, 6))
plt.subplots_adjust(bottom=0.25)  # Make room for the slider

# Initial parameters
initial_freq = 1.0
initial_amp = 1.0
initial_phase = 0.0

# Create the x values
x = np.linspace(0, 2*np.pi, 500)

# Create the initial plot
line, = ax.plot(x, initial_amp * np.sin(initial_freq * x + initial_phase), 'b-', linewidth=2)
ax.set_xlim(0, 2*np.pi)
ax.set_ylim(-2, 2)
ax.set_xlabel('x', fontsize=12)
ax.set_ylabel('sin(x)', fontsize=12)
ax.set_title('Interactive Sine Curve', fontsize=14)

# Add grid and text labels
ax.grid(True, linestyle='--', alpha=0.7)
ax.text(0.5, -1.8, 'Interactive Sine Wave Demonstration', 
        fontsize=10, ha='center', color='darkblue')
ax.text(np.pi/2, 1.5, 'Peak', fontsize=10, color='red')
ax.text(3*np.pi/2, -1.5, 'Trough', fontsize=10, color='red')

# Add zero-crossing markers
zero_crossings = [0, np.pi, 2*np.pi]
for x_val in zero_crossings:
    ax.plot(x_val, 0, 'ro', markersize=8, alpha=0.5)
    ax.text(x_val, 0.2, f'{x_val/np.pi:.1f}π', 
            ha='center', fontsize=10, color='darkgreen')

# Create slider axes
ax_freq = plt.axes([0.25, 0.15, 0.65, 0.03])
ax_amp = plt.axes([0.25, 0.1, 0.65, 0.03])
ax_phase = plt.axes([0.25, 0.05, 0.65, 0.03])

# Create sliders
freq_slider = Slider(ax_freq, 'Frequency', 0.1, 5.0, valinit=initial_freq, valstep=0.1)
amp_slider = Slider(ax_amp, 'Amplitude', 0.1, 2.0, valinit=initial_amp, valstep=0.1)
phase_slider = Slider(ax_phase, 'Phase', -np.pi, np.pi, valinit=initial_phase, valstep=0.1)

# Update function for the slider
def update(val):
    freq = freq_slider.val
    amp = amp_slider.val
    phase = phase_slider.val
    line.set_ydata(amp * np.sin(freq * x + phase))
    fig.canvas.draw_idle()

# Register the update function with each slider
freq_slider.on_changed(update)
amp_slider.on_changed(update)
phase_slider.on_changed(update)

plt.show()


        