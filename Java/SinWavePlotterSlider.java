import javax.swing.*;
import javax.swing.border.EmptyBorder;
import java.awt.*;
import java.awt.geom.Ellipse2D;
import java.awt.geom.Path2D;

/**
 * A complete, self-contained Swing application that plots a sine wave
 *      y = A * sin(2 * PI * f * t)
 * where the frequency f (in Hz) is controlled live by a JSlider.
 *
 * Compile:  javac SineWavePlotter.java
 * Run:      java SineWavePlotter
 */
public class SineWavePlotter extends JFrame {

    private final SineWavePanel sinePanel;
    private final JLabel freqLabel;

    public SineWavePlotter() {
        super("Sine Wave Plotter");
        setDefaultCloseOperation(JFrame.EXIT_ON_CLOSE);
        setLayout(new BorderLayout());

        // ---- Plot area ----
        sinePanel = new SineWavePanel();
        sinePanel.setPreferredSize(new Dimension(800, 420));
        add(sinePanel, BorderLayout.CENTER);

        // ---- Formula heading ----
        JLabel formula = new JLabel("y = sin(2\u03C0ft)   and   y = cos(2\u03C0ft)", SwingConstants.CENTER);
        formula.setFont(formula.getFont().deriveFont(Font.PLAIN, 16f));
        formula.setBorder(new EmptyBorder(10, 0, 0, 0));
        add(formula, BorderLayout.NORTH);

        // ---- Controls: slider + live value label ----
        JPanel controls = new JPanel();
        controls.setLayout(new BoxLayout(controls, BoxLayout.Y_AXIS));
        controls.setBorder(new EmptyBorder(5, 20, 15, 20));

        JSlider freqSlider = new JSlider(JSlider.HORIZONTAL, 0, 20, 2);
        freqSlider.setAlignmentX(Component.LEFT_ALIGNMENT);
        freqSlider.setMajorTickSpacing(5);
        freqSlider.setMinorTickSpacing(1);
        freqSlider.setPaintTicks(true);
        freqSlider.setPaintLabels(true);
        freqSlider.setSnapToTicks(true);

        freqLabel = new JLabel("Frequency: " + freqSlider.getValue() + " Hz");
        freqLabel.setFont(freqLabel.getFont().deriveFont(Font.BOLD, 14f));
        freqLabel.setAlignmentX(Component.LEFT_ALIGNMENT);
        updateTitle(freqSlider.getValue());

        // Every slider move updates the wave, the live label, and the window title
        freqSlider.addChangeListener(e -> {
            int freq = freqSlider.getValue();
            sinePanel.setFrequency(freq);
            freqLabel.setText("Frequency: " + freq + " Hz");
            updateTitle(freq);
        });

        controls.add(freqLabel);
        controls.add(Box.createVerticalStrut(6));
        controls.add(freqSlider);
        add(controls, BorderLayout.SOUTH);

        pack();
        setLocationRelativeTo(null);
    }

    /** Keeps the window title in sync with the current frequency. */
    private void updateTitle(int freq) {
        setTitle("Sine Wave Plotter \u2014 " + freq + " Hz");
    }

    public static void main(String[] args) {
        SwingUtilities.invokeLater(() -> new SineWavePlotter().setVisible(true));
    }

    /** Draws y = A * sin(2*PI*f*t) for the panel's current frequency. */
    private static class SineWavePanel extends JPanel {
        private double frequency = 2.0;       // Hz, updated live by the slider
        private final double amplitude = 1.0; // fixed for this example
        private final double duration = 2.0;  // seconds shown across the x-axis

        SineWavePanel() {
            setBackground(Color.WHITE);
        }

        void setFrequency(double frequency) {
            this.frequency = frequency;
            repaint();
        }

        @Override
        protected void paintComponent(Graphics g) {
            super.paintComponent(g);
            Graphics2D g2 = (Graphics2D) g;
            g2.setRenderingHint(RenderingHints.KEY_ANTIALIASING, RenderingHints.VALUE_ANTIALIAS_ON);

            int margin = 55;
            int w = getWidth();
            int h = getHeight();
            int plotWidth = w - 2 * margin;
            int halfHeight = (h - 2 * margin) / 2;
            int originX = margin;
            int originY = h / 2;

            drawGrid(g2, originX, originY, plotWidth, halfHeight, w, margin);
            drawSineLine(g2, originX, originY, plotWidth, halfHeight);
            drawCosineDots(g2, originX, originY, plotWidth, halfHeight);
            drawLegend(g2, w, margin);
        }

