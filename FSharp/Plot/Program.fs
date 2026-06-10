namespace SinCurvePlotter

open System
open Avalonia
open Avalonia.Controls
open Avalonia.Controls.ApplicationLifetimes
open Avalonia.Themes.Fluent

type App() =
    inherit Application()

    override this.Initialize() =
        this.Styles.Add(FluentTheme())

    override this.OnFrameworkInitializationCompleted() =
        match this.ApplicationLifetime with
        | :? IClassicDesktopStyleApplicationLifetime as desktop ->
            // Keep the app alive until *every* window is closed, so the two
            // windows behave as independent peers rather than one owning the app.
            desktop.ShutdownMode <- ShutdownMode.OnLastWindowClose

            // Two independent windows, each with its own state and starting frequency.
            let window1 = MainWindow("Sin Curve Plotter  Window 1", 10.0)
            window1.Position <- PixelPoint(80, 80)

            let window2 = MainWindow("Sin Curve Plotter  Window 2", 30.0)
            window2.Position <- PixelPoint(140, 140)

            // The lifetime shows MainWindow automatically; show the second one explicitly.
            desktop.MainWindow <- window1
            window2.Show()
        | _ -> ()

        base.OnFrameworkInitializationCompleted()

module Program =

    let buildAvaloniaApp () =
        AppBuilder
            .Configure<App>()
            .UsePlatformDetect()
            .LogToTrace()

    [<EntryPoint; STAThread>]
    let main argv =
        buildAvaloniaApp().StartWithClassicDesktopLifetime(argv)
