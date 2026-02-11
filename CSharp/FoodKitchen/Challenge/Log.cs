namespace Challenge;

using System;
using System.Diagnostics;


/// <summary>
/// A static thread safe logging class.
/// </summary>
static class Log
{
    /// <summary>
    /// Static constructor that configire trace listener to console output.
    /// </summary>
    static Log()
    {
        Trace.Listeners.Add(new ConsoleTraceListener(true));
    }

    /// <summary>
    /// Private method to print the message and add timestamp to it.
    /// </summary>
    /// <param name="header">Type of Log message: Info or Error</param>
    /// <param name="tag">Module name from where the message originates</param>
    /// <param name="message">The payload that needs to be printed.</param>
    private static void Print(string header, string tag, string message)
    {
        var timestamp = System.DateTime.Now.ToString("yyyy-MM-dd HH:mm:ss.fff");
        Trace.WriteLine($"[{timestamp}] {header} {tag}: {message}");
    }

    /// <summary>
    /// Public method to print the Error message.
    /// </summary>
    /// <param name="tag">Module name from where the message originates</param>
    /// <param name="message">The payload that needs to be printed.</param>
    public static void Error(string tag, string message)
    {
        Print("ERROR", tag, message);
    }

    /// <summary>
    /// Public method to print the Info message.
    /// </summary>
    /// <param name="tag">Module name from where the message originates</param>
    /// <param name="message">The payload that needs to be printed.</param>
    public static void Info(string tag, string message)
    {
        Print("INFO", tag, message);
    }

    /// <summary>
    /// Static method for DateTime formatter.Added for consistency in printing datetime values.
    /// </summary>
    /// <param name="timestamp">Timestamp that needs to be converted into string</param>
    public static string DateTime(DateTime timestamp) => timestamp.ToString("F");
}
