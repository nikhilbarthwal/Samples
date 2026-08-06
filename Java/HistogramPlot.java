import javax.swing.*;
import javax.swing.border.EmptyBorder;
import java.awt.*;
import java.awt.geom.Rectangle2D;
import java.awt.event.MouseAdapter;
import java.awt.event.MouseEvent;
import java.awt.event.WindowEvent;
import java.util.Random;

/**
 * A complete, self-contained Swing application that draws a histogram
 * comparing two randomly generated, normally-distributed datasets --
 * each bin shows two bars side by side, one per group.
 *
 * - "Regenerate Data" draws fresh random samples for both groups.
 * - Bin count is fixed at 20 (see BIN_COUNT in HistogramPanel).
 *
 * Compile:  javac HistogramPlotter.java
 * Run:      java HistogramPlotter
 */
public class HistogramPlotter extends JFrame {

    private static final int SAMPLE_COUNT = 2000;

    /** One dataset's generation parameters and display color. */
    private record SeriesConfig(String label, double mean, double stdDev, Color color) {}

    private static final SeriesConfig[] SERIES = {
            new SeriesConfig("Group A", 45, 12, new Color(60, 130, 200)),
            new SeriesConfig("Group B", 62, 10, new Color(220, 90, 30)),
    };

    private final HistogramPanel histPanel;

    public HistogramPlotter() {
        super("Histogram Plotter");
        setUndecorated(true);   // drop the OS title bar so we can draw our own, centered one
        setResizable(false);    // undecorated frames lose the native resize handles anyway
        setDefaultCloseOperation(JFrame.EXIT_ON_CLOSE);
        setLayout(new BorderLayout());

        // ---- Plot area ----
        histPanel = new HistogramPanel();
        histPanel.setPreferredSize(new Dimension(800, 420));
        add(histPanel, BorderLayout.CENTER);

        // ---- Heading ----
        JLabel heading = new JLabel(
                "Histogram of " + SAMPLE_COUNT + " samples each \u2014 "
                        + SERIES[0].label() + " vs " + SERIES[1].label(),
                SwingConstants.CENTER);
        heading.setFont(heading.getFont().deriveFont(Font.PLAIN, 16f));
        heading.setBorder(new EmptyBorder(10, 0, 0, 0));

        // ---- Custom title bar (centers the title; a native one can't be recentered) ----
        JPanel topArea = new JPanel(new BorderLayout());
        topArea.add(new TitleBar("Histogram Plotter", this), BorderLayout.NORTH);
        topArea.add(heading, BorderLayout.SOUTH);
        add(topArea, BorderLayout.NORTH);

        // ---- Controls: regenerate button ----
        JPanel controls = new JPanel();
        controls.setLayout(new BoxLayout(controls, BoxLayout.Y_AXIS));
        controls.setBorder(new EmptyBorder(5, 20, 15, 20));

        JButton regenerateButton = new JButton("Regenerate Data");
        regenerateButton.setAlignmentX(Component.LEFT_ALIGNMENT);
        regenerateButton.addActionListener(e -> histPanel.regenerateData());

        controls.add(regenerateButton);
        add(controls, BorderLayout.SOUTH);

        pack();
        setLocationRelativeTo(null);
    }

    public static void main(String[] args) {
        SwingUtilities.invokeLater(() -> new HistogramPlotter().setVisible(true));
    }

    /** Generates the random sample sets, bins them on shared edges, and paints grouped bars. */
    private static class HistogramPanel extends JPanel {
        private final Random random = new Random();
        private static final int BIN_COUNT = 20;

        private double[][] data;

        HistogramPanel() {
            setBackground(Color.WHITE);
            regenerateData();
        }

        void regenerateData() {
            data = new double[SERIES.length][SAMPLE_COUNT];
            for (int s = 0; s < SERIES.length; s++) {
                SeriesConfig cfg = SERIES[s];
                for (int i = 0; i < SAMPLE_COUNT; i++) {
                    data[s][i] = cfg.mean() + cfg.stdDev() * random.nextGaussian();
                }
            }
            repaint();
        }

        @Override
        protected void paintComponent(Graphics g) {
            super.paintComponent(g);
            Graphics2D g2 = (Graphics2D) g;
            g2.setRenderingHint(RenderingHints.KEY_ANTIALIASING, RenderingHints.VALUE_ANTIALIAS_ON);

            int[][] counts = countPerBin(data, BIN_COUNT);
            int maxCount = 1;
            for (int[] series : counts) {
                for (int c : series) maxCount = Math.max(maxCount, c);
            }

            int margin = 55;
            int originX = margin;
            int originY = getHeight() - margin;
            int plotWidth = getWidth() - 2 * margin;
            int plotHeight = getHeight() - 2 * margin;

            drawAxes(g2, originX, originY, plotWidth, plotHeight, maxCount);
            drawBars(g2, originX, originY, plotWidth, plotHeight, counts, maxCount);
            drawLegend(g2, originX + plotWidth, margin);
        }

        /** Bins every series on the SAME edges (combined min/max) so the groups line up and compare fairly. */
        private int[][] countPerBin(double[][] series, int bins) {
            double min = Double.POSITIVE_INFINITY;
            double max = Double.NEGATIVE_INFINITY;
            for (double[] values : series) {
                for (double v : values) {
                    min = Math.min(min, v);
                    max = Math.max(max, v);
                }
            }
            double range = Math.max(max - min, 1e-9);

            int[][] counts = new int[series.length][bins];
            for (int s = 0; s < series.length; s++) {
                for (double v : series[s]) {
                    int idx = (int) ((v - min) / range * bins);
                    if (idx >= bins) idx = bins - 1;
                    if (idx < 0) idx = 0;
                    counts[s][idx]++;
                }
            }
            return counts;
        }

