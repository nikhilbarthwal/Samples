module GraphPlot.Program

open System
open Avalonia
open Avalonia.Controls
open Avalonia.Controls.ApplicationLifetimes
open Avalonia.Controls.Primitives   // RangeBase
open Avalonia.Layout
open Avalonia.Media                  // Brushes
open Avalonia.Themes.Fluent
open ScottPlot.Avalonia              // AvaPlot

// ---------------------------------------------------------------------------
// Domain types. Colors are ScottPlot.Color, since ScottPlot renders the plot.
// Build them with ScottPlot.Colors.<Name> or ScottPlot.Color(r, g, b, a).
// If your real data uses System.Drawing.Color or Avalonia.Media.Color, convert
// when constructing a GraphSegment: ScottPlot.Color(c.R, c.G, c.B, c.A).
// (Keeping a single, fully-qualified color type avoids the name clash between
//  System.Drawing.Color / Avalonia.Media.Color / ScottPlot.Color.)
// ---------------------------------------------------------------------------
type Point = { x: float; y: float }

type GraphSegment =
    { Scatter: bool
      Color: ScottPlot.Color
      Points: Map<int, Point list> }

type Graph =
    { xStart: int64
      xEnd: int64
      yStart: float
      yEnd: float
      pMax: int
      Title: int -> string
      Elements: GraphSegment list }

// ---------------------------------------------------------------------------
// The window: a ScottPlot canvas that fills the space, with a p-slider docked
// underneath. Moving the slider redraws the plot for that value of p.
// ---------------------------------------------------------------------------
let private buildWindow (graph: Graph) : Window =
    let avaPlot = AvaPlot()
    let plot = avaPlot.Plot

    // Dark theme. These live on the Plot (not the plottables), so they survive
    // Plot.Clear() and only need to be set once.
    plot.FigureBackground.Color <- ScottPlot.Colors.Black
    plot.DataBackground.Color <- ScottPlot.Colors.Black
    plot.Axes.Color(ScottPlot.Colors.White)                       // frame, ticks, tick labels
    plot.Grid.MajorLineColor <- ScottPlot.Color(60uy, 60uy, 60uy, 255uy)
    // plot.HideGrid()
    plot.Axes.Title.Label.ForeColor <- ScottPlot.Colors.White

    let applyLimits () =
        plot.Axes.SetLimits(float graph.xStart, float graph.xEnd, graph.yStart, graph.yEnd)

    // Redraw everything for a given p.
    let render (p: int) =
        plot.Clear()

        for seg in graph.Elements do
            let pts = seg.Points |> Map.tryFind p |> Option.defaultValue []
            if not (List.isEmpty pts) then
                let xs = pts |> List.map (fun pt -> pt.x) |> List.toArray
                let ys = pts |> List.map (fun pt -> pt.y) |> List.toArray
                let s = plot.Add.Scatter(xs, ys)
                s.Color <- seg.Color
                if seg.Scatter then
                    s.LineWidth <- 0.0f       // markers only
                    s.MarkerSize <- 6.0f
                else
                    s.LineWidth <- 2.0f       // line only
                    s.MarkerSize <- 0.0f

        applyLimits ()                        // keep the axes fixed so the view doesn't jump
        plot.Title(graph.Title p)
        avaPlot.Refresh()

    // Slider (snaps to whole numbers 0..pMax) plus a "p = N" readout.
    let slider =
        Slider(
            Minimum = 0.0,
            Maximum = float graph.pMax,
            Value = 0.0,
            TickFrequency = 1.0,
            IsSnapToTickEnabled = true,
            SmallChange = 1.0,
            LargeChange = 1.0,
            MinWidth = 360.0,
            VerticalAlignment = VerticalAlignment.Center
        )

    let readout =
        TextBlock(
            Text = "p = 0",
            Foreground = Brushes.White,
            VerticalAlignment = VerticalAlignment.Center,
            Margin = Thickness(12.0, 0.0, 0.0, 0.0),
            MinWidth = 64.0
        )

    slider.PropertyChanged.Add(fun e ->
        // Avalonia properties are singletons, so reference equality is the check.
        if Object.ReferenceEquals(e.Property, RangeBase.ValueProperty) then
            let p = int (Math.Round slider.Value)
            readout.Text <- sprintf "p = %d" p
            render p)

    let controls =
        StackPanel(
            Orientation = Orientation.Horizontal,
            HorizontalAlignment = HorizontalAlignment.Center,
            Margin = Thickness(12.0)
        )
    controls.Children.Add(slider)
    controls.Children.Add(readout)

    let root = DockPanel()
    DockPanel.SetDock(controls, Dock.Bottom)
    root.Children.Add(controls)
    root.Children.Add(avaPlot)                // last child fills the remaining space

    let window =
        Window(
            Title = "Graph",
            Width = 900.0,
            Height = 600.0,
            Background = Brushes.Black,
            Content = root
        )

    // First draw once the control is attached and sized.
    window.Opened.Add(fun _ -> render 0)
    window

// ---------------------------------------------------------------------------
// Avalonia application host.
// ---------------------------------------------------------------------------
type App(graph: Graph) =
    inherit Application()

    override this.Initialize() =
        this.Styles.Add(FluentTheme())

    override this.OnFrameworkInitializationCompleted() =
        match this.ApplicationLifetime with
        | :? IClassicDesktopStyleApplicationLifetime as desktop ->
            desktop.MainWindow <- buildWindow graph
        | _ -> ()
        base.OnFrameworkInitializationCompleted()

/// Hand it a Graph and it opens a native window. Blocks until the window closes;
/// call it once as the app's entry point.
let plotGraph (graph: Graph) : unit =
    AppBuilder
        .Configure<App>(fun () -> App(graph))
        .UsePlatformDetect()
        .StartWithClassicDesktopLifetime([||])
    |> ignore

// ---------------------------------------------------------------------------
// Demo data so `dotnet run` shows something: a sine wave whose frequency grows
// with p (drawn as a line), plus an orange scatter overlay of the same curve.
// ---------------------------------------------------------------------------
let private twoPi = 2.0 * Math.PI

let demoGraph: Graph =
    let pMax = 10
    let makePoints1 sampleCount =
        [ for p in 0 .. pMax ->
              let freq = 1.0 + float p * 0.4
              p,
              [ for i in 0 .. sampleCount / 2 ->
                    let x = float i / float sampleCount * twoPi
                    { x = x; y = sin (freq * x) } ] ]
        |> Map.ofList

    let makePoints2 sampleCount =
        [ for p in 0 .. pMax ->
              let freq = 1.0 + float p * 0.4
              p,
              [ for i in 0 .. sampleCount ->
                    let x = float i / float sampleCount * twoPi
                    { x = x; y = cos (freq * x) } ] ]
        |> Map.ofList

    { xStart = 0L
      xEnd = 7L
      yStart = -1.2
      yEnd = 1.2
      pMax = pMax
      Title = fun p -> sprintf "Waveform at p = %d" p
      Elements =
        [ { Scatter = false; Color = ScottPlot.Color(0uy, 191uy, 255uy, 255uy); Points = makePoints1 200 }    // deep sky blue
          { Scatter = true;  Color = ScottPlot.Color(255uy, 165uy, 0uy, 255uy); Points = makePoints2 20 } ] }  // orange

[<EntryPoint; STAThread>]
let main _argv =
    plotGraph demoGraph
    0
