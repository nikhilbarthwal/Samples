open ScottPlot
open System

// Simple scatter plot example
let createSimpleScatterPlot () =
    // Create sample data
    let random = Random(42)
    let x = Array.init 50 (fun _ -> random.NextDouble() * 100.0)
    let y = Array.init 50 (fun _ -> random.NextDouble() * 100.0)
    
    // Create plot
    let myPlot = new Plot()
    
    // Add scatter plot
    let scatter = myPlot.Add.Scatter(x, y)
    scatter.MarkerSize <- 8.0f
    scatter.MarkerColor <- Colors.Blue
    scatter.LineWidth <- 0.0f // No connecting lines
    
    // Customize plot
    myPlot.Title("F# Scatter Plot Example") |> ignore
    myPlot.XLabel("X Values") |> ignore
    myPlot.YLabel("Y Values") |> ignore
    // myPlot.Grid.Enable() |> ignore
    
    // Save plot
    // myPlot.SavePng("fsharp_scatter.png", 800, 600)
    printfn "Scatter plot saved as fsharp_scatter.png"

// Multi-series scatter plot with functional style
let createMultiSeriesScatter () =
    let random = Random(42)
    
    // Generate data using F# functional constructs
    let generateData count offsetX offsetY =
        [| for _ in 1..count -> 
            (random.NextDouble() * 50.0 + offsetX, 
             random.NextDouble() * 50.0 + offsetY) |]
        |> Array.unzip
    
    let (x1, y1) = generateData 30 25.0 25.0
    let (x2, y2) = generateData 30 0.0 0.0
    
    let myPlot = Plot()
    
    // Add scatter series with pipeline operator
    let scatter1 = myPlot.Add.Scatter(x1, y1)
    scatter1.LegendText <- "Group A"
    scatter1.MarkerColor <- Colors.Red
    scatter1.MarkerSize <- 10.0f
    scatter1.LineWidth <- 0.0f
    
    let scatter2 = myPlot.Add.Scatter(x2, y2)
    scatter2.LegendText <- "Group B"
    scatter2.MarkerColor <- Colors.Green
    scatter2.MarkerSize <- 8.0f
    scatter2.LineWidth <- 0.0f
    
    // Configure plot using pipeline
    myPlot.Title("Multi-Series F# Scatter Plot") |> ignore
    myPlot.XLabel("X Axis") |> ignore
    myPlot.YLabel("Y Axis") |> ignore
    myPlot.ShowLegend() |> ignore
    // myPlot.Grid.Enable() |> ignore
    myPlot.Axes.SetLimits(0.0, 100.0, 0.0, 100.0) |> ignore
    
    // myPlot.SavePng("fsharp_multi_scatter.png", 800, 600)
    printfn "Multi-series scatter plot saved!"

// Mathematical function scatter plot
let createMathematicalScatter () =
    // Generate data with mathematical functions
    let x = [| for i in 0..100 -> float i * 0.1 |]
    let y1 = x |> Array.map (fun x -> sin(x) + Random().NextDouble() * 0.2 - 0.1)
    let y2 = x |> Array.map (fun x -> cos(x) + Random().NextDouble() * 0.2 - 0.1)
    
    let myPlot = new Plot()
    
    // Create scatter plots for noisy sin and cos functions
    let sinScatter = myPlot.Add.Scatter(x, y1)
    sinScatter.LegendText <- "Noisy Sin(x)"
    sinScatter.MarkerColor <- Colors.Blue
    sinScatter.MarkerSize <- 4.0f
    sinScatter.LineWidth <- 0.0f
    
    let cosScatter = myPlot.Add.Scatter(x, y2)
    cosScatter.LegendText <- "Noisy Cos(x)"
    cosScatter.MarkerColor <- Colors.Orange
    cosScatter.MarkerSize <- 4.0f
    cosScatter.LineWidth <- 0.0f
    
    myPlot.Title("Mathematical Functions with Noise") |> ignore
    myPlot.XLabel("X") |> ignore
    myPlot.YLabel("Y") |> ignore
    myPlot.ShowLegend() |> ignore
    // myPlot.Grid.Enable() |> ignore
    
    // myPlot.SavePng("fsharp_math_scatter.png", 800, 600)
    printfn "Mathematical scatter plot saved!"

// Record type for structured data plotting
type DataPoint = { X: float; Y: float; Category: string }

let createCategoricalScatter () =
    let random = Random(42)
    
    // Create sample data with categories
    let data = 
        [
            for i in 1..20 do
                yield { X = random.NextDouble() * 40.0 + 10.0
                        Y = random.NextDouble() * 40.0 + 10.0
                        Category = "Category A" }
            for i in 1..20 do
                yield { X = random.NextDouble() * 40.0 + 50.0
                        Y = random.NextDouble() * 40.0 + 50.0
                        Category = "Category B" }
        ]
    
    // Group by category and plot
    let myPlot = new Plot()
    
    data 
    |> List.groupBy (fun d -> d.Category)
    |> List.iteri (fun i (category, points) ->
        let x = points |> List.map (fun p -> p.X) |> List.toArray
        let y = points |> List.map (fun p -> p.Y) |> List.toArray
        
        let scatter = myPlot.Add.Scatter(x, y)
        scatter.LegendText <- category
        scatter.MarkerSize <- 8.0f
        scatter.LineWidth <- 0.0f
        scatter.MarkerColor <- if i = 0 then Colors.Purple else Colors.Teal
    )
    
    myPlot.Title("Categorical Scatter Plot") |> ignore
    myPlot.XLabel("X Values") |> ignore
    myPlot.YLabel("Y Values") |> ignore
    myPlot.ShowLegend() |> ignore
    // myPlot.Grid.Enable() |> ignore
    
    // myPlot.SavePng("fsharp_categorical_scatter.png", 800, 600)
    printfn "Categorical scatter plot saved!"

// Main execution
[<EntryPoint>]
let main argv =
    printfn "Creating F# scatter plots with ScottPlot..."
    
    createSimpleScatterPlot()
    createMultiSeriesScatter()
    createMathematicalScatter()
    createCategoricalScatter()
    
    printfn "All plots created successfully!"
    0

(* For GUI applications in F#:

// Windows Forms example
open ScottPlot.WinForms
open System.Windows.Forms

let createWinFormsPlot () =
    let form = new Form(Text = "F# ScottPlot", Width = 800, Height = 600)
    let formsPlot = new FormsPlot(Dock = DockStyle.Fill)
    
    // Add sample data
    let x = [| 1.0; 2.0; 3.0; 4.0; 5.0 |]
    let y = [| 2.0; 4.0; 3.0; 8.0; 6.0 |]
    
    formsPlot.Plot.Add.Scatter(x, y) |> ignore
    formsPlot.Plot.Title("Interactive F# Scatter Plot") |> ignore
    formsPlot.Refresh()
    
    form.Controls.Add(formsPlot)
    form.ShowDialog() |> ignore

*)
