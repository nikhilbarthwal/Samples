import numpy as np
import matplotlib.pyplot as plt
from matplotlib.widgets import Button

# Set up the figure and main axis
fig = plt.figure(figsize=(10, 7))
ax = fig.add_subplot(111)
plt.subplots_adjust(bottom=0.3, right=0.85)  # Make room for buttons and labels

# Initial parameters
freq = 1.0
amp = 1.0
phase = 0.0

# Create the x values
x = np.linspace(0, 2*np.pi, 500)

# Create the initial plot
line, = ax.plot(x, amp * np.sin(freq * x + phase), 'b-', linewidth=2)
ax.set_xlim(0, 2*np.pi)
ax.set_ylim(-2.5, 2.5)
ax.set_xlabel('x (radians)', fontsize=12)
ax.set_ylabel('Amplitude', fontsize=12)
ax.set_title('Interactive Sine Curve with Arrow Controls', fontsize=14)
ax.grid(True, linestyle='--', alpha=0.7)

# Add text labels below the plot
info_text = plt.figtext(0.5, 0.15, 
                       f'Current: Frequency = {freq:.1f} Hz, Amplitude = {amp:.1f}, Phase = {phase:.1f} rad',
                       ha='center', fontsize=12, bbox=dict(facecolor='lightgray', alpha=0.5))

# Add descriptive text
plt.figtext(0.5, 0.1, 
           'Use the arrow buttons to adjust the sine wave parameters',
           ha='center', fontsize=10, style='italic')

# Function to update the plot
def update_plot():
    line.set_ydata(amp * np.sin(freq * x + phase))
    info_text.set_text(f'Current: Frequency = {freq:.1f} Hz, Amplitude = {amp:.1f}, Phase = {phase:.1f} rad')
    plt.draw()

# Create button axes (left, bottom, width, height)
ax_freq_up = plt.axes([0.87, 0.7, 0.1, 0.05])
ax_freq_down = plt.axes([0.87, 0.64, 0.1, 0.05])
ax_amp_up = plt.axes([0.87, 0.5, 0.1, 0.05])
ax_amp_down = plt.axes([0.87, 0.44, 0.1, 0.05])
ax_phase_up = plt.axes([0.87, 0.3, 0.1, 0.05])
ax_phase_down = plt.axes([0.87, 0.24, 0.1, 0.05])

# Create buttons
btn_freq_up = Button(ax_freq_up, '↑', color='lightgoldenrodyellow')
btn_freq_down = Button(ax_freq_down, '↓', color='lightgoldenrodyellow')
btn_amp_up = Button(ax_amp_up, '↑', color='lightblue')
btn_amp_down = Button(ax_amp_down, '↓', color='lightblue')
btn_phase_up = Button(ax_phase_up, '↑', color='lightgreen')
btn_phase_down = Button(ax_phase_down, '↓', color='lightgreen')

# Add button labels
plt.figtext(0.92, 0.72, 'Frequency', ha='left', fontsize=10)
plt.figtext(0.92, 0.52, 'Amplitude', ha='left', fontsize=10)
plt.figtext(0.92, 0.32, 'Phase', ha='left', fontsize=10)

# Button event handlers
def freq_up(event):
    global freq
    freq += 0.1
    update_plot()

def freq_down(event):
    global freq
    freq = max(0.1, freq - 0.1)
    update_plot()

def amp_up(event):
    global amp
    amp = min(2.0, amp + 0.1)
    update_plot()

def amp_down(event):
    global amp
    amp = max(0.1, amp - 0.1)
    update_plot()

def phase_up(event):
    global phase
    phase += 0.1
    update_plot()

def phase_down(event):
    global phase
    phase -= 0.1
    update_plot()

# Connect buttons to handlers
btn_freq_up.on_clicked(freq_up)
btn_freq_down.on_clicked(freq_down)
btn_amp_up.on_clicked(amp_up)
btn_amp_down.on_clicked(amp_down)
btn_phase_up.on_clicked(phase_up)
btn_phase_down.on_clicked(phase_down)

plt.show()
