using Avalonia;
using Avalonia.Controls;
using Avalonia.Layout;
using Avalonia.Media;

namespace SinCurvePlotter;

public class MainWindow : Window
{
    private readonly SinPlotControl _plot;
    private readonly Slider         _slider;
    private readonly TextBlock      _freqLabel;

    public MainWindow()
    {
        Title        = "Sin Curve Plotter";
        Width        = 820;
        Height       = 560;
        MinWidth     = 600;
        MinHeight    = 440;
        Background   = new SolidColorBrush(Color.FromRgb(18, 18, 30));

        //  Title
        var title = new TextBlock
        {
            Text       = "Sin Curve Plotter",
            FontSize   = 15,
            FontWeight = FontWeight.SemiBold,
            Foreground = new SolidColorBrush(Color.FromRgb(130, 200, 255)),
            Margin     = new Thickness(20, 12, 0, 0)
        };

        //  Plot control
        _plot = new SinPlotControl
        {
            Frequency = 1.0,
            Margin    = new Thickness(20, 8, 20, 0),
            [Grid.RowProperty] = 1
        };

        //  Bottom bar
        var freqText = new TextBlock
        {
            Text       = "Frequency:",
            Foreground = new SolidColorBrush(Color.FromArgb(220, 180, 180, 210)),
            FontSize   = 12,
            VerticalAlignment = VerticalAlignment.Center,
            Margin     = new Thickness(20, 0, 8, 0)
        };

        _freqLabel = new TextBlock
        {
            Text       = "1.0 Hz",
            Foreground = new SolidColorBrush(Color.FromRgb(130, 200, 255)),
            FontSize   = 12,
            FontWeight = FontWeight.SemiBold,
            Width      = 58,
            VerticalAlignment = VerticalAlignment.Center
        };

        _slider = new Slider
        {
            Minimum      = 1,
            Maximum      = 100,
            Value        = 10,
            TickFrequency = 10,
            IsSnapToTickEnabled = false,
            Foreground   = new SolidColorBrush(Color.FromRgb(100, 180, 255)),
            VerticalAlignment = VerticalAlignment.Center,
            [Grid.ColumnProperty] = 2,
            HorizontalAlignment = HorizontalAlignment.Stretch,
            Margin = new Thickness(0, 0, 20, 0)
        };
        _slider.PropertyChanged += SliderChanged;

        var controlRow = new Grid
        {
            Background      = new SolidColorBrush(Color.FromRgb(28, 28, 46)),
            Height          = 52,
            ColumnDefinitions = new ColumnDefinitions("Auto,Auto,*"),
            [Grid.RowProperty] = 2
        };

        Grid.SetColumn(freqText,  0);
        Grid.SetColumn(_freqLabel, 1);
        Grid.SetColumn(_slider,   2);

        controlRow.Children.Add(freqText);
        controlRow.Children.Add(_freqLabel);
        controlRow.Children.Add(_slider);

        //  Root layout
        var root = new Grid
        {
            RowDefinitions = new RowDefinitions("Auto,*,Auto")
        };

        Grid.SetRow(title,      0);
        Grid.SetRow(_plot,      1);
        Grid.SetRow(controlRow, 2);

        root.Children.Add(title);
        root.Children.Add(_plot);
        root.Children.Add(controlRow);

        Content = root;
    }

    private void SliderChanged(object? sender, AvaloniaPropertyChangedEventArgs e)
    {
        if (e.Property != Slider.ValueProperty) return;
        double freq = _slider.Value / 10.0;
        _plot.Frequency = freq;
        _freqLabel.Text = $"{freq:F1} Hz";
    }
}
