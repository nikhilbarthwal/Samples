namespace SinCurvePlotter

open System
open System.Globalization
open Avalonia
open Avalonia.Controls
open Avalonia.Media

/// <summary>
/// Custom control that renders the sin curve using Avalonia's built-in drawing API.
/// Works cross-platform on Linux, macOS, and Windows.
/// </summary>
type SinPlotControl() =
    inherit Control()

    // Frequency property  changing it triggers a redraw
    static let frequencyProperty =
        AvaloniaProperty.Register<SinPlotControl, float>("Frequency", defaultValue = 1.0)

    static do
        // Redraw whenever Frequency changes
        // AddClassHandler already calls InvalidateVisual on every change, so the
        // frequency property fully drives redraws. (The C# original also called the
        // protected static Visual.AffectsRender here, but F# compiles `static do` into
        // separate startup code that cannot access that protected member  it throws
        // MethodAccessException at runtime  and it would be redundant anyway.)
        frequencyProperty.Changed.AddClassHandler<SinPlotControl, float>(fun c _ -> c.InvalidateVisual())
        |> ignore

    static member FrequencyProperty = frequencyProperty

    member this.Frequency
        with get () : float = this.GetValue(frequencyProperty)
        and set (value: float) = this.SetValue(frequencyProperty, value) |> ignore

    override this.Render(ctx: DrawingContext) =
        let bounds = this.Bounds
        let w = bounds.Width
        let h = bounds.Height

        let marginLeft   = 58.0
        let marginRight  = 20.0
        let marginTop    = 24.0
        let marginBottom = 38.0

        let plotW = w - marginLeft - marginRight
        let plotH = h - marginTop - marginBottom

        if w >= 1.0 && h >= 1.0 && plotW >= 1.0 && plotH >= 1.0 then
            //  Background
            ctx.DrawRectangle(
                SolidColorBrush(Color.FromRgb(24uy, 24uy, 40uy)),
                (null: IPen | null),
                Rect(0.0, 0.0, w, h))

            //  Grid
            let gridPen =
                Pen(
                    SolidColorBrush(Color.FromArgb(80uy, 60uy, 60uy, 100uy)),
                    1.0,
                    dashStyle = DashStyle([| 4.0; 4.0 |], 0.0))

            for i in 0..5 do
                let y = marginTop + float i * plotH / 5.0
                ctx.DrawLine(gridPen, Point(marginLeft, y), Point(marginLeft + plotW, y))

            for i in 0..8 do
                let x = marginLeft + float i * plotW / 8.0
                ctx.DrawLine(gridPen, Point(x, marginTop), Point(x, marginTop + plotH))

            //  Axes
            let axisPen = Pen(SolidColorBrush(Color.FromArgb(200uy, 90uy, 90uy, 140uy)), 1.5)
            let midY = marginTop + plotH / 2.0
            ctx.DrawLine(axisPen, Point(marginLeft, midY), Point(marginLeft + plotW, midY))
            ctx.DrawLine(axisPen, Point(marginLeft, marginTop), Point(marginLeft, marginTop + plotH))

            //  Y-axis labels
            let labelBrush = SolidColorBrush(Color.FromArgb(200uy, 140uy, 140uy, 180uy))
            let labelTypeface = Typeface("Monospace")
            let fontSize = 11.0

            SinPlotControl.DrawLabel(ctx, "+1.0", marginLeft - 6.0, marginTop,         labelBrush, labelTypeface, fontSize, true)
            SinPlotControl.DrawLabel(ctx, " 0.0", marginLeft - 6.0, midY,              labelBrush, labelTypeface, fontSize, true)
            SinPlotControl.DrawLabel(ctx, "-1.0", marginLeft - 6.0, marginTop + plotH, labelBrush, labelTypeface, fontSize, true)

            // X label
            SinPlotControl.DrawLabel(ctx, "Time ", marginLeft + plotW - 50.0, marginTop + plotH + 20.0,
                labelBrush, labelTypeface, fontSize, false)

            //  Sin curve
            let steps = int (plotW * 2.0)
            if steps >= 2 then
                let glowGeometry  = this.BuildCurveGeometry(steps, plotW, plotH, marginLeft, marginTop)
                let curveGeometry = this.BuildCurveGeometry(steps, plotW, plotH, marginLeft, marginTop)

                // Glow layer
                ctx.DrawGeometry(
                    (null: IBrush | null),
                    Pen(SolidColorBrush(Color.FromArgb(50uy, 80uy, 160uy, 255uy)), 8.0),
                    glowGeometry)

                // Main curve
                ctx.DrawGeometry(
                    (null: IBrush | null),
                    Pen(SolidColorBrush(Color.FromRgb(100uy, 180uy, 255uy)), 2.5),
                    curveGeometry)

                //  Plot border
                ctx.DrawRectangle(
                    (null: IBrush | null),
                    Pen(SolidColorBrush(Color.FromArgb(120uy, 70uy, 70uy, 110uy)), 1.0),
                    Rect(marginLeft, marginTop, plotW, plotH))

                //  Formula overlay
                let accentBrush = SolidColorBrush(Color.FromArgb(210uy, 100uy, 170uy, 230uy))
                SinPlotControl.DrawLabel(
                    ctx,
                    $"f = {this.Frequency:F1} Hz    y = sin({this.Frequency:F1}  t)",
                    marginLeft + 10.0, marginTop + 8.0,
                    accentBrush, labelTypeface, 11.5, false)

    member private this.BuildCurveGeometry
        (steps: int, plotW: float, plotH: float, marginLeft: float, marginTop: float) : StreamGeometry =
        let geo = StreamGeometry()
        use ctx2 = geo.Open()

        let mutable first = true
        for i in 0 .. steps - 1 do
            let t    = float i / float steps
            let xVal = t * 2.0 * Math.PI * 2.0          // 2 full base cycles
            let yVal = Math.Sin(this.Frequency * xVal)

            let px = marginLeft + t * plotW
            let py = marginTop  + (1.0 - yVal) / 2.0 * plotH

            let pt = Point(px, py)
            if first then
                ctx2.BeginFigure(pt, false)
                first <- false
            else
                ctx2.LineTo(pt)
        geo

    static member private DrawLabel
        (ctx: DrawingContext, text: string, x: float, y: float,
         brush: IBrush, typeface: Typeface, size: float, right: bool) =
        let ft =
            FormattedText(
                text, CultureInfo.CurrentCulture,
                FlowDirection.LeftToRight, typeface, size, brush)
        let drawX = if right then x - ft.Width else x
        ctx.DrawText(ft, Point(drawX, y - ft.Height / 2.0))
