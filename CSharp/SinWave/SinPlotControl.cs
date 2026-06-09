using System;
using Avalonia;
using Avalonia.Controls;
using Avalonia.Media;

namespace SinCurvePlotter;

/// <summary>
/// Custom control that renders the sin curve using Avalonia's built-in drawing API.
/// Works cross-platform on Linux, macOS, and Windows.
/// </summary>
public class SinPlotControl : Control
{
    // Frequency property  changing it triggers a redraw
    public static readonly StyledProperty<double> FrequencyProperty =
        AvaloniaProperty.Register<SinPlotControl, double>(nameof(Frequency), defaultValue: 1.0);

    public double Frequency
    {
        get => GetValue(FrequencyProperty);
        set => SetValue(FrequencyProperty, value);
    }

    static SinPlotControl()
    {
        // Redraw whenever Frequency changes
        FrequencyProperty.Changed.AddClassHandler<SinPlotControl>((c, _) => c.InvalidateVisual());
        AffectsRender<SinPlotControl>(FrequencyProperty);
    }

    public override void Render(DrawingContext ctx)
    {
        var bounds = Bounds;
        double w = bounds.Width;
        double h = bounds.Height;
        if (w < 1 || h < 1) return;

        const int marginLeft   = 58;
        const int marginRight  = 20;
        const int marginTop    = 24;
        const int marginBottom = 38;

        double plotW = w - marginLeft - marginRight;
        double plotH = h - marginTop - marginBottom;
        if (plotW < 1 || plotH < 1) return;

        //  Background
        ctx.DrawRectangle(new SolidColorBrush(Color.FromRgb(24, 24, 40)), null,
            new Rect(0, 0, w, h));

        //  Grid
        var gridPen = new Pen(new SolidColorBrush(Color.FromArgb(80, 60, 60, 100)), 1,
            dashStyle: new DashStyle(new double[] { 4, 4 }, 0));

        for (int i = 0; i <= 5; i++)
        {
            double y = marginTop + i * plotH / 5.0;
            ctx.DrawLine(gridPen, new Point(marginLeft, y), new Point(marginLeft + plotW, y));
        }
        for (int i = 0; i <= 8; i++)
        {
            double x = marginLeft + i * plotW / 8.0;
            ctx.DrawLine(gridPen, new Point(x, marginTop), new Point(x, marginTop + plotH));
        }

        //  Axes
        var axisPen = new Pen(new SolidColorBrush(Color.FromArgb(200, 90, 90, 140)), 1.5);
        double midY = marginTop + plotH / 2.0;
        ctx.DrawLine(axisPen, new Point(marginLeft, midY), new Point(marginLeft + plotW, midY));
        ctx.DrawLine(axisPen, new Point(marginLeft, marginTop), new Point(marginLeft, marginTop + plotH));

        //  Y-axis labels
        var labelBrush = new SolidColorBrush(Color.FromArgb(200, 140, 140, 180));
        var labelTypeface = new Typeface("Monospace");
        double fontSize = 11;

        DrawLabel(ctx, "+1.0", marginLeft - 6, marginTop,          labelBrush, labelTypeface, fontSize, right: true);
        DrawLabel(ctx, " 0.0", marginLeft - 6, midY,               labelBrush, labelTypeface, fontSize, right: true);
        DrawLabel(ctx, "-1.0", marginLeft - 6, marginTop + plotH,  labelBrush, labelTypeface, fontSize, right: true);

        // X label
        DrawLabel(ctx, "Time ", marginLeft + plotW - 50, marginTop + plotH + 20,
            labelBrush, labelTypeface, fontSize, right: false);

        //  Sin curve
        int steps = (int)(plotW * 2);
        if (steps < 2) return;

        var glowGeometry  = BuildCurveGeometry(steps, plotW, plotH, marginLeft, marginTop);
        var curveGeometry = BuildCurveGeometry(steps, plotW, plotH, marginLeft, marginTop);

        // Glow layer
        ctx.DrawGeometry(null,
            new Pen(new SolidColorBrush(Color.FromArgb(50, 80, 160, 255)), 8),
            glowGeometry);

        // Main curve
        ctx.DrawGeometry(null,
            new Pen(new SolidColorBrush(Color.FromRgb(100, 180, 255)), 2.5),
            curveGeometry);

        //  Plot border
        ctx.DrawRectangle(null,
            new Pen(new SolidColorBrush(Color.FromArgb(120, 70, 70, 110)), 1),
            new Rect(marginLeft, marginTop, plotW, plotH));

        //  Formula overlay
        var accentBrush = new SolidColorBrush(Color.FromArgb(210, 100, 170, 230));
        DrawLabel(ctx,
            $"f = {Frequency:F1} Hz    y = sin({Frequency:F1}  t)",
            marginLeft + 10, marginTop + 8,
            accentBrush, labelTypeface, 11.5, right: false);
    }

    private StreamGeometry BuildCurveGeometry(
        int steps, double plotW, double plotH, double marginLeft, double marginTop)
    {
        var geo = new StreamGeometry();
        using var ctx2 = geo.Open();

        bool first = true;
        for (int i = 0; i < steps; i++)
        {
            double t    = (double)i / steps;
            double xVal = t * 2 * Math.PI * 2;          // 2 full base cycles
            double yVal = Math.Sin(Frequency * xVal);

            double px = marginLeft + t * plotW;
            double py = marginTop  + (1.0 - yVal) / 2.0 * plotH;

            var pt = new Point(px, py);
            if (first) { ctx2.BeginFigure(pt, false); first = false; }
            else         ctx2.LineTo(pt);
        }
        return geo;
    }

    private static void DrawLabel(DrawingContext ctx, string text,
        double x, double y, IBrush brush, Typeface typeface, double size, bool right)
    {
        var ft = new FormattedText(text, System.Globalization.CultureInfo.CurrentCulture,
            FlowDirection.LeftToRight, typeface, size, brush);
        double drawX = right ? x - ft.Width : x;
        ctx.DrawText(ft, new Point(drawX, y - ft.Height / 2));
    }
}
