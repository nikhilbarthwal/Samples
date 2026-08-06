import javax.swing.*;
import javax.swing.border.EmptyBorder;
import java.awt.*;
import java.awt.geom.Ellipse2D;
import java.awt.geom.Path2D;

/**
 * A complete, self-contained Swing application that plots
 *      y = sin(2 * PI * f * t)   (solid line)
 *      y = cos(2 * PI * f * t)   (dots)
 * at a fixed frequency (see FREQUENCY_HZ).
 *
 * Compile:  javac SineWavePlotter.java
 * Run:      java SineWavePlotter
 */
public class SineWavePlotter extends JFrame {

    private static final int FREQUENCY_HZ = 2; // fixed now that the slider is gone

    private final SineWavePanel sinePanel;

    public SineWavePlotter() {
        super("Sine Wave Plotter \u2014 " + FREQUENCY_HZ + " Hz");
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

        pack();
        setLocationRelativeTo(null);
    }

    public static void main(String[] args) {
        SwingUtilities.invokeLater(() -> new SineWavePlotter().setVisible(true));
    }

    /** Draws the sine and cosine curves at the fixed FREQUENCY_HZ. */
    private static class SineWavePanel extends JPanel {
        private final double amplitude = 1.0; // fixed for this example
        private final double duration = 2.0;  // seconds shown across the x-axis

        SineWavePanel() {
            setBackground(Color.WHITE);
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
                double y = amplitude * Math.sin(2 * Math.PI * FREQUENCY_HZ * t);

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
                double y = amplitude * Math.cos(2 * Math.PI * FREQUENCY_HZ * t);

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