        private void drawGrid(Graphics2D g2, int originX, int originY, int plotWidth,
                               int halfHeight, int w, int margin) {
            g2.setFont(g2.getFont().deriveFont(11f));

            // +A / -A reference lines
            g2.setColor(new Color(210, 210, 210));
            g2.drawLine(originX, originY - halfHeight, w - margin, originY - halfHeight);
            g2.drawLine(originX, originY + halfHeight, w - margin, originY + halfHeight);

            // Vertical gridlines
            int divisions = 8;
            for (int i = 0; i <= divisions; i++) {
                int x = originX + i * plotWidth / divisions;
                g2.drawLine(x, originY - halfHeight, x, originY + halfHeight);
            }

            // Axes
            g2.setColor(Color.DARK_GRAY);
            g2.drawLine(originX, originY, w - margin, originY);
            g2.drawLine(originX, originY - halfHeight - 15, originX, originY + halfHeight + 15);

            // Labels
            g2.drawString("+A", originX - 32, originY - halfHeight + 4);
            g2.drawString("-A", originX - 32, originY + halfHeight + 4);
            g2.drawString("0", originX - 15, originY + 4);
            for (int i = 0; i <= divisions; i++) {
                double t = duration * i / divisions;
                int x = originX + i * plotWidth / divisions;
                g2.drawString(String.format("%.2f", t), x - 10, originY + halfHeight + 30);
            }
            g2.drawString("t (seconds)", w - margin - 55, originY + halfHeight + 50);
        }

        private void drawSineLine(Graphics2D g2, int originX, int originY, int plotWidth, int halfHeight) {
            Path2D path = new Path2D.Double();
            int steps = Math.max(plotWidth, 400);

            for (int i = 0; i <= steps; i++) {
                double t = duration * i / steps;
                double y = amplitude * Math.sin(2 * Math.PI * frequency * t);

                double px = originX + (t / duration) * plotWidth;
                double py = originY - (y / amplitude) * halfHeight;

                if (i == 0) path.moveTo(px, py);
                else path.lineTo(px, py);
            }

            g2.setColor(new Color(25, 100, 220));
            g2.setStroke(new BasicStroke(2.4f));
            g2.draw(path);
        }

        /** Plots y = A * cos(2*PI*f*t) as discrete dots -- no connecting line. */
        private void drawCosineDots(Graphics2D g2, int originX, int originY, int plotWidth, int halfHeight) {
            int dotSpacingPx = 10;
            int dotCount = Math.max(plotWidth / dotSpacingPx, 20);
            double dotRadius = 2.8;

            g2.setColor(new Color(220, 90, 30));
            for (int i = 0; i <= dotCount; i++) {
                double t = duration * i / dotCount;
                double y = amplitude * Math.cos(2 * Math.PI * frequency * t);

                double px = originX + (t / duration) * plotWidth;
                double py = originY - (y / amplitude) * halfHeight;

                g2.fill(new Ellipse2D.Double(px - dotRadius, py - dotRadius, dotRadius * 2, dotRadius * 2));
            }
        }

        /** Small color-coded key so sin (line) and cos (dots) are easy to tell apart. */
        private void drawLegend(Graphics2D g2, int w, int margin) {
            int x = w - margin - 130;
            int y = margin - 32;

            g2.setFont(g2.getFont().deriveFont(12f));

            g2.setColor(new Color(25, 100, 220));
            g2.setStroke(new BasicStroke(2.4f));
            g2.drawLine(x, y, x + 22, y);
            g2.setColor(Color.DARK_GRAY);
            g2.drawString("sin(2\u03C0ft)", x + 28, y + 4);

            int dotY = y + 18;
            g2.setColor(new Color(220, 90, 30));
            g2.fill(new Ellipse2D.Double(x + 3, dotY - 2.8, 5.6, 5.6));
            g2.fill(new Ellipse2D.Double(x + 15, dotY - 2.8, 5.6, 5.6));
            g2.setColor(Color.DARK_GRAY);
            g2.drawString("cos(2\u03C0ft)", x + 28, dotY + 4);
        }
    }
}
