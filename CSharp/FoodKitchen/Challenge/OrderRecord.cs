using System;
using System.Diagnostics;

namespace Challenge;

/// <summary>
/// An internal record keeper for Order, where Expiry date can be adjusted.
/// </summary>
class OrderRecord(Order order, DateTime orderTime)
{
    public string Id { get; } = order.Id;
    public string Name { get; } = order.Name;
    public string Destination { get; } =
        order.Temp switch
        {
            "hot" => Action.Heater,
            "cold" => Action.Cooler,
            "room" => Action.Shelf,
            _ => throw new Exception("Unknown temperature")
        };

    public long Price { get; } = order.Price;
    public DateTime OrderTime { get; } = orderTime;
    public DateTime Expiry { get; private set; } = orderTime + TimeSpan.FromSeconds(order.Freshness);

    /// <summary>
    /// Get the factors for expiry rate adjustments based on state transition.
    /// </summary>
    /// <param name="sourceTemp">Source destination from where transition is made.</param>
    /// <param name="destinationTemp">Target destination to where transition is made.</param>
    private (int factorNum, int factorDenum) GetFactors(string sourceTemp, string destinationTemp)
    {
        if (sourceTemp == Destination && destinationTemp == Action.Shelf)
            return (1, 2);

        if (sourceTemp == Action.Shelf && destinationTemp == Destination)
            return (2, 1);

        if (sourceTemp == Destination && destinationTemp == Destination)
            return (1, 1);

        if (sourceTemp == destinationTemp && destinationTemp != Destination)
            return (1, 2);

        Debug.Assert(true, "Illegal transition of state");
        return (-1, -1);
    }

    /// <summary>
    /// Adjust the expiry for state transition.
    /// </summary>
    /// <param name="sourceTemp">Source destination from where transition is made.</param>
    /// <param name="destinationTemp">Target destination to where transition is made.</param>
    public void AdjustExpiry(string sourceTemp, string destinationTemp)
    {
        var original = Log.DateTime(Expiry);
        (int factorNum, int factorDenum) = GetFactors(sourceTemp, destinationTemp);
        var now = DateTime.Now;
        Debug.Assert(now >= OrderTime);
        Debug.Assert(Expiry >= now);
        var usedTime = now - OrderTime;
        var unusedTime = Expiry - now;
        Expiry = OrderTime + usedTime + factorNum * unusedTime/factorDenum;
        Log.Info("Order Record", $"Adjusting Expiry for order = {order.Id} from {original} to {Log.DateTime(Expiry)}");
    }
}