        private void drawAxes(Graphics2D g2, int originX, int originY, int plotWidth, int plotHeight, int maxCount) {
            int rightEdge = originX + plotWidth;
            int topEdge = originY - plotHeight;
            g2.setFont(g2.getFont().deriveFont(11f));

            int gridLines = 4;
            for (int i = 0; i <= gridLines; i++) {
                int y = originY - i * plotHeight / gridLines;
                int value = maxCount * i / gridLines;
                g2.setColor(new Color(228, 228, 228));
                g2.drawLine(originX, y, rightEdge, y);
                g2.setColor(Color.DARK_GRAY);
                g2.drawString(String.valueOf(value), originX - 34, y + 4);
            }

            g2.setColor(Color.DARK_GRAY);
            g2.drawLine(originX, originY, rightEdge, originY);
            g2.drawLine(originX, originY, originX, topEdge - 10);

            g2.drawString("frequency", originX - 45, topEdge - 20);
            g2.drawString("value", rightEdge - 20, originY + 38);
        }

        /** Draws each bin as a cluster of side-by-side bars, one per series. */
        private void drawBars(Graphics2D g2, int originX, int originY, int plotWidth, int plotHeight,
                               int[][] counts, int maxCount) {
            int bins = counts[0].length;
            int numSeries = counts.length;
            double slot = (double) plotWidth / bins;
            double groupPadding = slot * 0.12;
            double barWidth = (slot - groupPadding) / numSeries;
            double innerGap = barWidth * 0.06;

            for (int i = 0; i < bins; i++) {
                for (int s = 0; s < numSeries; s++) {
                    double barHeight = (double) counts[s][i] / maxCount * plotHeight;
                    double x = originX + i * slot + groupPadding / 2 + s * barWidth;
                    double y = originY - barHeight;
                    double width = Math.max(barWidth - innerGap, 1);

                    Rectangle2D.Double bar = new Rectangle2D.Double(x, y, width, barHeight);
                    g2.setColor(SERIES[s].color());
                    g2.fill(bar);
                    g2.setColor(SERIES[s].color().darker());
                    g2.draw(bar);
                }
            }
        }

        private void drawLegend(Graphics2D g2, int rightEdge, int margin) {
            int x = rightEdge - 110;
            int y = margin - 32;
            g2.setFont(g2.getFont().deriveFont(12f));

            for (int s = 0; s < SERIES.length; s++) {
                int swatchY = y + s * 18;
                g2.setColor(SERIES[s].color());
                g2.fillRect(x, swatchY - 9, 14, 14);
                g2.setColor(Color.DARK_GRAY);
                g2.drawString(SERIES[s].label(), x + 20, swatchY + 2);
            }
        }
    }

    /**
     * A custom, draggable title bar used in place of the OS-drawn one, since a
     * native title bar's text position can't be controlled from Java. Requires
     * the frame to be constructed with setUndecorated(true).
     */
    private static class TitleBar extends JPanel {
        TitleBar(String title, JFrame frame) {
            setLayout(new BorderLayout());
            setBackground(new Color(45, 45, 48));
            setPreferredSize(new Dimension(0, 34));

            JLabel titleLabel = new JLabel(title, SwingConstants.CENTER);
            titleLabel.setForeground(Color.WHITE);
            titleLabel.setFont(titleLabel.getFont().deriveFont(Font.PLAIN, 13f));

            JButton minimizeBtn = makeButton("\u2013", new Color(80, 80, 84));
            JButton closeBtn = makeButton("\u00D7", new Color(196, 43, 28));
            minimizeBtn.addActionListener(e -> frame.setState(Frame.ICONIFIED));
            closeBtn.addActionListener(e -> frame.dispatchEvent(new WindowEvent(frame, WindowEvent.WINDOW_CLOSING)));

            JPanel buttons = new JPanel(new FlowLayout(FlowLayout.RIGHT, 0, 0));
            buttons.setOpaque(false);
            buttons.add(minimizeBtn);
            buttons.add(closeBtn);

            // Balances the button panel's width so the label centers on the true
            // middle of the window, not just the space left of the buttons
            JPanel spacer = new JPanel();
            spacer.setOpaque(false);
            spacer.setPreferredSize(new Dimension(88, 34));

            add(spacer, BorderLayout.WEST);
            add(titleLabel, BorderLayout.CENTER);
            add(buttons, BorderLayout.EAST);

            // Undecorated frames have no native title bar to drag, so this bar drags the window itself
            MouseAdapter drag = new MouseAdapter() {
                private Point start;

                @Override
                public void mousePressed(MouseEvent e) {
                    start = e.getPoint();
                }

                @Override
                public void mouseDragged(MouseEvent e) {
                    Point loc = frame.getLocation();
                    frame.setLocation(loc.x + e.getX() - start.x, loc.y + e.getY() - start.y);
                }
            };
            addMouseListener(drag);
            addMouseMotionListener(drag);
        }

        private JButton makeButton(String symbol, Color hoverColor) {
            JButton btn = new JButton(symbol) {
                @Override
                protected void paintComponent(Graphics g) {
                    if (getModel().isRollover()) {
                        g.setColor(hoverColor);
                        g.fillRect(0, 0, getWidth(), getHeight());
                    }
                    super.paintComponent(g);
                }
            };
            btn.setPreferredSize(new Dimension(44, 34));
            btn.setFont(btn.getFont().deriveFont(14f));
            btn.setForeground(Color.WHITE);
            btn.setFocusPainted(false);
            btn.setBorderPainted(false);
            btn.setContentAreaFilled(false);
            return btn;
        }
    }
}
