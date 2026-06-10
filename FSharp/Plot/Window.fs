namespace SinCurvePlotter

open Avalonia
open Avalonia.Controls
open Avalonia.Layout
open Avalonia.Media

/// A standalone plotter window. Each instance owns its own plot control,
/// slider, and label, so multiple windows run fully independently.
type MainWindow(windowTitle: string, initialValue: float) as this =
    inherit Window()

    //  Plot control
    let plot =
        SinPlotControl(
            Frequency = initialValue / 10.0,
            Margin = Thickness(20.0, 8.0, 20.0, 0.0))

    let freqLabel =
        TextBlock(
            Text = $"{initialValue / 10.0:F1} Hz",
            Foreground = SolidColorBrush(Color.FromRgb(130uy, 200uy, 255uy)),
            FontSize = 12.0,
            FontWeight = FontWeight.SemiBold,
            Width = 58.0,
            VerticalAlignment = VerticalAlignment.Center)

    let slider =
        Slider(
            Minimum = 1.0,
            Maximum = 100.0,
            Value = initialValue,
            TickFrequency = 10.0,
            IsSnapToTickEnabled = false,
            Foreground = SolidColorBrush(Color.FromRgb(100uy, 180uy, 255uy)),
            VerticalAlignment = VerticalAlignment.Center,
            HorizontalAlignment = HorizontalAlignment.Stretch,
            Margin = Thickness(0.0, 0.0, 20.0, 0.0))

    do
        this.Title      <- windowTitle
        this.Width      <- 820.0
        this.Height     <- 560.0
        this.MinWidth   <- 600.0
        this.MinHeight  <- 440.0
        this.Background <- SolidColorBrush(Color.FromRgb(18uy, 18uy, 30uy))

        //  Title
        let title =
            TextBlock(
                Text = windowTitle,
                FontSize = 15.0,
                FontWeight = FontWeight.SemiBold,
                Foreground = SolidColorBrush(Color.FromRgb(130uy, 200uy, 255uy)),
                Margin = Thickness(20.0, 12.0, 0.0, 0.0))

        //  Bottom bar
        let freqText =
            TextBlock(
                Text = "Frequency:",
                Foreground = SolidColorBrush(Color.FromArgb(220uy, 180uy, 180uy, 210uy)),
                FontSize = 12.0,
                VerticalAlignment = VerticalAlignment.Center,
                Margin = Thickness(20.0, 0.0, 8.0, 0.0))

        slider.PropertyChanged.Add(this.SliderChanged)

        let controlRow =
            Grid(
                Background = SolidColorBrush(Color.FromRgb(28uy, 28uy, 46uy)),
                Height = 52.0,
                ColumnDefinitions = ColumnDefinitions("Auto,Auto,*"))

        Grid.SetColumn(freqText,  0)
        Grid.SetColumn(freqLabel, 1)
        Grid.SetColumn(slider,    2)

        controlRow.Children.Add(freqText)
        controlRow.Children.Add(freqLabel)
        controlRow.Children.Add(slider)

        //  Root layout
        let root = Grid(RowDefinitions = RowDefinitions("Auto,*,Auto"))

        Grid.SetRow(title,      0)
        Grid.SetRow(plot,       1)
        Grid.SetRow(controlRow, 2)

        root.Children.Add(title)
        root.Children.Add(plot)
        root.Children.Add(controlRow)

        this.Content <- root

    /// Parameterless constructor keeps the original default behaviour.
    new() = MainWindow("Sin Curve Plotter", 10.0)

    member private _.SliderChanged(e: AvaloniaPropertyChangedEventArgs) =
        if e.Property = Slider.ValueProperty then
            let freq = slider.Value / 10.0
            plot.Frequency <- freq
            freqLabel.Text <- $"{freq:F1} Hz"
